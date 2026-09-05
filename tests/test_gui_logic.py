"""Strukturtest der Oberflaechenlogik gegen ein Tkinter-Doppel.

WICHTIG (Ehrlichkeit): Diese Tests ersetzen KEINEN echten GUI-Test. Sie
pruefen, dass der Oberflaechencode fehlerfrei durchlaeuft, die richtigen
Controller-Funktionen aufruft und Ergebnisse korrekt anzeigt. Aussehen,
Layout und echtes Tk-Verhalten sind damit nicht geprueft; das geschieht auf
einem Windows-Rechner nach docs/ABNAHME.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import tk_double
from test_controller import make_controller


@pytest.fixture
def gui(portable_root):
    dialogs = tk_double.install()
    for module in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[module]
    from ui import tk_app

    controller = make_controller(portable_root)
    report = controller.bootstrap()
    window = tk_app.MainWindow(controller, report)
    yield window, controller, dialogs, tk_app
    controller.shutdown()


def test_main_window_builds_all_tabs(gui):
    window, controller, _, _ = gui
    assert window.notebook.children, "die Registerkarten muessen angelegt sein"
    assert window.chat.buffer, "die Begruessung muss im Chat stehen"
    assert "bereit" in window.chat.buffer
    assert "OFFLINE" in window.mode_label.options["text"]
    assert "Wissensstand" in window.knowledge_label.options["text"]


def test_send_question_shows_answer_and_sources(gui):
    window, controller, _, _ = gui
    window.entry.insert("end", "Welche Pflichtangaben muss eine Rechnung enthalten?")
    window._send()
    assert "Welche Pflichtangaben" in window.chat.buffer
    assert "QUELLEN" in window.chat.buffer
    assert window.sources.buffer, "das Quellenfeld muss gefuellt sein"
    assert "Fachmodul" in window.sources.buffer
    assert len(controller.messages()) == 2


def test_capture_candidate_is_offered_and_stored_on_yes(gui):
    window, controller, dialogs, _ = gui
    dialogs.answers = [True]
    window.entry.insert("end", "Wir verwenden grundsaetzlich SKR03.")
    window._send()
    questions = [m for m in dialogs.messages if m[0] == "frage"]
    assert questions, "es muss nachgefragt werden, bevor gespeichert wird"
    assert "SKR03" in questions[0][2]
    entry = controller.memory.get("company.chart_of_accounts")
    assert entry is not None and "SKR03" in entry.content


def test_capture_candidate_not_stored_on_no(gui):
    window, controller, dialogs, _ = gui
    dialogs.answers = [False]
    window.entry.insert("end", "Wir verwenden grundsaetzlich SKR04.")
    window._send()
    assert controller.memory.get("company.chart_of_accounts") is None


def test_memory_tab_lists_and_archives(gui):
    window, controller, dialogs, _ = gui
    controller.remember_manual("company.name", "Unternehmensname", "Muster GmbH", "profile")
    window._refresh_memory()
    assert window.memory_tree.rows, "der Eintrag muss in der Tabelle stehen"
    values = list(window.memory_tree.rows.values())[0]["values"]
    assert values[0] == "company.name" and "Muster GmbH" in values[3]

    window.memory_tree.select_row(0)
    dialogs.answers = [True]
    window._archive_memory()
    assert controller.memory.get("company.name") is None
    assert controller.memory.history("company.name"), "der Verlauf bleibt erhalten"


def test_document_tab_adds_file(gui, tmp_path):
    window, controller, dialogs, _ = gui
    beleg = tmp_path / "rechnung.txt"
    beleg.write_text("# Rechnung 2026-1\nNettobetrag 100,00 EUR zuzueglich Umsatzsteuer.\n",
                     encoding="utf-8")
    dialogs.open_file = str(beleg)
    window._add_document()
    assert window.document_tree.rows, "der Beleg muss in der Liste erscheinen"
    assert "Beleg aufgenommen" in window.chat.buffer


def test_offline_update_reports_honestly(gui):
    window, controller, dialogs, _ = gui
    controller.network.force(False, "Test: offline")
    dialogs.answers = [True]      # trotzdem versuchen
    window._run_update(False)
    assert any("Kein Internet" in title for _, title, _ in dialogs.messages)
    assert "no_network" in window.update_log.buffer.lower() or \
           "NO_NETWORK" in window.update_log.buffer
    assert controller.knowledge.stats()["documents"] > 0, "lokales Wissen bleibt nutzbar"


def test_network_loss_message_mentions_local_knowledge(gui):
    window, controller, _, _ = gui
    controller.network.force(True, "Test: online")
    controller.network.force(False, "Test: Verbindung verloren")
    assert "Internetverbindung verloren" in window.chat.buffer
    assert "lokalen Wissensstand" in window.chat.buffer


def test_settings_are_saved_to_disk(gui):
    window, controller, dialogs, _ = gui
    # Bewusst Werte, die von der Vorgabe abweichen: gespeichert wird nur,
    # was abweicht. "weekly" ist seit der Umstellung selbst die Vorgabe und
    # taugt deshalb nicht mehr als Nachweis.
    window.setting_vars["updates.schedule"].set("monthly")
    window.setting_vars["retrieval.top_k"].set("12")
    window._save_settings()
    assert controller.paths.settings_file.is_file()
    text = controller.paths.settings_file.read_text(encoding="utf-8")
    assert "monthly" in text and "12" in text


def test_startup_window_reports_state(portable_root):
    tk_double.install()
    for module in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[module]
    from ui import tk_app

    controller = make_controller(portable_root)
    try:
        window = tk_app.StartupWindow(controller)
        # run() startet die Ereignisschleife; hier wird der Ablauf direkt geprueft
        report = controller.bootstrap()
        window._write(report.as_text())
        assert "Systempruefung" in window.text.buffer
        assert "Fachwissen" in window.text.buffer
        assert "Der Buchhalter kann gestartet werden." in window.text.buffer
    finally:
        controller.shutdown()


# ======================================================================
# Moduswahl in der Oberflaeche
# ======================================================================

def test_moduswahl_in_der_oberflaeche(gui):
    """Der Benutzer waehlt den Modus im Fenster - mit Ansage und dauerhaft."""
    import json

    from pkc.netstate import Mode

    window, controller, dialogs, _ = gui
    assert controller.mode is Mode.OFFLINE   # so richtet der Testhelfer ein

    window.mode_var.set("ONLINE")
    window._on_mode_changed()

    assert controller.mode is Mode.ONLINE
    # Der Benutzer muss erfahren, was jetzt gilt
    ansagen = " ".join(m[2] for m in dialogs.messages if m[0] == "info")
    assert "Online-Modus aktiv" in ansagen
    assert "lokal" in ansagen.lower(), "ONLINE darf lokale Funktionen nicht in Frage stellen"

    # ... und die Wahl muss auf der Platte stehen
    gespeichert = json.loads(controller.paths.settings_file.read_text(encoding="utf-8"))
    assert gespeichert["network"]["mode"] == "ONLINE"


def test_offline_wahl_zeigt_die_richtige_ansage(gui):
    from pkc.netstate import Mode

    window, controller, dialogs, _ = gui
    controller.set_mode(Mode.HYBRID)
    window.mode_var.set("OFFLINE")
    window._on_mode_changed()

    assert controller.mode is Mode.OFFLINE
    ansagen = " ".join(m[2] for m in dialogs.messages if m[0] == "info")
    assert "keine externen Online-Dienste" in ansagen


def test_gleicher_modus_loest_keine_meldung_aus(gui):
    """Wer denselben Eintrag noch einmal waehlt, soll nicht belaestigt werden."""
    window, controller, dialogs, _ = gui
    vorher = len(dialogs.messages)
    window.mode_var.set(controller.mode.value)
    window._on_mode_changed()
    assert len(dialogs.messages) == vorher
