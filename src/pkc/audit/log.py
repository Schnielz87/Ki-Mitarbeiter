"""Nachvollziehbares Protokoll aller relevanten Vorgaenge."""

from __future__ import annotations

import json
from typing import Any

from ..db import Database, utc_now


class AuditLog:
    """Schreibt in ``audit_log`` der Unternehmensdatenbank."""

    def __init__(self, db: Database, enabled: bool = True, actor: str = "benutzer"):
        self.db = db
        self.enabled = bool(enabled)
        self.actor = actor

    def record(
        self,
        action: str,
        object_type: str = "",
        object_id: str = "",
        status: str = "ok",
        actor: str | None = None,
        **detail: Any,
    ) -> int | None:
        if not self.enabled:
            return None
        cursor = self.db.execute(
            "INSERT INTO audit_log (ts, actor, action, object_type, object_id, status, detail_json)"
            " VALUES (?,?,?,?,?,?,?)",
            (utc_now(), actor or self.actor, action, object_type, object_id, status,
             json.dumps(detail, ensure_ascii=False, default=str)),
        )
        return int(cursor.lastrowid)

    def entries(self, limit: int = 200, action: str | None = None) -> list[dict]:
        sql = "SELECT * FROM audit_log"
        params: list[Any] = []
        if action:
            sql += " WHERE action=?"
            params.append(action)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = self.db.query(sql, params)
        out = []
        for row in rows:
            item = dict(row)
            item["detail"] = json.loads(item.pop("detail_json") or "{}")
            out.append(item)
        return out

    def count(self) -> int:
        return int(self.db.scalar("SELECT COUNT(*) FROM audit_log", default=0) or 0)
