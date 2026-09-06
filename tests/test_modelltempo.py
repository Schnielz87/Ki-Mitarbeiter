"""Warum eine Antwort lange dauert - und was die Anwendung dazu sagen muss.

Anlass ist eine Rueckmeldung aus dem Betrieb: 200 Sekunden fuer eine
Antwort, 0,3 Token je Sekunde. Die Ursache stand im selben Fenster, wurde
aber nirgends benannt: auf einem Rechner, dem die Anwendung selbst das
Profil STANDARD empfiehlt, war das HIGH-Modell eingerichtet worden - 9 GB
Gewichte auf einem Rechner mit weniger Arbeitsspeicher. Dann laedt der
Rechner staendig von der Festplatte nach, und jedes Token wartet darauf.

Die Anwendung hat dazu geschwiegen, und zwar dreimal:

* Sie hat das Modell ohne ein Wort geladen, obwohl es nicht passt.
* Sie hat danach "standard" in der Auswahl angezeigt, obwohl das
  14B-Modell lief - die Anzeige widersprach der Zeile darueber.
* Sie hat "0.3 Token je Sekunde" gemeldet, ohne zu sagen, ob das normal
  ist oder was daran zu aendern waere.

Alle drei Punkte werden hier festgehalten.
"""

from __future__ import annotations

import sys

import pytest

import tk_double
from pkc.hardware import GRUNDBEDARF_GB, modelleignung, tempoeinschaetzung
from pkc.llm.manager import LlmManager
from pkc.llm.providers import RetrievalOnlyProvider
from test_controller import make_controller


# -- Passt das Modell auf den Rechner? -----------------------------------

def test_grosses_modell_auf_kleinem_rechner_ist_zu_gross():
    """Genau der Fall aus dem Betrieb: 8,99 GB Datei (ab 24 GB) auf 16 GB."""
    urteil = modelleignung(24, 16, 8.99)
    assert urteil["stufe"] == "zu_gross"
    assert "16" in urteil["text"]
    assert "ausgelagert" in urteil["text"], "der Grund muss dastehen, nicht nur das Urteil"


def test_passendes_modell_wird_nicht_schlechtgeredet():
    assert modelleignung(12, 16, 4.68)["stufe"] == "gut"
    assert modelleignung(24, 32, 8.99)["stufe"] == "gut"


def test_knapp_ist_eine_eigene_stufe():
    """Zwischen "laeuft" und "laeuft nicht" liegt "laeuft, aber langsam".

    Massgeblich ist die Modelldatei, nicht die Empfehlung des Anbieters:
    das 14B-Modell ist 8,99 GB gross und laeuft auf 20 GB durchaus - nur
    eben langsamer als auf den empfohlenen 24 GB.
    """
    urteil = modelleignung(24, 20, 8.99)
    assert urteil["stufe"] == "knapp"
    assert "langsamer" in urteil["text"]


def test_der_grundbedarf_des_betriebssystems_wird_mitgerechnet():
    """Der Arbeitsspeicher steht nicht ganz dem Modell zur Verfuegung."""
    assert GRUNDBEDARF_GB >= 4.0
    # 8 GB Rechner, 4,68 GB Modell: rechnerisch passt die Datei bequem -
    # nur bleibt neben Windows nichts mehr uebrig.
    assert modelleignung(12, 8, 4.68)["stufe"] == "zu_gross"


def test_unbekannter_arbeitsspeicher_wird_nicht_geraten():
    assert modelleignung(24, None, 8.99)["stufe"] == "unbekannt"


# -- Was heisst die gemessene Zahl? --------------------------------------

def test_gemessenes_tempo_wird_eingeordnet():
    langsam = tempoeinschaetzung(0.3)
    assert langsam["stufe"] == "sehr langsam"
    assert "Arbeitsspeicher" in langsam["text"], (
        "die haeufigste Ursache gehoert in die Auskunft")
    assert tempoeinschaetzung(6.0)["stufe"] == "zuegig"
    assert tempoeinschaetzung(2.5)["stufe"] == "brauchbar"
    assert tempoeinschaetzung(1.2)["stufe"] == "langsam"


# -- Die Registerkarte ---------------------------------------------------

@pytest.fixture
def fenster(portable_root):
    dialoge = tk_double.install()
    for modul in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[modul]
    from ui import tk_app

    controller = make_controller(portable_root)
    controller.config.set("llm.provider", "local")
    controller.llm = LlmManager(RetrievalOnlyProvider("kein Modell"))
    controller.rag.llm = controller.llm
    bericht = controller.bootstrap()
    window = tk_app.MainWindow(controller, bericht)
    try:
        yield window, controller, dialoge
    finally:
        controller.shutdown()


def _mit_speicher(window, gb: float) -> None:
    """Tut so, als haette der Rechner so viel Arbeitsspeicher."""
    echte_lage = window.controller.modell_lage

    def lage():
        daten = echte_lage()
        daten["hardware"]["arbeitsspeicher_gb"] = gb
        return daten

    window.controller.modell_lage = lage
    window._refresh_modell()


def test_auswahl_kennzeichnet_zu_grosse_modelle(fenster):
    """Wer waehlt, muss sehen, was er waehlt - vor dem Klick.

    16 GB Arbeitsspeicher ist genau der Fall aus dem Betrieb.
    """
    window, _, _ = fenster
    _mit_speicher(window, 16.0)
    eintraege = window.modell_auswahl.options["values"]

    zu_gross = [e for e in eintraege if "ZU GROSS" in e]
    assert zu_gross, "auf einem 16-GB-Rechner passt das 14B-Modell nicht"
    assert all("high" in e for e in zu_gross), (
        "nur das grosse Modell darf so gekennzeichnet sein")
    assert any(e.startswith("standard") and "ZU GROSS" not in e for e in eintraege)


def test_rueckfrage_warnt_vor_einem_zu_grossen_modell(fenster, monkeypatch):
    """Die Warnung gehoert vor den Download, nicht in den Testbericht."""
    window, controller, dialoge = fenster
    _mit_speicher(window, 16.0)
    window.modell_wahl.set(next(e for e in window.modell_auswahl.options["values"]
                                if e.startswith("high")))
    monkeypatch.setattr(controller, "modell_beziehen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("nein")))
    dialoge.answers = [False]
    window._modell_einrichten()

    frage = next(m[2] for m in dialoge.messages if m[0] == "frage")
    assert "Zu gross fuer diesen Rechner" in frage
    assert "kleineres Modell" in frage, "es muss auch dastehen, was zu tun waere"


def test_auswahl_zeigt_nach_dem_einrichten_das_installierte_modell(fenster, monkeypatch):
    """Sonst steht "standard" da, waehrend das 14B-Modell laeuft.

    Genau das war im Betrieb zu sehen: die Zeile "Einsatzbereit" nannte
    qwen2.5-14b, die Auswahlliste darunter "standard Qwen2.5-7B".
    """
    window, controller, _ = fenster
    lage = controller.modell_lage()
    hoch = next(q for q in lage["katalog"] if q["profil"] == "high")

    echte_lage = controller.modell_lage

    def mit_modell():
        daten = echte_lage()
        daten["modelle"] = [{"name": hoch["datei"], "groesse_gb": 9.0, "pfad": "x"}]
        return daten

    controller.modell_lage = mit_modell
    window.modell_wahl.set("")            # wie nach einem Neustart
    window._refresh_modell()

    assert window.modell_wahl.get().startswith("high"), (
        "die Auswahl muss zeigen, was tatsaechlich installiert ist")


def test_eine_getroffene_wahl_wird_nicht_ueberschrieben(fenster):
    """Ein Klick des Benutzers darf nicht bei der naechsten Aktualisierung verschwinden."""
    window, _, _ = fenster
    gewaehlt = next(e for e in window.modell_auswahl.options["values"]
                    if e.startswith("light"))
    window.modell_wahl.set(gewaehlt)
    window._refresh_modell()
    assert window.modell_wahl.get() == gewaehlt


def test_langsames_ergebnis_wird_erklaert(fenster, monkeypatch):
    window, controller, dialoge = fenster
    _mit_speicher(window, 16.0)
    window.modell_wahl.set(next(e for e in window.modell_auswahl.options["values"]
                                if e.startswith("high")))
    monkeypatch.setattr(controller, "modell_beziehen", lambda *a, **k: {
        "ok": True, "meldung": "geladen", "quelle": {"name": "Testmodell"},
        "pfad": "x.gguf", "bytes": 1, "teile": 1})
    monkeypatch.setattr(controller, "modell_neu_laden", lambda: None)
    monkeypatch.setattr(controller, "modell_probe", lambda *a, **k: {
        "ok": True, "dauer_s": 200.6, "token_je_sekunde": 0.3, "text": "..."})
    dialoge.answers = [True]
    window._modell_einrichten()

    protokoll = window.modell_log.buffer
    assert "sehr langsam" in protokoll
    assert "Was hilft" in protokoll
    assert "kleineres Modell" in protokoll
    assert "Grafikkarte" in protokoll, "der zweite Hebel gehoert genannt"


def test_zuegiges_ergebnis_bekommt_keine_ratschlaege(fenster, monkeypatch):
    """Wer keine Probleme hat, braucht keine Liste mit Abhilfen."""
    window, controller, dialoge = fenster
    monkeypatch.setattr(controller, "modell_beziehen", lambda *a, **k: {
        "ok": True, "meldung": "geladen", "quelle": {"name": "Testmodell"},
        "pfad": "x.gguf", "bytes": 1, "teile": 1})
    monkeypatch.setattr(controller, "modell_neu_laden", lambda: None)
    monkeypatch.setattr(controller, "modell_probe", lambda *a, **k: {
        "ok": True, "dauer_s": 2.0, "token_je_sekunde": 8.0, "text": "..."})
    dialoge.answers = [True]
    window._modell_einrichten()

    assert "zuegig" in window.modell_log.buffer
    assert "Was hilft" not in window.modell_log.buffer


# -- Die Einstellungen ---------------------------------------------------

def test_geschwindigkeitseinstellungen_gibt_es(fenster):
    """Der Hinweistext nennt sie - dann muss es sie auch geben."""
    window, _, _ = fenster
    for schluessel in ("llm.gpu_layers", "llm.threads", "llm.context_tokens"):
        assert schluessel in window.setting_vars, f"{schluessel} fehlt in den Einstellungen"


def test_werte_werden_als_zahl_gespeichert(fenster):
    """Als Text faellt die Einstellung beim naechsten Start still zurueck."""
    window, controller, _ = fenster
    window.setting_vars["llm.gpu_layers"].set("35")
    window.setting_vars["llm.context_tokens"].set("4096")
    window._save_settings()

    assert controller.config.get("llm.gpu_layers") == 35
    assert controller.config.get("llm.context_tokens") == 4096


def test_geaenderte_werte_wirken_sofort(fenster, monkeypatch):
    """Sonst tut die Einstellung bis zum Neustart nichts - ohne ein Wort."""
    window, controller, _ = fenster
    neu_geladen = []
    monkeypatch.setattr(controller, "modell_neu_laden",
                        lambda: neu_geladen.append(True))

    window.setting_vars["llm.gpu_layers"].set("20")
    window._save_settings()
    assert neu_geladen, "die Modellanbindung muss neu aufgebaut werden"

    neu_geladen.clear()
    window._save_settings()
    assert not neu_geladen, "ohne Aenderung darf nichts neu aufgebaut werden"


def test_gpu_schichten_erreichen_den_modelldienst(portable_root, tmp_path):
    """Die Einstellung muss bis in den Aufruf des Dienstes durchschlagen."""
    from pkc.llm.server import Llamaserver

    server = Llamaserver(programm=tmp_path / "llama-server",
                         modell=tmp_path / "m.gguf", gpu_layers=35, threads=8,
                         kontext=4096, port=1)
    befehl = server._befehl()
    assert "-ngl" in befehl and befehl[befehl.index("-ngl") + 1] == "35"
    assert "-t" in befehl and befehl[befehl.index("-t") + 1] == "8"
    assert befehl[befehl.index("-c") + 1] == "4096"


def test_ohne_gpu_wird_kein_schalter_gesetzt(tmp_path):
    """0 heisst "nur CPU" - dann darf der Schalter gar nicht auftauchen."""
    from pkc.llm.server import Llamaserver

    befehl = Llamaserver(programm=tmp_path / "llama-server",
                         modell=tmp_path / "m.gguf", port=1)._befehl()
    assert "-ngl" not in befehl and "-t" not in befehl
