"""Antwort und Rohtreffer trennen (Abschnitte 5, 6, 13, 15, 18).

Kern der Vorgabe: Der Benutzer darf nicht hauptsaechlich die Rohdaten des
Retrievalsystems sehen. Eine Liste von Fundstellen ist kein Ersatz fuer ein
fehlendes Sprachmodell - und technische Angaben wie Modellpfade gehoeren
nicht in die Antwort.
"""

from __future__ import annotations

import pytest

from pkc.llm.base import ChatMessage
from pkc.llm.providers import RetrievalOnlyProvider
from pkc.rag.fragetyp import Fragetyp
from test_controller import make_controller


# ------------------------------------------------- Fallback ohne Modell
def test_fallback_ist_kurz_und_taeuscht_nichts_vor():
    anbieter = RetrievalOnlyProvider(reason="kein Modell auf dem Datentraeger")
    antwort = anbieter.generate([
        ChatMessage("system", "FUNDSTELLEN\n[1] Irgendetwas"),
        ChatMessage("user", "Wie buche ich Skonto?"),
    ])
    assert not antwort.is_generated
    assert "keine KI-Antwort" in antwort.text
    # Kurz: der Hinweis darf die Antwort nicht ersetzen
    assert len(antwort.text.splitlines()) <= 12
    # Und er verweist auf den Quellenbereich, statt Auszuege einzubauen
    assert "Quellen der letzten Antwort" in antwort.text


def test_fallback_nennt_keine_dateipfade():
    """Abschnitt 18: keine Modellpfade in der normalen Antwort."""
    anbieter = RetrievalOnlyProvider(
        reason="kein GGUF-Modell in D:\\Portable\\models")
    antwort = anbieter.generate([ChatMessage("user", "Frage")])
    assert "GGUF" not in antwort.text
    assert "\\models" not in antwort.text
    assert "D:" not in antwort.text
    # ... der Grund bleibt fuer Status und Protokoll erhalten
    assert "GGUF" in antwort.meta["reason"]


def test_fallback_behauptet_bei_smalltalk_keine_fehlende_quelle():
    """Bei Konversation wurde bewusst nicht gesucht - das ist kein Mangel."""
    from pkc.rag.engine import KEINE_RECHERCHE

    anbieter = RetrievalOnlyProvider()
    antwort = anbieter.generate([
        ChatMessage("system", f"* {KEINE_RECHERCHE} (Begruessung)"),
        ChatMessage("user", "Hallo"),
    ])
    assert "keine passende Fundstelle" not in antwort.text
    assert "Fundstellen gefunden" not in antwort.text


# ------------------------------------------------------ in der Antwort
def test_ohne_modell_keine_auszuege_im_hauptbereich(portable_root):
    """Frueher standen acht Fundstellen mit vollem Text in der Antwort."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        from pkc.llm.manager import LlmManager

        controller.llm = LlmManager(RetrievalOnlyProvider(reason="Test"))
        controller.rag.llm = controller.llm

        ergebnis = controller.ask("Wie lange muessen Eingangsrechnungen aufbewahrt werden?")
        text = ergebnis.answer.text

        assert ergebnis.answer.references, "die Fundstellen muessen weiter vorliegen"
        # Die Bezeichnungen ja - die langen Auszuege nicht.
        for referenz in ergebnis.answer.references:
            auszug = (referenz.excerpt or "").strip()
            if len(auszug) > 80:
                assert auszug[:80] not in text, \
                    "Auszuege gehoeren in den Quellenbereich, nicht in die Antwort"
    finally:
        controller.shutdown()


def test_smalltalk_bekommt_keinen_quellenabschnitt(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        ergebnis = controller.ask("Hallo")
        assert ergebnis.answer.fragetyp is Fragetyp.SMALLTALK
        assert "**QUELLEN**" not in ergebnis.answer.text
        assert "Keine lokale Fundstelle verwendet" not in ergebnis.answer.text
    finally:
        controller.shutdown()


def test_fachfrage_behaelt_den_quellenabschnitt(portable_root):
    """Regressionsschutz - die Belegpflicht bleibt."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        ergebnis = controller.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")
        assert "**QUELLEN**" in ergebnis.answer.text
        assert ergebnis.answer.references
    finally:
        controller.shutdown()


# --------------------------------------------------- Recherche-Details
def test_recherche_befehl_zeigt_rohtreffer(portable_root, capsys):
    from ui.cli import main

    wurzel = str(portable_root.root)
    assert main(["--root", wurzel, "--offline", "recherche",
                 "Welche Pflichtangaben muss eine Rechnung enthalten?"]) == 0
    ausgabe = capsys.readouterr().out
    assert "Einstufung" in ausgabe
    assert "Bewertung" in ausgabe, "die technischen Angaben gehoeren hierher"
    assert "Dokument" in ausgabe


def test_recherche_befehl_recherchiert_bei_smalltalk_nicht(portable_root, capsys):
    from ui.cli import main

    assert main(["--root", str(portable_root.root), "--offline",
                 "recherche", "Hallo"]) == 0
    ausgabe = capsys.readouterr().out
    assert "bewusst nicht recherchiert" in ausgabe


# ------------------------------------------------------------- Modell
def test_modell_status_meldet_fehlendes_modell(portable_root, capsys):
    from ui.cli import main

    code = main(["--root", str(portable_root.root), "--offline", "modell", "status"])
    assert code == 2, "fehlendes Modell ist ein Hinweis, kein Erfolg"
    ausgabe = capsys.readouterr().out
    assert "kein Sprachmodell eingerichtet" in ausgabe
    assert "modell empfehlen" in ausgabe, "der naechste Schritt muss dastehen"


def test_modell_laden_ist_offline_gesperrt(portable_root, capsys, monkeypatch):
    from ui.cli import main

    def darf_nicht(*a, **k):
        raise AssertionError("Im OFFLINE-Betrieb darf nichts geladen werden.")

    monkeypatch.setattr("pkc.llm.bezug.laden", darf_nicht)
    code = main(["--root", str(portable_root.root), "--offline", "modell", "laden",
                 "--url", "https://beispiel.invalid/modell.gguf"])
    assert code == 2
    assert "OFFLINE" in capsys.readouterr().out


def test_download_prueft_die_pruefsumme(tmp_path, http_server):
    """Eine falsche Pruefsumme muss die Datei verwerfen, nicht behalten."""
    from pkc.llm.bezug import laden

    url = http_server.add("/modell.gguf", b"nicht wirklich ein Modell")

    schlecht = laden(url, tmp_path, erwartete_pruefsumme="00" * 32)
    assert not schlecht.ok
    assert "stimmt NICHT" in schlecht.meldung
    assert list(tmp_path.glob("*.gguf")) == [], "die Datei muss verworfen sein"
    assert list(tmp_path.glob("*.teil")) == [], "auch die Teildatei muss weg sein"

    gut = laden(url, tmp_path, erwartete_pruefsumme=schlecht.pruefsumme)
    assert gut.ok and gut.pfad.is_file()
    assert "Pruefsumme bestaetigt" in gut.meldung


def test_download_ohne_pruefsumme_sagt_es(tmp_path, http_server):
    from pkc.llm.bezug import laden

    url = http_server.add("/m.gguf", b"inhalt")
    ergebnis = laden(url, tmp_path)
    assert ergebnis.ok
    assert "nicht gegen Manipulation geprueft" in ergebnis.meldung


def test_download_ueberschreibt_nicht_versehentlich(tmp_path, http_server):
    from pkc.llm.bezug import laden

    url = http_server.add("/m.gguf", b"inhalt")
    assert laden(url, tmp_path).ok
    zweiter = laden(url, tmp_path)
    assert not zweiter.ok and "bereits" in zweiter.meldung


# ------------------------------------------- Primaerquellen (Abschnitt 17)
def test_warnt_wenn_nur_sekundaerquellen_vorliegen(portable_root):
    """Eine Antwort aus Fachmodulen sieht sonst genauso belegt aus wie eine
    aus dem Gesetzestext."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        ergebnis = controller.ask("Was ist Reverse Charge?")
        assert ergebnis.answer.references
        assert all(r.priority >= 5 for r in ergebnis.answer.references), \
            "im Auslieferungszustand gibt es nur Fachmodule"
        warnungen = " ".join(ergebnis.answer.warnings)
        assert "Sekundaerquellen" in warnungen
        assert "Primaerquelle" in warnungen
    finally:
        controller.shutdown()


def test_keine_sekundaerwarnung_bei_smalltalk(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        ergebnis = controller.ask("Hallo")
        assert "Sekundaerquellen" not in " ".join(ergebnis.answer.warnings)
    finally:
        controller.shutdown()


# ------------------------------------------------ Rueckfragen (Abschnitt 10)
def test_komplexer_fall_fordert_rueckfragen_an(portable_root):
    """Bei fehlenden Angaben soll gefragt statt geraten werden."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        from pkc.rag.fragetyp import einstufen

        frage = ("Wir haben eine Rechnung aus Frankreich von einem Unternehmer "
                 "erhalten, wie buchen wir das?")
        bundle = controller.rag.builder.build([], [])
        nachrichten = controller.rag.build_messages(
            frage, bundle, einstufung=einstufen(frage))
        anweisung = "\n".join(m.content for m in nachrichten if m.role == "system")
        assert "gezielt nach" in anweisung
        assert "statt zu raten" in anweisung
        assert "hoechstens drei" in anweisung
    finally:
        controller.shutdown()
