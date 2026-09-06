"""Sprachmodell-Anbindung gegen einen echten (lokalen) Modelldienst.

Damit ist der Weg geprueft, der im portablen Betrieb empfohlen wird:
``llama-server`` aus llama.cpp laeuft auf 127.0.0.1 und spricht das
OpenAI-kompatible Protokoll. Derselbe Code bedient spaeter auch einen
Online-Dienst.

Nicht geprueft (weil in der Entwicklungsumgebung kein GGUF-Modell und keine
Bezugsquelle verfuegbar war): die Inferenz mit einem echten Modell ueber
``llama-cpp-python``. Das ist in PROJEKTSTATUS.md als offener Abnahmeschritt
vermerkt.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from pkc.llm.base import ChatMessage, LlmError
from pkc.llm.manager import LlmManager, discover_models
from pkc.llm.providers import (
    LlamaCppProvider, OpenAICompatibleProvider, RetrievalOnlyProvider, ScriptedProvider,
)


class _ModelHandler(BaseHTTPRequestHandler):
    behaviour = "ok"
    seen: list[dict] = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.endswith("/v1/models"):
            payload = json.dumps({"data": [{"id": "testmodell"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        request = json.loads(self.rfile.read(length) or b"{}")
        _ModelHandler.seen.append(request)

        if _ModelHandler.behaviour == "error":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Modell ueberlastet")
            return
        if _ModelHandler.behaviour == "garbage":
            payload = b'{"unerwartet": true}'
        else:
            question = request["messages"][-1]["content"]
            payload = json.dumps({
                "model": "testmodell",
                "choices": [{
                    "message": {"role": "assistant",
                                "content": f"Antwort auf: {question[:60]}"},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 120, "completion_tokens": 20},
            }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


@pytest.fixture
def model_server():
    _ModelHandler.behaviour = "ok"
    _ModelHandler.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ModelHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    class Control:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        handler = _ModelHandler

    try:
        yield Control()
    finally:
        server.shutdown()
        server.server_close()


def test_local_server_answers(model_server):
    provider = OpenAICompatibleProvider(model_server.base, model="testmodell",
                                        name="local-server")
    ok, detail = provider.available()
    assert ok, detail

    response = provider.generate(
        [ChatMessage("system", "Du bist Buchhalter."),
         ChatMessage("user", "Wie wird ein innergemeinschaftlicher Erwerb gebucht?")]
    )
    assert response.text.startswith("Antwort auf: Wie wird ein innergemeinschaftlicher")
    assert response.prompt_tokens == 120 and response.completion_tokens == 20
    assert response.is_generated
    # Systemnachricht und Frage wurden korrekt uebertragen
    sent = model_server.handler.seen[-1]
    assert sent["messages"][0]["role"] == "system"
    assert sent["stream"] is False


def test_server_error_becomes_clear_message(model_server):
    model_server.handler.behaviour = "error"
    provider = OpenAICompatibleProvider(model_server.base)
    with pytest.raises(LlmError) as info:
        provider.generate([ChatMessage("user", "Frage")])
    assert "500" in str(info.value)


def test_unexpected_answer_is_detected(model_server):
    model_server.handler.behaviour = "garbage"
    provider = OpenAICompatibleProvider(model_server.base)
    with pytest.raises(LlmError):
        provider.generate([ChatMessage("user", "Frage")])


def test_unreachable_server_is_reported_not_crashed():
    provider = OpenAICompatibleProvider("http://127.0.0.1:1", model="x")
    ok, detail = provider.available()
    assert not ok and "nicht erreichbar" in detail
    with pytest.raises(LlmError):
        provider.generate([ChatMessage("user", "Frage")])


def test_manager_falls_back_to_local_when_online_fails(model_server):
    """Faellt das Online-Modell aus, arbeitet das lokale weiter - nie umgekehrt."""
    local = ScriptedProvider(fixed="Lokale Antwort")
    online = OpenAICompatibleProvider("http://127.0.0.1:1", model="online",
                                      requires_internet=True, name="online-modell")
    manager = LlmManager(local, online, allow_online=True)
    response = manager.generate([ChatMessage("user", "Frage")], prefer_online=True)
    assert response.text == "Lokale Antwort"
    assert response.meta["fallback_von"], "der Ausfall muss dokumentiert sein"


def test_manager_without_any_model_is_honest():
    manager = LlmManager(RetrievalOnlyProvider("kein Modell auf dem Datentraeger"))
    response = manager.generate([ChatMessage("user", "Wie buche ich Skonto?")])
    assert not response.is_generated
    # Auf die Substanz pruefen, nicht auf eine bestimmte Formulierung:
    # es muss erkennbar sein, dass KEINE Antwort erzeugt wurde und woran es
    # liegt - und es darf keine Ersatzantwort vorgetaeuscht werden.
    assert "keine KI-Antwort" in response.text
    assert "kein Sprachmodell" in response.text
    assert "modell" in response.text.lower(), "der Weg zur Einrichtung muss genannt sein"
    # Der technische Grund gehoert NICHT in die Antwort (Abschnitt 18:
    # keine Modellpfade, keine internen Meldungen in der normalen Antwort),
    # sondern in die Metadaten - fuer Status, Protokoll und Fehlersuche.
    assert response.meta.get("reason") == "kein Modell auf dem Datentraeger"
    assert "Datentraeger" not in response.text, \
        "der technische Grund darf die Antwort nicht belasten"


def test_llama_cpp_provider_reports_missing_model(tmp_path):
    provider = LlamaCppProvider(tmp_path / "gibt-es-nicht.gguf")
    ok, detail = provider.available()
    assert not ok and "nicht gefunden" in detail


def test_model_discovery(tmp_path):
    models = tmp_path / "models"
    models.mkdir()
    assert discover_models(models) == []
    (models / "Qwen2.5-7B-Instruct-Q4_K_M.gguf").write_bytes(b"0" * 4096)
    (models / "liesmich.txt").write_text("kein Modell", encoding="utf-8")
    found = discover_models(models)
    assert len(found) == 1
    assert found[0].quantisation == "Q4_K_M" and found[0].name.endswith(".gguf")
