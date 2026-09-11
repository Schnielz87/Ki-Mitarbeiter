"""Weg B: PORTIVA auch ohne offenes Fenster starten lassen.

**Das ist die Ausnahme, nicht die Vorgabe.** Im Normalfall laufen
Aufgaben, solange PORTIVA offen ist, und Verpasstes wird beim naechsten
Start nachgeholt. Das genuegt fuer einen Arbeitsplatz, der tagsueber
ohnehin laeuft, und es hinterlaesst auf dem Rechner nichts.

Wer eine naechtliche Auswertung braucht, kann PORTIVA in die
Aufgabenplanung von Windows eintragen lassen. Das geht - und es
widerspricht dem Grundgedanken "portabel, keine unkontrollierte Ablage
auf dem Wirtsrechner" (Abschnitt 20). Deshalb:

* Es passiert **nur auf ausdrueckliche Anweisung**.
* Vorher steht im Klartext da, was zurueckbleibt - ``SPUREN``.
* Es laesst sich mit einem Knopf wieder entfernen, und das Entfernen
  wird geprueft, nicht behauptet.

**Ein Eintrag, nicht einer je Aufgabe.** Windows startet PORTIVA, und
PORTIVA entscheidet dann selbst, was faellig ist. Zehn Windows-Eintraege
fuer zehn Aufgaben waeren zehn Dinge, die man einzeln wieder loswerden
muss.

**Der Haken, den man kennen muss:** der Eintrag merkt sich einen Pfad.
Steckt der Datentraeger das naechste Mal an einem anderen Buchstaben,
zeigt er ins Leere. ``zustand()`` prueft das und sagt es.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..logging_setup import get_logger

log = get_logger(__name__)

#: Name des Eintrags in der Windows-Aufgabenplanung.
EINTRAG = "PORTIVA - geplante Aufgaben"

#: Was auf dem Rechner zurueckbleibt. Wortwoertlich das, was der Mensch
#: vor der Zustimmung zu lesen bekommt.
SPUREN = (
    "Wenn Sie das einschalten, bleibt auf DIESEM Computer etwas zurueck:\n\n"
    "• Ein Eintrag in der Aufgabenplanung von Windows mit dem Namen "
    f"„{EINTRAG}“.\n"
    "• Darin der Pfad zu PORTIVA auf Ihrem Datentraeger und die Uhrzeit.\n"
    "• Windows fuehrt darueber Protokoll, wann der Eintrag gelaufen ist.\n\n"
    "Das ist alles - keine Installation, keine Registrierungsschluessel "
    "ausserhalb der Aufgabenplanung, keine Dateien im Programmordner von "
    "Windows. Ihre Unternehmensdaten bleiben auf dem Datentraeger.\n\n"
    "Zwei Dinge sollten Sie wissen:\n\n"
    "1. Der Eintrag merkt sich den Pfad. Steckt der Datentraeger das "
    "naechste Mal an einem anderen Laufwerksbuchstaben, zeigt er ins "
    "Leere - PORTIVA sagt Ihnen das dann.\n"
    "2. Auf einem fremden Rechner sollten Sie das nicht einschalten. "
    "Dort gehoert der Eintrag nicht hin, und Sie muessten daran denken, "
    "ihn wieder zu entfernen."
)


@dataclass(frozen=True)
class Zustand:
    """Was die Aufgabenplanung von Windows gerade hergibt."""

    moeglich: bool
    eingetragen: bool = False
    uhrzeit: str = ""
    pfad: str = ""
    hinweis: str = ""

    @property
    def pfad_stimmt(self) -> bool:
        return bool(self.pfad) and Path(self.pfad).exists()


def verfuegbar() -> bool:
    """Nur unter Windows, und nur wenn schtasks da ist."""
    if os.name != "nt":
        return False
    return _schtasks(["/Query", "/?"]).erfolg


@dataclass(frozen=True)
class _Ergebnis:
    erfolg: bool
    ausgabe: str = ""


def _schtasks(argumente: list[str], _laufen=None) -> _Ergebnis:
    """Ruft schtasks auf. ``_laufen`` ist fuer Tests austauschbar."""
    laufen = _laufen or _wirklich_laufen
    try:
        return laufen(["schtasks", *argumente])
    except Exception as fehler:                 # pragma: no cover - defensiv
        log.debug("schtasks nicht aufrufbar: %s", fehler)
        return _Ergebnis(False, str(fehler))


def _wirklich_laufen(befehl: list[str]) -> _Ergebnis:   # pragma: no cover
    fertig = subprocess.run(befehl, capture_output=True, text=True,
                            timeout=30, check=False)
    return _Ergebnis(fertig.returncode == 0,
                     (fertig.stdout or "") + (fertig.stderr or ""))


class WindowsPlanung:
    """Traegt PORTIVA in die Aufgabenplanung von Windows ein - oder nicht.

    ``laufen`` ist die Funktion, die den Befehl ausfuehrt. Im Betrieb ist
    das ``subprocess``; im Test ein Doppel. So laesst sich der ganze
    Ablauf pruefen, ohne auf einem Testrechner Eintraege zu hinterlassen -
    was gerade bei dieser Funktion das Letzte waere, was man will.
    """

    def __init__(self, programm: Path | str, laufen=None,
                 windows: bool | None = None):
        self.programm = Path(programm)
        self._laufen = laufen or _wirklich_laufen
        self._windows = os.name == "nt" if windows is None else windows

    # -- Auskunft ------------------------------------------------------
    def zustand(self) -> Zustand:
        if not self._windows:
            return Zustand(
                moeglich=False,
                hinweis="Die Aufgabenplanung von Windows gibt es nur unter "
                        "Windows. Auf diesem System laufen Aufgaben, "
                        "solange PORTIVA geoeffnet ist.")
        ergebnis = _schtasks(["/Query", "/TN", EINTRAG, "/FO", "LIST"],
                             self._laufen)
        if not ergebnis.erfolg:
            return Zustand(moeglich=True, eingetragen=False,
                           hinweis="Kein Eintrag in der Aufgabenplanung. "
                                   "Aufgaben laufen, solange PORTIVA "
                                   "geoeffnet ist.")
        uhrzeit, pfad = _auslesen(ergebnis.ausgabe)
        zustand = Zustand(moeglich=True, eingetragen=True, uhrzeit=uhrzeit,
                          pfad=pfad)
        if pfad and not Path(pfad).exists():
            return Zustand(
                moeglich=True, eingetragen=True, uhrzeit=uhrzeit, pfad=pfad,
                hinweis=f"Der Eintrag zeigt auf {pfad} - dort liegt nichts "
                        "mehr. Wahrscheinlich hat der Datentraeger einen "
                        "anderen Laufwerksbuchstaben bekommen. Bitte neu "
                        "eintragen.")
        return zustand

    # -- Aendern -------------------------------------------------------
    def eintragen(self, uhrzeit: str = "07:00") -> Zustand:
        """Legt den Eintrag an. Nur nach ausdruecklicher Anweisung."""
        if not self._windows:
            raise RuntimeError(
                "Die Aufgabenplanung von Windows gibt es nur unter Windows.")
        if not self.programm.exists():
            raise RuntimeError(
                f"Die Programmdatei gibt es nicht: {self.programm}. Ein "
                "Eintrag, der ins Leere zeigt, ist schlimmer als keiner.")
        ergebnis = _schtasks(
            ["/Create", "/TN", EINTRAG, "/TR",
             f'"{self.programm}" aufgaben lauf', "/SC", "DAILY",
             "/ST", uhrzeit, "/F"], self._laufen)
        if not ergebnis.erfolg:
            raise RuntimeError(
                "Der Eintrag liess sich nicht anlegen. Windows meldet: "
                + (ergebnis.ausgabe.strip() or "nichts Naeheres") +
                "\n\nHaeufigster Grund: die Aufgabenplanung verlangt hier "
                "Administratorrechte.")
        log.info("Windows-Aufgabenplanung: Eintrag angelegt (%s)", uhrzeit)
        return self.zustand()

    def entfernen(self) -> bool:
        """Entfernt den Eintrag - und prueft, ob er wirklich weg ist.

        Geprueft, nicht behauptet: ``schtasks /Delete`` meldet auch dann
        Erfolg, wenn es nichts zu loeschen gab. Ein "entfernt", das
        nichts entfernt hat, waere eine Scheinerfuellung.
        """
        if not self._windows:
            return False
        _schtasks(["/Delete", "/TN", EINTRAG, "/F"], self._laufen)
        nachher = self.zustand()
        if nachher.eingetragen:
            log.warning("Windows-Aufgabenplanung: Eintrag ist noch da")
            return False
        log.info("Windows-Aufgabenplanung: Eintrag entfernt")
        return True


def _auslesen(ausgabe: str) -> tuple[str, str]:
    """Liest Uhrzeit und Pfad aus der Ausgabe von ``schtasks /Query``."""
    uhrzeit = ""
    pfad = ""
    for zeile in (ausgabe or "").splitlines():
        wert = zeile.split(":", 1)[1].strip() if ":" in zeile else ""
        kopf = zeile.split(":", 1)[0].strip().lower()
        if kopf in ("start time", "startzeit") and wert:
            uhrzeit = wert[:5]
        elif kopf in ("task to run", "auszufuehrende aufgabe") and wert:
            pfad = wert.strip('"').split('" ')[0].strip('"')
            if " aufgaben" in pfad:
                pfad = pfad.split(" aufgaben")[0]
    return uhrzeit, pfad
