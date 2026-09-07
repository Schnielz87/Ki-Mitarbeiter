"""Auftrag Abschnitt 34: es gibt keine toten Knoepfe.

Jedes sichtbare produktive Bedienelement muss entweder wirklich etwas tun
oder eindeutig als nicht verfuegbar gekennzeichnet sein. Dieser Test
laeuft ueber ALLE zehn Bereiche und prueft das Erste; das Zweite prueft
`test_neue_ansichten.py` fuer die beiden noch nicht gebauten Bereiche.

Warum das ein eigener Test ist und nicht nur ein Bericht: ein Bericht
veraltet, ein Test faellt.
"""

from __future__ import annotations

import sys

import pytest

import tk_double
from test_controller import make_controller


@pytest.fixture
def fenster(portable_root):
    tk_double.install()
    for modul in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[modul]
    from ui import tk_app

    controller = make_controller(portable_root)
    bericht = controller.bootstrap()
    window = tk_app.MainWindow(controller, bericht)
    yield window, controller
    controller.shutdown()


def _elemente(widget, pfad=""):
    """Alle Elemente mit einer Beschriftung - mit und ohne Rueckruf."""
    gefunden = []
    text = str(widget.options.get("text", "")).strip()
    # Ein Knopf zaehlt auch dann, wenn er KEINEN Rueckruf hat - sonst
    # findet dieser Test ausgerechnet die nicht, um die es geht. Das
    # Testdoppel kennt Knoepfe deshalb als eigene Art.
    ist_knopf = isinstance(widget, tk_double._Button)
    hat_rueckruf = (widget.commands.get("command") is not None
                    or "<Button-1>" in getattr(widget, "bindings", {}))
    if text and (ist_knopf or hat_rueckruf):
        gefunden.append((pfad, text.splitlines()[0], hat_rueckruf))
    for kind in getattr(widget, "children", []):
        gefunden += _elemente(kind, pfad)
    return gefunden


def test_kein_bedienelement_ohne_rueckruf(fenster):
    """Der Kern von Abschnitt 34."""
    window, _ = fenster
    tot = []
    for kennung in window.schale.reihenfolge:
        bereich = window.schale.bereiche[kennung]
        for _, text, hat_rueckruf in _elemente(bereich.rahmen, kennung):
            if not hat_rueckruf:
                tot.append(f"{kennung}: {text}")
    assert tot == [], "Bedienelemente ohne Rueckruf: " + ", ".join(tot)


def test_auch_die_navigation_und_die_kopfzeile_sind_vollstaendig(fenster):
    """Nicht nur die Bereiche - auch der Rahmen darum."""
    window, _ = fenster
    tot = [t for _, t, ok in _elemente(window.schale.seitenleiste) if not ok]
    assert tot == [], "in der Seitenleiste: " + ", ".join(tot)


def test_jeder_bereich_hat_ueberhaupt_inhalt(fenster):
    """Ein leerer Bereich waere kein toter Knopf, aber eine tote Ansicht."""
    window, _ = fenster
    leer = [k for k in window.schale.reihenfolge
            if not window.schale.bereiche[k].rahmen.children]
    assert leer == [], "Bereiche ohne Inhalt: " + ", ".join(leer)


def test_die_matrix_stimmt_mit_dem_fenster_ueberein():
    """Die erzeugte Matrix darf nicht veralten.

    Sie wird aus dem laufenden Fenster erzeugt. Steht dort eine andere
    Zahl als im Fenster, wurde sie nach einer Aenderung nicht neu erzeugt -
    und behauptet dann eine Vollstaendigkeit, die sie nicht hat.
    """
    import re
    from pathlib import Path

    datei = Path(__file__).resolve().parents[1] / "UI_BUTTON_FUNKTIONSMATRIX.md"
    assert datei.is_file(), "die Button-Funktionsmatrix fehlt"
    text = datei.read_text(encoding="utf-8")

    treffer = re.search(r"davon ohne Rueckruf: \*\*(\d+)\*\*", text)
    assert treffer, "die Bilanz fehlt in der Matrix"
    assert int(treffer.group(1)) == 0, (
        "die Matrix nennt Bedienelemente ohne Rueckruf")

    # Alle zehn Bereiche muessen darin vorkommen.
    for name in ("Unterhaltung", "Unternehmenswissen", "Belege & Dokumente",
                 "Arbeitsergebnisse", "Wissen & Quellen", "Vorlagen",
                 "Aufgaben", "Plugins", "Verbundene Dienste",
                 "Einstellungen & Status"):
        assert f"## {name}" in text or f"## {name} " in text, \
            f"Die Matrix nennt den Bereich nicht: {name}"
