"""Unternehmenswissen, Belege und Wissen & Quellen nach dem Zielentwurf.

Kacheln mit Zahlen, ein Dokumenten-Workflow und eine sichtbare
Update-Pipeline - alles auf Diensten, die es schon gab.
"""

from __future__ import annotations

import sys

import pytest

import tk_double
from test_controller import make_controller


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


# --------------------------------------------------- Unternehmenswissen
def test_die_kacheln_zaehlen_die_eintraege(fenster):
    """Eine flache Liste sagt nicht, was das Unternehmen hinterlegt hat."""
    window, controller, _ = fenster
    controller.remember_manual("company.name", "Unternehmensname",
                               "Muster GmbH", "profile")
    controller.remember_manual("company.chart_of_accounts", "Kontenrahmen",
                               "SKR03", "accounting")
    window._refresh_memory()

    _, profil = window._memory_kachel_widgets["Unternehmensprofil"]
    _, buchhaltung = window._memory_kachel_widgets["Buchhaltung"]
    assert "1 Eintraege" in profil.options["text"]
    assert "1 Eintraege" in buchhaltung.options["text"]


def test_eine_kachel_filtert_die_liste(fenster):
    """Eine Kachel, die nur eine Zahl zeigt und sonst nichts tut, waere ein
    toter Knopf (Auftrag Abschnitt 34)."""
    window, controller, _ = fenster
    controller.remember_manual("company.name", "Unternehmensname",
                               "Muster GmbH", "profile")
    controller.remember_manual("company.chart_of_accounts", "Kontenrahmen",
                               "SKR03", "accounting")
    window._refresh_memory()
    assert len(window.memory_tree.rows) == 2

    kachel, _ = window._memory_kachel_widgets["Buchhaltung"]
    kachel.bindings["<Button-1>"](None)

    werte = [z["values"][0] for z in window.memory_tree.rows.values()]
    assert werte == ["company.chart_of_accounts"], werte


def test_alles_anzeigen_hebt_den_filter_auf(fenster):
    window, controller, _ = fenster
    controller.remember_manual("company.name", "Name", "Muster GmbH", "profile")
    controller.remember_manual("company.chart_of_accounts", "Kontenrahmen",
                               "SKR03", "accounting")
    window._refresh_memory()
    window._memory_kachel_widgets["Buchhaltung"][0].bindings["<Button-1>"](None)
    assert len(window.memory_tree.rows) == 1

    window._show_all_memory()
    assert len(window.memory_tree.rows) == 2


def test_die_kacheln_wachsen_nicht_bei_jeder_aktualisierung(fenster):
    window, _, _ = fenster
    window._refresh_memory()
    anzahl = len(window.memory_kacheln.children)
    for _ in range(3):
        window._refresh_memory()
    assert len(window.memory_kacheln.children) == anzahl


# ------------------------------------------------------------- Belege
def test_der_workflow_zeigt_das_ergebnis(fenster, tmp_path):
    window, controller, dialoge = fenster
    beleg = tmp_path / "rechnung.txt"
    beleg.write_text(
        "# Rechnung 2026-9\n\n"
        + ("Die Eingangsrechnung des franzoesischen Lieferanten weist einen "
           "Nettobetrag von 300,00 EUR aus. Umsatzsteuer ist nicht "
           "ausgewiesen; es liegt ein Hinweis auf die Steuerschuldnerschaft "
           "des Leistungsempfaengers vor. ") * 6,
        encoding="utf-8")
    dialoge.open_file = str(beleg)
    window._add_document()

    zeile = list(window.document_tree.rows.values())[0]["values"]
    assert "rechnung" in str(zeile[0]).lower()
    assert "Abschnitte erkannt" in str(zeile[4]), (
        f"die Ergebnisspalte muss das Analyseergebnis nennen: {zeile[4]!r}")
    assert "1 Dokumente" in window.documents_hint.options["text"]


def test_ein_leeres_dokument_bekommt_auch_ein_ergebnis(fenster, tmp_path):
    """Ein Gedankenstrich laesst offen, ob nichts gefunden wurde oder ob
    gar nichts passiert ist."""
    window, _, dialoge = fenster
    beleg = tmp_path / "kurz.txt"
    beleg.write_text("Kurz.\n", encoding="utf-8")
    dialoge.open_file = str(beleg)
    window._add_document()

    zeile = list(window.document_tree.rows.values())[0]["values"]
    assert str(zeile[4]) not in ("", "—"), "auch hier gehoert eine Auskunft hin"


def test_in_unterhaltung_uebernehmen_wechselt_und_bereitet_vor(fenster, tmp_path):
    """Es wird nichts automatisch gefragt - der Beleg wird genannt und die
    Frage vorbereitet. Was gefragt wird, entscheidet der Benutzer."""
    window, controller, dialoge = fenster
    beleg = tmp_path / "vertrag.txt"
    beleg.write_text("# Vertrag\nLaufzeit 24 Monate.\n", encoding="utf-8")
    dialoge.open_file = str(beleg)
    window._add_document()
    window.document_tree.select_row(0)

    # Ausdruecklich woanders hingehen. Sonst prueft der Test nichts: die
    # Anwendung startet in der Unterhaltung, und "ist dort" waere auch
    # ohne den Wechsel wahr.
    window.schale.zeigen("belege")
    window._beleg_uebernehmen()

    assert window.schale.aktiv == "unterhaltung", (
        "die Uebernahme muss zur Unterhaltung wechseln")
    assert "Dokument uebernommen" in window.chat.buffer
    assert "vertrag" in window.entry.buffer.lower()
    assert len(controller.messages()) == 0, "es darf nichts abgeschickt worden sein"


def test_erneut_analysieren_meldet_eine_verschwundene_datei(fenster, tmp_path):
    window, controller, dialoge = fenster
    beleg = tmp_path / "weg.txt"
    beleg.write_text("# Beleg\nInhalt.\n", encoding="utf-8")
    dialoge.open_file = str(beleg)
    window._add_document()
    window.document_tree.select_row(0)

    from pathlib import Path

    abgelegt = Path(controller.documents()[0]["path"])
    if not abgelegt.is_absolute():
        abgelegt = controller.paths.root / abgelegt
    abgelegt.unlink()
    window._beleg_erneut()
    assert any("nicht mehr da" in text for _, _, text in dialoge.messages)


# --------------------------------------------------- Wissen & Quellen
def test_die_kennzahlen_stehen_oben(fenster):
    window, _, _ = fenster
    window._refresh_update_lage()
    for titel in ("Wissensstand", "Quellen", "Letzte Pruefung", "Naechste Pruefung"):
        wert = window._wissen_kachel_widgets[titel].options["text"]
        assert wert and wert != "—", f"{titel} ist leer"


def test_die_pipeline_zeigt_alle_fuenf_schritte(fenster):
    """Die Schritte gab es laengst - sie liefen nur unsichtbar ab, und ein
    Vorgang, den niemand sieht, wirkt wie ein Stillstand."""
    window, _, _ = fenster
    assert list(window._pipeline_schritte) == [
        "Pruefen", "Staging", "Validieren", "Indexieren", "Aktivieren"]
    for label in window._pipeline_schritte.values():
        assert "○" in label.options["text"], "zu Beginn ist nichts erledigt"


def test_ein_gescheitertes_update_faerbt_den_schritt_rot(fenster):
    """So ist zu sehen, WO es hakte - nicht nur, DASS es hakte."""
    window, _, _ = fenster
    window._pipeline_setzen(2, fehler=True)
    farben = {name: label.options["fg"]
              for name, label in window._pipeline_schritte.items()}
    assert farben["Pruefen"] == "#1c7a45", "erledigte Schritte sind gruen"
    assert farben["Validieren"] == "#a32626", "der gescheiterte ist rot"
    assert farben["Aktivieren"] == "#9aa8b8", "spaetere bleiben offen"


def test_ein_offline_update_laesst_die_pipeline_nicht_gruen_werden(fenster):
    """Sonst zeigte die Anzeige einen Erfolg, den es nicht gab."""
    window, controller, dialoge = fenster
    controller.network.force(False, "Test: offline")
    dialoge.answers = [True]
    window._run_update(False)

    farben = [label.options["fg"] for label in window._pipeline_schritte.values()]
    assert "#1c7a45" not in farben[3:], (
        "Indexieren und Aktivieren duerfen ohne Netz nicht als erledigt gelten")
