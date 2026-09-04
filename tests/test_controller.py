"""Gesamttest der Anwendungssteuerung - dieselbe Logik, die die Oberflaeche nutzt."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.controller import AppController
from pkc.config import Config
from pkc.llm.manager import LlmManager
from pkc.llm.providers import ScriptedProvider
from pkc.netstate import Mode, NetworkMonitor
from pkc.paths import Paths


def make_controller(paths: Paths, responder=None, online: bool = False) -> AppController:
    """Controller mit Testanbieter statt echtem Modell und ohne Netzzugriff."""
    config = Config.load(paths)
    config.set("llm.provider", "echo")
    config.set("retrieval.embedding_dim", 256)
    monitor = NetworkMonitor([], enabled=False)
    monitor.force(online, "Test")
    controller = AppController(paths, config, monitor, console_logging=False)
    provider = ScriptedProvider(
        responder or (lambda messages: "**ERGEBNIS**\nGetestete Antwort mit Beleg [1].")
    )
    controller.llm = LlmManager(provider)
    controller.rag.llm = controller.llm
    controller._test_provider = provider  # type: ignore[attr-defined]
    return controller


@pytest.fixture
def controller(portable_root):
    ctrl = make_controller(portable_root)
    ctrl.bootstrap()
    yield ctrl
    ctrl.shutdown()


def test_bootstrap_reports_real_state(portable_root):
    ctrl = make_controller(portable_root)
    report = ctrl.bootstrap()
    try:
        assert report.usable, report.as_text()
        names = {i.name: i for i in report.items}
        assert names["Datenverzeichnis"].ok
        assert names["Fachwissen"].ok and "Dokumente" in names["Fachwissen"].detail
        assert names["Unternehmensgedaechtnis"].ok
        assert report.mode is Mode.OFFLINE
        # Die Datenbanken liegen tatsaechlich auf der Platte
        assert portable_root.knowledge_db.is_file()
        assert portable_root.company_db.is_file()
        assert (portable_root.root / ".portable_root").is_file()
        text = report.as_text()
        assert "Systempruefung" in text and "Betriebsart" in text
    finally:
        ctrl.shutdown()


def test_offline_question_uses_local_knowledge(controller):
    outcome = controller.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")
    assert outcome.answer.mode == "OFFLINE"
    assert outcome.answer.references, "es muessen lokale Fundstellen gefunden werden"
    assert any("Rechnung" in r.reference or "Rechnung" in r.title
               for r in outcome.answer.references)
    assert "QUELLEN" in outcome.answer.text
    assert "WISSENSSTAND" in outcome.answer.text
    # Die Nachricht und ihre Quellen sind gespeichert
    messages = controller.messages()
    assert len(messages) == 2 and messages[0]["role"] == "user"
    assert messages[1]["sources"], "Quellenbelege muessen gespeichert sein"


def test_invented_citations_are_removed(portable_root):
    ctrl = make_controller(portable_root, lambda m: "Antwort mit erfundener Quelle [42] und [1].")
    ctrl.bootstrap()
    try:
        outcome = ctrl.ask("Wie funktioniert der Vorsteuerabzug?")
        body = outcome.answer.text.split("**HINWEISE DER ANWENDUNG**")[0]
        assert "[42]" not in body, "die erfundene Fundstelle muss aus der Antwort verschwinden"
        assert "[1]" in body, "die gueltige Fundstelle bleibt erhalten"
        assert any("nicht gab" in w for w in outcome.answer.warnings)
        # und der Nutzer erfaehrt davon
        assert "[42]" in outcome.answer.text.split("**HINWEISE DER ANWENDUNG**")[1]
    finally:
        ctrl.shutdown()


def test_company_knowledge_is_captured_and_persisted(controller, portable_root):
    outcome = controller.ask("Wir verwenden grundsaetzlich SKR03.")
    keys = [c.mem_key for c in outcome.capture_candidates]
    assert "company.chart_of_accounts" in keys, "der Kontenrahmen muss erkannt werden"

    candidate = next(c for c in outcome.capture_candidates
                     if c.mem_key == "company.chart_of_accounts")
    controller.remember(candidate)
    entry = controller.memory.get("company.chart_of_accounts")
    assert entry is not None and "SKR03" in entry.content
    controller.shutdown()

    # Neustart auf demselben Datentraeger: das Wissen ist wieder da
    restarted = make_controller(portable_root)
    restarted.bootstrap()
    try:
        again = restarted.memory.get("company.chart_of_accounts")
        assert again is not None and "SKR03" in again.content
        found = restarted.memory.search("Kontenrahmen")
        assert found and "SKR03" in found[0].content
    finally:
        restarted.shutdown()


def test_knowledge_survives_drive_letter_change(portable_root, tmp_path, monkeypatch):
    """Simuliert D: -> E: sowie einen zweiten PC: derselbe Datenbestand, neuer Pfad."""
    ctrl = make_controller(portable_root)
    ctrl.bootstrap()
    ctrl.remember_manual("company.chart_of_accounts", "Kontenrahmen",
                         "Das Unternehmen verwendet SKR03.", "accounting")
    ctrl.remember_manual("company.approval_rules", "Freigaberegel",
                         "Rechnungen ab 5.000 EUR muessen freigegeben werden.", "approval")
    ctrl.shutdown()

    # Der komplette Datentraeger wird an einen anderen Ort mit Leerzeichen kopiert
    # (ausserhalb der Quelle, sonst kopierte man in sich selbst)
    other = tmp_path.parent / "Anderer PC" / "E Laufwerk" / "Portable-Buchhalter"
    if other.exists():
        shutil.rmtree(other)
    other.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(portable_root.root, other)

    monkeypatch.setenv("KIM_ROOT", str(other))
    moved = Paths(other)
    ctrl2 = make_controller(moved)
    report = ctrl2.bootstrap()
    try:
        assert report.usable
        assert str(ctrl2.paths.root) == str(other)
        entry = ctrl2.memory.get("company.chart_of_accounts")
        assert entry is not None and "SKR03" in entry.content
        assert ctrl2.memory.get("company.approval_rules") is not None
        # und die Fachwissensbasis ist ebenfalls mitgewandert
        assert ctrl2.knowledge.stats()["documents"] > 0
        outcome = ctrl2.ask("Welchen Kontenrahmen verwendet dieses Unternehmen?")
        context = outcome.answer.context
        assert context is not None and "SKR03" in context.company_block
    finally:
        ctrl2.shutdown()


def test_onboarding_tracks_progress(controller):
    done, total = controller.onboarding_progress()
    assert done == 0 and total > 15
    controller.answer_onboarding("company.name", "Muster Handels GmbH")
    controller.answer_onboarding("company.chart_of_accounts", "SKR03")
    done_after, _ = controller.onboarding_progress()
    assert done_after == 2
    open_questions = [q for q in controller.onboarding_questions() if not q["beantwortet"]]
    assert all(q["titel"] for q in open_questions)


def test_document_upload_and_search(controller, tmp_path):
    beleg = tmp_path / "eingangsrechnung.txt"
    beleg.write_text(
        "# Eingangsrechnung 2026-4711\n"
        "Lieferant: Meier Werkzeuge GmbH, Musterweg 3, 04109 Leipzig\n"
        "Rechnungsdatum 12.03.2026, Leistungsdatum 10.03.2026\n"
        "Position: 10 Schraubendreher, Nettobetrag 250,00 EUR, 19 Prozent Umsatzsteuer 47,50 EUR\n"
        "Gesamtbetrag 297,50 EUR. Steuernummer 231/123/45678\n",
        encoding="utf-8",
    )
    result = controller.add_document(beleg)
    assert result["status"] == "aufgenommen" and result["abschnitte"] >= 1
    stored = Path(controller.paths.root) / result["pfad"]
    assert stored.is_file(), "der Beleg muss tatsaechlich auf der SSD liegen"

    hits = controller.search_documents("Schraubendreher Meier")
    assert hits and "Schraubendreher" in hits[0]["text"]

    # Erneutes Hinzufuegen derselben Datei wird erkannt
    again = controller.add_document(beleg)
    assert again["status"] == "bereits_vorhanden"


def test_backup_writes_real_files_with_checksums(controller):
    controller.remember_manual("company.name", "Unternehmensname", "Muster GmbH", "profile")
    info = controller.backup("test")
    directory = Path(controller.paths.root) / info["verzeichnis"]
    assert (directory / "company.db").is_file()
    assert (directory / "knowledge.db").is_file()
    manifest = json.loads((directory / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["pruefsummen"]["company.db"] == info["pruefsummen"]["company.db"]


def test_status_and_export(controller):
    controller.remember_manual("company.chart_of_accounts", "Kontenrahmen", "SKR04", "accounting")
    status = controller.status()
    assert status["betriebsart"] == "OFFLINE"
    assert status["fachwissen"]["dokumente"] > 0
    assert status["unternehmenswissen"]["active"] == 1

    target = controller.export_company_profile()
    assert target.is_file()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert any(e["mem_key"] == "company.chart_of_accounts" for e in data["eintraege"])
    readable = target.parent / "unternehmensprofil.md"
    assert readable.is_file() and "SKR04" in readable.read_text(encoding="utf-8")


def test_conversation_export(controller):
    controller.ask("Was ist eine Kleinbetragsrechnung?")
    path = controller.export_conversation()
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Frage" in text and "Antwort" in text
