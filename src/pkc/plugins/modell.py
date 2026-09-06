"""Was ein Plugin ist: Manifest, Kategorien, Berechtigungen (Erweiterung E5).

Die Erweiterung verlangt ein allgemeines Erweiterungssystem - nicht nur
Connectoren. Ein Plugin bringt eine neue Faehigkeit mit, ohne dass der Kern
neu gebaut wird.

Hier steht nur die Beschreibung eines Plugins. Was beim Installieren und
Laden geschieht, steht in ``verwaltung.py``; was ein Plugin darf, in
``kontext.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Fassung der Plugin-Schnittstelle. Ein Plugin nennt die Fassung, gegen die
#: es gebaut wurde; passt sie nicht, wird es nicht geladen (E5.110).
API_VERSION = 1

#: Kategorien nach E5.104 - erweiterbar, aber benannt, damit die Oberflaeche
#: Plugins gruppieren kann.
KATEGORIEN = (
    "CONNECTOR",        # externe Dienste, ERP, Cloud, E-Mail
    "KNOWLEDGE",        # zusaetzliche Wissensquellen und Fachmodule
    "AUTOMATION",       # wiederkehrende Ablaeufe
    "FILE_HANDLER",     # zusaetzliche Ausgabeformate (E4)
    "MODEL",            # weitere Sprachmodelle oder Modellzugaenge
    "UI",               # Ansichten und Auswertungen
)

#: Berechtigungen nach E5.106. Jede ist einzeln zu erteilen; ohne Erteilung
#: gibt der Kontext die Funktion nicht heraus.
BERECHTIGUNGEN: dict[str, str] = {
    "COMPANY_MEMORY_READ": "Unternehmensgedaechtnis lesen",
    "COMPANY_MEMORY_WRITE": "Unternehmensgedaechtnis aendern",
    "KNOWLEDGE_READ": "Fachwissen durchsuchen",
    "KNOWLEDGE_WRITE": "Fachwissen ergaenzen",
    "DATABASE_READ": "Datenbank lesen",
    "DATABASE_WRITE": "Datenbank schreiben",
    "FILE_READ": "Dateien im Kundenbereich lesen",
    "FILE_WRITE": "Dateien im Kundenbereich schreiben",
    "CALENDAR_READ": "Kalender lesen",
    "CALENDAR_WRITE": "Kalendereintraege anlegen",
    "NETWORK_ACCESS": "Verbindung ins Internet oder Firmennetz",
    "MICROPHONE_ACCESS": "Mikrofon verwenden",
}

#: Berechtigungen, die besonders schwer wiegen: sie koennen Unternehmensdaten
#: veraendern oder nach aussen tragen. Die Oberflaeche hebt sie hervor.
SCHWERWIEGEND = frozenset({
    "COMPANY_MEMORY_WRITE", "DATABASE_WRITE", "KNOWLEDGE_WRITE",
    "FILE_WRITE", "NETWORK_ACCESS", "MICROPHONE_ACCESS", "CALENDAR_WRITE",
})

_ID = re.compile(r"^[a-z][a-z0-9_\-]{2,63}$")
_VERSION = re.compile(r"^\d+(\.\d+){0,3}([a-z0-9\-]*)$")


class PluginFehler(RuntimeError):
    """Ein Plugin liess sich nicht pruefen, installieren oder laden."""


class BerechtigungFehlt(PluginFehler):
    """Das Plugin hat etwas verlangt, wofuer es keine Erlaubnis hat."""


@dataclass
class Manifest:
    """Die Selbstbeschreibung eines Plugins (E5.101)."""

    id: str
    name: str
    version: str
    api: int = API_VERSION
    kategorie: str = "AUTOMATION"
    einstieg: str = ""                      # Modul:Funktion, z.B. "plugin:anmelden"
    beschreibung: str = ""
    autor: str = ""
    lizenz: str = ""
    #: Verlangte Berechtigungen (E5.106).
    berechtigungen: list[str] = field(default_factory=list)
    #: Braucht das Plugin eine Verbindung? (E5.105)
    benoetigt_netz: bool = False
    #: Weitere Plugins, die vorhanden sein muessen (E5.111).
    benoetigt_plugins: list[str] = field(default_factory=list)
    #: Datei -> SHA-256. Damit ist der Code Teil der Signatur (E5.109).
    dateien: dict[str, str] = field(default_factory=dict)

    # -- Pruefung ------------------------------------------------------
    def pruefen(self) -> None:
        """Wirft ``PluginFehler``, wenn das Manifest nicht tragfaehig ist."""
        if not _ID.match(self.id or ""):
            raise PluginFehler(
                "Die Plugin-Kennung muss klein geschrieben sein und darf nur "
                f"Buchstaben, Ziffern, '-' und '_' enthalten: '{self.id}'"
            )
        if not self.name.strip():
            raise PluginFehler("Dem Plugin fehlt ein Name.")
        if not _VERSION.match(self.version or ""):
            raise PluginFehler(f"Unbrauchbare Versionsangabe: '{self.version}'")
        if self.kategorie not in KATEGORIEN:
            raise PluginFehler(
                f"Unbekannte Kategorie '{self.kategorie}'. Moeglich: {', '.join(KATEGORIEN)}"
            )
        if ":" not in (self.einstieg or ""):
            raise PluginFehler(
                "Der Einstieg muss 'modul:funktion' lauten - so weiss der Kern, "
                "was er aufrufen soll."
            )
        unbekannt = [b for b in self.berechtigungen if b not in BERECHTIGUNGEN]
        if unbekannt:
            raise PluginFehler(
                "Unbekannte Berechtigung(en): " + ", ".join(unbekannt)
                + ". Bekannt sind: " + ", ".join(sorted(BERECHTIGUNGEN))
            )
        if self.benoetigt_netz and "NETWORK_ACCESS" not in self.berechtigungen:
            raise PluginFehler(
                "Das Plugin gibt an, eine Verbindung zu brauchen, verlangt aber "
                "keine Berechtigung NETWORK_ACCESS."
            )

    @property
    def modul(self) -> str:
        return self.einstieg.split(":", 1)[0]

    @property
    def funktion(self) -> str:
        return self.einstieg.split(":", 1)[1]

    @property
    def schwerwiegende_rechte(self) -> list[str]:
        return [b for b in self.berechtigungen if b in SCHWERWIEGEND]

    def as_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "version": self.version, "api": self.api,
            "kategorie": self.kategorie, "einstieg": self.einstieg,
            "beschreibung": self.beschreibung, "autor": self.autor, "lizenz": self.lizenz,
            "berechtigungen": sorted(self.berechtigungen),
            "benoetigt_netz": self.benoetigt_netz,
            "benoetigt_plugins": sorted(self.benoetigt_plugins),
            "dateien": dict(sorted(self.dateien.items())),
        }

    @classmethod
    def from_dict(cls, daten: dict) -> "Manifest":
        if not isinstance(daten, dict):
            raise PluginFehler("Das Manifest ist keine Zuordnung von Schluessel zu Wert.")
        unbekannt = set(daten) - {f for f in cls.__dataclass_fields__}
        if unbekannt:
            raise PluginFehler(
                "Unbekannte Angaben im Manifest: " + ", ".join(sorted(unbekannt))
            )
        manifest = cls(
            id=str(daten.get("id", "")), name=str(daten.get("name", "")),
            version=str(daten.get("version", "")), api=int(daten.get("api", API_VERSION)),
            kategorie=str(daten.get("kategorie", "AUTOMATION")).upper(),
            einstieg=str(daten.get("einstieg", "")),
            beschreibung=str(daten.get("beschreibung", "")),
            autor=str(daten.get("autor", "")), lizenz=str(daten.get("lizenz", "")),
            berechtigungen=[str(b).upper() for b in daten.get("berechtigungen", [])],
            benoetigt_netz=bool(daten.get("benoetigt_netz", False)),
            benoetigt_plugins=[str(p) for p in daten.get("benoetigt_plugins", [])],
            dateien={str(k): str(v) for k, v in (daten.get("dateien") or {}).items()},
        )
        manifest.pruefen()
        return manifest
