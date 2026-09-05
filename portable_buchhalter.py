#!/usr/bin/env python3
"""Startpunkt des portablen KI-Buchhalters.

Ohne Argumente startet die grafische Oberflaeche.  Mit Argumenten wird die
Kommandozeile verwendet (``--help`` zeigt alle Befehle).  Diese Datei ist
zugleich der Einstiegspunkt fuer den Windows-Build (PORTABLE_BUCHHALTER.exe).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

#: Umgebungsvariable fuer den unbeaufsichtigten Betrieb.  Ist sie gesetzt,
#: unterbleibt jedes Meldungsfenster - die Meldung geht dann nur nach stderr
#: und in die Protokolldatei.  Notwendig ueberall dort, wo niemand auf "OK"
#: klicken kann: automatische Tests, Bauablaeufe, Dienste.  Ein modales
#: Fenster wartet sonst endlos.
UNBEAUFSICHTIGT = "KIM_UNBEAUFSICHTIGT"


def _unbeaufsichtigt() -> bool:
    wert = os.environ.get(UNBEAUFSICHTIGT, "").strip().lower()
    return wert not in ("", "0", "nein", "false")


def _meldungsfenster(titel: str, text: str) -> None:
    """Zeigt die Meldung als Fenster - blockiert bis zum Klick auf OK."""
    try:
        import tkinter
        from tkinter import messagebox

        fenster = tkinter.Tk()
        fenster.withdraw()
        messagebox.showerror(titel, text)
        fenster.destroy()
        return
    except Exception:
        pass
    # Kein Tkinter vorhanden - unter Windows bleibt das Meldungsfeld
    # des Betriebssystems als letzter Weg.
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, text, titel, 0x10)
    except Exception:
        pass


def _melden(titel: str, text: str) -> None:
    """Meldet einen Startfehler so, dass der Nutzer ihn auch wirklich sieht.

    Beim Doppelklick laeuft die Fensterfassung ohne Konsole - eine Ausgabe auf
    stderr waere unsichtbar. Deshalb zusaetzlich ein Meldungsfenster, soweit
    moeglich, und in jedem Fall eine Datei im Logverzeichnis.
    """
    print(f"{titel}\n\n{text}", file=sys.stderr)
    try:
        protokoll = ROOT / "logs" / "startfehler.txt"
        protokoll.parent.mkdir(parents=True, exist_ok=True)
        protokoll.write_text(f"{titel}\n\n{text}\n", encoding="utf-8")
    except OSError:
        pass
    if _unbeaufsichtigt():
        return
    _meldungsfenster(titel, text)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in ("--gui", "gui"):
        from ui.cli import main as cli_main
        return cli_main(argv)
    try:
        from ui.tk_app import run
    except ImportError as exc:
        _melden(
            "Portabler Buchhalter - Oberflaeche nicht verfuegbar",
            "Die grafische Oberflaeche konnte nicht geladen werden.\n\n"
            f"Grund: {exc}\n\n"
            "Auf diesem System fehlt vermutlich Tkinter. Der Buchhalter laesst "
            "sich trotzdem ueber die Kommandozeile bedienen:\n\n"
            "    PORTABLE_BUCHHALTER_KONSOLE.exe check\n"
            "    PORTABLE_BUCHHALTER_KONSOLE.exe chat\n\n"
            "Einzelheiten stehen in logs\\startfehler.txt.",
        )
        return 3
    try:
        return run()
    except Exception as exc:  # der Nutzer darf nicht vor einem stummen Fenster sitzen
        import traceback

        _melden(
            "Portabler Buchhalter - unerwarteter Fehler",
            f"{type(exc).__name__}: {exc}\n\n"
            "Der vollstaendige Verlauf steht in logs\\startfehler.txt und "
            "logs\\app.log.\n\n" + traceback.format_exc()[-1500:],
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
