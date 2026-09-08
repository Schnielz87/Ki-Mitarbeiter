"""Wenn eine Frage eine Datei verlangt, muss eine Datei entstehen.

Der Anlass: In einer Fallstudie stand woertlich *"Der Buchhalter soll
eine Excel-Arbeitsmappe ... erstellen"*. Der Buchhalter antwortete mit
Text und erzeugte nichts. Die Faehigkeit war vorhanden - neun Formate,
im Windows-Bauablauf nachgewiesen. Sie wurde nur nie ausgeloest.

Geprueft wird beides: dass eine bestellte Datei wirklich auf dem
Datentraeger landet, **und** dass nicht bei jeder Erwaehnung eines
Formats ungefragt Dateien entstehen.
"""

from __future__ import annotations

import pytest

from pkc.artefakte.wunsch import erkennen
from pkc.llm.base import LlmResponse
from pkc.llm.manager import LlmManager
from test_controller import make_controller


class Modelldoppel:
    name, model = "testmodell", "doppel"

    def __init__(self, antwort="**ERGEBNIS**\n\n| Posten | Betrag |\n|---|---|\n"
                               "| Fuhrpark | 45.000,00 |\n| Server | 12.000,00 |"):
        self.antwort = antwort

    def available(self):
        return True, "bereit"

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None):
        return LlmResponse(text=self.antwort, provider=self.name,
                           model=self.model, meta={"generated": True})

    def describe(self):
        return {"anbieter": self.name, "modell": self.model}


@pytest.fixture
def buchhalter(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap()
    controller.llm = LlmManager(Modelldoppel())
    controller.rag.llm = controller.llm
    try:
        yield controller
    finally:
        controller.shutdown()


# -- Die Erkennung fuer sich -------------------------------------------
@pytest.mark.parametrize("frage,format", [
    ("Der Buchhalter soll eine Excel-Arbeitsmappe erstellen.", "xlsx"),
    ("Erstelle mir bitte eine Exceltabelle mit den Abschreibungen.", "xlsx"),
    ("Bitte gib mir das als PDF.", "pdf"),
    ("Erzeuge ein Word-Dokument mit dem Buchungsvorschlag.", "docx"),
    ("Ich brauche eine CSV-Datei der Belege.", "csv"),
    ("Bau mir eine Praesentation mit den Zahlen.", "pptx"),
])
def test_eine_bestellung_wird_erkannt(frage, format):
    wunsch = erkennen(frage)
    assert wunsch is not None, f"nicht erkannt: {frage}"
    assert wunsch.format == format


@pytest.mark.parametrize("frage", [
    "Was ist der Unterschied zwischen CSV und Excel?",
    "Welche Pflichtangaben muss eine Rechnung enthalten?",
    "Erklaer mir, wie eine Excel-Tabelle aufgebaut ist.",
    "Kann man eine PDF nachtraeglich aendern?",
    "Wie funktioniert der Vorsteuerabzug?",
])
def test_eine_wissensfrage_bestellt_nichts(frage):
    """Sonst entstehen bei jedem Gespraech ungefragt Dateien."""
    assert erkennen(frage) is None, f"faelschlich als Bestellung erkannt: {frage}"


@pytest.mark.parametrize("frage", [
    "Erklaer mir bitte, wie ich eine Excel-Tabelle erstelle.",
    "Kannst du mir erklaeren, wie man ein Word-Dokument erzeugt?",
    "Was ist eine Exceltabelle und wie erstellt man sie?",
])
def test_eine_frage_nach_dem_wie_bestellt_nichts(frage):
    """Der schwierige Fall: Aufforderungswort UND Wissensfrage in einem Satz.

    "Erklaer mir, wie ich eine Excel-Tabelle erstelle" enthaelt
    "erstelle" - und ist trotzdem keine Bestellung. Wer das nicht
    unterscheidet, legt bei jeder Nachfrage eine Datei an.

    Diese Faelle standen zuerst nicht in den Tests. Der Schutz dagegen
    war eingebaut, aber unbewiesen: eine Gegenprobe, die ihn
    abgeschaltet hat, ist nicht angesprungen. Eingebauter Code, den kein
    Test braucht, ist kein Schutz - er ist eine Vermutung.
    """
    assert erkennen(frage) is None, f"faelschlich als Bestellung erkannt: {frage}"


def test_bei_mehreren_formaten_gewinnt_das_reichere():
    """"Excel oder CSV" ergibt Excel - daraus laesst sich CSV machen,
    umgekehrt geht Formatierung verloren."""
    assert erkennen("Erstelle das als Excel oder CSV.").format == "xlsx"


# -- Der ganze Weg durch die Anwendung ---------------------------------
def test_die_bestellte_excel_datei_liegt_wirklich_auf_dem_datentraeger(buchhalter):
    """Nicht "es gab keinen Fehler", sondern: die Datei ist da und hat Inhalt."""
    ergebnis = buchhalter.ask(
        "Der Buchhalter soll eine Excel-Arbeitsmappe mit den "
        "Abschreibungen zum 30.09.2026 erstellen.")

    assert ergebnis.datei_fehler == "", ergebnis.datei_fehler
    assert ergebnis.datei is not None, (
        "Es wurde eine Excel-Arbeitsmappe verlangt - es ist keine entstanden.")
    pfad = ergebnis.datei.pfad
    assert pfad.exists(), f"{pfad} gibt es nicht"
    assert pfad.suffix == ".xlsx"
    assert pfad.stat().st_size > 200, "die Datei ist verdaechtig klein"

    # Und sie steht im Verzeichnis der Arbeitsergebnisse - sonst findet
    # sie niemand wieder.
    namen = [eintrag["name"] for eintrag in buchhalter.artefakt_liste()]
    assert pfad.name in namen


def test_eine_wissensfrage_erzeugt_keine_datei(buchhalter):
    vorher = len(buchhalter.artefakt_liste())
    ergebnis = buchhalter.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")
    assert ergebnis.datei is None
    assert len(buchhalter.artefakt_liste()) == vorher


def test_ein_fehlschlag_wird_nicht_verschwiegen(buchhalter, monkeypatch):
    """Wer eine Datei bestellt und keine bekommt, muss erfahren warum."""
    def kaputt(*args, **kwargs):
        raise RuntimeError("Datentraeger voll")

    monkeypatch.setattr(buchhalter, "datei_erzeugen", kaputt)
    ergebnis = buchhalter.ask("Erstelle mir bitte eine Exceltabelle.")

    assert ergebnis.datei is None
    assert "Datentraeger voll" in ergebnis.datei_fehler
    # Und die Antwort selbst kommt trotzdem an.
    assert ergebnis.answer.text


# -- Im Fenster sichtbar -----------------------------------------------
def test_die_erzeugte_datei_wird_in_der_unterhaltung_gemeldet(portable_root):
    """Eine Datei, von der niemand erfaehrt, ist keine erzeugte Datei.

    Sie liegt im Ordner - aber der Anwender sieht nur einen Text und
    haelt die Bestellung fuer ignoriert. Genau das war der Eindruck des
    Auftraggebers.
    """
    import sys

    import tk_double

    tk_double.install()
    tk_double.ui_module_freigeben()
    from ui import tk_app

    controller = make_controller(portable_root)
    bericht = controller.bootstrap()
    controller.llm = LlmManager(Modelldoppel())
    controller.rag.llm = controller.llm
    try:
        fenster = tk_app.MainWindow(controller, bericht)
        vorher = fenster.chat.buffer
        fenster.entry.insert(
            "end", "Erstelle mir bitte eine Exceltabelle mit den Abschreibungen.")
        fenster._send()
        neu = fenster.chat.buffer[len(vorher):]
        assert "Datei erzeugt" in neu, (
            "Die erzeugte Datei wird in der Unterhaltung nicht gemeldet:\n" + neu)
        assert ".xlsx" in neu, "Der Dateiname muss dastehen"
        assert "Arbeitsergebnisse" in neu, "Wo sie liegt, muss dastehen"
    finally:
        controller.shutdown()


def test_ein_fehlschlag_wird_auch_im_fenster_gemeldet(portable_root, monkeypatch):
    import tk_double

    tk_double.install()
    tk_double.ui_module_freigeben()
    from ui import tk_app

    controller = make_controller(portable_root)
    bericht = controller.bootstrap()
    controller.llm = LlmManager(Modelldoppel())
    controller.rag.llm = controller.llm

    def kaputt(*args, **kwargs):
        raise RuntimeError("Datentraeger voll")

    monkeypatch.setattr(controller, "datei_erzeugen", kaputt)
    try:
        fenster = tk_app.MainWindow(controller, bericht)
        vorher = fenster.chat.buffer
        fenster.entry.insert("end", "Erstelle mir bitte eine Exceltabelle.")
        fenster._send()
        neu = fenster.chat.buffer[len(vorher):]
        assert "konnte nicht erzeugt werden" in neu
        assert "Datentraeger voll" in neu
    finally:
        controller.shutdown()
