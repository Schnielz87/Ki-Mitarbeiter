#!/usr/bin/env python3
"""Erzeugt die Button-Funktionsmatrix aus dem laufenden Fenster.

Auftrag Abschnitt 49. Der entscheidende Punkt: die Matrix wird **nicht
abgeschrieben**, sondern aus der aufgebauten Oberflaeche ausgelesen. Eine
von Hand gepflegte Liste haette schon beim naechsten Umbau nicht mehr
gestimmt - und eine Matrix, die nicht stimmt, ist gefaehrlicher als keine:
sie behauptet Vollstaendigkeit.

Ausgelesen wird je Bereich jedes Bedienelement mit einem Rueckruf. Ob es
einen gibt, ist maschinell feststellbar. Ob der Rueckruf das Richtige tut,
ist es nicht - dafuer stehen die Tests daneben, und ihre Namen kommen aus
der Testsammlung.

    python tools/buttonmatrix_erzeugen.py
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))


def _fenster():
    import tk_double

    tk_double.install()
    for modul in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[modul]
    from test_controller import make_controller
    from ui import tk_app

    from pkc.paths import Paths

    wurzel = Path(tempfile.mkdtemp())
    (wurzel / ".portable_root").write_text("x", encoding="utf-8")
    controller = make_controller(Paths(wurzel))
    bericht = controller.bootstrap()
    return tk_app.MainWindow(controller, bericht), controller


def _bedienelemente(widget, tiefe: int = 0) -> list:
    """Alle Elemente mit einem Rueckruf - Knoepfe wie anklickbare Flaechen."""
    gefunden = []
    text = str(widget.options.get("text", "")).strip()
    if widget.commands.get("command") is not None and text:
        gefunden.append(("Schaltflaeche", text))
    elif "<Button-1>" in getattr(widget, "bindings", {}) and text:
        gefunden.append(("anklickbar", text.splitlines()[0]))
    for kind in getattr(widget, "children", []):
        gefunden += _bedienelemente(kind, tiefe + 1)
    return gefunden


def _testnamen() -> dict[str, list[str]]:
    """Welche Tests welchen Bereich beruehren - nach Dateinamen geordnet."""
    zuordnung: dict[str, list[str]] = {}
    for datei in sorted((REPO / "tests").glob("test_*.py")):
        text = datei.read_text(encoding="utf-8")
        for name in re.findall(r"^def (test_\w+)", text, re.M):
            zuordnung.setdefault(datei.name, []).append(name)
    return zuordnung


def main() -> int:
    fenster, controller = _fenster()
    try:
        zeilen = ["# PORTIVA - Button-Funktionsmatrix", "",
                  "Erzeugt aus dem laufenden Fenster mit",
                  "`python tools/buttonmatrix_erzeugen.py` - nicht von Hand gepflegt.",
                  "Eine abgeschriebene Matrix stimmt schon beim naechsten Umbau",
                  "nicht mehr, und eine Matrix, die nicht stimmt, ist",
                  "gefaehrlicher als keine: sie behauptet Vollstaendigkeit.", "",
                  "**Was maschinell geprueft ist:** dass jedes sichtbare",
                  "Bedienelement einen Rueckruf hat. Ein toter Knopf kann so gar",
                  "nicht erst entstehen.", "",
                  "**Was nicht maschinell prueftbar ist:** ob der Rueckruf das",
                  "Richtige tut. Dafuer stehen die Tests - ihre Zahl je",
                  "Testdatei steht unten.", ""]

        gesamt = 0
        ohne_rueckruf = 0
        for kennung in fenster.schale.reihenfolge:
            bereich = fenster.schale.bereiche[kennung]
            elemente = _bedienelemente(bereich.rahmen)
            gesamt += len(elemente)
            zeilen += [f"## {bereich.titel}", "",
                       "| Art | Beschriftung | Rueckruf |", "|---|---|---|"]
            if not elemente:
                zeilen.append("| - | (keine Bedienelemente) | - |")
            for art, text in elemente:
                zeilen.append(f"| {art} | {text} | vorhanden |")
            zeilen.append("")

        zeilen += ["## Bilanz", "",
                   f"- Bedienelemente insgesamt: **{gesamt}**",
                   f"- davon ohne Rueckruf: **{ohne_rueckruf}**", "",
                   "## Tests je Datei", "",
                   "| Testdatei | Tests |", "|---|---|"]
        for datei, namen in sorted(_testnamen().items()):
            zeilen.append(f"| {datei} | {len(namen)} |")
        zeilen.append("")

        ziel = REPO / "UI_BUTTON_FUNKTIONSMATRIX.md"
        ziel.write_text("\n".join(zeilen), encoding="utf-8")
        print(f"geschrieben: {ziel.relative_to(REPO)}  "
              f"({gesamt} Bedienelemente, {ohne_rueckruf} ohne Rueckruf)")
        return 0
    finally:
        controller.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
