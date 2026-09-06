"""Konkrete Sprachmodell-Anbieter.

* ``LlamaCppProvider``          - lokales GGUF-Modell im selben Prozess
* ``OpenAICompatibleProvider``  - lokaler llama-server ODER Online-Dienst
* ``RetrievalOnlyProvider``     - Notbetrieb ohne Modell (ehrliche Ausgabe)
* ``ScriptedProvider``          - deterministischer Anbieter fuer Tests

Der Notbetrieb ist bewusst kein Modellersatz: er erzeugt keine formulierte
Fachantwort, sondern gibt die gefundenen Fundstellen aus und sagt klar, dass
kein Sprachmodell verfuegbar war.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from ..logging_setup import get_logger
from .base import ChatMessage, LlmError, LlmResponse

log = get_logger(__name__)


def _teil_aus_brocken(brocken: Any) -> tuple[str, str]:
    """Zieht Textstueck und Abbruchgrund aus einem Antwortbrocken.

    Sowohl llama-cpp-python als auch OpenAI-kompatible Dienste liefern beim
    schrittweisen Erzeugen dieselbe Form: ``choices[0].delta.content``. Aeltere
    Dienste schicken stattdessen ``text``. Beides wird angenommen; alles
    andere wird uebergangen, statt die laufende Antwort abzubrechen.
    """
    try:
        choice = brocken["choices"][0]
    except (KeyError, IndexError, TypeError):
        return "", ""
    delta = choice.get("delta") or {}
    stueck = delta.get("content") or choice.get("text") or ""
    return (stueck if isinstance(stueck, str) else ""), (choice.get("finish_reason") or "")


class LlamaCppProvider:
    """Lokales GGUF-Modell ueber ``llama-cpp-python`` (im Prozess)."""

    def __init__(
        self,
        model_path: str | Path,
        context_tokens: int = 8192,
        threads: int = 0,
        gpu_layers: int = 0,
        chat_format: str | None = None,
    ):
        self.model_path = Path(model_path)
        self.context_tokens = int(context_tokens)
        self.threads = int(threads)
        self.gpu_layers = int(gpu_layers)
        self.chat_format = chat_format
        self.name = "local-llama-cpp"
        self.model = self.model_path.name
        self._llama: Any = None
        self._load_error = ""

    def available(self) -> tuple[bool, str]:
        if not self.model_path.is_file():
            return False, f"Modelldatei nicht gefunden: {self.model_path}"
        try:
            import llama_cpp  # noqa: F401
        except ImportError:
            return False, (
                "Das Paket 'llama-cpp-python' ist nicht installiert. "
                "Alternative: llama-server aus ./runtime starten und den Anbieter "
                "'local-server' verwenden."
            )
        if self._load_error:
            return False, self._load_error
        return True, f"Lokales Modell bereit: {self.model_path.name}"

    def _ensure_loaded(self) -> Any:
        if self._llama is not None:
            return self._llama
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:
            raise LlmError("llama-cpp-python ist nicht installiert.") from exc
        kwargs: dict[str, Any] = {
            "model_path": str(self.model_path),
            "n_ctx": self.context_tokens,
            "n_gpu_layers": self.gpu_layers,
            "verbose": False,
        }
        if self.threads:
            kwargs["n_threads"] = self.threads
        if self.chat_format:
            kwargs["chat_format"] = self.chat_format
        try:
            self._llama = Llama(**kwargs)
        except Exception as exc:  # llama.cpp meldet unterschiedliche Fehler
            self._load_error = f"Modell konnte nicht geladen werden: {exc}"
            raise LlmError(self._load_error) from exc
        log.info("Lokales Modell geladen: %s", self.model_path.name)
        return self._llama

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None,
                 on_token: Callable[[str], None] | None = None) -> LlmResponse:
        """Erzeugt eine Antwort; mit ``on_token`` Stueck fuer Stueck.

        Abschnitt 21: die Antwort soll waehrend der Erzeugung erscheinen. Ohne
        ``on_token`` bleibt es beim bisherigen Verhalten - eine vollstaendige
        Antwort am Stueck. Das ist der Rueckfallweg, wenn die Oberflaeche
        keine schrittweise Ausgabe anfordert.
        """
        llama = self._ensure_loaded()
        started = time.monotonic()
        anfrage = {
            "messages": [m.as_dict() for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": list(stop) if stop else None,
        }
        if on_token is None:
            try:
                result = llama.create_chat_completion(**anfrage)
            except Exception as exc:
                raise LlmError(f"Lokale Inferenz fehlgeschlagen: {exc}") from exc
            choice = result["choices"][0]
            usage = result.get("usage", {})
            return LlmResponse(
                text=(choice["message"]["content"] or "").strip(),
                provider=self.name, model=self.model,
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                elapsed=time.monotonic() - started,
                truncated=choice.get("finish_reason") == "length",
            )

        teile: list[str] = []
        grund = ""
        try:
            for brocken in llama.create_chat_completion(stream=True, **anfrage):
                stueck, grund_neu = _teil_aus_brocken(brocken)
                if grund_neu:
                    grund = grund_neu
                if stueck:
                    teile.append(stueck)
                    on_token(stueck)
        except Exception as exc:
            raise LlmError(f"Lokale Inferenz fehlgeschlagen: {exc}") from exc
        return LlmResponse(
            text="".join(teile).strip(),
            provider=self.name, model=self.model,
            elapsed=time.monotonic() - started,
            truncated=grund == "length",
            meta={"streaming": True},
        )

    def describe(self) -> dict:
        return {
            "anbieter": self.name, "modell": self.model, "pfad": str(self.model_path),
            "kontext": self.context_tokens, "gpu_layers": self.gpu_layers,
            "benoetigt_internet": False,
        }

    def unload(self) -> None:
        self._llama = None


class OpenAICompatibleProvider:
    """Beliebiger OpenAI-kompatibler Endpunkt.

    Deckt zwei Faelle ab:
    * **lokal**: ``llama-server`` aus llama.cpp auf ``127.0.0.1`` - keine
      Kompilierung von Python-Bindings noetig, ideal fuer den portablen Betrieb.
    * **online**: ein Cloud-Dienst, sofern der Nutzer ihn ausdruecklich
      freigibt.
    """

    def __init__(
        self,
        base_url: str,
        model: str = "local",
        api_key: str = "",
        timeout: float = 180.0,
        requires_internet: bool = False,
        name: str = "openai-kompatibel",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model or "local"
        self.api_key = api_key
        self.timeout = float(timeout)
        self.requires_internet = bool(requires_internet)
        self.name = name

    @property
    def _endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/chat/completions"
        return f"{self.base_url}/v1/chat/completions"

    def available(self) -> tuple[bool, str]:
        if not self.base_url:
            return False, "Keine Adresse fuer den Modelldienst konfiguriert."
        probe = urllib.request.Request(f"{self.base_url.rstrip('/')}/v1/models", method="GET")
        if self.api_key:
            probe.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(probe, timeout=min(10.0, self.timeout)) as response:
                if 200 <= response.status < 300:
                    return True, f"Modelldienst erreichbar: {self.base_url}"
                return False, f"Modelldienst antwortete mit HTTP {response.status}."
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                return False, f"Modelldienst lehnt die Anmeldung ab (HTTP {exc.code})."
            return True, f"Modelldienst erreichbar (HTTP {exc.code} auf /v1/models)."
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            return False, f"Modelldienst nicht erreichbar: {exc}"

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None,
                 on_token: Callable[[str], None] | None = None) -> LlmResponse:
        payload = {
            "model": self.model,
            "messages": [m.as_dict() for m in messages],
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "stream": on_token is not None,
        }
        if stop:
            payload["stop"] = list(stop)
        request = urllib.request.Request(
            self._endpoint, data=json.dumps(payload).encode("utf-8"), method="POST"
        )
        request.add_header("Content-Type", "application/json")
        if self.api_key:
            request.add_header("Authorization", f"Bearer {self.api_key}")

        started = time.monotonic()
        if on_token is not None:
            return self._strom(request, on_token, started)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise LlmError(f"Modelldienst meldete HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
            raise LlmError(f"Modelldienst nicht erreichbar: {exc}") from exc

        try:
            choice = data["choices"][0]
            text = (choice.get("message", {}).get("content") or "").strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError(f"Unerwartete Antwort des Modelldienstes: {str(data)[:200]}") from exc
        usage = data.get("usage") or {}
        return LlmResponse(
            text=text, provider=self.name, model=data.get("model", self.model),
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            elapsed=time.monotonic() - started,
            truncated=choice.get("finish_reason") == "length",
        )

    def _strom(self, request, on_token: Callable[[str], None], started: float) -> LlmResponse:
        """Liest die Antwort als Ereignisstrom (Abschnitt 21).

        Der Dienst schickt Zeilen der Form ``data: {...}`` und zum Schluss
        ``data: [DONE]``. Bricht der Strom mittendrin ab, gilt das nicht als
        halbe Antwort: der Aufrufer bekommt einen Fehler und damit den
        ehrlichen Weg in den Notbetrieb.
        """
        teile: list[str] = []
        grund = ""
        abgeschlossen = False
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                for rohzeile in response:
                    zeile = rohzeile.decode("utf-8", errors="replace").strip()
                    if not zeile or not zeile.startswith("data:"):
                        continue
                    nutzlast = zeile[5:].strip()
                    if nutzlast == "[DONE]":
                        abgeschlossen = True
                        break
                    try:
                        brocken = json.loads(nutzlast)
                    except json.JSONDecodeError:
                        continue
                    stueck, grund_neu = _teil_aus_brocken(brocken)
                    if grund_neu:
                        grund = grund_neu
                        abgeschlossen = True
                    if stueck:
                        teile.append(stueck)
                        on_token(stueck)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise LlmError(f"Modelldienst meldete HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise LlmError(f"Modelldienst nicht erreichbar: {exc}") from exc
        text = "".join(teile).strip()
        if not text:
            raise LlmError("Der Modelldienst hat keinen Text geliefert.")
        if not abgeschlossen:
            # Ein Strom, der einfach aufhoert, ist kein fertiger Satz. Er als
            # Antwort auszugeben waere die gefaehrlichste Variante: er sieht
            # vollstaendig aus. Also gilt er als Ausfall.
            raise LlmError(
                "Der Modelldienst hat die Antwort nicht zu Ende geliefert "
                f"(abgebrochen nach {len(text)} Zeichen)."
            )
        return LlmResponse(
            text=text, provider=self.name, model=self.model,
            elapsed=time.monotonic() - started,
            truncated=grund == "length",
            meta={"streaming": True},
        )

    def describe(self) -> dict:
        return {
            "anbieter": self.name, "modell": self.model, "adresse": self.base_url,
            "benoetigt_internet": self.requires_internet,
        }


class MitgelieferterServerProvider(OpenAICompatibleProvider):
    """Der mitgelieferte llama.cpp-Server - von der Anwendung selbst gestartet.

    Der Dienst wird **nicht** beim Programmstart hochgefahren, sondern bei der
    ersten Frage. Sonst wuerde jeder Start der Anwendung das Laden eines
    mehrere Gigabyte grossen Modells abwarten, auch wenn der Benutzer nur
    kurz im Unternehmenswissen nachsehen will.
    """

    def __init__(self, server, protokollordner=None, name: str = "mitgelieferter-server"):
        super().__init__(base_url="http://127.0.0.1:0", model=server.modell.name,
                         requires_internet=False, name=name)
        self.server = server
        self.protokollordner = protokollordner
        self.startfehler = ""

    def available(self) -> tuple[bool, str]:
        """Beurteilt die Lage, **ohne** den Dienst zu starten."""
        if self.startfehler:
            return False, self.startfehler
        if not Path(self.server.programm).is_file():
            return False, f"Der Modelldienst fehlt: {self.server.programm}"
        if not Path(self.server.modell).is_file():
            return False, f"Die Modelldatei fehlt: {self.server.modell}"
        if self.server.laeuft:
            return True, f"Modell laeuft: {self.server.modell.name}"
        groesse = Path(self.server.modell).stat().st_size / 1024**3
        return True, (
            f"Modell bereit: {self.server.modell.name} ({groesse:.1f} GB). "
            "Der Dienst wird bei der ersten Frage gestartet - das dauert "
            "einmalig etwas."
        )

    def _sicherstellen(self) -> None:
        if self.server.laeuft:
            return
        try:
            self.base_url = self.server.starten(self.protokollordner).rstrip("/")
            self.startfehler = ""
        except Exception as fehler:
            self.startfehler = str(fehler)
            raise LlmError(f"Der Modelldienst konnte nicht gestartet werden: {fehler}") from fehler

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None,
                 on_token: Callable[[str], None] | None = None) -> LlmResponse:
        self._sicherstellen()
        return super().generate(messages, max_tokens, temperature, stop, on_token=on_token)

    def describe(self) -> dict:
        return {
            "anbieter": self.name,
            "modell": self.model,
            "programm": str(self.server.programm),
            "laeuft": self.server.laeuft,
            "benoetigt_internet": False,
        }

    def beenden(self) -> None:
        self.server.beenden()


class RetrievalOnlyProvider:
    """Notbetrieb: kein Sprachmodell verfuegbar.

    Gibt die gefundenen Fundstellen unveraendert aus und benennt klar, dass
    keine Modellantwort erzeugt wurde. Es wird nichts formuliert, was wie eine
    fachliche Wuerdigung aussehen koennte.
    """

    def __init__(self, reason: str = ""):
        self.name = "kein-modell"
        self.model = "keines"
        self.reason = reason

    def available(self) -> tuple[bool, str]:
        return True, "Notbetrieb ohne Sprachmodell"

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None) -> LlmResponse:
        """Kurze, ehrliche Statusmeldung - **keine** Ersatzantwort.

        Frueher stand hier ein langer Text, dem anschliessend saemtliche
        Fundstellen mit vollem Auszug angehaengt wurden. Das las sich wie
        eine Antwort, war aber keine: eine Liste von Rohtreffern ist kein
        Ersatz fuer ein fehlendes Sprachmodell. Wer sie sehen will, oeffnet
        die Fundstellen ausdruecklich.
        """
        # Wirklich vorhandene Fundstellen erkennt man an der Nummerierung
        # "[1]", nicht am blossen Vorkommen des Wortes: der Kontextblock
        # traegt die Ueberschrift auch dann, wenn nichts gefunden wurde -
        # und bei Smalltalk wird gar nicht erst gesucht.
        # Wirklich vorhandene Fundstellen erkennt man an der Nummerierung
        # "[1]", nicht am blossen Vorkommen des Wortes: der Kontextblock
        # traegt die Ueberschrift auch dann, wenn nichts gefunden wurde.
        alles = "\n".join(m.content for m in messages if m.role == "system")
        nicht_gesucht = "Recherche: nicht durchgefuehrt" in alles
        hat_kontext = "[1]" in alles
        lines = [
            "**Es konnte keine KI-Antwort erzeugt werden.**",
            "",
            # Kein Dateipfad in der normalen Antwort (Abschnitt 18) - der
            # gehoert in die Systempruefung und ins Protokoll.
            "Auf diesem Rechner ist kein Sprachmodell eingerichtet.",
        ]
        if nicht_gesucht:
            # Konversation - hier fehlt keine Fundstelle, es wurde bewusst
            # keine gesucht. Das darf nicht wie ein Mangel klingen.
            pass
        elif hat_kontext:
            lines += [
                "",
                "Die lokale Recherche hat passende Fundstellen gefunden. Sie stehen "
                "rechts unter *Quellen der letzten Antwort*; eine fachliche "
                "Wuerdigung ist daraus **nicht** abgeleitet.",
            ]
        else:
            lines += [
                "",
                "Zu dieser Frage wurde lokal ausserdem keine passende Fundstelle "
                "gefunden.",
            ]
        lines += [
            "",
            "Einrichten mit: `PORTABLE_BUCHHALTER_KONSOLE.exe modell empfehlen`",
        ]
        return LlmResponse(
            text="\n".join(lines), provider=self.name, model=self.model,
            meta={"generated": False, "reason": self.reason},
        )

    def describe(self) -> dict:
        return {"anbieter": self.name, "modell": "keines", "grund": self.reason,
                "benoetigt_internet": False}


class ScriptedProvider:
    """Deterministischer Anbieter fuer automatische Tests."""

    def __init__(self, responder: Callable[[Sequence[ChatMessage]], str] | None = None,
                 fixed: str = "TESTANTWORT"):
        self.name = "test-anbieter"
        self.model = "scripted"
        self.responder = responder
        self.fixed = fixed
        self.calls: list[list[ChatMessage]] = []

    def available(self) -> tuple[bool, str]:
        return True, "Testanbieter aktiv"

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None) -> LlmResponse:
        self.calls.append(list(messages))
        text = self.responder(messages) if self.responder else self.fixed
        return LlmResponse(text=text, provider=self.name, model=self.model,
                           prompt_tokens=sum(len(m.content) // 4 for m in messages),
                           completion_tokens=len(text) // 4)

    def describe(self) -> dict:
        return {"anbieter": self.name, "modell": self.model, "benoetigt_internet": False}
