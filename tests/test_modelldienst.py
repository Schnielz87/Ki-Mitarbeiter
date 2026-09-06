"""Der mitgelieferte Modelldienst: starten, antworten, beenden.

Warum das wichtig ist: fuer ``llama-cpp-python`` gibt es keine fertigen
Pakete. Ein Kunde muesste uebersetzen - fuer eine portable Anwendung
undenkbar. Deshalb liegt der fertige ``llama-server`` aus llama.cpp im
Ordner ``runtime`` und wird von der Anwendung selbst gestartet.

Geprueft wird hier gegen einen **Stellvertreter**: ein kleines Programm, das
dasselbe HTTP-Protokoll spricht wie llama.cpp. Damit laesst sich alles
pruefen, was schiefgehen kann - Programmstart, Warten auf die Bereitschaft,
Anfrage, Abbruch, Beenden - ohne ein mehrere Gigabyte grosses Modell.

Was hier NICHT geprueft wird: das echte llama.cpp mit einem echten Modell.
Das laeuft im Windows-Bauablauf (Schritt "Sprachmodell") gegen die
tatsaechliche Programmdatei und ein echtes GGUF-Modell.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from pkc.llm.base import ChatMessage, LlmError
from pkc.llm.manager import LlmManager
from pkc.llm.providers import MitgelieferterServerProvider
from pkc.llm.server import Llamaserver, beschreibung, finde_server

#: Ein Stellvertreter fuer llama-server: dieselben Endpunkte, ohne Modell.
STELLVERTRETER = '''import json, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer

verzoegerung = float("{verzoegerung}")
port = 0
for i, wert in enumerate(sys.argv):
    if wert == "--port":
        port = int(sys.argv[i + 1])

class Griff(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/health"):
            self._antwort({{"status": "ok"}})
            return
        if self.path.startswith("/v1/models"):
            self._antwort({{"data": [{{"id": "stellvertreter"}}]}})
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        laenge = int(self.headers.get("Content-Length", 0))
        anfrage = json.loads(self.rfile.read(laenge) or b"{{}}")
        frage = anfrage["messages"][-1]["content"]
        text = "Antwort des Stellvertreters auf: " + frage[:40]
        if anfrage.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for stueck in text.split(" "):
                brocken = json.dumps({{"choices": [{{"delta": {{"content": stueck + " "}}}}]}})
                self.wfile.write(("data: " + brocken + "\\n\\n").encode())
                self.wfile.flush()
            ende = json.dumps({{"choices": [{{"delta": {{}}, "finish_reason": "stop"}}]}})
            self.wfile.write(("data: " + ende + "\\n\\ndata: [DONE]\\n\\n").encode())
            return
        self._antwort({{
            "model": "stellvertreter",
            "choices": [{{"message": {{"role": "assistant", "content": text}},
                        "finish_reason": "stop"}}],
            "usage": {{"prompt_tokens": 5, "completion_tokens": 7}},
        }})

    def _antwort(self, nutzlast):
        roh = json.dumps(nutzlast).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)

time.sleep(verzoegerung)
HTTPServer(("127.0.0.1", port), Griff).serve_forever()
'''

VERSAGER = '''import sys
sys.stderr.write("error: konnte das Modell nicht laden\\n")
sys.exit(1)
'''


#: Der Stellvertreter wird ueber den Python-Interpreter gestartet. Direkt
#: ausfuehrbar waere er nur unter Linux; Windows lehnt eine Textdatei mit der
#: Endung .exe ab (WinError 216). So laeuft derselbe Test auf beiden Systemen.
VORLAUF = [sys.executable]


def _programm(ordner: Path, vorlage: str = STELLVERTRETER, verzoegerung: float = 0.0) -> Path:
    """Legt eine Programmdatei mit dem Namen von llama-server an."""
    ordner.mkdir(parents=True, exist_ok=True)
    name = "llama-server.exe" if os.name == "nt" else "llama-server"
    ziel = ordner / name
    ziel.write_text(vorlage.format(verzoegerung=verzoegerung), encoding="utf-8")
    if os.name != "nt":
        ziel.chmod(0o755)
    return ziel


def _modell(ordner: Path, name: str = "probe.gguf") -> Path:
    ordner.mkdir(parents=True, exist_ok=True)
    ziel = ordner / name
    ziel.write_bytes(b"GGUF" + b"\0" * 4096)
    return ziel


@pytest.fixture
def dienst(tmp_path):
    """Ein startbereiter Dienst mit Stellvertreter und Modelldatei."""
    programm = _programm(tmp_path / "runtime" / "llama")
    modell = _modell(tmp_path / "models")
    server = Llamaserver(programm=programm, modell=modell, vorlauf=VORLAUF)
    try:
        yield server
    finally:
        server.beenden()


# -- Die Programmdatei finden -------------------------------------------

def test_programm_wird_im_laufzeitordner_gefunden(tmp_path):
    programm = _programm(tmp_path / "runtime" / "llama")
    assert finde_server(tmp_path / "runtime") == programm


def test_programm_wird_auch_ohne_unterordner_gefunden(tmp_path):
    programm = _programm(tmp_path / "runtime")
    assert finde_server(tmp_path / "runtime") == programm


def test_programm_wird_auch_in_einem_versionsordner_gefunden(tmp_path):
    programm = _programm(tmp_path / "runtime" / "llama-b1234-win-cpu")
    assert finde_server(tmp_path / "runtime") == programm


def test_ohne_programm_kein_treffer(tmp_path):
    (tmp_path / "runtime").mkdir()
    assert finde_server(tmp_path / "runtime") is None
    assert beschreibung(None) == "nicht vorhanden"


# -- Starten und Beenden ------------------------------------------------

def test_dienst_startet_antwortet_und_endet(dienst):
    adresse = dienst.starten()
    assert adresse.startswith("http://127.0.0.1:")
    assert dienst.laeuft and dienst.bereit()

    vorgang = dienst._vorgang
    dienst.beenden()
    assert not dienst.laeuft
    assert vorgang.poll() is not None, "der Vorgang muss wirklich beendet sein"


def test_dienst_hoert_nur_auf_dem_eigenen_rechner(dienst):
    """Der Dienst ist kein Netzwerkdienst (Masterprompt 5, 69)."""
    befehl = dienst._befehl()
    assert "--host" in befehl
    assert befehl[befehl.index("--host") + 1] == "127.0.0.1"


def test_zweimal_starten_startet_nicht_zweimal(dienst):
    erste = dienst.starten()
    vorgang = dienst._vorgang
    assert dienst.starten() == erste
    assert dienst._vorgang is vorgang


def test_beenden_ist_mehrfach_aufrufbar(dienst):
    dienst.starten()
    dienst.beenden()
    dienst.beenden()          # darf nicht scheitern


def test_dienst_wartet_bis_der_server_bereit_ist(tmp_path):
    """Ein Modell braucht Zeit zum Laden - solange darf nicht gefragt werden."""
    programm = _programm(tmp_path / "runtime", verzoegerung=1.5)
    server = Llamaserver(programm=programm, modell=_modell(tmp_path / "models"),
                         vorlauf=VORLAUF)
    try:
        begonnen = time.monotonic()
        server.starten()
        gedauert = time.monotonic() - begonnen
        assert gedauert >= 1.4, "es wurde nicht auf die Bereitschaft gewartet"
        assert server.bereit()
    finally:
        server.beenden()


def test_fehlstart_wird_verstaendlich_gemeldet(tmp_path):
    programm = _programm(tmp_path / "runtime", vorlage=VERSAGER)
    server = Llamaserver(programm=programm, modell=_modell(tmp_path / "models"),
                         startgrenze=10.0, vorlauf=VORLAUF)
    with pytest.raises(RuntimeError) as fehler:
        server.starten(protokollordner=tmp_path / "logs")
    assert "nicht hochgekommen" in str(fehler.value)
    assert "Modell" in str(fehler.value), "die Ausgabe des Programms muss mitkommen"


def test_fehlende_dateien_werden_benannt(tmp_path):
    server = Llamaserver(programm=tmp_path / "fehlt", modell=_modell(tmp_path / "models"),
                         vorlauf=VORLAUF)
    with pytest.raises(RuntimeError) as fehler:
        server.starten()
    assert "Programmdatei fehlt" in str(fehler.value)

    server = Llamaserver(programm=_programm(tmp_path / "runtime"),
                         modell=tmp_path / "weg.gguf", vorlauf=VORLAUF)
    with pytest.raises(RuntimeError) as fehler:
        server.starten()
    assert "Modelldatei fehlt" in str(fehler.value)


# -- Der Anbieter -------------------------------------------------------

def test_anbieter_startet_den_dienst_nicht_beim_pruefen(dienst):
    """Der Programmstart darf nicht auf ein ladendes Modell warten."""
    anbieter = MitgelieferterServerProvider(dienst)
    bereit, hinweis = anbieter.available()
    assert bereit
    assert not dienst.laeuft, "available() darf den Dienst nicht starten"
    assert "erste" in hinweis.lower()


def test_anbieter_startet_den_dienst_bei_der_ersten_frage(dienst):
    anbieter = MitgelieferterServerProvider(dienst)
    antwort = anbieter.generate([ChatMessage("user", "Wie buche ich eine Rechnung?")])
    assert dienst.laeuft
    assert "Wie buche ich" in antwort.text
    assert antwort.is_generated


def test_anbieter_gibt_stueckweise_heraus(dienst):
    gesehen: list[str] = []
    anbieter = MitgelieferterServerProvider(dienst)
    antwort = anbieter.generate([ChatMessage("user", "Frage")], on_token=gesehen.append)
    assert len(gesehen) > 1, "die Antwort muss waehrend der Erzeugung ankommen"
    assert antwort.text.startswith("Antwort des Stellvertreters")


def test_anbieter_meldet_fehlstart_als_modellfehler(tmp_path):
    programm = _programm(tmp_path / "runtime", vorlage=VERSAGER)
    server = Llamaserver(programm=programm, modell=_modell(tmp_path / "models"),
                         startgrenze=10.0, vorlauf=VORLAUF)
    anbieter = MitgelieferterServerProvider(server, protokollordner=tmp_path / "logs")
    with pytest.raises(LlmError):
        anbieter.generate([ChatMessage("user", "Frage")])
    bereit, hinweis = anbieter.available()
    assert not bereit and "nicht hochgekommen" in hinweis


def test_manager_beendet_den_dienst(dienst):
    anbieter = MitgelieferterServerProvider(dienst)
    manager = LlmManager(anbieter)
    manager.generate([ChatMessage("user", "Frage")])
    assert dienst.laeuft

    manager.beenden()
    assert not dienst.laeuft, "beim Beenden muss der Dienst heruntergefahren werden"


# -- Zusammenspiel mit der Konfiguration --------------------------------

def test_anwendung_waehlt_den_mitgelieferten_dienst(portable_root):
    """Liegen Modell und Programmdatei vor, wird der Dienst genommen."""
    from pkc.config import Config

    _programm(portable_root.get("runtime") / "llama")
    _modell(portable_root.get("models"), "buchhalter-7b.gguf")

    manager = LlmManager.from_config(Config.load(portable_root), portable_root)
    try:
        assert isinstance(manager.primary, MitgelieferterServerProvider)
        bereit, hinweis = manager.primary.available()
        assert bereit and "buchhalter-7b.gguf" in hinweis
    finally:
        manager.beenden()


def test_ohne_programmdatei_wird_das_ehrlich_gesagt(portable_root):
    from pkc.config import Config
    from pkc.llm.providers import RetrievalOnlyProvider

    _modell(portable_root.get("models"))
    manager = LlmManager.from_config(Config.load(portable_root), portable_root)
    assert isinstance(manager.primary, RetrievalOnlyProvider)
    bereit, hinweis = manager.primary.available()
    assert "modell einrichten" in " ".join(manager.notices).lower()
