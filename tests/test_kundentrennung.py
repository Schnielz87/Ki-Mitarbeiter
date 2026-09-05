"""Kundentrennung und Datenkontrolle (Masterprompt 61, 62).

Der Kern ist eine einzige Zusage: Unternehmenswissen von Kunde A darf unter
keinen Umstaenden bei Kunde B, in einem anderen Unternehmensprofil, in einer
anderen portablen Installation oder im allgemeinen Fachwissen auftauchen.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from pkc.paths import Paths, sanitise_customer_id
from test_controller import make_controller


@pytest.fixture
def zwei_kunden(portable_root):
    """Zwei Unternehmen auf demselben Datentraeger."""
    verwalter = make_controller(portable_root)
    verwalter.bootstrap()
    verwalter.create_customer("kunde_a", "Alpha Handels GmbH")
    verwalter.create_customer("kunde_b", "Beta Bau AG")
    verwalter.shutdown()

    a = make_controller(portable_root.for_customer("kunde_a"))
    a.bootstrap()
    b = make_controller(portable_root.for_customer("kunde_b"))
    b.bootstrap()
    yield a, b, portable_root
    a.shutdown()
    b.shutdown()


def test_unternehmenswissen_bleibt_getrennt(zwei_kunden):
    a, b, _ = zwei_kunden
    a.remember_manual("company.name", "Unternehmensname", "Alpha Handels GmbH", "profile")
    a.remember_manual("company.chart_of_accounts", "Kontenrahmen",
                      "Alpha verwendet SKR03.", "accounting")
    b.remember_manual("company.name", "Unternehmensname", "Beta Bau AG", "profile")

    assert a.memory.get("company.name").content == "Alpha Handels GmbH"
    assert b.memory.get("company.name").content == "Beta Bau AG"

    # Der Kontenrahmen von A existiert bei B ueberhaupt nicht
    assert b.memory.get("company.chart_of_accounts") is None
    assert not b.memory.search("SKR03")
    assert not b.memory.search("Alpha")

    # ... und umgekehrt
    assert not a.memory.search("Beta Bau")


def test_daten_liegen_in_getrennten_verzeichnissen(zwei_kunden):
    a, b, wurzel = zwei_kunden
    assert a.paths.company_db != b.paths.company_db
    assert "kunde_a" in str(a.paths.company_db)
    assert "kunde_b" in str(b.paths.company_db)
    assert a.paths.company_db.is_file() and b.paths.company_db.is_file()
    # Beide unterhalb von customers/, nicht im gemeinsamen Bereich
    assert a.paths.company_db.is_relative_to(wurzel.customers_dir)
    assert b.paths.company_db.is_relative_to(wurzel.customers_dir)


def test_fachwissen_wird_geteilt_und_bleibt_frei_von_unternehmensdaten(zwei_kunden):
    """Fachwissen ist fuer alle gleich - und darf keine Unternehmensdaten enthalten."""
    a, b, _ = zwei_kunden
    assert a.paths.knowledge_db == b.paths.knowledge_db, "Fachwissen wird geteilt"
    a.remember_manual("company.secret", "Interne Regel",
                      "Alpha zahlt Lieferant Meier immer erst nach 60 Tagen.", "rule")

    # Die Unternehmensangabe darf in der gemeinsamen Wissensdatenbank nicht auftauchen
    treffer = a.knowledge_db.scalar(
        "SELECT COUNT(*) FROM chunks WHERE text LIKE '%Alpha%' OR text LIKE '%Meier%'",
        default=0,
    )
    assert treffer == 0, "Unternehmensdaten duerfen nicht ins Fachwissen gelangen"
    assert not b.memory.search("Meier")


def test_gespraeche_und_belege_bleiben_getrennt(zwei_kunden, tmp_path):
    a, b, _ = zwei_kunden
    a.ask("Was ist eine Kleinbetragsrechnung?")
    beleg = tmp_path / "alpha_rechnung.txt"
    beleg.write_text("# Rechnung Alpha\nGeheimer Sonderrabatt 42 Prozent.\n",
                     encoding="utf-8")
    a.add_document(beleg)

    assert len(a.conversations()) == 1
    assert len(b.conversations()) == 0
    assert len(a.documents()) == 1
    assert len(b.documents()) == 0
    assert not b.search_documents("Sonderrabatt")


def test_kundenkennung_kann_nicht_ausbrechen(portable_root):
    """Eine Kennung wie '../andererkunde' wuerde die Trennung aushebeln."""
    for boese in ("../andererkunde", "a/b", "..", "kunde/../andere"):
        with pytest.raises(ValueError) as fehler:
            sanitise_customer_id(boese)
        assert "Unzulaessige Kundenkennung" in str(fehler.value)

    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        with pytest.raises(ValueError):
            controller.create_customer("../ausbruch")
    finally:
        controller.shutdown()


def test_export_enthaelt_alles_und_keine_lizenz(zwei_kunden, tmp_path):
    """Masterprompt 62: der Kunde muss seine Daten vollstaendig exportieren koennen."""
    a, _, _ = zwei_kunden
    a.remember_manual("company.name", "Unternehmensname", "Alpha Handels GmbH", "profile")
    a.ask("Wie pruefe ich eine Rechnung?")

    ergebnis = a.export_customer(tmp_path / "export")
    ordner = Path(ergebnis["verzeichnis"])
    assert (ordner / "company.db").is_file()
    assert (ordner / "unternehmenswissen.json").is_file()

    wissen = json.loads((ordner / "unternehmenswissen.json").read_text(encoding="utf-8"))
    assert any(e["content"] == "Alpha Handels GmbH" for e in wissen)

    beschreibung = json.loads((ordner / "EXPORT.json").read_text(encoding="utf-8"))
    assert beschreibung["kunde"] == "kunde_a"
    assert "versionen" in beschreibung
    assert not (ordner / "license.json").exists(), "eine Lizenz gehoert nicht in den Export"


def test_gespraech_und_beleg_loeschen(zwei_kunden, tmp_path):
    a, _, _ = zwei_kunden
    a.ask("Was gilt bei Skonto?")
    uid = a.conversation_uid
    beleg = tmp_path / "beleg.txt"
    beleg.write_text("# Beleg\nEin ausreichend langer Belegtext zum Testen.\n",
                     encoding="utf-8")
    doc_uid = a.add_document(beleg)["doc_uid"]

    assert a.delete_conversation(uid) is True
    assert a.conversations() == []
    assert a.company_db.scalar("SELECT COUNT(*) FROM messages", default=0) == 0

    assert a.delete_document(doc_uid) is True
    assert a.documents() == []
    assert a.delete_document(doc_uid) is False, "zweites Loeschen meldet ehrlich nichts"


def test_kunde_loeschen_verlangt_bestaetigung_und_sichert_vorher(zwei_kunden):
    a, b, wurzel = zwei_kunden
    b.remember_manual("company.name", "Unternehmensname", "Beta Bau AG", "profile")
    b.shutdown()      # der zu loeschende Bereich wird zuerst geschlossen

    # ohne Bestaetigung passiert nichts
    with pytest.raises(ValueError) as fehler:
        a.delete_customer("kunde_b")
    assert "wiederholt werden" in str(fehler.value)
    assert wurzel.for_customer("kunde_b").customer_root.is_dir()

    # der eigene Bereich kann nicht geloescht werden
    with pytest.raises(ValueError) as fehler:
        a.delete_customer("kunde_a", confirm="kunde_a")
    assert "geoeffnete Kundenbereich" in str(fehler.value)

    # mit Bestaetigung: geloescht, aber vorher gesichert
    ergebnis = a.delete_customer("kunde_b", confirm="kunde_b")
    assert not wurzel.for_customer("kunde_b").customer_root.exists()
    assert ergebnis["geloeschte_dateien"] > 0
    sicherung = Path(ergebnis["export"])
    assert sicherung.is_dir() and (sicherung / "company.db").is_file()

    # Kunde A ist unberuehrt
    assert a.paths.company_db.is_file()
    protokoll = [e["action"] for e in a.audit.entries()]
    assert "kunde_geloescht" in protokoll


def test_einzelinstanz_verhaelt_sich_unveraendert(portable_root):
    """Ohne Kundenkennung bleibt alles wie bisher - keine Umstellung noetig."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        assert controller.customer_id == ""
        assert controller.paths.company_db == portable_root.company_db
        assert "customers" not in str(controller.paths.company_db)
        controller.remember_manual("company.name", "Name", "Einzel GmbH", "profile")
        assert controller.memory.get("company.name").content == "Einzel GmbH"
    finally:
        controller.shutdown()


def test_beenden_ist_mehrfach_aufrufbar(portable_root):
    """Ein zweiter Aufruf darf nichts mehr tun und nichts kaputt machen."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    controller.shutdown()
    controller.shutdown()          # zweites Mal: still


def test_beenden_ueberlebt_jeden_einzelnen_fehler(portable_root):
    """Das Beenden darf nie der Grund fuer einen Absturz sein.

    Der wirkliche Fall dahinter: der Datentraeger wird im Betrieb abgezogen.
    Dann schlaegt jeder Schritt des Beendens fehl - die Netzueberwachung, der
    Abschlusseintrag im Protokoll, das Schliessen beider Datenbanken. Hier
    wird jeder dieser Schritte einzeln zum Scheitern gebracht, damit jede
    Absicherung wirklich angefasst wird und nicht nur dasteht.
    """
    controller = make_controller(portable_root)
    controller.bootstrap()

    class Kaputt:
        def __init__(self, name):
            self.name = name

        def __call__(self, *args, **kwargs):
            raise OSError(f"{self.name}: Datentraeger nicht mehr erreichbar")

    controller.network.stop = Kaputt("network.stop")
    controller.audit.record = Kaputt("audit.record")
    controller.knowledge_db.close = Kaputt("knowledge_db.close")
    controller.company_db.close = Kaputt("company_db.close")

    controller.shutdown()          # kein Absturz, obwohl alles fehlschlaegt
    assert controller._beendet is True


@pytest.mark.skipif(
    os.name == "nt",
    reason="Windows laesst eine geoeffnete Datei nicht loeschen - der Fall ist "
           "dort nicht herstellbar; die Absicherung selbst prueft der Test darueber",
)
def test_beenden_nach_geloeschtem_datenbereich(portable_root):
    """Derselbe Fall am echten Dateisystem, soweit das Betriebssystem es zulaesst."""
    import shutil

    controller = make_controller(portable_root)
    controller.bootstrap()
    shutil.rmtree(portable_root.get("database"))
    controller.shutdown()          # Datenbereich weg - trotzdem kein Absturz


def test_sicherung_auf_zweites_ziel(portable_root, tmp_path):
    """Masterprompt 75: eine Sicherung nur auf demselben Datentraeger hilft nicht."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        controller.remember_manual("company.name", "Name", "Muster GmbH", "profile")
        zweites_ziel = tmp_path.parent / "NAS" / "sicherungen"
        info = controller.backup("monatsende", target=zweites_ziel)

        assert info["extern"] is True
        ordner = Path(info["pfad"])
        assert ordner.is_relative_to(zweites_ziel)
        assert not ordner.is_relative_to(portable_root.root), \
            "die Sicherung darf nicht auf demselben Datentraeger liegen"
        assert (ordner / "company.db").is_file()
        assert (ordner / "MANIFEST.json").is_file()
    finally:
        controller.shutdown()


def test_zwei_sicherungen_in_derselben_sekunde(portable_root):
    """Zwei Sicherungen kurz hintereinander duerfen sich nicht ueberschreiben."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        erste = controller.backup("a")
        zweite = controller.backup("a")
        assert erste["pfad"] != zweite["pfad"]
        assert Path(erste["pfad"]).is_dir() and Path(zweite["pfad"]).is_dir()
    finally:
        controller.shutdown()


def test_gefuehrte_einrichtung_zeigt_offene_schritte(portable_root):
    """Masterprompt 74: das Onboarding muss reproduzierbar sein."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        schritte = controller.setup_wizard_steps()
        assert len(schritte) == 7
        assert schritte[0]["erledigt"] is True, "die Installation steht"
        # Ohne Modell und ohne Onboarding sind die Schritte offen - und benannt
        offen = [s for s in schritte if not s["erledigt"]]
        assert any("Sprachmodell" in s["schritt"] for s in offen)
        assert all(s["befehl"] for s in offen), "jeder offene Schritt nennt den Weg"

        erledigt_vorher, gesamt = controller.setup_progress()
        controller.answer_onboarding("company.name", "Muster GmbH")
        for schluessel in ("company.legal_form", "company.industry",
                           "company.fiscal_year", "company.chart_of_accounts",
                           "company.vat_status", "company.erp"):
            controller.answer_onboarding(schluessel, "Angabe")
        controller.remember_manual("company.approval_rules", "Freigabe",
                                   "Ab 5.000 EUR Geschaeftsfuehrung.", "approval")
        erledigt_nachher, _ = controller.setup_progress()
        assert erledigt_nachher > erledigt_vorher, "der Fortschritt muss sichtbar werden"
    finally:
        controller.shutdown()
