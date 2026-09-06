"""Was ein Plugin darf - und wie es an den Kern kommt (E5.102, E5.103, E5.106).

Ein Plugin bekommt **nicht** die Anwendung, sondern diesen Kontext. Jede
Funktion darin prueft vorher die erteilte Berechtigung. Was nicht erteilt
wurde, gibt es nicht.

Ehrlich zur Reichweite (E5.108): das ist eine **vermittelte Schnittstelle**,
keine Sandkastenumgebung des Betriebssystems. Ein Plugin ist Python-Code und
laeuft im selben Prozess mit den Rechten der Anwendung; wer eigenen Code
ausfuehrt, kann die Vermittlung technisch umgehen. Der Schutz besteht
deshalb aus drei Teilen, die zusammengehoeren:

1. nur signierte Pakete gelten als vertrauenswuerdig (``paket.py``),
2. jede Berechtigung wird einzeln erteilt und protokolliert,
3. der Benutzer sieht vor der Installation, was verlangt wird.

Eine Trennung auf Prozessebene ist damit **nicht** erreicht. Das ist in
PLUGIN_KONZEPT.md als offener Punkt festgehalten und nicht anders behauptet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..logging_setup import get_logger
from .modell import BerechtigungFehlt, Manifest

log = get_logger(__name__)


@dataclass
class Werkzeug:
    """Eine Faehigkeit, die ein Plugin anmeldet (E5.103)."""

    name: str
    beschreibung: str
    funktion: Callable[..., Any]
    plugin: str = ""


@dataclass
class Pluginkontext:
    """Die Schnittstelle, die ein Plugin beim Anmelden bekommt."""

    manifest: Manifest
    berechtigungen: frozenset[str]
    #: Ordner nur fuer dieses Plugin - im Kundenbereich, nie im Programmordner.
    datenordner: Path
    #: Zugaenge, die der Kern bereitstellt. Nie direkt an das Plugin gegeben.
    _memory: Any = None
    _knowledge: Any = None
    _audit: Any = None
    _artefakte: Any = None
    _netz_erlaubt: bool = False
    werkzeuge: list[Werkzeug] = field(default_factory=list)

    # -- Rechtepruefung ------------------------------------------------
    def _verlangt(self, recht: str) -> None:
        if recht not in self.berechtigungen:
            raise BerechtigungFehlt(
                f"Das Plugin '{self.manifest.id}' hat versucht, "
                f"'{recht}' zu nutzen. Diese Berechtigung wurde nicht erteilt."
            )

    def darf(self, recht: str) -> bool:
        return recht in self.berechtigungen

    # -- Anmeldungen ---------------------------------------------------
    def werkzeug_anmelden(self, name: str, beschreibung: str,
                          funktion: Callable[..., Any]) -> Werkzeug:
        """Meldet eine neue Faehigkeit an (E5.103). Braucht keine Berechtigung.

        Eine angemeldete Faehigkeit tut fuer sich noch nichts - sie wird erst
        aufgerufen, wenn der Benutzer sie nutzt, und kann dabei nur, was die
        erteilten Rechte hergeben.
        """
        werkzeug = Werkzeug(name=name, beschreibung=beschreibung,
                            funktion=funktion, plugin=self.manifest.id)
        self.werkzeuge.append(werkzeug)
        return werkzeug

    def dateiformat_anmelden(self, schreiber) -> None:
        """Meldet ein zusaetzliches Ausgabeformat an (E4, Kategorie FILE_HANDLER)."""
        from ..artefakte import registrieren

        registrieren(schreiber)

    # -- Unternehmensgedaechtnis ---------------------------------------
    def gedaechtnis_lesen(self, schluessel: str):
        self._verlangt("COMPANY_MEMORY_READ")
        return self._memory.get(schluessel) if self._memory else None

    def gedaechtnis_liste(self, limit: int = 100):
        self._verlangt("COMPANY_MEMORY_READ")
        return self._memory.list(limit=limit) if self._memory else []

    def gedaechtnis_schreiben(self, schluessel: str, titel: str, inhalt: str,
                              kategorie: str = "") -> None:
        self._verlangt("COMPANY_MEMORY_WRITE")
        if self._memory is None:
            return
        self._memory.set(schluessel, titel, inhalt, source=f"plugin:{self.manifest.id}",
                         category=kategorie)
        self.protokollieren("gedaechtnis_geaendert", schluessel)

    # -- Fachwissen ----------------------------------------------------
    def wissen_suchen(self, frage: str, limit: int = 8):
        self._verlangt("KNOWLEDGE_READ")
        if self._knowledge is None:
            return []
        return self._knowledge.search(frage, limit=limit)

    # -- Dateien -------------------------------------------------------
    def datei_lesen(self, name: str) -> bytes:
        self._verlangt("FILE_READ")
        return (self.datenordner / _sicher(name)).read_bytes()

    def datei_schreiben(self, name: str, inhalt: bytes | str) -> Path:
        self._verlangt("FILE_WRITE")
        ziel = self.datenordner / _sicher(name)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(inhalt, str):
            ziel.write_text(inhalt, encoding="utf-8")
        else:
            ziel.write_bytes(inhalt)
        return ziel

    def artefakt_erzeugen(self, inhalt, format: str, name: str = ""):
        self._verlangt("FILE_WRITE")
        if self._artefakte is None:
            raise BerechtigungFehlt("Die Dateiausgabe steht nicht zur Verfuegung.")
        return self._artefakte.erzeugen(inhalt, format, name,
                                        unterordner=f"plugin_{self.manifest.id}")

    # -- Netz ----------------------------------------------------------
    def netz_abrufen(self, adresse: str, zeitgrenze: float = 30.0) -> bytes:
        """Ein Abruf - nur mit Recht **und** nur, wenn der Modus es zulaesst.

        Die Berechtigung allein genuegt nicht: im Betriebsmodus OFFLINE
        greift auch ein berechtigtes Plugin nicht ins Netz (E5.105).
        """
        self._verlangt("NETWORK_ACCESS")
        if not self._netz_erlaubt:
            raise BerechtigungFehlt(
                "Die Anwendung arbeitet gerade ohne Netzzugriff. Das Plugin "
                f"'{self.manifest.id}' darf deshalb nichts abrufen."
            )
        import urllib.request

        from ..updater.http_client import _ssl_kontext

        self.protokollieren("netzabruf", adresse)
        anfrage = urllib.request.Request(adresse, headers={"User-Agent": "PORTIVA-Plugin"})
        with urllib.request.urlopen(anfrage, timeout=zeitgrenze,
                                    context=_ssl_kontext()) as antwort:
            return antwort.read()

    # -- Protokoll -----------------------------------------------------
    def protokollieren(self, aktion: str, gegenstand: str = "", **angaben) -> None:
        """Jede nennenswerte Handlung eines Plugins wird festgehalten (E5.118)."""
        log.info("Plugin %s: %s %s", self.manifest.id, aktion, gegenstand)
        if self._audit is None:
            return
        try:
            self._audit.record(f"plugin_{aktion}", "plugin", self.manifest.id,
                               gegenstand=gegenstand, **angaben)
        except Exception as fehler:                     # Protokoll darf nie blockieren
            log.debug("Plugin-Protokoll fehlgeschlagen: %s", fehler)


def _sicher(name: str) -> str:
    reiner = str(name).replace("\\", "/")
    if reiner.startswith("/") or ".." in Path(reiner).parts:
        raise BerechtigungFehlt(
            f"Ein Plugin darf nur in seinem eigenen Ordner arbeiten: {name}"
        )
    return reiner
