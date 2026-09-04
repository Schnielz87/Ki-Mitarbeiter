"""Die Nutzungskette aus Masterprompt 49 und 51 in einem Durchlauf.

Dieser Test bildet die geforderte Abnahmekette so weit ab, wie sie ohne
Windows, ohne Bildschirm und ohne echtes Sprachmodell abbildbar ist:

    Start (offline) -> Fachfrage -> Unternehmenswissen speichern ->
    beenden -> Datentraeger an anderen Ort -> starten -> Wissen ist da ->
    online gehen -> Wissensupdate -> offline gehen -> neues Wissen nutzen

Ersetzt: das Sprachmodell durch einen Testanbieter, die amtlichen Quellen
durch einen echten lokalen HTTP-Server, den zweiten Rechner durch ein
anderes Wurzelverzeichnis mit Leerzeichen im Pfad.

Nicht ersetzbar und daher **nicht** hierdurch abgedeckt: die gebaute EXE,
die echte Tkinter-Oberflaeche, ein echtes Sprachmodell, die echten amtlichen
Server, ein echter zweiter PC. Dafuer: docs/ABNAHME.md.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from pkc.netstate import Mode
from pkc.paths import Paths
from test_controller import make_controller

BMF_NEU = b"""<html><head><title>Neues Verwaltungsschreiben zur Belegausgabepflicht</title></head>
<body><h1>Belegausgabepflicht</h1>
<p>Ab dem Veranlagungszeitraum 2027 gilt fuer die Belegausgabe eine neue
Vereinfachungsregel. Bei Kleinbetragsrechnungen unterhalb der Grenze kann die
Belegausgabe unter den im Schreiben genannten Voraussetzungen unterbleiben.
Massgeblich ist dieses Schreiben in Verbindung mit Paragraph 146a AO.</p></body></html>"""


@pytest.fixture
def testquelle(portable_root, http_server):
    """Ein lokaler Server tritt an die Stelle der amtlichen Quellen."""
    url = http_server.add("/bmf/belegausgabe.html", BMF_NEU,
                          "text/html; charset=utf-8", '"v1"')
    registry = {
        "sources": [{
            "source_id": "T_BMF", "name": "Testquelle Verwaltungsschreiben",
            "publisher": "Test", "priority": 2, "kind": "admin",
            "base_url": http_server.base, "licence": "Test",
            "documents": [{
                "doc_uid": "T_BELEGAUSGABE", "url": url,
                "title": "Neues Verwaltungsschreiben zur Belegausgabepflicht",
                "citation": "BMF-Schreiben Belegausgabe", "format": "html",
                "kind": "admin",
            }],
        }]
    }
    (portable_root.get("config") / "source_registry.json").write_text(
        json.dumps(registry), encoding="utf-8"
    )
    return http_server


def test_vollstaendige_nutzungskette(portable_root, testquelle, tmp_path):
    # --- TEST 2/3: ohne Internet starten und eine Fachfrage stellen --------
    buchhalter = make_controller(portable_root, online=False)
    bericht = buchhalter.bootstrap()
    assert bericht.usable, bericht.as_text()
    assert bericht.mode is Mode.OFFLINE
    assert bericht.knowledge_date, "der lokale Wissensstand muss ausgewiesen sein"

    antwort = buchhalter.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")
    assert antwort.answer.references, "offline muss lokal recherchiert werden"
    assert "QUELLEN" in antwort.answer.text
    assert "WISSENSSTAND" in antwort.answer.text

    # --- TEST 4: neue Unternehmensinformation speichern -------------------
    erkannt = buchhalter.ask("Wir verwenden grundsaetzlich SKR03.")
    kandidat = next(c for c in erkannt.capture_candidates
                    if c.mem_key == "company.chart_of_accounts")
    buchhalter.remember(kandidat)
    buchhalter.remember_manual(
        "company.approval_rules", "Freigaberegel",
        "Rechnungen ab 5.000 EUR muessen durch den Geschaeftsfuehrer freigegeben werden.",
        "approval",
    )

    # --- TEST 5: Programm beenden ----------------------------------------
    buchhalter.shutdown()

    # --- TEST 6/7: Datentraeger an einen anderen Ort, dort starten --------
    zweiter_pc = tmp_path.parent / "Zweiter PC" / "Laufwerk E" / "Portable Buchhalter"
    if zweiter_pc.exists():
        shutil.rmtree(zweiter_pc)
    zweiter_pc.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(portable_root.root, zweiter_pc)

    unterwegs = make_controller(Paths(zweiter_pc), online=False)
    bericht2 = unterwegs.bootstrap()
    assert bericht2.usable, bericht2.as_text()

    # --- TEST 8: das Unternehmenswissen ist dort vorhanden ----------------
    kontenrahmen = unterwegs.memory.get("company.chart_of_accounts")
    assert kontenrahmen is not None and "SKR03" in kontenrahmen.content
    assert unterwegs.memory.get("company.approval_rules") is not None

    frage = unterwegs.ask("Welchen Kontenrahmen verwendet dieses Unternehmen?")
    assert frage.answer.context is not None
    assert "SKR03" in frage.answer.context.company_block, \
        "das Unternehmenswissen muss in den Modellkontext einfliessen"

    # auch die Gespraechshistorie ist mitgewandert
    assert len(unterwegs.conversations()) >= 1

    # --- TEST 9: anderer Laufwerksbuchstabe -------------------------------
    assert str(unterwegs.paths.root) == str(zweiter_pc)
    assert " " in str(zweiter_pc), "der Zielpfad enthaelt absichtlich Leerzeichen"

    # --- TEST 10: online gehen und Wissen aktualisieren -------------------
    unterwegs.network.force(True, "Test: Verbindung hergestellt")
    assert unterwegs.mode is Mode.HYBRID
    lauf = unterwegs.run_update(trigger="abnahme")
    assert lauf.status == "success", lauf.as_markdown()
    assert lauf.updated == 1

    berichtsdatei = zweiter_pc / "updates" / lauf.run_id / "bericht.md"
    assert berichtsdatei.is_file(), "der Updatebericht muss als Datei vorliegen"
    original = zweiter_pc / "resources" / "raw" / "T_BMF" / "T_BELEGAUSGABE.html"
    assert original.is_file(), "das Original muss lokal gespeichert sein"

    # --- TEST 11: Internet wieder abschalten ------------------------------
    unterwegs.network.force(False, "Test: Verbindung getrennt")
    assert unterwegs.mode is Mode.OFFLINE

    # --- TEST 12: das neu geladene Wissen ist offline nutzbar -------------
    neu = unterwegs.ask("Was gilt fuer die Belegausgabepflicht ab 2027?")
    fundstellen = " ".join(r.reference + r.excerpt for r in neu.answer.references)
    assert "Belegausgabe" in fundstellen, (
        "das online geladene Schreiben muss offline auffindbar sein"
    )
    assert neu.answer.mode == "OFFLINE"
    unterwegs.shutdown()

    # --- und nach einem weiteren Neustart ist alles immer noch da ---------
    nochmal = make_controller(Paths(zweiter_pc), online=False)
    nochmal.bootstrap()
    try:
        assert "SKR03" in nochmal.memory.get("company.chart_of_accounts").content
        treffer = nochmal.searcher.search("Belegausgabepflicht", top_k=5)
        assert any("Belegausgabe" in h.title or "Belegausgabe" in h.text for h in treffer)
    finally:
        nochmal.shutdown()


def test_kein_server_noetig(portable_root):
    """Der Grundbetrieb kommt ohne jeden Serverdienst aus (Masterprompt 5)."""
    buchhalter = make_controller(portable_root, online=False)
    buchhalter.bootstrap()
    try:
        buchhalter.remember_manual("company.name", "Unternehmensname", "Muster GmbH", "profile")
        buchhalter.ask("Wie pruefe ich eine Eingangsrechnung?")
        buchhalter.backup("ohne-server")
        buchhalter.export_company_profile()

        # Alles liegt in Dateien unterhalb der Wurzel
        wurzel = portable_root.root
        for pfad in (portable_root.company_db, portable_root.knowledge_db):
            assert pfad.is_file() and str(pfad).startswith(str(wurzel))
        assert (wurzel / "company" / "unternehmensprofil.md").is_file()
        assert any((wurzel / "backups").iterdir())
    finally:
        buchhalter.shutdown()


def test_wiederherstellung_ohne_chat(portable_root):
    """Der Stand ist allein von der Platte ablesbar (Masterprompt 45)."""
    buchhalter = make_controller(portable_root, online=False)
    buchhalter.bootstrap()
    try:
        buchhalter.remember_manual("company.name", "Unternehmensname", "Muster GmbH", "profile")
        buchhalter.backup("stand")
        info = buchhalter.restore_info()
        assert info["wurzel"] == str(portable_root.root)
        assert info["sicherungen"], "die Sicherungen muessen auffindbar sein"
        assert info["wissensstand"], "der Wissensstand muss ablesbar sein"
    finally:
        buchhalter.shutdown()
