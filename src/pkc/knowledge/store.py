"""Lokale Fachwissensdatenbank (Dokumente, Abschnitte, Metadaten)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from ..db import Database, utc_now
from ..logging_setup import get_logger
from .chunker import Chunk

log = get_logger(__name__)


@dataclass
class StoredDocument:
    id: int
    doc_uid: str
    source_id: str
    title: str
    citation: str
    url: str
    kind: str
    status: str
    priority: int
    version: int
    fetched_at: str | None
    published_at: str | None
    valid_from: str | None
    valid_to: str | None
    sha256: str | None
    path_raw: str | None
    path_normalized: str | None
    licence: str | None
    meta: dict

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "StoredDocument":
        data = dict(row)
        return cls(
            id=data["id"], doc_uid=data["doc_uid"], source_id=data["source_id"],
            title=data["title"], citation=data.get("citation") or "",
            url=data.get("url") or "", kind=data.get("kind") or "",
            status=data["status"], priority=data["priority"], version=data["version"],
            fetched_at=data.get("fetched_at"), published_at=data.get("published_at"),
            valid_from=data.get("valid_from"), valid_to=data.get("valid_to"),
            sha256=data.get("sha256"), path_raw=data.get("path_raw"),
            path_normalized=data.get("path_normalized"), licence=data.get("licence"),
            meta=json.loads(data.get("meta_json") or "{}"),
        )


class KnowledgeStore:
    """Schreib-/Lesezugriff auf ``knowledge.db``."""

    def __init__(self, db: Database):
        self.db = db

    # -- Quellen -------------------------------------------------------
    def upsert_source(
        self, source_id: str, name: str, publisher: str = "", priority: int = 5,
        kind: str = "secondary", base_url: str = "", licence: str = "",
        enabled: bool = True, meta: dict | None = None,
    ) -> None:
        self.db.execute(
            """INSERT INTO sources (source_id, name, publisher, priority, kind, base_url,
                                    licence, enabled, meta_json)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET
                   name=excluded.name, publisher=excluded.publisher,
                   priority=excluded.priority, kind=excluded.kind,
                   base_url=excluded.base_url, licence=excluded.licence,
                   enabled=excluded.enabled, meta_json=excluded.meta_json""",
            (source_id, name, publisher, priority, kind, base_url, licence,
             1 if enabled else 0, json.dumps(meta or {}, ensure_ascii=False)),
        )

    def mark_source_checked(self, source_id: str, success: bool, error: str = "") -> None:
        now = utc_now()
        if success:
            self.db.execute(
                "UPDATE sources SET last_checked=?, last_success=?, last_error='' WHERE source_id=?",
                (now, now, source_id),
            )
        else:
            self.db.execute(
                "UPDATE sources SET last_checked=?, last_error=? WHERE source_id=?",
                (now, error[:500], source_id),
            )

    def sources(self) -> list[dict]:
        return [dict(r) for r in self.db.query("SELECT * FROM sources ORDER BY priority, source_id")]

    # -- Dokumente -----------------------------------------------------
    def get_document(self, doc_uid: str) -> StoredDocument | None:
        row = self.db.one("SELECT * FROM documents WHERE doc_uid=?", (doc_uid,))
        return StoredDocument.from_row(row) if row else None

    def cache_headers(self, doc_uid: str) -> tuple[str | None, str | None]:
        row = self.db.one("SELECT etag, last_modified FROM documents WHERE doc_uid=?", (doc_uid,))
        return (row["etag"], row["last_modified"]) if row else (None, None)

    def upsert_document(
        self,
        doc_uid: str,
        source_id: str,
        title: str,
        *,
        url: str = "",
        kind: str = "law",
        citation: str = "",
        path_raw: str | None = None,
        path_normalized: str | None = None,
        sha256: str | None = None,
        size: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        published_at: str | None = None,
        valid_from: str | None = None,
        valid_to: str | None = None,
        licence: str = "",
        priority: int = 5,
        collection: str = "knowledge",
        status: str = "active",
        meta: dict | None = None,
    ) -> int:
        """Legt ein Dokument an oder erhoeht dessen Version. Gibt die ID zurueck."""
        now = utc_now()
        existing = self.db.one("SELECT id, version, sha256 FROM documents WHERE doc_uid=?", (doc_uid,))
        payload = json.dumps(meta or {}, ensure_ascii=False)
        if existing is None:
            cur = self.db.execute(
                """INSERT INTO documents
                   (doc_uid, source_id, collection, title, url, kind, citation, path_raw,
                    path_normalized, sha256, bytes, etag, last_modified, published_at,
                    fetched_at, valid_from, valid_to, version, licence, status, priority, meta_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?,?)""",
                (doc_uid, source_id, collection, title, url, kind, citation, path_raw,
                 path_normalized, sha256, size, etag, last_modified, published_at, now,
                 valid_from, valid_to, licence, status, priority, payload),
            )
            return int(cur.lastrowid)

        version = existing["version"] + (1 if sha256 and sha256 != existing["sha256"] else 0)
        self.db.execute(
            """UPDATE documents SET source_id=?, title=?, url=?, kind=?, citation=?,
                   path_raw=COALESCE(?, path_raw), path_normalized=COALESCE(?, path_normalized),
                   sha256=COALESCE(?, sha256), bytes=COALESCE(?, bytes),
                   etag=?, last_modified=?, published_at=COALESCE(?, published_at),
                   fetched_at=?, valid_from=COALESCE(?, valid_from),
                   valid_to=COALESCE(?, valid_to), version=?, licence=?, status=?,
                   priority=?, meta_json=?
               WHERE doc_uid=?""",
            (source_id, title, url, kind, citation, path_raw, path_normalized, sha256, size,
             etag, last_modified, published_at, now, valid_from, valid_to, version, licence,
             status, priority, payload, doc_uid),
        )
        return int(existing["id"])

    def replace_chunks(self, doc_id: int, chunks: Sequence[Chunk]) -> int:
        """Ersetzt alle Abschnitte eines Dokuments (inkl. Volltextindex)."""
        self.db.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
        self.db.executemany(
            "INSERT INTO chunks (doc_id, ord, heading, citation, text, tokens, sha256) "
            "VALUES (?,?,?,?,?,?,?)",
            [(doc_id, c.ord, c.heading, c.citation, c.text, c.tokens, c.sha256) for c in chunks],
        )
        return len(chunks)

    def chunk_rows(self, doc_id: int | None = None, missing_embeddings: bool = False) -> list[sqlite3.Row]:
        sql = "SELECT c.* FROM chunks c"
        params: list[Any] = []
        conditions = []
        if missing_embeddings:
            sql += " LEFT JOIN embeddings e ON e.chunk_id = c.id"
            conditions.append("e.chunk_id IS NULL")
        if doc_id is not None:
            conditions.append("c.doc_id = ?")
            params.append(doc_id)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY c.doc_id, c.ord"
        return self.db.query(sql, params)

    def delete_document(self, doc_uid: str) -> bool:
        cur = self.db.execute("DELETE FROM documents WHERE doc_uid=?", (doc_uid,))
        return cur.rowcount > 0

    def documents(self, status: str = "active", limit: int = 1000) -> list[StoredDocument]:
        sql = "SELECT * FROM documents"
        params: list[Any] = []
        if status != "all":
            sql += " WHERE status=?"
            params.append(status)
        sql += " ORDER BY priority, source_id, title LIMIT ?"
        params.append(limit)
        return [StoredDocument.from_row(r) for r in self.db.query(sql, params)]

    # -- Wissensstand --------------------------------------------------
    def set_state(self, key: str, value: str) -> None:
        self.db.execute(
            "INSERT INTO knowledge_state (key, value, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, value, utc_now()),
        )

    def get_state(self, key: str, default: str | None = None) -> str | None:
        row = self.db.one("SELECT value FROM knowledge_state WHERE key=?", (key,))
        return row["value"] if row else default

    def knowledge_date(self) -> str | None:
        """Wissensstand = juengstes erfolgreiches Abrufdatum."""
        explicit = self.get_state("knowledge_date")
        if explicit:
            return explicit
        return self.db.scalar("SELECT MAX(fetched_at) FROM documents WHERE status='active'")

    def stats(self) -> dict:
        return {
            "sources": self.db.scalar("SELECT COUNT(*) FROM sources", default=0),
            "documents": self.db.scalar("SELECT COUNT(*) FROM documents WHERE status='active'", default=0),
            "chunks": self.db.scalar("SELECT COUNT(*) FROM chunks", default=0),
            "embeddings": self.db.scalar("SELECT COUNT(*) FROM embeddings", default=0),
            "knowledge_date": self.knowledge_date(),
            "last_update_run": self.db.scalar(
                "SELECT MAX(finished_at) FROM update_runs WHERE status IN ('success','partial')"
            ),
        }
