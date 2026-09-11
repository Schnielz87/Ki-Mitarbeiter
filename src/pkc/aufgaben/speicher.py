"""Wo die Aufgaben liegen.

Eine einzelne Datei ``aufgaben.json`` unter ``workspace/aufgaben`` -
Kundendaten wie alles dort. Welche Sicherung wann lief, geht nur dieses
Unternehmen etwas an.

Bewusst keine Datenbanktabelle: es sind wenige Eintraege, sie werden
selten geschrieben, und eine lesbare Datei laesst sich im Zweifel von
Hand ansehen. Geschrieben wird ueber eine Zwischendatei, damit ein
Abbruch keine halbe Aufgabenliste hinterlaesst.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..artefakte.werk import dateiname
from ..logging_setup import get_logger
from .ausloeser import Ausloeser
from .modell import Aufgabe

log = get_logger(__name__)

DATEI = "aufgaben.json"


class AufgabenFehler(RuntimeError):
    """Etwas stimmt nicht - mit einem Satz fuer den Menschen."""


class Aufgabenspeicher:
    """Verwaltet die Aufgaben eines Kundenbereichs."""

    def __init__(self, paths, audit=None):
        self.paths = paths
        self.audit = audit

    @property
    def ordner(self) -> Path:
        return self.paths.get("aufgaben")

    def _datei(self) -> Path:
        return self.ordner / DATEI

    # -- Lesen und Schreiben -------------------------------------------
    def _lesen(self) -> list[dict]:
        datei = self._datei()
        if not datei.is_file():
            return []
        try:
            inhalt = json.loads(datei.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as fehler:
            # Eine beschaedigte Datei darf den Bereich nicht unbenutzbar
            # machen. Sie wird gemeldet, nicht ueberschrieben.
            log.warning("Aufgabenliste nicht lesbar: %s", fehler)
            return []
        return inhalt if isinstance(inhalt, list) else []

    def _schreiben(self, eintraege: list[dict]) -> None:
        datei = self._datei()
        datei.parent.mkdir(parents=True, exist_ok=True)
        vorlaeufig = datei.with_suffix(".json.teil")
        vorlaeufig.write_text(
            json.dumps(eintraege, ensure_ascii=False, indent=2),
            encoding="utf-8")
        vorlaeufig.replace(datei)

    # -- Auskunft ------------------------------------------------------
    def liste(self) -> list[Aufgabe]:
        aufgaben = []
        for eintrag in self._lesen():
            try:
                aufgabe = Aufgabe.aus_dict(eintrag)
            except Exception as fehler:         # pragma: no cover - defensiv
                log.warning("Aufgabe uebersprungen: %s", fehler)
                continue
            if aufgabe.kennung:
                aufgaben.append(aufgabe)
        return sorted(aufgaben, key=lambda a: a.name.lower())

    def holen(self, kennung: str) -> Aufgabe | None:
        for aufgabe in self.liste():
            if aufgabe.kennung == kennung:
                return aufgabe
        return None

    # -- Aendern -------------------------------------------------------
    def anlegen(self, name: str, aktion: str, ausloeser: Ausloeser,
                aktiv: bool = True) -> Aufgabe:
        if not (name or "").strip():
            raise AufgabenFehler("Eine Aufgabe braucht einen Namen.")
        if not (aktion or "").strip():
            raise AufgabenFehler("Eine Aufgabe braucht eine Aktion.")
        aufgabe = Aufgabe(
            kennung=self._freie_kennung(name), name=name.strip(),
            aktion=aktion, ausloeser=ausloeser, aktiv=aktiv,
            angelegt=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.sichern(aufgabe)
        self._melden("aufgabe.angelegt", aufgabe)
        log.info("Aufgabe angelegt: %s (%s)", aufgabe.name, aufgabe.kennung)
        return aufgabe

    def sichern(self, aufgabe: Aufgabe) -> Aufgabe:
        """Schreibt eine Aufgabe zurueck - neu oder geaendert."""
        eintraege = [e for e in self._lesen()
                     if e.get("kennung") != aufgabe.kennung]
        eintraege.append(aufgabe.as_dict())
        self._schreiben(eintraege)
        return aufgabe

    def entfernen(self, kennung: str) -> bool:
        aufgabe = self.holen(kennung)
        if aufgabe is None:
            return False
        self._schreiben([e for e in self._lesen()
                         if e.get("kennung") != kennung])
        self._melden("aufgabe.entfernt", aufgabe)
        return True

    def umschalten(self, kennung: str, aktiv: bool) -> Aufgabe:
        aufgabe = self.holen(kennung)
        if aufgabe is None:
            raise AufgabenFehler(f"Diese Aufgabe gibt es nicht: {kennung}")
        aufgabe.aktiv = aktiv
        self.sichern(aufgabe)
        self._melden("aufgabe.aktiviert" if aktiv else "aufgabe.pausiert",
                     aufgabe)
        return aufgabe

    def _freie_kennung(self, name: str) -> str:
        grund = dateiname(name, "aufgabe").lower()
        vorhanden = {e.get("kennung") for e in self._lesen()}
        if grund not in vorhanden:
            return grund
        nummer = 2
        while f"{grund}_{nummer}" in vorhanden:
            nummer += 1
        return f"{grund}_{nummer}"

    def _melden(self, aktion: str, aufgabe: Aufgabe) -> None:
        if self.audit is None:
            return
        try:
            self.audit.record(aktion, "aufgabe", aufgabe.kennung, status="ok",
                              aktion_kennung=aufgabe.aktion)
        except Exception as ausnahme:       # Protokoll darf nie blockieren
            log.debug("Aufgabe nicht protokolliert: %s", ausnahme)
