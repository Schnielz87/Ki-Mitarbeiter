"""Hybride Recherche: Volltext (BM25) + Vektoraehnlichkeit.

Die beiden Trefferlisten werden mit Reciprocal Rank Fusion (RRF) zusammen-
gefuehrt.  RRF braucht keine kalibrierten Scores und ist damit robust gegen
die sehr unterschiedlichen Wertebereiche von BM25 und Kosinusaehnlichkeit.

Zusaetzlich wirkt die Quellenhierarchie (Masterprompt 26): Treffer aus
Primaerquellen werden gegenueber Sekundaerquellen bevorzugt.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from ..db import Database
from ..logging_setup import get_logger
from .embeddings import EmbeddingProvider, cosine, pack_vector, unpack_vector

log = get_logger(__name__)

_WORD = re.compile(r"[\wäöüÄÖÜß§]+", re.UNICODE)

#: Sehr haeufige deutsche Woerter, die als alleinige Suchbegriffe nichts bringen.
STOPWORDS = {
    "der", "die", "das", "und", "oder", "ist", "sind", "ein", "eine", "einen",
    "einer", "eines", "dem", "den", "des", "mit", "von", "fuer", "für", "auf",
    "bei", "im", "in", "an", "zu", "zur", "zum", "als", "auch", "wird", "werden",
    "kann", "muss", "wie", "was", "wann", "wo", "warum", "nicht", "sich", "es",
    "wir", "ich", "sie", "man", "aber", "nur", "noch", "dass", "hat", "haben",
}


def fts_query(text: str, max_terms: int = 18) -> str:
    """Baut eine sichere FTS5-Abfrage: OR-verknuepfte Praefixterme."""
    words = [w.lower() for w in _WORD.findall(text or "")]
    terms: list[str] = []
    for word in words:
        if len(word) < 3 or word in STOPWORDS:
            continue
        cleaned = word.replace('"', "")
        if cleaned and cleaned not in terms:
            terms.append(cleaned)
    if not terms:
        terms = [w for w in words if len(w) > 1][:4]
    if not terms:
        return ""
    # Deutsche Wortbildung: "aufbewahren" soll auch "Aufbewahrungsfrist" finden.
    # Dafuer wird bei langen Woertern zusaetzlich ein gekuerzter Stamm gesucht.
    expanded: list[str] = []
    for term in terms[:max_terms]:
        expanded.append(term)
        if len(term) >= 9:
            stem = term[:7]
            if stem not in expanded:
                expanded.append(stem)
    return " OR ".join(f'"{t}"*' for t in expanded)


@dataclass
class Hit:
    """Ein Rechercheergebnis mit vollstaendigem Quellennachweis."""

    chunk_id: int
    doc_uid: str
    title: str
    citation: str
    heading: str
    text: str
    source_id: str
    url: str
    priority: int
    score: float
    origin: str = "knowledge"
    valid_from: str | None = None
    valid_to: str | None = None
    fetched_at: str | None = None
    lexical_rank: int | None = None
    vector_rank: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def reference(self) -> str:
        """Fundstellenbezeichnung ohne Dopplung von Zitat und Titel."""
        citation = (self.citation or "").strip()
        title = (self.title or "").strip()
        if citation and title:
            if title.lower() in citation.lower():
                return citation
            if citation.lower() in title.lower():
                return title
            return f"{citation} - {title}"
        return citation or title or self.doc_uid

    def excerpt(self, length: int = 320) -> str:
        text = " ".join(self.text.split())
        return text if len(text) <= length else text[: length - 1].rstrip() + "…"


def rrf_merge(
    ranked_lists: Sequence[Sequence[int]], k: int = 60, weights: Sequence[float] | None = None
) -> dict[int, float]:
    """Reciprocal Rank Fusion. Gibt {id: score} zurueck."""
    weights = list(weights or [1.0] * len(ranked_lists))
    scores: dict[int, float] = {}
    for list_index, ids in enumerate(ranked_lists):
        weight = weights[list_index] if list_index < len(weights) else 1.0
        for rank, identifier in enumerate(ids, start=1):
            scores[identifier] = scores.get(identifier, 0.0) + weight / (k + rank)
    return scores


class HybridSearcher:
    """Recherche ueber die Fachwissensdatenbank."""

    def __init__(
        self,
        db: Database,
        embedder: EmbeddingProvider | None = None,
        priority_boost: float = 0.004,
    ):
        self.db = db
        self.embedder = embedder
        self.priority_boost = float(priority_boost)

    # -- Einbettungen pflegen -----------------------------------------
    def index_embeddings(self, batch: int = 64, limit: int | None = None) -> int:
        """Berechnet fehlende Einbettungen. Gibt die Anzahl zurueck."""
        if self.embedder is None:
            return 0
        rows = self.db.query(
            "SELECT c.id, c.text, c.heading, c.citation FROM chunks c "
            "LEFT JOIN embeddings e ON e.chunk_id = c.id WHERE e.chunk_id IS NULL "
            "ORDER BY c.id" + (f" LIMIT {int(limit)}" if limit else "")
        )
        total = 0
        for start in range(0, len(rows), batch):
            block = rows[start:start + batch]
            texts = [
                " ".join(p for p in (r["citation"], r["heading"], r["text"]) if p)
                for r in block
            ]
            vectors = self.embedder.embed(texts)
            self.db.executemany(
                "INSERT OR REPLACE INTO embeddings (chunk_id, model, dim, norm, vector) "
                "VALUES (?,?,?,?,?)",
                [
                    (row["id"], self.embedder.name, len(vec), 1.0, pack_vector(vec))
                    for row, vec in zip(block, vectors)
                ],
            )
            total += len(block)
        if total:
            log.info("%s Einbettungen berechnet (%s)", total, self.embedder.name)
        return total

    def drop_embeddings(self) -> int:
        cur = self.db.execute("DELETE FROM embeddings")
        return cur.rowcount

    # -- Suche ---------------------------------------------------------
    def lexical(self, query: str, limit: int = 40) -> list[tuple[int, float]]:
        expression = fts_query(query)
        if not expression:
            return []
        try:
            rows = self.db.query(
                "SELECT rowid, bm25(chunks_fts, 1.0, 2.0, 3.0) AS score FROM chunks_fts "
                "WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?",
                (expression, limit),
            )
        except sqlite3.OperationalError as exc:
            log.warning("Volltextsuche fehlgeschlagen (%s): %s", expression[:60], exc)
            return []
        return [(int(r["rowid"]), -float(r["score"])) for r in rows]

    def vector(self, query: str, limit: int = 40) -> list[tuple[int, float]]:
        if self.embedder is None:
            return []
        rows = self.db.query("SELECT chunk_id, dim, vector FROM embeddings")
        if not rows:
            return []
        query_vector = self.embedder.embed([query])[0]
        scored: list[tuple[int, float]] = []
        for row in rows:
            dim = int(row["dim"])
            if dim != len(query_vector):
                continue
            scored.append((int(row["chunk_id"]), cosine(query_vector, unpack_vector(row["vector"], dim))))
        scored.sort(key=lambda item: -item[1])
        return scored[:limit]

    def search(
        self,
        query: str,
        top_k: int = 8,
        lexical_candidates: int = 40,
        vector_candidates: int = 40,
        min_score: float = 0.0,
        as_of: str | None = None,
    ) -> list[Hit]:
        """Hybride Suche mit Quellenpriorisierung und Zeitbezug."""
        lexical = self.lexical(query, lexical_candidates)
        vector = self.vector(query, vector_candidates)
        if not lexical and not vector:
            return []

        lexical_ids = [cid for cid, _ in lexical]
        vector_ids = [cid for cid, _ in vector]
        # Die Volltextsuche ist die verlaessliche Grundlage; die Vektorsuche
        # ergaenzt sie (und ist ohne echtes Einbettungsmodell deutlich schwaecher).
        # Sie wird daher geringer gewichtet, damit sie gute Treffer nicht verdraengt.
        fused = rrf_merge([lexical_ids, vector_ids], weights=[1.0, 0.45])
        lexical_rank = {cid: i + 1 for i, cid in enumerate(lexical_ids)}
        vector_rank = {cid: i + 1 for i, cid in enumerate(vector_ids)}

        candidates = sorted(fused.items(), key=lambda item: -item[1])[: max(top_k * 4, 20)]
        if not candidates:
            return []
        placeholders = ",".join("?" for _ in candidates)
        rows = self.db.query(
            f"""SELECT c.id AS chunk_id, c.text, c.heading, c.citation AS chunk_citation,
                       d.doc_uid, d.title, d.citation AS doc_citation, d.source_id, d.url,
                       d.priority, d.valid_from, d.valid_to, d.fetched_at, d.status
                FROM chunks c JOIN documents d ON d.id = c.doc_id
                WHERE c.id IN ({placeholders})""",
            [cid for cid, _ in candidates],
        )
        by_id = {int(r["chunk_id"]): r for r in rows}

        hits: list[Hit] = []
        for chunk_id, score in candidates:
            row = by_id.get(chunk_id)
            if row is None or row["status"] != "active":
                continue
            if as_of and not _valid_at(row["valid_from"], row["valid_to"], as_of):
                continue
            priority = int(row["priority"] or 5)
            final = score + self.priority_boost * (5 - priority)
            if final < min_score:
                continue
            hits.append(
                Hit(
                    chunk_id=chunk_id, doc_uid=row["doc_uid"], title=row["title"],
                    citation=row["chunk_citation"] or row["doc_citation"] or "",
                    heading=row["heading"] or "", text=row["text"],
                    source_id=row["source_id"], url=row["url"] or "", priority=priority,
                    score=round(final, 6), valid_from=row["valid_from"],
                    valid_to=row["valid_to"], fetched_at=row["fetched_at"],
                    lexical_rank=lexical_rank.get(chunk_id),
                    vector_rank=vector_rank.get(chunk_id),
                )
            )
        hits.sort(key=lambda h: (-h.score, h.priority))
        return hits[:top_k]


def _valid_at(valid_from: str | None, valid_to: str | None, as_of: str) -> bool:
    """Zeitbezogener Rechtsstand (Masterprompt 25)."""
    if valid_from and as_of < valid_from:
        return False
    if valid_to and as_of > valid_to:
        return False
    return True
