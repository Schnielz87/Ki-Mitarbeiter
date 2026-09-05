"""Startpunkt: ein Fehler beim Start darf nie stumm bleiben.

Beim Doppelklick laeuft die Fensterfassung ohne Konsole. Eine Meldung auf
stderr saehe der Nutzer dort nicht - er saesse vor einem Programm, das
scheinbar nichts tut.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _startpunkt():
    spec = importlib.util.spec_from_file_location(
        "portable_buchhalter_start", ROOT / "portable_buchhalter.py"
    )
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_missing_gui_is_reported_not_swallowed(monkeypatch, tmp_path, capsys):
    modul = _startpunkt()
    monkeypatch.setattr(modul, "ROOT", tmp_path)
    monkeypatch.setitem(sys.modules, "ui.tk_app", None)   # Import schlaegt fehl

    code = modul.main([])

    assert code == 3
    fehlertext = capsys.readouterr().err
    assert "Oberflaeche" in fehlertext
    assert "KONSOLE" in fehlertext, "der Ausweg ueber die Kommandozeile muss genannt werden"
    protokoll = tmp_path / "logs" / "startfehler.txt"
    assert protokoll.is_file(), "die Meldung muss auch als Datei erhalten bleiben"
    assert "Tkinter" in protokoll.read_text(encoding="utf-8")


def test_unexpected_error_is_reported(monkeypatch, tmp_path, capsys):
    modul = _startpunkt()
    monkeypatch.setattr(modul, "ROOT", tmp_path)

    class Kaputt:
        @staticmethod
        def run():
            raise RuntimeError("Datenbank nicht lesbar")

    monkeypatch.setitem(sys.modules, "ui.tk_app", Kaputt)

    code = modul.main([])

    assert code == 1
    assert "Datenbank nicht lesbar" in capsys.readouterr().err
    protokoll = tmp_path / "logs" / "startfehler.txt"
    assert protokoll.is_file() and "RuntimeError" in protokoll.read_text(encoding="utf-8")


def test_arguments_go_to_the_command_line(monkeypatch):
    modul = _startpunkt()
    gerufen = {}

    class CliDouble:
        @staticmethod
        def main(argv):
            gerufen["argv"] = argv
            return 0

    monkeypatch.setitem(sys.modules, "ui.cli", CliDouble)
    assert modul.main(["check", "--quiet"]) == 0
    assert gerufen["argv"] == ["check", "--quiet"]
