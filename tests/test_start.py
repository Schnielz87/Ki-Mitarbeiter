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


def test_no_dialog_in_unattended_mode(monkeypatch, tmp_path, capsys):
    """Ohne Aufsicht darf kein Fenster aufgehen - es wartet sonst endlos.

    Der Fehler dahinter hat die Windows-Ablaeufe 11 bis 16 stundenlang im
    Schritt "Tests auf Windows" haengen lassen: ein modales Meldungsfenster,
    auf dessen "OK" niemand klickt.
    """
    modul = _startpunkt()
    monkeypatch.setattr(modul, "ROOT", tmp_path)
    monkeypatch.setenv(modul.UNBEAUFSICHTIGT, "1")

    geoeffnet = []
    monkeypatch.setattr(modul, "_meldungsfenster",
                        lambda titel, text: geoeffnet.append(titel))

    modul._melden("Titel", "Text")

    assert geoeffnet == [], "im unbeaufsichtigten Betrieb darf kein Fenster aufgehen"
    assert "Titel" in capsys.readouterr().err, "die Meldung muss trotzdem ankommen"
    assert (tmp_path / "logs" / "startfehler.txt").is_file()


def test_dialog_is_shown_when_someone_can_click(monkeypatch, tmp_path):
    """Beim Doppelklick ist das Fenster der einzige sichtbare Weg."""
    modul = _startpunkt()
    monkeypatch.setattr(modul, "ROOT", tmp_path)
    monkeypatch.delenv(modul.UNBEAUFSICHTIGT, raising=False)

    geoeffnet = []
    monkeypatch.setattr(modul, "_meldungsfenster",
                        lambda titel, text: geoeffnet.append(titel))

    modul._melden("Titel", "Text")

    assert geoeffnet == ["Titel"]


@pytest.mark.parametrize("wert, erwartet", [
    ("1", True), ("ja", True), ("wahr", True), ("true", True),
    ("", False), ("0", False), ("nein", False), ("false", False),
])
def test_unattended_switch_reads_the_usual_spellings(monkeypatch, wert, erwartet):
    modul = _startpunkt()
    monkeypatch.setenv(modul.UNBEAUFSICHTIGT, wert)
    assert modul._unbeaufsichtigt() is erwartet


def test_start_tests_never_reach_the_real_dialog(monkeypatch, tmp_path, capsys):
    """Die Vorkehrung aus conftest.py greift auch ohne eigenes Zutun.

    Ohne sie wuerde dieser Test unter Windows haengen statt fehlzuschlagen -
    deshalb wird hier bewusst nichts gepatcht ausser der Wurzel.
    """
    modul = _startpunkt()
    monkeypatch.setattr(modul, "ROOT", tmp_path)
    monkeypatch.setitem(sys.modules, "ui.tk_app", None)

    assert modul.main([]) == 3
    assert modul._unbeaufsichtigt(), "conftest.py muss den unbeaufsichtigten Betrieb setzen"
