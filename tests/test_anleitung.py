"""Die Bedienungsanleitung darf nichts versprechen, was es nicht gibt.

Die Anleitung wird aus `tools/anleitung_erzeugen.py` erzeugt. Sie nennt
Befehle der Konsolenfassung und Ordner auf dem Datentraeger. Beides kann
sich im Programm aendern, ohne dass jemand daran denkt, die Anleitung
nachzuziehen - dann steht dort eine Anweisung, die ins Leere laeuft.

Dieser Test vergleicht deshalb den Text der Anleitung mit dem Programm.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUELLE = (ROOT / "tools" / "anleitung_erzeugen.py").read_text(encoding="utf-8")

#: Der Programmname taucht auch im Fliesstext auf ("... KONSOLE.exe
#: verwenden - dieselbe Anwendung"). Solche Stellen sind keine Befehle; sie
#: erkennt man daran, dass ein Gedankenstrich folgt.
_BEFEHL = re.compile(r"PORTABLE_BUCHHALTER_KONSOLE\.exe\s+([a-z]+)(?![a-z])(?!\s+-\s)")


def test_alle_genannten_befehle_gibt_es_wirklich():
    from ui.cli import build_parser

    parser = build_parser()
    unterbefehle = set()
    for aktion in parser._subparsers._group_actions:      # noqa: SLF001 - Testzugriff
        unterbefehle.update(aktion.choices)

    genannt = set(_BEFEHL.findall(QUELLE))
    erfunden = sorted(genannt - unterbefehle)
    assert not erfunden, (
        "Die Anleitung nennt Befehle, die es nicht gibt: " + ", ".join(erfunden)
    )


def test_die_wichtigen_neuen_befehle_stehen_in_der_anleitung():
    """Was gebaut wurde, muss auch erklaert sein - sonst findet es niemand."""
    genannt = set(_BEFEHL.findall(QUELLE))
    for befehl in ("datei", "plugin", "quellen", "modus"):
        assert befehl in genannt, f"Der Befehl '{befehl}' fehlt in der Anleitung."


def test_genannte_ordner_stimmen_mit_dem_layout_ueberein():
    from pkc.paths import LAYOUT

    for name in ("workspace\\\\artefakte", "workspace/artefakte"):
        if name in QUELLE:
            break
    else:
        raise AssertionError("Die Anleitung sagt nicht, wo erzeugte Dateien liegen.")
    assert LAYOUT["artefakte"] == "workspace/artefakte", \
        "Der Ablageort hat sich geaendert - die Anleitung muss nachgezogen werden."


def test_die_anleitung_liegt_vor():
    ziel = ROOT / "docs" / "BEDIENUNGSANLEITUNG.docx"
    assert ziel.is_file() and ziel.stat().st_size > 20_000, \
        "docs/BEDIENUNGSANLEITUNG.docx fehlt oder ist unvollstaendig."
