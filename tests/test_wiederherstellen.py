"""Sicherung wiederherstellen - Risiko R8 aus der GAP-Analyse.

Bisher gab es nur ``restore_info``: es las, was da ist, stellte aber
nichts wieder her. Ein Knopf dafuer waere ein toter Knopf gewesen.

Wiederherstellen ueberschreibt den aktuellen Stand. Es ist die
einschneidendste Handlung der Anwendung - diese Tests halten fest, dass
sie sich entsprechend verhaelt.
"""

from __future__ import annotations

import sys

import pytest

import tk_double
from test_controller import make_controller


@pytest.fixture
def anwendung(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        yield controller
    finally:
        controller.shutdown()


def test_ohne_bestaetigung_geschieht_nichts(anwendung):
    anwendung.remember_manual("company.name", "Name", "Vorher GmbH", "profile")
    sicherung = anwendung.backup("probe")

    with pytest.raises(ValueError) as fehler:
        anwendung.wiederherstellen(sicherung["verzeichnis"].split("/")[-1])
    assert "Bestaetigung" in str(fehler.value)


def test_eine_sicherung_wird_wirklich_zurueckgespielt(anwendung):
    """Ende zu Ende: sichern, aendern, zurueckspielen, alter Stand ist da."""
    anwendung.remember_manual("company.name", "Name", "Vorher GmbH", "profile")
    sicherung = anwendung.backup("probe")
    name = Path(sicherung["pfad"]).name

    anwendung.remember_manual("company.name", "Name", "Nachher GmbH", "profile")
    assert "Nachher" in anwendung.memory.get("company.name").content

    ergebnis = anwendung.wiederherstellen(name, bestaetigt=True)

    assert ergebnis["ok"]
    assert "company.db" in ergebnis["dateien"]
    assert "Vorher" in anwendung.memory.get("company.name").content, (
        "der alte Stand muss wirklich zurueck sein")


def test_der_bisherige_stand_wird_vorher_gesichert(anwendung):
    """Wer sich vertut, kommt zurueck. Ohne das waere die
    Wiederherstellung selbst der gefaehrlichste Knopf im Programm."""
    anwendung.remember_manual("company.name", "Name", "Erster Stand", "profile")
    erste = Path(anwendung.backup("erste")["pfad"]).name

    anwendung.remember_manual("company.name", "Name", "Zweiter Stand", "profile")
    ergebnis = anwendung.wiederherstellen(erste, bestaetigt=True)

    assert ergebnis["sicherung_vorher"], "es muss vorher gesichert worden sein"
    namen = [s["name"] for s in anwendung.sicherungen()]
    assert any("vor-wiederherstellung" in n for n in namen), namen


def test_eine_beschaedigte_sicherung_wird_abgewiesen(anwendung):
    """Eine beschaedigte Sicherung einzuspielen macht aus einem heilen
    Stand einen kaputten."""
    anwendung.remember_manual("company.name", "Name", "Vorher GmbH", "profile")
    sicherung = anwendung.backup("kaputt")
    pfad = Path(sicherung["pfad"])

    # Eine Datei nachtraeglich veraendern, die wirklich in der Sicherung
    # steht - dann stimmt ihre Pruefsumme nicht mehr.
    (pfad / "company.db").write_bytes(b"kaputt")

    eintrag = next(s for s in anwendung.sicherungen() if s["name"] == pfad.name)
    assert eintrag["vollstaendig"] is False
    assert "veraendert" in eintrag["befund"]

    with pytest.raises(ValueError) as fehler:
        anwendung.wiederherstellen(pfad.name, bestaetigt=True)
    assert "unversehrt" in str(fehler.value)


def test_eine_zusaetzliche_datei_macht_die_sicherung_fraglich(anwendung):
    """Eine Datei zu viel steht in keiner Pruefsumme - niemand weiss, woher
    sie kommt, und beim Einspielen wuerde sie mit zurueckgeschrieben.

    Aufgefallen, weil ein Test eine Datei anlegte, die es in der Sicherung
    gar nicht gab, und die Pruefung ihn trotzdem durchwinkte.
    """
    pfad = Path(anwendung.backup("zusatz")["pfad"])
    (pfad / "fremd.json").write_text("{}", encoding="utf-8")

    eintrag = next(s for s in anwendung.sicherungen() if s["name"] == pfad.name)
    assert eintrag["vollstaendig"] is False
    assert "nicht im Verzeichnis" in eintrag["befund"]
    assert "fremd.json" in eintrag["befund"]


def test_eine_unversehrte_sicherung_wird_als_solche_erkannt(anwendung):
    sicherung = anwendung.backup("heil")
    eintrag = next(s for s in anwendung.sicherungen()
                   if s["name"] == Path(sicherung["pfad"]).name)
    assert eintrag["vollstaendig"] is True
    assert "Pruefsummen stimmen" in eintrag["befund"]


def test_die_anwendung_laeuft_danach_weiter(anwendung):
    """Die Datenbanken werden geschlossen und ersetzt. Danach muessen sie
    wieder offen sein - sonst sieht der Benutzer nur noch Folgefehler."""
    anwendung.remember_manual("company.name", "Name", "Vorher GmbH", "profile")
    name = Path(anwendung.backup("weiter")["pfad"]).name
    vorher_company = anwendung.company_db
    vorher_knowledge = anwendung.knowledge_db
    anwendung.wiederherstellen(name, bestaetigt=True)

    # Alles, was auf den Datenbanken aufsetzt, muss weiter benutzbar sein.
    assert anwendung.memory.list(limit=5) is not None
    assert anwendung.knowledge.stats()["documents"] >= 0
    anwendung.remember_manual("company.city", "Ort", "Musterstadt", "profile")
    assert anwendung.memory.get("company.city") is not None

    # Und zwar ueber NEU geoeffnete Verbindungen. Eine Datenbank oeffnet
    # sich zwar von selbst wieder, aber je Thread getrennt: ein
    # Hintergrundfaden haette sonst weiter die alte, ersetzte Datei offen
    # und lieferte einen Stand, den es nicht mehr gibt. Ausserdem laufen
    # beim Neuoeffnen die Migrationen - eine aeltere Sicherung braucht sie.
    assert anwendung.company_db is not vorher_company
    assert anwendung.knowledge_db is not vorher_knowledge
    assert anwendung.memory.db is anwendung.company_db, (
        "die Speicher muessen auf die neue Verbindung zeigen")


def test_eine_unbekannte_sicherung_wird_benannt(anwendung):
    with pytest.raises(ValueError) as fehler:
        anwendung.wiederherstellen("gibtsnicht", bestaetigt=True)
    assert "gibt es nicht" in str(fehler.value)


# ------------------------------------------------------ im Fenster
@pytest.fixture
def fenster(portable_root):
    dialoge = tk_double.install()
    for modul in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[modul]
    from ui import tk_app

    controller = make_controller(portable_root)
    bericht = controller.bootstrap()
    window = tk_app.MainWindow(controller, bericht)
    yield window, controller, dialoge
    controller.shutdown()


def test_ohne_sicherung_wird_das_gesagt(fenster):
    """Kein stiller Knopf - wer drueckt, bekommt eine Antwort."""
    window, _, dialoge = fenster
    window._wiederherstellen()
    assert any("noch keine Sicherung" in text for _, _, text in dialoge.messages)


def test_das_fenster_fragt_vor_dem_ueberschreiben(fenster):
    window, controller, dialoge = fenster
    controller.remember_manual("company.name", "Name", "Vorher GmbH", "profile")
    name = Path(controller.backup("probe")["pfad"]).name
    controller.remember_manual("company.name", "Name", "Nachher GmbH", "profile")

    dialoge.answers = [name, False]      # Name eintragen, dann abbrechen
    window._wiederherstellen()
    assert "Nachher" in controller.memory.get("company.name").content, (
        "ohne Bestaetigung darf nichts ueberschrieben werden")

    dialoge.answers = [name, True]
    window._wiederherstellen()
    assert "Vorher" in controller.memory.get("company.name").content


def test_das_fenster_weist_eine_beschaedigte_sicherung_ab(fenster):
    window, controller, dialoge = fenster
    pfad = Path(controller.backup("kaputt")["pfad"])
    (pfad / "company.db").write_bytes(b"kaputt")

    dialoge.answers = [pfad.name]
    window._wiederherstellen()
    fehler = [t for art, _, t in dialoge.messages if art == "fehler"]
    assert any("unversehrt" in t or "BESCHAEDIGT" in t for t in fehler), fehler


from pathlib import Path      # noqa: E402  (unten, damit die Doku oben steht)
