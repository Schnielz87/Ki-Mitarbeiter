"""Freigaben (Human-in-the-Loop, Masterprompt 41).

Zustandsautomat:

    ENTWURF -> GEPRUEFT -> FREIGEGEBEN -> AUSGEFUEHRT
        |          |            |
        +----------+------------+--> ABGELEHNT

Ohne den Zustand ``FREIGEGEBEN`` darf nichts ausgefuehrt werden - weder eine
Buchung noch eine Meldung, eine Zahlung oder eine Stammdatenaenderung.  Die
Regel wird hier technisch durchgesetzt, nicht nur dokumentiert.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..db import Database, utc_now
from ..logging_setup import get_logger
from .log import AuditLog

log = get_logger(__name__)


class ApprovalState(str, Enum):
    ENTWURF = "ENTWURF"
    GEPRUEFT = "GEPRUEFT"
    FREIGEGEBEN = "FREIGEGEBEN"
    AUSGEFUEHRT = "AUSGEFUEHRT"
    ABGELEHNT = "ABGELEHNT"


ALLOWED_TRANSITIONS: dict[ApprovalState, set[ApprovalState]] = {
    ApprovalState.ENTWURF: {ApprovalState.GEPRUEFT, ApprovalState.ABGELEHNT},
    ApprovalState.GEPRUEFT: {ApprovalState.FREIGEGEBEN, ApprovalState.ABGELEHNT,
                             ApprovalState.ENTWURF},
    ApprovalState.FREIGEGEBEN: {ApprovalState.AUSGEFUEHRT, ApprovalState.ABGELEHNT},
    ApprovalState.AUSGEFUEHRT: set(),
    ApprovalState.ABGELEHNT: {ApprovalState.ENTWURF},
}


class ApprovalError(RuntimeError):
    """Ein unzulaessiger Zustandsuebergang wurde versucht."""


@dataclass
class Approval:
    uid: str
    object_type: str
    title: str
    state: ApprovalState
    payload: dict
    created_at: str
    updated_at: str
    requested_by: str = ""
    decided_by: str = ""
    decided_at: str = ""
    note: str = ""

    @property
    def executable(self) -> bool:
        return self.state is ApprovalState.FREIGEGEBEN

    def as_dict(self) -> dict:
        data = self.__dict__.copy()
        data["state"] = self.state.value
        return data


class ApprovalStore:
    """Verwaltung der Freigabevorgaenge."""

    def __init__(self, db: Database, audit: AuditLog | None = None):
        self.db = db
        self.audit = audit

    def create(
        self, object_type: str, title: str, payload: dict | None = None,
        requested_by: str = "ki-mitarbeiter", note: str = "",
    ) -> Approval:
        now = utc_now()
        uid = uuid.uuid4().hex[:16]
        self.db.execute(
            """INSERT INTO approvals (uid, object_type, title, state, payload_json,
                   created_at, updated_at, requested_by, note)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (uid, object_type, title, ApprovalState.ENTWURF.value,
             json.dumps(payload or {}, ensure_ascii=False), now, now, requested_by, note),
        )
        if self.audit:
            self.audit.record("freigabe_angelegt", "approval", uid,
                              titel=title, art=object_type)
        return self.get(uid)  # type: ignore[return-value]

    def get(self, uid: str) -> Approval | None:
        row = self.db.one("SELECT * FROM approvals WHERE uid=?", (uid,))
        if row is None:
            return None
        return Approval(
            uid=row["uid"], object_type=row["object_type"], title=row["title"],
            state=ApprovalState(row["state"]), payload=json.loads(row["payload_json"] or "{}"),
            created_at=row["created_at"], updated_at=row["updated_at"],
            requested_by=row["requested_by"] or "", decided_by=row["decided_by"] or "",
            decided_at=row["decided_at"] or "", note=row["note"] or "",
        )

    def transition(
        self, uid: str, target: ApprovalState, by: str = "benutzer", note: str = "",
    ) -> Approval:
        approval = self.get(uid)
        if approval is None:
            raise ApprovalError(f"Freigabevorgang {uid} existiert nicht.")
        allowed = ALLOWED_TRANSITIONS[approval.state]
        if target not in allowed:
            raise ApprovalError(
                f"Uebergang {approval.state.value} -> {target.value} ist nicht zulaessig. "
                f"Moeglich waere: {', '.join(sorted(s.value for s in allowed)) or 'nichts'}."
            )
        now = utc_now()
        decided = target in (ApprovalState.FREIGEGEBEN, ApprovalState.ABGELEHNT)
        self.db.execute(
            "UPDATE approvals SET state=?, updated_at=?, note=?, "
            "decided_by=CASE WHEN ? THEN ? ELSE decided_by END, "
            "decided_at=CASE WHEN ? THEN ? ELSE decided_at END WHERE uid=?",
            (target.value, now, note or approval.note, decided, by, decided, now, uid),
        )
        if self.audit:
            self.audit.record(
                "freigabe_status", "approval", uid, status="ok",
                actor=by, von=approval.state.value, nach=target.value, hinweis=note,
            )
        log.info("Freigabe %s: %s -> %s", uid, approval.state.value, target.value)
        return self.get(uid)  # type: ignore[return-value]

    def require_executable(self, uid: str) -> Approval:
        """Wirft, wenn der Vorgang nicht freigegeben ist. Von Connectoren genutzt."""
        approval = self.get(uid)
        if approval is None:
            raise ApprovalError(f"Freigabevorgang {uid} existiert nicht.")
        if not approval.executable:
            raise ApprovalError(
                f"Der Vorgang '{approval.title}' ist im Zustand {approval.state.value} "
                "und darf nicht ausgefuehrt werden. Erforderlich: FREIGEGEBEN."
            )
        return approval

    def list(self, state: ApprovalState | None = None, limit: int = 100) -> list[Approval]:
        sql = "SELECT uid FROM approvals"
        params: list[Any] = []
        if state is not None:
            sql += " WHERE state=?"
            params.append(state.value)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return [a for a in (self.get(r["uid"]) for r in self.db.query(sql, params)) if a]

    def open_count(self) -> int:
        return int(self.db.scalar(
            "SELECT COUNT(*) FROM approvals WHERE state IN ('ENTWURF','GEPRUEFT','FREIGEGEBEN')",
            default=0,
        ) or 0)
