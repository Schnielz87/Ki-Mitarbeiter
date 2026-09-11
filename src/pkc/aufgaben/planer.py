"""Der Planer: prueft, was faellig ist, und fuehrt es aus.

**Weg C, Vorgabe A.** PORTIVA laeuft nur, solange es geoeffnet ist. Der
Planer prueft deshalb waehrend des Betriebs in einem ruhigen Takt, was
faellig ist, und holt beim Start nach, was ausgefallen ist. Wer mehr
will - eine naechtliche Auswertung ohne offenes Fenster -, schaltet die
Windows-Aufgabenplanung ausdruecklich dazu und erfaehrt dabei, was das
auf dem Rechner hinterlaesst (siehe ``windows_planung.py``).

**Vier Gruende, aus denen ein faelliger Lauf nicht stattfindet** - und
in allen vieren gilt dasselbe: der Lauf wird als *uebersprungen*
vermerkt, und die Aufgabe bleibt faellig. Sie gilt nicht als erledigt,
nur weil sie nicht laufen konnte.

1. Die Aufgabe ist pausiert.
2. Die Aktion gibt es nicht (mehr) - etwa nach einem entfernten Plugin.
3. Die Aktion braucht Internet, und es ist keines da.
4. Die Aktion gibt etwas nach aussen und niemand hat es bestaetigt.

Der vierte Punkt ist der wichtigste. Die Erlaubnis beim Anlegen genuegt
dort nicht; gefragt wird bei **jeder** Ausfuehrung. Eine Automation, die
nach der ersten Zustimmung dauerhaft Daten verschickt, waere genau das,
was die Sicherheitsvorgaben ausschliessen.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from ..logging_setup import get_logger
from .aktionen import hole as aktion_holen
from .modell import Aufgabe, Lauf

log = get_logger(__name__)

#: Wie oft waehrend des Betriebs nachgesehen wird. Eine Minute reicht:
#: die kuerzeste erlaubte Wiederholung ist eine Stunde.
TAKT_SEKUNDEN = 60


class Planer:
    """Prueft Faelligkeiten und fuehrt Aufgaben aus."""

    def __init__(self, speicher, controller, audit=None):
        self.speicher = speicher
        self.controller = controller
        self.audit = audit

    # -- Auskunft ------------------------------------------------------
    def faellige(self, jetzt: datetime | None = None,
                 start: bool = False) -> list[Aufgabe]:
        jetzt = jetzt or datetime.now()
        return [a for a in self.speicher.liste()
                if a.faellig(jetzt, start=start)]

    # -- Ausfuehren ----------------------------------------------------
    def ausfuehren(self, kennung: str, *, jetzt: datetime | None = None,
                   bestaetigt: bool = False,
                   von_hand: bool = False) -> Lauf:
        """Fuehrt eine Aufgabe aus und vermerkt den Lauf.

        ``von_hand`` bedeutet: der Mensch hat gerade darauf gedrueckt.
        Dann laeuft sie auch, wenn sie pausiert ist - ein Knopf "Jetzt
        ausfuehren" muss ausfuehren.
        """
        jetzt = jetzt or datetime.now()
        aufgabe = self.speicher.holen(kennung)
        if aufgabe is None:
            raise KeyError(f"Diese Aufgabe gibt es nicht: {kennung}")

        grund = self._warum_nicht(aufgabe, bestaetigt, von_hand)
        if grund:
            return self._vermerken(aufgabe, jetzt, "uebersprungen", grund, 0.0)

        aktion = aktion_holen(aufgabe.aktion)
        begonnen = time.monotonic()
        try:
            meldung = aktion.funktion(self.controller) or "Erledigt."
        except Exception as fehler:
            dauer = time.monotonic() - begonnen
            log.warning("Aufgabe fehlgeschlagen: %s (%s)", aufgabe.name, fehler)
            return self._vermerken(aufgabe, jetzt, "fehler", str(fehler),
                                   dauer, gelaufen=True)
        dauer = time.monotonic() - begonnen
        return self._vermerken(aufgabe, jetzt, "ok", meldung, dauer,
                               gelaufen=True)

    def _warum_nicht(self, aufgabe: Aufgabe, bestaetigt: bool,
                     von_hand: bool) -> str:
        if not aufgabe.aktiv and not von_hand:
            return "Die Aufgabe ist pausiert."
        aktion = aktion_holen(aufgabe.aktion)
        if aktion is None:
            return (f"Die Aktion „{aufgabe.aktion}“ gibt es nicht mehr. "
                    "Kam sie aus einem Plugin, ist dieses entfernt oder "
                    "abgeschaltet.")
        if aktion.nach_aussen and not bestaetigt:
            return ("Diese Aktion gibt Daten nach aussen. Sie braucht bei "
                    "jeder Ausfuehrung eine ausdrueckliche Bestaetigung - "
                    "die Erlaubnis beim Anlegen genuegt dafuer nicht.")
        if aktion.braucht_netz and not self._online():
            return ("Keine Internetverbindung. Die Aufgabe bleibt faellig "
                    "und laeuft, sobald wieder eine besteht.")
        return ""

    def _online(self) -> bool:
        try:
            return bool(self.controller.lage.online_moeglich)
        except Exception:                       # pragma: no cover - defensiv
            return False

    def _vermerken(self, aufgabe: Aufgabe, jetzt: datetime, ergebnis: str,
                   meldung: str, dauer: float,
                   gelaufen: bool = False) -> Lauf:
        lauf = Lauf(zeitpunkt=jetzt.strftime("%Y-%m-%d %H:%M:%S"),
                    ergebnis=ergebnis, meldung=meldung, dauer=dauer)
        aufgabe.vermerken(lauf)
        if gelaufen:
            # Nur ein wirklich gelaufener Versuch verschiebt die
            # Faelligkeit - auch ein fehlgeschlagener. Sonst liefe eine
            # Aufgabe, die jedes Mal scheitert, im Minutentakt weiter.
            aufgabe.letzter_lauf = jetzt.isoformat(timespec="seconds")
        self.speicher.sichern(aufgabe)
        self._melden(aufgabe, lauf)
        return lauf

    def _melden(self, aufgabe: Aufgabe, lauf: Lauf) -> None:
        if self.audit is None:
            return
        try:
            self.audit.record("aufgabe.gelaufen", "aufgabe", aufgabe.kennung,
                              status=lauf.ergebnis, meldung=lauf.meldung[:200])
        except Exception as ausnahme:       # Protokoll darf nie blockieren
            log.debug("Lauf nicht protokolliert: %s", ausnahme)

    # -- Der Durchlauf -------------------------------------------------
    def durchlauf(self, *, jetzt: datetime | None = None,
                  start: bool = False,
                  bestaetigen: Callable[[Aufgabe], bool] | None = None
                  ) -> list[Lauf]:
        """Fuehrt alles aus, was jetzt faellig ist.

        ``bestaetigen`` wird nur fuer Aktionen mit Aussenwirkung gefragt.
        Fehlt die Funktion, gilt das als "nicht bestaetigt" - Schweigen
        ist keine Zustimmung.
        """
        jetzt = jetzt or datetime.now()
        laeufe = []
        for aufgabe in self.faellige(jetzt, start=start):
            aktion = aktion_holen(aufgabe.aktion)
            bestaetigt = False
            if aktion is not None and aktion.nach_aussen:
                bestaetigt = bool(bestaetigen and bestaetigen(aufgabe))
            laeufe.append(self.ausfuehren(aufgabe.kennung, jetzt=jetzt,
                                          bestaetigt=bestaetigt))
        return laeufe
