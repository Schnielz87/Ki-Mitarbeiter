"""Persistentes Unternehmensgedaechtnis (Masterprompt 13-17).

Kernzusagen:
* Alles liegt in ``database/company.db`` auf dem portablen Datentraeger.
* Jede Aenderung erzeugt eine neue Version; alte Staende bleiben in
  ``memory_history`` nachvollziehbar erhalten (keine unsichtbaren
  Ueberschreibungen).
* Loeschen ist standardmaessig ein Archivieren; echtes Loeschen ist moeglich,
  wird aber protokolliert.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..db import Database, utc_now
from ..logging_setup import get_logger
from .schema_keys import CATEGORIES, WELL_KNOWN_KEYS

log = get_logger(__name__)


def _fts_query(text: str) -> str:
    """Baut eine sichere FTS5-Abfrage aus freier Benutzereingabe."""
    tokens = [t for t in "".join(ch if ch.isalnum() else " " for ch in text).split() if len(t) > 1]
    if not tokens:
        return ""
    return " OR ".join(f'"{t}"*' for t in tokens[:16])


@dataclass
class MemoryEntry:
    mem_key: str
    category: str
    title: str
    content: str
    value: Any = None
    status: str = "active"
    version: int = 1
    confidence: float = 1.0
    source: str | None = None
    origin: str = "user"
    valid_from: str | None = None
    valid_to: str | None = None
    review_at: str | None = None
    tags: str = ""
    created_at: str = ""
    updated_at: str = ""
    created_by: str = "user"
    id: int | None = None
    score: float = field(default=0.0, compare=False)

    @classmethod
    def from_row(cls, row: sqlite3.Row, score: float = 0.0) -> "MemoryEntry":
        data = dict(row)
        raw = data.pop("value_json", None)
        return cls(
            id=data.get("id"),
            mem_key=data["mem_key"],
            category=data["category"],
            title=data["title"],
            content=data["content"],
            value=json.loads(raw) if raw else None,
            status=data["status"],
            version=data["version"],
            confidence=data["confidence"],
            source=data.get("source"),
            origin=data.get("origin", "user"),
            valid_from=data.get("valid_from"),
            valid_to=data.get("valid_to"),
            review_at=data.get("review_at"),
            tags=data.get("tags", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            created_by=data.get("created_by", "user"),
            score=score,
        )

    def as_dict(self) -> dict:
        data = {
            "mem_key": self.mem_key, "category": self.category, "title": self.title,
            "content": self.content, "value": self.value, "status": self.status,
            "version": self.version, "confidence": self.confidence,
            "source": self.source, "origin": self.origin,
            "valid_from": self.valid_from, "valid_to": self.valid_to,
            "review_at": self.review_at, "tags": self.tags,
            "created_at": self.created_at, "updated_at": self.updated_at,
            "created_by": self.created_by,
        }
        return data

    def as_prompt_line(self) -> str:
        label = CATEGORIES.get(self.category, self.category)
        suffix = ""
        if self.valid_from or self.valid_to:
            suffix = f" [gueltig {self.valid_from or '?'} bis {self.valid_to or 'offen'}]"
        return f"- ({label}) {self.title}: {self.content}{suffix}"


class MemoryStore:
    """CRUD, Versionierung und Suche fuer das Unternehmensgedaechtnis."""

    def __init__(self, db: Database):
        self.db = db

    # -- Schreiben -----------------------------------------------------
    def put(
        self,
        mem_key: str,
        title: str,
        content: str,
        category: str = "other",
        *,
        value: Any = None,
        source: str | None = None,
        origin: str = "user",
        confidence: float = 1.0,
        tags: str = "",
        valid_from: str | None = None,
        valid_to: str | None = None,
        review_at: str | None = None,
        created_by: str = "user",
        reason: str | None = None,
    ) -> MemoryEntry:
        """Legt einen Eintrag an oder erzeugt eine neue Version.

        Idempotent: identischer Inhalt erzeugt *keine* neue Version.
        """
        if category not in CATEGORIES:
            category = "other"
        now = utc_now()
        current = self.get(mem_key)

        if current is not None:
            unchanged = (
                current.content.strip() == content.strip()
                and current.title == title
                and current.category == category
                and current.value == value
                and current.status == "active"
                and current.valid_from == valid_from
                and current.valid_to == valid_to
            )
            if unchanged:
                return current
            with self.db.transaction():
                self._archive_row(current, "update", reason or "Neue Fassung gespeichert", created_by, now)
                entry = self._insert(
                    mem_key, category, title, content, value, current.version + 1,
                    confidence, source, origin, valid_from, valid_to, review_at,
                    tags or current.tags, current.created_at or now, now, created_by,
                )
                self._history(entry, "update", reason or "Neue Fassung gespeichert", created_by, now)
            log.info("Unternehmenswissen aktualisiert: %s (v%s)", mem_key, entry.version)
            return entry

        with self.db.transaction():
            entry = self._insert(
                mem_key, category, title, content, value, 1, confidence, source,
                origin, valid_from, valid_to, review_at, tags, now, now, created_by,
            )
            self._history(entry, "create", reason or "Erstanlage", created_by, now)
        log.info("Unternehmenswissen gespeichert: %s", mem_key)
        return entry

    def _insert(
        self, mem_key, category, title, content, value, version, confidence, source,
        origin, valid_from, valid_to, review_at, tags, created_at, updated_at, created_by,
    ) -> MemoryEntry:
        cur = self.db.execute(
            """INSERT INTO memory
               (mem_key, category, title, content, value_json, status, version,
                confidence, source, origin, valid_from, valid_to, review_at, tags,
                created_at, updated_at, created_by)
               VALUES (?,?,?,?,?,'active',?,?,?,?,?,?,?,?,?,?,?)""",
            (mem_key, category, title, content,
             json.dumps(value, ensure_ascii=False) if value is not None else None,
             version, confidence, source, origin, valid_from, valid_to, review_at,
             tags, created_at, updated_at, created_by),
        )
        row = self.db.one("SELECT * FROM memory WHERE id=?", (cur.lastrowid,))
        assert row is not None
        return MemoryEntry.from_row(row)

    def _archive_row(self, entry: MemoryEntry, change: str, reason: str, by: str, now: str) -> None:
        self.db.execute(
            "UPDATE memory SET status='superseded', updated_at=? WHERE mem_key=? AND status='active'",
            (now, entry.mem_key),
        )

    def _history(self, entry: MemoryEntry, change: str, reason: str, by: str, now: str) -> None:
        self.db.execute(
            """INSERT INTO memory_history
               (mem_key, version, change_type, changed_at, changed_by, reason, snapshot_json)
               VALUES (?,?,?,?,?,?,?)""",
            (entry.mem_key, entry.version, change, now, by, reason,
             json.dumps(entry.as_dict(), ensure_ascii=False)),
        )

    # -- Lesen ---------------------------------------------------------
    def get(self, mem_key: str) -> MemoryEntry | None:
        row = self.db.one(
            "SELECT * FROM memory WHERE mem_key=? AND status='active' ORDER BY version DESC LIMIT 1",
            (mem_key,),
        )
        return MemoryEntry.from_row(row) if row else None

    def list(
        self,
        category: str | None = None,
        status: str = "active",
        limit: int = 500,
        offset: int = 0,
    ) -> list[MemoryEntry]:
        sql = "SELECT * FROM memory WHERE 1=1"
        params: list[Any] = []
        if status != "all":
            sql += " AND status=?"
            params.append(status)
        if category:
            sql += " AND category=?"
            params.append(category)
        sql += " ORDER BY category, title LIMIT ? OFFSET ?"
        params += [limit, offset]
        return [MemoryEntry.from_row(r) for r in self.db.query(sql, params)]

    def history(self, mem_key: str) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM memory_history WHERE mem_key=? ORDER BY version DESC, id DESC",
            (mem_key,),
        )
        out = []
        for row in rows:
            item = dict(row)
            item["snapshot"] = json.loads(item.pop("snapshot_json"))
            out.append(item)
        return out

    def search(self, text: str, limit: int = 10, status: str = "active") -> list[MemoryEntry]:
        query = _fts_query(text)
        if not query:
            return []
        try:
            rows = self.db.query(
                """SELECT m.*, bm25(memory_fts) AS rank_score
                   FROM memory_fts
                   JOIN memory m ON m.id = memory_fts.rowid
                   WHERE memory_fts MATCH ? AND (? = 'all' OR m.status = ?)
                   ORDER BY rank_score LIMIT ?""",
                (query, status, status, limit),
            )
        except sqlite3.OperationalError as exc:  # pragma: no cover - defensiv
            log.warning("Volltextsuche im Unternehmensgedaechtnis fehlgeschlagen: %s", exc)
            return []
        results = []
        for row in rows:
            data = dict(row)
            score = -float(data.pop("rank_score") or 0.0)
            results.append(MemoryEntry.from_row(row, score))
        return results

    def all_active_for_prompt(self, max_entries: int = 60) -> list[MemoryEntry]:
        """Wohlbekannte Stammdaten zuerst - sie gehoeren immer in den Kontext."""
        entries = self.list(status="active", limit=max_entries * 2)
        priority = list(WELL_KNOWN_KEYS)
        entries.sort(key=lambda e: (priority.index(e.mem_key) if e.mem_key in priority else 999, e.category, e.title))
        return entries[:max_entries]

    # -- Verwalten -----------------------------------------------------
    def archive(self, mem_key: str, reason: str = "", by: str = "user") -> bool:
        entry = self.get(mem_key)
        if entry is None:
            return False
        now = utc_now()
        with self.db.transaction():
            self.db.execute(
                "UPDATE memory SET status='archived', updated_at=? WHERE mem_key=? AND status='active'",
                (now, mem_key),
            )
            entry.status = "archived"
            self._history(entry, "archive", reason or "archiviert", by, now)
        log.info("Unternehmenswissen archiviert: %s", mem_key)
        return True

    def restore(self, mem_key: str, by: str = "user") -> MemoryEntry | None:
        row = self.db.one(
            "SELECT * FROM memory WHERE mem_key=? AND status='archived' ORDER BY version DESC LIMIT 1",
            (mem_key,),
        )
        if row is None:
            return None
        now = utc_now()
        with self.db.transaction():
            self.db.execute("UPDATE memory SET status='active', updated_at=? WHERE id=?", (now, row["id"]))
            entry = MemoryEntry.from_row(self.db.one("SELECT * FROM memory WHERE id=?", (row["id"],)))
            self._history(entry, "restore", "wiederhergestellt", by, now)
        return entry

    def delete(self, mem_key: str, reason: str = "", by: str = "user", hard: bool = False) -> bool:
        """Standard: archivieren. ``hard=True`` loescht endgueltig (protokolliert)."""
        if not hard:
            return self.archive(mem_key, reason or "geloescht (archiviert)", by)
        entry = self.get(mem_key)
        now = utc_now()
        with self.db.transaction():
            if entry is not None:
                self._history(entry, "delete", reason or "endgueltig geloescht", by, now)
            cur = self.db.execute("DELETE FROM memory WHERE mem_key=?", (mem_key,))
        log.warning("Unternehmenswissen endgueltig geloescht: %s", mem_key)
        return cur.rowcount > 0

    # -- Kennzahlen ----------------------------------------------------
    def stats(self) -> dict:
        return {
            "active": self.db.scalar("SELECT COUNT(*) FROM memory WHERE status='active'", default=0),
            "archived": self.db.scalar("SELECT COUNT(*) FROM memory WHERE status='archived'", default=0),
            "superseded": self.db.scalar("SELECT COUNT(*) FROM memory WHERE status='superseded'", default=0),
            "history": self.db.scalar("SELECT COUNT(*) FROM memory_history", default=0),
            "categories": {
                r["category"]: r["n"]
                for r in self.db.query(
                    "SELECT category, COUNT(*) n FROM memory WHERE status='active' GROUP BY category"
                )
            },
        }

    def export(self) -> list[dict]:
        return [e.as_dict() for e in self.list(status="all", limit=100000)]

    def import_entries(self, entries: Iterable[dict], by: str = "import") -> int:
        count = 0
        for item in entries:
            if item.get("status") != "active":
                continue
            self.put(
                item["mem_key"], item.get("title", item["mem_key"]), item.get("content", ""),
                item.get("category", "other"), value=item.get("value"),
                source=item.get("source"), origin="import", created_by=by,
                tags=item.get("tags", ""), valid_from=item.get("valid_from"),
                valid_to=item.get("valid_to"),
            )
            count += 1
        return count
