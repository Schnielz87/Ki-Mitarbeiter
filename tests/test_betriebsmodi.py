"""Betriebsmodi HYBRID / OFFLINE / ONLINE (Masterprompt-Erweiterung).

Der Kern: **Betriebsmodus und Internetstatus sind zwei getrennte Zustaende.**
Der Modus ist eine Entscheidung des Benutzers, der Internetstatus ein
Befund. Die Anwendung darf eine Entscheidung nie selbsttaetig aufheben.

Frueher wurde der Modus aus dem Netzbefund abgeleitet. Damit waere OFFLINE
keine Entscheidung gewesen, sondern nur die Beschreibung eines Zustands -
und ein wiederkehrendes Netz haette den Benutzer unbemerkt zurueck in den
Onlinebetrieb versetzt.
"""

from __future__ import annotations

import json

import pytest

from pkc.config import Config
from pkc.netstate import Betriebsart, Mode, NetworkMonitor
from test_controller import make_controller


@pytest.fixture
def betriebsart(portable_root):
    config = Config.load(portable_root)
    monitor = NetworkMonitor([], enabled=False)
    return Betriebsart(config, monitor), monitor, config


# ------------------------------------------------------------- Grundlagen
def test_es_gibt_genau_drei_modi():
    assert {m.value for m in Mode} == {"HYBRID", "OFFLINE", "ONLINE"}


def test_vorgabe_ist_hybrid(betriebsart):
    art, _, _ = betriebsart
    assert art.modus is Mode.HYBRID


def test_nur_offline_verbietet_onlinezugriff():
    assert Mode.OFFLINE.erlaubt_online is False
    assert Mode.HYBRID.erlaubt_online is True
    assert Mode.ONLINE.erlaubt_online is True


# ------------------------------------------------- TEST 1 bis 6 der Vorgabe
def test_1_hybrid_mit_internet(betriebsart):
    """Lokale und Onlinefunktionen verfuegbar."""
    art, monitor, _ = betriebsart
    art.waehlen(Mode.HYBRID)
    monitor.force(True, "Test")
    lage = art.lage()
    assert lage.modus is Mode.HYBRID
    assert lage.internet is True
    assert lage.online_moeglich is True


def test_2_hybrid_ohne_internet_arbeitet_lokal_weiter(betriebsart):
    """Der gewaehlte Modus bleibt - nur online geht eben nicht."""
    art, monitor, _ = betriebsart
    art.waehlen(Mode.HYBRID)
    monitor.force(False, "Test: getrennt")
    lage = art.lage()
    assert lage.modus is Mode.HYBRID, "der Modus springt nicht selbsttaetig um"
    assert lage.internet is False
    assert lage.online_moeglich is False
    assert "lokal weiter" in lage.grund


def test_3_offline_trotz_vorhandenem_internet(betriebsart):
    """Der wichtigste Fall: die Entscheidung schlaegt den Befund."""
    art, monitor, _ = betriebsart
    monitor.force(True, "Test: Verbindung besteht")
    art.waehlen(Mode.OFFLINE)

    lage = art.lage()
    assert lage.modus is Mode.OFFLINE
    assert lage.online_moeglich is False, \
        "trotz Verbindung darf im OFFLINE-Modus nichts abgerufen werden"
    # Es wird nicht einmal geprueft - eine Netzpruefung waere selbst ein
    # Netzzugriff.
    assert "nicht einmal geprueft" in lage.grund


def test_4_wahl_ueberlebt_den_neustart(portable_root):
    """Programm schliessen, neu starten - OFFLINE bleibt OFFLINE."""
    config = Config.load(portable_root)
    monitor = NetworkMonitor([], enabled=False)
    Betriebsart(config, monitor).waehlen(Mode.OFFLINE)

    # Neustart: alles frisch einlesen
    frisch = Config.load(portable_root)
    art = Betriebsart(frisch, NetworkMonitor([], enabled=False))
    assert art.modus is Mode.OFFLINE

    gespeichert = json.loads(
        (portable_root.get("config") / "settings.json").read_text(encoding="utf-8"))
    assert gespeichert["network"]["mode"] == "OFFLINE"


def test_5_online_laesst_lokale_funktionen_unangetastet(portable_root):
    """ONLINE heisst nicht: lokale Funktionen abschalten."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        controller.remember_manual("company.chart_of_accounts", "Kontenrahmen",
                                   "SKR03", "accounting")
        controller.set_mode(Mode.ONLINE)
        assert controller.mode is Mode.ONLINE

        # Lokales Unternehmenswissen und lokale Recherche bleiben verfuegbar
        assert controller.memory.get("company.chart_of_accounts") is not None
        ergebnis = controller.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")
        assert ergebnis.answer.references, "die lokale Recherche muss weiter funktionieren"
    finally:
        controller.shutdown()


def test_6_von_offline_zurueck_nach_hybrid(betriebsart):
    art, monitor, _ = betriebsart
    art.waehlen(Mode.OFFLINE)
    assert art.lage().online_moeglich is False

    monitor.force(True, "Test")
    art.waehlen(Mode.HYBRID)
    assert art.lage().online_moeglich is True


# ------------------------------------------------------------- Sonstiges
def test_moduswechsel_wird_protokolliert(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        vorher = controller.audit.count()
        controller.set_mode(Mode.ONLINE, grund="Test")
        assert controller.audit.count() > vorher

        passend = controller.audit.entries(limit=20, action="betriebsmodus")
        assert passend, "der Moduswechsel muss im Protokoll stehen"
        eintrag = passend[0]
        # Vorher und Nachher gehoeren dazu - sonst ist der Eintrag wertlos
        detail = json.dumps(eintrag, ensure_ascii=False)
        assert "OFFLINE" in detail and "ONLINE" in detail
    finally:
        controller.shutdown()


def test_jeder_modus_hat_eine_verstaendliche_ansage():
    """Beim Wechsel muss der Benutzer erfahren, was jetzt gilt."""
    assert "Offline-Modus aktiv" in Mode.OFFLINE.beschreibung
    assert "keine externen Online-Dienste" in Mode.OFFLINE.beschreibung
    assert "Online-Modus aktiv" in Mode.ONLINE.beschreibung
    assert "Hybrid-Modus aktiv" in Mode.HYBRID.beschreibung
    # ONLINE darf nicht suggerieren, dass lokale Daten wegfallen
    assert "lokal" in Mode.ONLINE.beschreibung.lower()


def test_unbekannter_wert_fuehrt_nie_zum_absturz():
    assert Mode.parse("quatsch") is Mode.HYBRID
    assert Mode.parse(None) is Mode.HYBRID
    assert Mode.parse("") is Mode.HYBRID
    assert Mode.parse("offline") is Mode.OFFLINE
    assert Mode.parse("Online") is Mode.ONLINE


def test_kommandozeile_zeigt_und_wechselt(portable_root, capsys):
    from ui.cli import main

    wurzel = str(portable_root.root)
    assert main(["--root", wurzel, "modus", "OFFLINE"]) == 0
    ausgabe = capsys.readouterr().out
    assert "Offline-Modus aktiv" in ausgabe
    assert "OFFLINE" in ausgabe

    # Eigener Aufruf - die Wahl muss noch stehen
    assert main(["--root", wurzel, "modus"]) == 0
    assert "OFFLINE" in capsys.readouterr().out


def test_modellrouting_folgt_der_betriebsart(portable_root, monkeypatch):
    """E6.12: OFFLINE nur lokal, ONLINE darf ein Online-Modell bevorzugen."""
    from test_controller import make_controller

    from pkc.netstate import Mode

    controller = make_controller(portable_root)
    try:
        controller.bootstrap()
        gesehen: list[bool] = []

        def merken(*args, **kwargs):
            gesehen.append(bool(kwargs.get("prefer_online")))
            from pkc.rag.engine import AnswerResult
            return AnswerResult(text="Antwort")

        monkeypatch.setattr(controller.rag, "answer", merken)

        controller.set_mode(Mode.OFFLINE)
        controller.ask("Wie buche ich eine Rechnung?")
        assert gesehen[-1] is False, "im Offlinebetrieb nie ein Online-Modell"

        controller.network.force(True, "Test: online")
        controller.set_mode(Mode.HYBRID)
        controller.ask("Wie buche ich eine Rechnung?")
        assert gesehen[-1] is False, "HYBRID arbeitet mit dem lokalen Modell"

        controller.set_mode(Mode.ONLINE)
        controller.ask("Wie buche ich eine Rechnung?")
        assert gesehen[-1] is True, "ONLINE darf das Online-Modell bevorzugen"
    finally:
        controller.shutdown()
