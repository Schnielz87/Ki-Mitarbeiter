"""Connector-Grundgeruest (Masterprompt 40).

Feste Regeln, die hier technisch durchgesetzt werden:

* **Standard ist READ ONLY.**  Ein Connector im Lesemodus kann nicht
  schreiben - der Aufruf schlaegt fehl, statt stillschweigend zu wirken.
* **Schreiben nur mit Freigabe.**  Jeder Schreibvorgang braucht einen
  Freigabevorgang im Zustand FREIGEGEBEN (siehe ``pkc.audit.approvals``).
* **Ablauf:** Vorschlag -> Vorschau -> menschliche Freigabe -> Ausfuehrung
  -> Protokoll.
* **Kein Vortaeuschen.**  Ist ein Connector nicht konfiguriert, meldet er das
  klar und liefert keine erfundenen Daten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Protocol

from ..audit.approvals import ApprovalError, ApprovalStore
from ..audit.log import AuditLog
from ..logging_setup import get_logger

log = get_logger(__name__)


class ConnectorMode(str, Enum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    DISABLED = "disabled"


class ConnectorError(RuntimeError):
    """Der Connector konnte die Anfrage nicht ausfuehren."""


class NotConfigured(ConnectorError):
    """Der Connector ist vorhanden, aber nicht eingerichtet."""


class WriteRequiresApproval(ConnectorError):
    """Ein Schreibvorgang ohne gueltige Freigabe wurde versucht."""


@dataclass
class ConnectorInfo:
    connector_id: str
    name: str
    system: str
    mode: ConnectorMode
    configured: bool
    capabilities: list[str] = field(default_factory=list)
    detail: str = ""
    open_questions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "id": self.connector_id, "name": self.name, "system": self.system,
            "modus": self.mode.value, "eingerichtet": self.configured,
            "faehigkeiten": self.capabilities, "hinweis": self.detail,
            "offene_fragen": self.open_questions,
        }


@dataclass
class ConnectorResult:
    ok: bool
    rows: list[dict] = field(default_factory=list)
    message: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.rows)


class Connector:
    """Basisklasse aller Connectoren."""

    connector_id = "basis"
    name = "Basis-Connector"
    system = "unbestimmt"
    capabilities: tuple[str, ...] = ()
    #: Fragen, die vor einer echten Integration mit dem Kunden zu klaeren sind.
    open_questions: tuple[str, ...] = ()

    def __init__(
        self,
        config: dict | None = None,
        mode: ConnectorMode = ConnectorMode.READ_ONLY,
        approvals: ApprovalStore | None = None,
        audit: AuditLog | None = None,
        secret_lookup=None,
    ):
        self.config = config or {}
        self.mode = mode
        self.approvals = approvals
        self.audit = audit
        self.secret_lookup = secret_lookup

    # -- Zustand -------------------------------------------------------
    def configured(self) -> tuple[bool, str]:
        return False, "Nicht eingerichtet."

    def info(self) -> ConnectorInfo:
        configured, detail = self.configured()
        return ConnectorInfo(
            connector_id=self.connector_id, name=self.name, system=self.system,
            mode=self.mode, configured=configured, capabilities=list(self.capabilities),
            detail=detail, open_questions=list(self.open_questions),
        )

    def test(self) -> ConnectorResult:
        configured, detail = self.configured()
        return ConnectorResult(ok=configured, message=detail)

    # -- Lesen ---------------------------------------------------------
    def read(self, query: str = "", **kwargs) -> ConnectorResult:
        raise NotConfigured(
            f"{self.name}: Lesen ist fuer diesen Connector nicht implementiert."
        )

    # -- Schreiben -----------------------------------------------------
    def propose_write(self, payload: dict, title: str = "") -> str:
        """Erzeugt einen Freigabevorgang. Gibt dessen Kennung zurueck."""
        if self.approvals is None:
            raise ConnectorError(
                f"{self.name}: Ohne Freigabeverwaltung sind Schreibvorgaenge gesperrt."
            )
        approval = self.approvals.create(
            "erp_write", title or f"Schreibvorgang {self.name}",
            payload={"connector": self.connector_id, "daten": payload},
        )
        if self.audit:
            self.audit.record("connector_schreibvorschlag", "connector",
                              self.connector_id, freigabe=approval.uid)
        return approval.uid

    def preview_write(self, payload: dict) -> ConnectorResult:
        """Zeigt, was geschrieben wuerde - ohne zu schreiben."""
        return ConnectorResult(
            ok=True, rows=[payload],
            message=f"{self.name}: Vorschau. Es wurde nichts geschrieben.",
        )

    def write(self, payload: dict, approval_uid: str) -> ConnectorResult:
        """Fuehrt einen Schreibvorgang aus - nur mit gueltiger Freigabe."""
        if self.mode is not ConnectorMode.READ_WRITE:
            raise WriteRequiresApproval(
                f"{self.name} laeuft im Modus '{self.mode.value}'. Schreiben ist gesperrt. "
                "Der Modus muss ausdruecklich auf 'read_write' gesetzt werden."
            )
        if self.approvals is None:
            raise WriteRequiresApproval(
                f"{self.name}: Ohne Freigabeverwaltung sind Schreibvorgaenge gesperrt."
            )
        try:
            approval = self.approvals.require_executable(approval_uid)
        except ApprovalError as exc:
            raise WriteRequiresApproval(str(exc)) from exc
        result = self._perform_write(payload, approval_uid)
        if self.audit:
            self.audit.record(
                "connector_schreibvorgang", "connector", self.connector_id,
                status="ok" if result.ok else "fehler", freigabe=approval_uid,
                titel=approval.title,
            )
        return result

    def _perform_write(self, payload: dict, approval_uid: str) -> ConnectorResult:
        raise NotConfigured(
            f"{self.name}: Schreiben ist fuer diesen Connector nicht implementiert."
        )
