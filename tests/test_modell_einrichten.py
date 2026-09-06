"""Der gefuehrte Weg zum Sprachmodell - und die Anwendung mit Modell.

Abschnitt 13 der Erweiterung E6 ist deutlich: "kein Sprachmodell verfuegbar"
ist kein annehmbarer Endzustand. Hier wird geprueft, dass der Weg dorthin in
der Anwendung selbst liegt, dass er niemand ueberfaehrt - und dass die
Anwendung mit einem laufenden Modelldienst tatsaechlich eine formulierte
Antwort mit Quellen liefert.

Das Modell ist dabei ein Stellvertreter (siehe ``test_modelldienst.py``):
ein Programm, das dasselbe Protokoll spricht. Damit ist die **Kette**
geprueft, nicht die fachliche Qualitaet eines echten Modells. Die haengt vom
Modell ab und wird im Windows-Bauablauf mit einem echten GGUF-Modell
nachgewiesen.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.controller import AppController
from pkc.config import Config
from pkc.llm import katalog as katalogmodul
from pkc.netstate import NetworkMonitor
from test_modelldienst import _modell, _programm


def _anwendung(paths, online: bool = True) -> AppController:
    """Eine Anwendung mit der **echten** Modellanbindung.

    Bewusst nicht ``make_controller``: das setzt einen Testanbieter ein und
    haette damit genau das ersetzt, was hier geprueft werden soll.
    """
    config = Config.load(paths)
    config.set("retrieval.embedding_dim", 256)
    config.set("network.mode", "HYBRID" if online else "OFFLINE")
    monitor = NetworkMonitor([], enabled=False)
    monitor.force(online, "Test")
    return AppController(paths, config, monitor, console_logging=False)

KATALOG = {
    "stand": "2026-01-01",
    "modelle": [
        {
            "id": "probe-klein", "profil": "probe", "name": "Probemodell (klein)",
            "lizenz": "Apache-2.0", "herkunft": "Testkatalog",
            "url": "https://beispiel.invalid/probe.gguf", "datei": "probe.gguf",
            "groesse_gb": 0.4, "min_ram_gb": 2, "produktiv": False,
            "hinweis": "nur zum Ausprobieren", "pruefung": {},
        },
        {
            "id": "gross-geprueft", "profil": "standard", "name": "Standardmodell",
            "lizenz": "Apache-2.0", "herkunft": "Testkatalog",
            "url": "https://beispiel.invalid/gross.gguf", "datei": "gross.gguf",
            "groesse_gb": 4.7, "min_ram_gb": 12, "produktiv": True,
            "pruefung": {"erreichbar": True, "geprueft_am": "2026-09-06",
                         "sha256": "a" * 64},
        },
    ],
}


@pytest.fixture
def anwendung(portable_root):
    """Eine Anwendung mit hinterlegtem Katalog."""
    (portable_root.get("config")).mkdir(parents=True, exist_ok=True)
    (portable_root.get("config") / "model_catalog.json").write_text(
        json.dumps(KATALOG), encoding="utf-8")
    controller = _anwendung(portable_root)
    controller.bootstrap(build_embeddings=False)
    try:
        yield controller
    finally:
        controller.shutdown()


# -- Der Katalog ---------------------------------------------------------

def test_katalog_kennzeichnet_ungepruefte_quellen(anwendung):
    katalog = anwendung.modell_katalog()
    klein = katalog.nach_id("probe-klein")
    gross = katalog.nach_id("gross-geprueft")

    assert not klein.geprueft, "ohne Pruefung darf nichts als geprueft gelten"
    assert klein.pruefstand == "nicht geprueft"
    assert klein.sha256 == "", "eine Pruefsumme entsteht nur beim Pruefen"

    assert gross.geprueft
    assert "2026-09-06" in gross.pruefstand and "Pruefsumme" in gross.pruefstand


def test_katalog_findet_ueber_kennung_und_profil(anwendung):
    katalog = anwendung.modell_katalog()
    assert katalog.waehlen("probe-klein").id == "probe-klein"
    assert katalog.waehlen("standard").id == "gross-geprueft"
    assert katalog.waehlen("gibtsnicht") is None
    assert [q.id for q in katalog.produktiv] == ["gross-geprueft"]


def test_fehlender_katalog_ist_kein_absturz(tmp_path):
    katalog = katalogmodul.laden(tmp_path)
    assert len(katalog) == 0 and "fehlt" in katalog.fehler


def test_pruefergebnis_wird_eingetragen(tmp_path):
    """Der Bauablauf traegt ein, was er tatsaechlich abgerufen hat."""
    (tmp_path / "model_catalog.json").write_text(json.dumps(KATALOG), encoding="utf-8")
    assert katalogmodul.pruefung_eintragen(
        tmp_path, "probe-klein",
        {"erreichbar": True, "geprueft_am": "2026-09-07", "sha256": "b" * 64},
    )
    assert katalogmodul.laden(tmp_path).nach_id("probe-klein").geprueft
    assert not katalogmodul.pruefung_eintragen(tmp_path, "gibtsnicht", {})


# -- Die Lage ------------------------------------------------------------

def test_lage_benennt_was_fehlt(anwendung):
    lage = anwendung.modell_lage()
    assert lage["fehlt"] == ["die Modelldatei", "der Modelldienst (runtime/llama)"]
    assert lage["bereit"] is False, "ohne Modell ist nichts bereit"
    assert lage["empfehlung"], "es muss ein Vorschlag dastehen"
    assert lage["hardware"]["arbeitsspeicher_gb"]


def test_lage_erkennt_dienst_und_modell(anwendung, portable_root):
    _programm(portable_root.get("runtime") / "llama")
    _modell(portable_root.get("models"), "probe.gguf")
    anwendung.modell_neu_laden()

    lage = anwendung.modell_lage()
    assert lage["fehlt"] == []
    assert lage["bereit"] is True
    assert lage["dienst_vorhanden"] and "llama-server" in lage["dienst"]


# -- Der Bezug -----------------------------------------------------------

def test_offline_wird_nichts_geladen(anwendung, monkeypatch):
    from pkc.netstate import Mode

    monkeypatch.setattr("pkc.llm.bezug.laden", _darf_nicht)
    anwendung.set_mode(Mode.OFFLINE)
    with pytest.raises(ValueError) as fehler:
        anwendung.modell_beziehen("probe-klein", bestaetigt=True)
    assert "OFFLINE" in str(fehler.value)


def test_ohne_bestaetigung_wird_nichts_geladen(anwendung, monkeypatch):
    monkeypatch.setattr("pkc.llm.bezug.laden", _darf_nicht)
    anwendung.network.force(True, "Test: online")
    with pytest.raises(ValueError) as fehler:
        anwendung.modell_beziehen("probe-klein")
    text = str(fehler.value)
    assert "bestaetigen" in text.lower()
    assert "0.4" in text and "Apache-2.0" in text, "Groesse und Lizenz muessen dastehen"
    assert "nicht geprueft" in text, "der Pruefstand der Quelle gehoert dazu"


def test_unbekannte_auswahl_nennt_die_moeglichkeiten(anwendung):
    anwendung.network.force(True, "Test: online")
    with pytest.raises(ValueError) as fehler:
        anwendung.modell_beziehen("gibtsnicht", bestaetigt=True)
    assert "probe-klein" in str(fehler.value)


def test_zu_wenig_platz_wird_vorher_gemeldet(anwendung, monkeypatch):
    import collections
    import shutil as _shutil

    Platte = collections.namedtuple("Platte", "total used free")
    monkeypatch.setattr(_shutil, "disk_usage", lambda p: Platte(1, 1, 1024**3))
    monkeypatch.setattr("pkc.llm.bezug.laden", _darf_nicht)
    anwendung.network.force(True, "Test: online")

    with pytest.raises(ValueError) as fehler:
        anwendung.modell_beziehen("gross-geprueft", bestaetigt=True)
    assert "frei" in str(fehler.value)


def test_hinterlegte_pruefsumme_wird_weitergereicht(anwendung, monkeypatch):
    """Ist eine Pruefsumme geprueft, muss sie beim Laden auch angewandt werden."""
    gesehen = {}

    def merken(url, ziel, pruefsumme="", name="", ueberschreiben=False, fortschritt=None):
        from pkc.llm.bezug import Ladeergebnis

        gesehen.update(url=url, pruefsumme=pruefsumme, name=name)
        return Ladeergebnis(ok=True, pfad=Path(ziel) / name, pruefsumme="b" * 64,
                            meldung="geladen")

    monkeypatch.setattr("pkc.llm.bezug.laden", merken)
    anwendung.network.force(True, "Test: online")
    ergebnis = anwendung.modell_beziehen("gross-geprueft", bestaetigt=True)

    assert gesehen["pruefsumme"] == "a" * 64, "die gepruefte Pruefsumme muss mit"
    assert gesehen["name"] == "gross.gguf"
    assert ergebnis["ok"] and ergebnis["pruefsumme_vergleichbar"]


def test_ohne_pruefsumme_wird_das_gesagt(anwendung, monkeypatch):
    def ohne(url, ziel, pruefsumme="", name="", ueberschreiben=False, fortschritt=None):
        from pkc.llm.bezug import Ladeergebnis

        assert pruefsumme == "", "fuer eine ungepruefte Quelle gibt es keine Pruefsumme"
        return Ladeergebnis(ok=True, pfad=Path(ziel) / name, pruefsumme="c" * 64,
                            meldung="geladen")

    monkeypatch.setattr("pkc.llm.bezug.laden", ohne)
    anwendung.network.force(True, "Test: online")
    ergebnis = anwendung.modell_beziehen("probe-klein", bestaetigt=True)
    assert ergebnis["ok"] and not ergebnis["pruefsumme_vergleichbar"]


def test_bezug_wird_protokolliert(anwendung, monkeypatch):
    def geht(url, ziel, pruefsumme="", name="", ueberschreiben=False, fortschritt=None):
        from pkc.llm.bezug import Ladeergebnis

        return Ladeergebnis(ok=True, pfad=Path(ziel) / name, pruefsumme="d" * 64,
                            meldung="geladen")

    monkeypatch.setattr("pkc.llm.bezug.laden", geht)
    anwendung.network.force(True, "Test: online")
    anwendung.modell_beziehen("probe-klein", bestaetigt=True)

    eintraege = [z["action"] for z in anwendung.company_db.query(
        "SELECT action FROM audit_log ORDER BY id DESC LIMIT 50")]
    assert "modell_bezug" in eintraege and "modell_bezug_ende" in eintraege


# -- Die Probe und der Betrieb mit Modell --------------------------------

def test_probe_ohne_modell_ist_ehrlich(anwendung):
    ergebnis = anwendung.modell_probe()
    assert ergebnis["ok"] is False
    assert ergebnis["grund"]


def test_probe_mit_dienst_meldet_die_antwort(anwendung, portable_root):
    _programm(portable_root.get("runtime") / "llama")
    _modell(portable_root.get("models"), "probe.gguf")
    anwendung.modell_neu_laden()

    ergebnis = anwendung.modell_probe()
    assert ergebnis["ok"], ergebnis.get("grund")
    assert ergebnis["text"], "es muss ein Text zurueckkommen"
    assert ergebnis["dauer_s"] >= 0


def test_anwendung_antwortet_mit_modell_und_quellen(anwendung, portable_root):
    """Der eigentliche Punkt: eine Fachfrage, beantwortet mit Modell.

    Ohne Modell stand hier bisher "Es konnte keine KI-Antwort erzeugt
    werden". Mit laufendem Dienst muss eine formulierte Antwort samt
    Quellenteil und Wissensstand herauskommen.
    """
    _programm(portable_root.get("runtime") / "llama")
    _modell(portable_root.get("models"), "probe.gguf")
    anwendung.modell_neu_laden()

    ergebnis = anwendung.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")
    text = ergebnis.answer.text

    assert "Es konnte keine KI-Antwort erzeugt werden" not in text
    assert ergebnis.answer.model_answered, "die Antwort muss vom Modell stammen"
    assert "QUELLEN" in text and "WISSENSSTAND" in text
    assert "kein Sprachmodell verfuegbar" not in text
    assert ergebnis.answer.references, "die Recherche muss trotzdem laufen"


def test_der_dienst_wird_beim_beenden_heruntergefahren(portable_root):
    """Ein weiterlaufender Modelldienst haelt still den Speicher belegt."""
    (portable_root.get("config")).mkdir(parents=True, exist_ok=True)
    (portable_root.get("config") / "model_catalog.json").write_text(
        json.dumps(KATALOG), encoding="utf-8")
    _programm(portable_root.get("runtime") / "llama")
    _modell(portable_root.get("models"), "probe.gguf")

    controller = _anwendung(portable_root)
    controller.bootstrap(build_embeddings=False)
    controller.modell_probe()
    server = controller.llm.primary.server
    assert server.laeuft

    controller.shutdown()
    assert not server.laeuft, "beim Beenden muss der Dienst mit heruntergefahren werden"


def _darf_nicht(*args, **kwargs):
    raise AssertionError("Hier darf nichts geladen werden.")
