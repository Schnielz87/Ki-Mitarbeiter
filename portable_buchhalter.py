#!/usr/bin/env python3
"""Startpunkt des portablen KI-Buchhalters.

Ohne Argumente startet die grafische Oberflaeche.  Mit Argumenten wird die
Kommandozeile verwendet (``--help`` zeigt alle Befehle).  Diese Datei ist
zugleich der Einstiegspunkt fuer den Windows-Build (PORTABLE_BUCHHALTER.exe).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in ("--gui", "gui"):
        from ui.cli import main as cli_main
        return cli_main(argv)
    try:
        from ui.tk_app import run
    except ImportError as exc:
        print(
            "Die grafische Oberflaeche konnte nicht geladen werden.\n"
            f"Grund: {exc}\n\n"
            "Auf diesem System fehlt vermutlich Tkinter. Die Anwendung laesst sich "
            "trotzdem ueber die Kommandozeile bedienen, zum Beispiel:\n"
            "    portable_buchhalter.py check\n"
            "    portable_buchhalter.py chat\n",
            file=sys.stderr,
        )
        return 3
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
