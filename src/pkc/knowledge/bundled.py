"""Aufnahme der mitgelieferten Fachmodule in die lokale Wissensdatenbank.

Diese Module sind der Grund, warum der Mitarbeiter **ab dem ersten Start ohne
Internet** fachlich arbeiten kann.  Sie sind ausdruecklich Sekundaerquellen
(Prioritaet 5) und werden als solche gekennzeichnet - amtliche Quellen, die
spaeter per Update dazukommen, haben Vorrang.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..db import utc_now
from ..logging_setup import get_logger
from ..paths import Paths
from .chunker import chunk_document
from .extract import ExtractionError, extract
from .store import KnowledgeStore

log = get_logger(__name__)

BUNDLED_SOURCE_ID = "P00_MITGELIEFERTE_FACHMODULE"


def ingest_bundled_modules(
    store: KnowledgeStore,
    paths: Paths,
    knowledge_dir: Path,
    profile_id: str,
    chunk_tokens: int = 400,
    chunk_overlap: int = 60,
) -> dict:
    """Nimmt alle Markdown-Module eines Profils auf. Idempotent ueber SHA-256."""
    result = {"gefunden": 0, "neu": 0, "aktualisiert": 0, "unveraendert": 0,
              "fehlgeschlagen": 0, "fehler": []}
    if not knowledge_dir.is_dir():
        result["fehler"].append(f"Fachmodulverzeichnis fehlt: {knowledge_dir}")
        return result

    store.upsert_source(
        BUNDLED_SOURCE_ID,
        "Mitgelieferte Fachmodule des Mitarbeiterprofils",
        publisher="Anwendung",
        priority=5,
        kind="secondary",
        base_url="",
        licence="Bestandteil der Anwendung - aufbereitete Sekundaerquelle",
        enabled=True,
        meta={"profil": profile_id, "hinweis":
              "Sekundaerquelle. Amtliche Primaerquellen haben Vorrang."},
    )

    files = sorted(knowledge_dir.glob("*.md"))
    result["gefunden"] = len(files)
    for path in files:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        doc_uid = f"MODUL_{profile_id.upper()}_{path.stem.upper()}"
        existing = store.get_document(doc_uid)
        if existing is not None and existing.sha256 == digest:
            result["unveraendert"] += 1
            continue
        try:
            document = extract(raw, "text/markdown", "text", path.name)
        except ExtractionError as exc:
            result["fehlgeschlagen"] += 1
            result["fehler"].append(f"{path.name}: {exc}")
            continue
        chunks = chunk_document(document, chunk_tokens, chunk_overlap)
        if not chunks:
            result["fehlgeschlagen"] += 1
            result["fehler"].append(f"{path.name}: keine Abschnitte")
            continue
        title = document.title or path.stem.replace("_", " ")
        doc_id = store.upsert_document(
            doc_uid, BUNDLED_SOURCE_ID, title,
            url="", kind="module", citation=f"Fachmodul {title}",
            path_raw=paths.relative(path), sha256=digest, size=len(raw),
            licence="Bestandteil der Anwendung", priority=5,
            meta={"datei": path.name, "profil": profile_id, "aufgenommen_am": utc_now()},
        )
        store.replace_chunks(doc_id, chunks)
        result["neu" if existing is None else "aktualisiert"] += 1

    log.info(
        "Fachmodule aufgenommen: %s neu, %s aktualisiert, %s unveraendert, %s fehlerhaft",
        result["neu"], result["aktualisiert"], result["unveraendert"], result["fehlgeschlagen"],
    )
    return result
