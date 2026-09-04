"""ERP-Connectoren fuer SAP, Wilken und DATEV.

**Ehrlicher Stand:** Diese drei Connectoren sind **nicht** angebunden.  Fuer
eine echte Integration fehlen Angaben, die nur der Betreiber liefern kann
(Produktversion, Schnittstellenart, Zugaenge, Netzwerkfreigaben).  Deshalb
melden sie klar, dass sie nicht eingerichtet sind, und liefern die Liste der
zu klaerenden Punkte - statt Daten vorzutaeuschen.

Der Weg zur echten Anbindung ist vorbereitet: Sobald die Fragen beantwortet
sind, wird je System entweder der generische REST-Connector konfiguriert oder
eine spezialisierte Klasse davon abgeleitet.
"""

from __future__ import annotations

from .base import Connector, ConnectorResult, NotConfigured


class _ErpStub(Connector):
    """Gemeinsame Basis der noch nicht angebundenen ERP-Systeme."""

    integration_paths: tuple[str, ...] = ()

    def configured(self) -> tuple[bool, str]:
        return False, (
            f"{self.name} ist in dieser Installation nicht angebunden. "
            "Vor einer Integration sind die offenen Fragen zu klaeren "
            "(siehe ERP_CONNECTOR_KONZEPT.md)."
        )

    def read(self, query: str = "", **kwargs) -> ConnectorResult:
        raise NotConfigured(
            f"{self.name} ist nicht angebunden. Es werden keine Daten geliefert. "
            f"Moegliche Integrationswege: {', '.join(self.integration_paths)}."
        )

    def _perform_write(self, payload: dict, approval_uid: str) -> ConnectorResult:
        raise NotConfigured(
            f"{self.name} ist nicht angebunden. Es wird nichts geschrieben."
        )


class SapConnector(_ErpStub):
    connector_id = "sap"
    name = "SAP"
    system = "SAP ERP / S/4HANA"
    integration_paths = ("OData ueber SAP Gateway", "RFC/BAPI", "CDS-Views", "Dateiexport")
    open_questions = (
        "Welche SAP-Version und welches Release (ECC 6.0, S/4HANA on premise, Cloud)?",
        "Steht ein SAP Gateway mit OData-Services zur Verfuegung?",
        "Ist RFC/BAPI-Zugriff erlaubt und ist ein technischer Benutzer vorhanden?",
        "Welche Berechtigungsobjekte hat dieser Benutzer (nur lesend?)?",
        "Ist ein VPN-Zugang oder eine Netzwerkfreigabe erforderlich?",
        "Gibt es ein Qualitaetssystem fuer Tests?",
        "Welche Belegarten und Buchungskreise sind relevant?",
    )


class WilkenConnector(_ErpStub):
    connector_id = "wilken"
    name = "Wilken"
    system = "Wilken ERP / Wilken P/5"
    integration_paths = ("REST-Schnittstelle", "SOAP", "Datenbanksicht (lesend)", "Dateiimport")
    open_questions = (
        "Welches Wilken-Produkt und welche Version wird eingesetzt?",
        "Welche Schnittstellen sind lizenziert und freigeschaltet?",
        "Ist ein lesender Datenbankzugriff erlaubt, oder nur die API?",
        "Welche Mandanten und Buchungskreise sind relevant?",
        "Wie erfolgt die Authentifizierung?",
    )


class DatevConnector(_ErpStub):
    connector_id = "datev"
    name = "DATEV"
    system = "DATEV Rechnungswesen / Unternehmen online"
    integration_paths = (
        "DATEV-Format (EXTF) fuer Buchungsstapel - Dateiimport/-export",
        "DATEVconnect (lokale REST-Schnittstelle)",
        "DATEV Unternehmen online API",
    )
    open_questions = (
        "Erfolgt der Austausch ueber DATEV-Format-Dateien oder ueber DATEVconnect?",
        "Welche Beraternummer und Mandantennummer gelten?",
        "Welcher Kontenrahmen (SKR03, SKR04) und welche Sachkontenlaenge?",
        "Wer besitzt die erforderlichen DATEV-Zugaenge und Zertifikate?",
        "Sollen Buchungsstapel nur erzeugt (Vorschlag) oder auch uebertragen werden?",
    )
