"""Wartezeit auf eine Antwort - woraus sie besteht und was sie senkt.

Anlass ist eine deutliche Rueckmeldung aus dem Betrieb: "eine Antwort dauert
immer noch viel zu lange". Zu Recht.

Die Wartezeit entsteht an drei Stellen, und nur eine davon ist das Rechnen:

1. **Modell laden** - mehrere Gigabyte von der Platte. Geschah bisher bei
   der ersten Frage, stand also voll in deren Wartezeit.
2. **Kontext verarbeiten** (Vorlauf) - jedes Token des Prompts muss durch
   das Modell, bevor das erste Wort erscheint. Gemessen wurden 2712 Token.
3. **Antwort erzeugen** - jedes Token einzeln. Erlaubt waren 1024; bei vier
   Token je Sekunde sind das vier Minuten.

Punkt 2 und 3 sind Einstellungen, keine Naturkonstanten. Punkt 1 ist eine
Frage des Zeitpunkts. Alle drei werden hier festgehalten.
"""

from __future__ import annotations

import threading
import time

import pytest

from pkc.llm import tempo
from pkc.llm.base import ChatMessage, LlmResponse
from pkc.llm.manager import LlmManager
from test_controller import make_controller


# -- Das Budget ----------------------------------------------------------

def test_stufen_sind_durchgaengig_geordnet():
    """Schneller heisst: weniger von allem. Sonst waere es keine Stufe."""
    reihe = [tempo.stufe(n) for n in ("schnell", "ausgewogen", "ausfuehrlich")]
    for feld in ("max_output_tokens", "kontext_tokens", "top_k", "verlauf"):
        werte = [s[feld] for s in reihe]
        assert werte == sorted(werte), f"{feld} ist nicht aufsteigend: {werte}"


def test_vorgabe_ist_nicht_die_langsamste_stufe():
    """Eine Antwort, auf die niemand wartet, nuetzt niemandem."""
    assert tempo.VORGABE != "ausfuehrlich"
    assert tempo.stufe(tempo.VORGABE)["max_output_tokens"] < 1024


def test_unbekannte_stufe_faellt_auf_die_vorgabe():
    assert tempo.stufe("gibtsnicht") == tempo.stufe(tempo.VORGABE)
    assert tempo.stufe("")["label"] == tempo.stufe(tempo.VORGABE)["label"]


# -- Was tatsaechlich beim Modell ankommt --------------------------------

def _prompt_messen(paths, stufe: str) -> tuple[int, int]:
    """Baut eine echte Frage und misst, was beim Modell ankaeme."""
    controller = make_controller(paths)
    controller.config.set("llm.tempo", stufe)
    controller.config.set("retrieval.top_k", 0)      # aus der Stufe ableiten
    controller.tempo_anwenden()
    controller.bootstrap(build_embeddings=True)
    gemessen: dict = {}

    class Messend:
        name = "messung"
        model = "x"

        def available(self):
            return True, ""

        def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None,
                     on_token=None):
            gemessen["zeichen"] = sum(len(m.content) for m in messages)
            gemessen["max_tokens"] = max_tokens
            return LlmResponse(text="**ERGEBNIS**\nTest [1].", provider="messung",
                               model="x")

    controller.llm = LlmManager(Messend())
    controller.rag.llm = controller.llm
    try:
        controller.ask("Welche Pflichtangaben braucht eine Rechnung nach dem UStG?")
    finally:
        controller.shutdown()
    return gemessen["zeichen"] // 4, gemessen["max_tokens"]


def test_schnell_schickt_weniger_zum_modell_als_ausfuehrlich(portable_root, tmp_path):
    """Der Vergleich ist der Beleg - nicht die Zusage einer Sekundenzahl."""
    from pkc.paths import Paths

    zweite = Paths(tmp_path)
    (tmp_path / ".portable_root").touch()

    schnell_prompt, schnell_aus = _prompt_messen(portable_root, "schnell")
    lang_prompt, lang_aus = _prompt_messen(zweite, "ausfuehrlich")

    assert schnell_aus < lang_aus, "die Antwortlaenge muss sich unterscheiden"
    assert schnell_prompt < lang_prompt, "der Kontext muss sich unterscheiden"
    # Der Ausgabeteil ist der groesste Posten der Gesamtzeit.
    assert schnell_aus <= lang_aus / 2


def test_antwortlaenge_kommt_aus_dem_tempo(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap(build_embeddings=False)
    try:
        for stufe in tempo.namen():
            controller.config.set("llm.tempo", stufe)
            assert controller.antwortlaenge() == tempo.stufe(stufe)["max_output_tokens"]

        # Ein ausdruecklicher Wert hat Vorrang - sonst waere die Einstellung
        # wirkungslos, sobald jemand eine Stufe waehlt.
        controller.config.set("llm.max_output_tokens", 222)
        assert controller.antwortlaenge() == 222
    finally:
        controller.shutdown()


def test_die_alte_vorgabe_war_der_groesste_posten():
    """1024 Token bei vier Token je Sekunde sind vier Minuten."""
    alt = tempo.geschaetzte_wartezeit(
        {"kontext_tokens": 3200, "max_output_tokens": 1024}, 1257, 60, 4)
    neu = tempo.geschaetzte_wartezeit(tempo.stufe("schnell"), 1257, 60, 4)
    assert neu["gesamt_s"] < alt["gesamt_s"] / 2, (
        f"aus {alt['gesamt_s']} s wurden {neu['gesamt_s']} s - zu wenig")


# -- Der Zeitpunkt: vorladen ---------------------------------------------

class Ladender:
    """Ein Anbieter, der - wie ein echtes Modell - Zeit zum Laden braucht."""

    name = "ladend"
    model = "x"

    def __init__(self, dauer: float = 0.3):
        self.dauer = dauer
        self.geladen = threading.Event()
        self.starts = 0

    def available(self):
        return True, ""

    def vorladen(self):
        self.starts += 1
        time.sleep(self.dauer)
        self.geladen.set()

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None,
                 on_token=None):
        if not self.geladen.is_set():
            self.vorladen()
        return LlmResponse(text="ok", provider="ladend", model="x")


def test_modell_wird_beim_start_im_hintergrund_geladen(portable_root):
    """Sonst steht die volle Ladezeit in der Wartezeit der ersten Frage."""
    controller = make_controller(portable_root)
    anbieter = Ladender(0.3)
    controller.llm = LlmManager(anbieter)
    controller.rag.llm = controller.llm

    begonnen = time.monotonic()
    controller.bootstrap(build_embeddings=False)
    gebraucht = time.monotonic() - begonnen
    try:
        assert anbieter.starts == 1, "der Start muss das Laden anstossen"
        assert gebraucht < 0.3, (
            "das Laden darf den Start nicht aufhalten - es laeuft nebenher")
        anbieter.geladen.wait(timeout=5)
        assert anbieter.geladen.is_set()
    finally:
        controller.shutdown()


def test_vorladen_laesst_sich_abschalten(portable_root):
    controller = make_controller(portable_root)
    anbieter = Ladender(0.05)
    controller.llm = LlmManager(anbieter)
    controller.rag.llm = controller.llm
    controller.config.set("llm.vorladen", False)
    controller.bootstrap(build_embeddings=False)
    try:
        assert anbieter.starts == 0
    finally:
        controller.shutdown()


def test_vorladen_und_erste_frage_starten_nicht_zweimal(tmp_path):
    """Zwei Vorgaenge mit je mehreren Gigabyte waeren nicht hinnehmbar."""
    from pkc.llm.providers import MitgelieferterServerProvider

    class Server:
        def __init__(self):
            self.starts = 0
            self._laeuft = False
            self.programm = tmp_path / "llama-server"
            self.modell = tmp_path / "m.gguf"
            self.programm.write_text("x")
            self.modell.write_text("x")

        @property
        def laeuft(self):
            return self._laeuft

        def starten(self, protokollordner=None):
            self.starts += 1
            time.sleep(0.2)
            self._laeuft = True
            return "http://127.0.0.1:1"

    server = Server()
    anbieter = MitgelieferterServerProvider(server)
    faeden = [threading.Thread(target=anbieter.vorladen) for _ in range(4)]
    for f in faeden:
        f.start()
    for f in faeden:
        f.join(timeout=5)

    assert server.starts == 1, f"der Dienst wurde {server.starts} Mal gestartet"


# -- Die Zeit bis zum ersten Wort ----------------------------------------

def test_zeit_bis_zum_ersten_wort_wird_gemessen():
    """Das ist die Zahl, die der Benutzer als Wartezeit erlebt."""
    antwort = LlmResponse(text="x", provider="p", model="m",
                          elapsed=12.0, erstes_token_s=3.5)
    assert antwort.erstes_token_s == 3.5


def test_probe_meldet_die_zeit_bis_zum_ersten_wort(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap(build_embeddings=False)

    class Stroemend:
        name = "strom"
        model = "x"

        def available(self):
            return True, ""

        def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None,
                     on_token=None):
            assert on_token is not None, (
                "die Probe muss schrittweise laufen, sonst gibt es kein erstes Wort")
            for stueck in ("UStG ", "steht ", "fuer ..."):
                on_token(stueck)
            return LlmResponse(text="UStG steht fuer ...", provider="strom",
                               model="x", elapsed=4.0, erstes_token_s=1.0,
                               completion_tokens=12)

    controller.llm = LlmManager(Stroemend())
    controller.rag.llm = controller.llm
    try:
        probe = controller.modell_probe()
        assert probe["ok"]
        assert probe["erstes_wort_s"] == 1.0
        assert probe["dauer_s"] == 4.0
        # Das Tempo zaehlt ab dem ersten Wort - vorher wird nichts geschrieben.
        assert probe["token_je_sekunde"] == pytest.approx(12 / 3.0, abs=0.2)
    finally:
        controller.shutdown()


# -- Der Modelldienst ----------------------------------------------------

def test_tempoflags_stehen_im_befehl(tmp_path):
    from pkc.llm.server import Llamaserver

    befehl = Llamaserver(programm=tmp_path / "llama-server",
                         modell=tmp_path / "m.gguf", port=1)._befehl()
    assert "-fa" in befehl, "Flash Attention beschleunigt vor allem den Vorlauf"
    assert "--cache-type-k" in befehl, "ein kleinerer Kontextspeicher verhindert Auslagern"
    assert "-tb" in befehl, "die Kontextverarbeitung soll alle Kerne bekommen"


def test_ohne_tempoflags_bleibt_der_befehl_schlicht(tmp_path):
    """Fuer die Fehlersuche muss der einfache Aufruf erreichbar bleiben."""
    from pkc.llm.server import Llamaserver

    befehl = Llamaserver(programm=tmp_path / "llama-server",
                         modell=tmp_path / "m.gguf", port=1,
                         tempoflags=False)._befehl()
    assert "-fa" not in befehl and "--cache-type-k" not in befehl


# -- Die Oberflaeche -----------------------------------------------------

def test_tempo_ist_in_der_oberflaeche_einstellbar(portable_root):
    import sys

    import tk_double

    tk_double.install()
    for modul in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[modul]
    from ui import tk_app

    controller = make_controller(portable_root)
    bericht = controller.bootstrap()
    window = tk_app.MainWindow(controller, bericht)
    try:
        assert "llm.tempo" in window.setting_vars, (
            "der wirksamste Regler fuer die Wartezeit fehlt in den Einstellungen")

        # Und er muss sofort wirken, nicht erst nach einem Neustart.
        window.setting_vars["llm.tempo"].set("schnell")
        window.setting_vars["retrieval.top_k"].set("0")
        window._save_settings()
        assert controller.rag.top_k == tempo.stufe("schnell")["top_k"]
        assert controller.rag.builder.max_context_tokens == \
            tempo.stufe("schnell")["kontext_tokens"]
        assert controller.antwortlaenge() == tempo.stufe("schnell")["max_output_tokens"]

        window.setting_vars["llm.tempo"].set("ausfuehrlich")
        window._save_settings()
        assert controller.rag.builder.max_context_tokens == \
            tempo.stufe("ausfuehrlich")["kontext_tokens"]
    finally:
        controller.shutdown()


# -- Die Fassung des Modelldienstes --------------------------------------

def _dienst(ordner, fassung: str):
    ziel = ordner / "llama" / fassung
    ziel.mkdir(parents=True, exist_ok=True)
    import os
    datei = ziel / ("llama-server.exe" if os.name == "nt" else "llama-server")
    datei.write_text("x")
    return datei


def test_mit_grafikkarte_wird_die_vulkan_fassung_gewaehlt(tmp_path):
    """Der groesste Einzelhebel fuer die Wartezeit."""
    from pkc.llm.server import waehle_server

    _dienst(tmp_path, "cpu")
    _dienst(tmp_path, "vulkan")

    programm, fassung = waehle_server(tmp_path, grafikkarte=True)
    assert fassung == "vulkan" and programm.parent.name == "vulkan"

    programm, fassung = waehle_server(tmp_path, grafikkarte=False)
    assert fassung == "cpu", "ohne Karte waere die Grafikfassung sinnlos"


def test_ohne_vulkan_fassung_bleibt_es_bei_der_cpu(tmp_path):
    from pkc.llm.server import waehle_server

    _dienst(tmp_path, "cpu")
    programm, fassung = waehle_server(tmp_path, grafikkarte=True)
    assert fassung == "cpu" and programm is not None


def test_aeltere_ablage_ohne_unterordner_wird_noch_gefunden(tmp_path):
    """Ein Paket aus der Zeit vor den zwei Fassungen darf nicht ausfallen."""
    import os

    ordner = tmp_path / "llama"
    ordner.mkdir(parents=True)
    (ordner / ("llama-server.exe" if os.name == "nt" else "llama-server")).write_text("x")

    from pkc.llm.server import finde_server, waehle_server

    assert finde_server(tmp_path) is not None
    assert waehle_server(tmp_path, grafikkarte=True)[1] == "cpu"


def test_scheiternde_grafikfassung_faellt_auf_die_cpu_zurueck(tmp_path):
    """Fehlt der Treiber, muss die CPU-Fassung uebernehmen - nicht nichts."""
    import sys

    from pkc.llm.server import Llamaserver

    modell = tmp_path / "m.gguf"
    modell.write_text("x")
    kaputt = tmp_path / "kaputt.py"
    kaputt.write_text("import sys; sys.exit(1)\n")
    gut = tmp_path / "gut.py"
    gut.write_text(
        "import http.server, sys\n"
        "port = int(sys.argv[sys.argv.index('--port') + 1])\n"
        "class H(http.server.BaseHTTPRequestHandler):\n"
        "    def do_GET(self):\n"
        "        self.send_response(200); self.end_headers(); self.wfile.write(b'{}')\n"
        "    def log_message(self, *a): pass\n"
        "http.server.HTTPServer(('127.0.0.1', port), H).serve_forever()\n")

    server = Llamaserver(programm=kaputt, modell=modell, rueckfall=gut,
                         vorlauf=[sys.executable], startgrenze=10.0)
    try:
        adresse = server.starten()
        assert adresse.startswith("http://127.0.0.1:")
        assert server.benutzt == gut, "es muss die Rueckfalldatei laufen"
    finally:
        server.beenden()


# -- Der Befehl fuer die Messung -----------------------------------------

def test_einstellungen_setzen_speichert_als_zahl(portable_root, capsys):
    """Als Text faellt die Einstellung beim naechsten Start still zurueck."""
    from pkc.config import Config
    from ui.cli import main

    wurzel = str(portable_root.root)
    assert main(["--root", wurzel, "--offline", "einstellungen", "setzen",
                 "--schluessel", "llm.gpu_layers", "--wert", "35"]) == 0
    capsys.readouterr()
    assert Config.load(portable_root).get("llm.gpu_layers") == 35

    assert main(["--root", wurzel, "--offline", "einstellungen", "setzen",
                 "--schluessel", "llm.vorladen", "--wert", "false"]) == 0
    capsys.readouterr()
    assert Config.load(portable_root).get("llm.vorladen") is False


def test_einstellungen_setzen_wirkt_sofort(portable_root, capsys):
    """Der Bauablauf misst je Stufe - ohne Sofortwirkung waere das sinnlos."""
    from ui.cli import main

    assert main(["--root", str(portable_root.root), "--offline", "einstellungen",
                 "setzen", "--schluessel", "llm.tempo", "--wert", "schnell"]) == 0
    text = capsys.readouterr().out
    assert "vorher" in text and "jetzt" in text and "schnell" in text


def test_einstellungen_zeigen_nennt_die_tempowerte(portable_root, capsys):
    from ui.cli import main

    assert main(["--root", str(portable_root.root), "--offline",
                 "einstellungen", "zeigen"]) == 0
    text = capsys.readouterr().out
    assert "llm.tempo" in text and "llm.gpu_layers" in text


def test_probe_gibt_die_wartezeit_getrennt_aus(portable_root, capsys, monkeypatch):
    """Zwei Zahlen: bis zum ersten Wort - und wie schnell es danach laeuft."""
    from ui import cli

    monkeypatch.setattr(
        "app.controller.AppController.modell_probe",
        lambda self, *a, **k: {"ok": True, "anbieter": "x", "modell": "m",
                               "dauer_s": 9.0, "erstes_wort_s": 2.5,
                               "token": 60, "token_je_sekunde": 9.2, "text": "..."})

    class Args:
        root = str(portable_root.root)
        offline = True
        quiet = True
        kunde_bereich = ""
        aktion = "pruefen"

    assert cli.cmd_modell(Args()) == 0
    text = capsys.readouterr().out
    assert "erstes Wort" in text and "2.5" in text
    assert "9.2 Token je Sekunde" in text
