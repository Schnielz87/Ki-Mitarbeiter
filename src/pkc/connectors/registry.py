"""Registrierung und Aufbau der Connectoren aus der Konfiguration."""

from __future__ import annotations

from typing import Callable, Iterable

from ..audit.approvals import ApprovalStore
from ..audit.log import AuditLog
from ..logging_setup import get_logger
from .base import Connector, ConnectorInfo, ConnectorMode
from .erp_stubs import DatevConnector, SapConnector, WilkenConnector
from .files import CsvConnector, ExcelConnector
from .rest import GenericRestConnector

log = get_logger(__name__)

CONNECTOR_CLASSES: dict[str, type[Connector]] = {
    CsvConnector.connector_id: CsvConnector,
    ExcelConnector.connector_id: ExcelConnector,
    GenericRestConnector.connector_id: GenericRestConnector,
    SapConnector.connector_id: SapConnector,
    WilkenConnector.connector_id: WilkenConnector,
    DatevConnector.connector_id: DatevConnector,
}


class ConnectorRegistry:
    def __init__(self, connectors: dict[str, Connector]):
        self.connectors = connectors

    def get(self, connector_id: str) -> Connector | None:
        return self.connectors.get(connector_id)

    def info(self) -> list[ConnectorInfo]:
        return [c.info() for c in self.connectors.values()]

    def configured_ids(self) -> list[str]:
        return [cid for cid, c in self.connectors.items() if c.configured()[0]]

    def __len__(self) -> int:
        return len(self.connectors)


def build_registry(
    config,
    approvals: ApprovalStore | None = None,
    audit: AuditLog | None = None,
    secret_lookup: Callable[[str], str | None] | None = None,
) -> ConnectorRegistry:
    """Baut alle bekannten Connectoren; Standardmodus ist nur lesend."""
    default_mode = ConnectorMode(str(config.get("connectors.default_mode", "read_only")))
    settings = config.get("connectors.settings", {}) or {}
    built: dict[str, Connector] = {}
    for connector_id, klass in CONNECTOR_CLASSES.items():
        entry = dict(settings.get(connector_id, {}) or {})
        mode_value = entry.pop("mode", default_mode.value)
        try:
            mode = ConnectorMode(mode_value)
        except ValueError:
            log.warning("Unbekannter Connector-Modus %r fuer %s - nutze read_only",
                        mode_value, connector_id)
            mode = ConnectorMode.READ_ONLY
        built[connector_id] = klass(
            config=entry, mode=mode, approvals=approvals, audit=audit,
            secret_lookup=secret_lookup,
        )
    return ConnectorRegistry(built)
