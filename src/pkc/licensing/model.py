"""Lizenzdaten und ihre kanonische Darstellung (Masterprompt 86)."""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SCHEMA_VERSION = 1


class LicenseError(RuntimeError):
    """Die Lizenz konnte nicht gelesen oder nicht geprueft werden."""


class LicenseState(str, Enum):
    GUELTIG = "GUELTIG"
    FEHLT = "FEHLT"
    UNGUELTIG_SIGNATUR = "UNGUELTIG_SIGNATUR"
    FALSCHE_INSTANZ = "FALSCHE_INSTANZ"
    ABGELAUFEN = "ABGELAUFEN"
    FALSCHES_PRODUKT = "FALSCHES_PRODUKT"
    MODUL_NICHT_LIZENZIERT = "MODUL_NICHT_LIZENZIERT"
    BESCHAEDIGT = "BESCHAEDIGT"
    NICHT_PRUEFBAR = "NICHT_PRUEFBAR"
    NICHT_ERFORDERLICH = "NICHT_ERFORDERLICH"


def canonical_bytes(payload: dict) -> bytes:
    """Eindeutige Byte-Darstellung fuer Signatur und Pruefung.

    Sortierte Schluessel und feste Trennzeichen - sonst haette dieselbe
    Lizenz je nach Schreibweise eine andere Signatur.
    """
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


@dataclass
class License:
    """Inhalt einer Lizenzdatei."""

    license_id: str
    customer: str
    customer_id: str
    product: str
    product_version: str
    modules: list[str]
    license_type: str                 # instanz | unternehmen | standort | zeitlich
    allowed_instances: int
    instance_id: str
    carrier_fingerprint: str
    activation_date: str
    expiry_date: str | None = None
    maintenance_until: str | None = None
    issued_at: str = ""
    issuer: str = ""
    notes: str = ""
    schema_version: int = SCHEMA_VERSION
    extra: dict[str, Any] = field(default_factory=dict)

    def payload(self) -> dict:
        """Genau die Felder, die signiert werden."""
        return {
            "schema_version": self.schema_version,
            "license_id": self.license_id,
            "customer": self.customer,
            "customer_id": self.customer_id,
            "product": self.product,
            "product_version": self.product_version,
            "modules": sorted(self.modules),
            "license_type": self.license_type,
            "allowed_instances": self.allowed_instances,
            "instance_id": self.instance_id,
            "carrier_fingerprint": self.carrier_fingerprint,
            "activation_date": self.activation_date,
            "expiry_date": self.expiry_date,
            "maintenance_until": self.maintenance_until,
            "issued_at": self.issued_at,
            "issuer": self.issuer,
            "notes": self.notes,
            "extra": self.extra,
        }

    @classmethod
    def from_payload(cls, data: dict) -> "License":
        try:
            return cls(
                license_id=data["license_id"], customer=data["customer"],
                customer_id=data.get("customer_id", ""), product=data["product"],
                product_version=data.get("product_version", ""),
                modules=list(data.get("modules", [])),
                license_type=data.get("license_type", "instanz"),
                allowed_instances=int(data.get("allowed_instances", 1)),
                instance_id=data.get("instance_id", ""),
                carrier_fingerprint=data.get("carrier_fingerprint", ""),
                activation_date=data.get("activation_date", ""),
                expiry_date=data.get("expiry_date"),
                maintenance_until=data.get("maintenance_until"),
                issued_at=data.get("issued_at", ""), issuer=data.get("issuer", ""),
                notes=data.get("notes", ""),
                schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
                extra=dict(data.get("extra", {})),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise LicenseError(f"Lizenzdatei ist unvollstaendig: {exc}") from exc

    def expired(self, heute: _dt.date | None = None) -> bool:
        if not self.expiry_date:
            return False
        heute = heute or _dt.date.today()
        try:
            return heute > _dt.date.fromisoformat(self.expiry_date)
        except ValueError:
            return True      # unlesbares Datum gilt als abgelaufen

    def covers_module(self, modul: str) -> bool:
        return "*" in self.modules or modul in self.modules

    def summary(self) -> dict:
        return {
            "lizenz_id": self.license_id, "kunde": self.customer,
            "produkt": self.product, "module": self.modules,
            "lizenztyp": self.license_type, "instanzen": self.allowed_instances,
            "instanz_id": self.instance_id, "aktiviert_am": self.activation_date,
            "gueltig_bis": self.expiry_date or "unbefristet",
            "wartung_bis": self.maintenance_until or "-",
            "ausgestellt_von": self.issuer,
        }


@dataclass
class LicenseStatus:
    """Ergebnis der Lizenzpruefung."""

    state: LicenseState
    message: str
    license: License | None = None
    required: bool = True
    instance_id: str = ""
    carrier: dict = field(default_factory=dict)
    hints: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return self.state in (LicenseState.GUELTIG, LicenseState.NICHT_ERFORDERLICH)

    @property
    def productive_allowed(self) -> bool:
        """Darf die Anwendung produktiv genutzt werden?"""
        return self.valid or not self.required

    def as_dict(self) -> dict:
        return {
            "zustand": self.state.value, "meldung": self.message,
            "gueltig": self.valid, "produktiv_erlaubt": self.productive_allowed,
            "lizenz_erforderlich": self.required, "instanz_id": self.instance_id,
            "datentraeger": self.carrier, "hinweise": self.hints,
            "lizenz": self.license.summary() if self.license else None,
        }

    def as_text(self) -> str:
        zeilen = [f"Lizenzzustand: {self.state.value}", "", self.message, ""]
        if self.license is not None:
            for schluessel, wert in self.license.summary().items():
                zeilen.append(f"  {schluessel:16s}: {wert}")
        else:
            zeilen.append(f"  Instanz-ID      : {self.instance_id or 'unbekannt'}")
        if self.hints:
            zeilen += ["", "Hinweise:"] + [f"  - {h}" for h in self.hints]
        return "\n".join(zeilen)
