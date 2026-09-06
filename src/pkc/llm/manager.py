"""Auswahl und Verwaltung des Sprachmodells.

Reihenfolge (Masterprompt 32/33): das **lokale** Modell ist die Grundlage.
Online-Modelle sind optional und werden nur benutzt, wenn der Nutzer sie
ausdruecklich freigegeben hat. Faellt ein Online-Modell aus, wird das lokale
Modell weiterverwendet - nie umgekehrt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
import inspect
from typing import Any, Callable, Iterable, Sequence

from ..logging_setup import get_logger
from .base import ChatMessage, LlmError, LlmProvider, LlmResponse
from .providers import (
    MitgelieferterServerProvider,
    LlamaCppProvider, OpenAICompatibleProvider, RetrievalOnlyProvider,
)

log = get_logger(__name__)


def _kann_strom(provider: LlmProvider) -> bool:
    """Nimmt der Anbieter eine Rueckmeldung je Textstueck entgegen?

    Geprueft wird die Unterschrift, nicht der Name: so bleiben eigene
    Anbieter und Testdoppel ohne Aenderung benutzbar.
    """
    try:
        return "on_token" in inspect.signature(provider.generate).parameters
    except (TypeError, ValueError):
        return False

MODEL_SUFFIXES = (".gguf",)

#: Empfehlungen je Hardwareprofil. Bewusst nur Modelle mit freier Lizenz.
RECOMMENDED_MODELS = {
    "light": {
        "name": "Qwen2.5-3B-Instruct (Q4_K_M)",
        "licence": "Apache-2.0",
        "size_gb": 2.0,
        "min_ram_gb": 6,
        "note": "Fuer aeltere Buerorechner. Fachqualitaet begrenzt - Antworten "
                "muessen besonders sorgfaeltig geprueft werden.",
    },
    "standard": {
        "name": "Qwen2.5-7B-Instruct (Q4_K_M)",
        "licence": "Apache-2.0",
        "size_gb": 4.7,
        "min_ram_gb": 12,
        "note": "Empfohlener Standard: gute deutsche Sprachqualitaet bei "
                "vertretbarem Speicherbedarf.",
    },
    "high": {
        "name": "Mistral-Nemo-Instruct-2407 (Q5_K_M) oder Qwen2.5-14B-Instruct (Q4_K_M)",
        "licence": "Apache-2.0",
        "size_gb": 9.0,
        "min_ram_gb": 24,
        "note": "Beste Fachqualitaet. GPU empfohlen, auf CPU deutlich langsamer.",
    },
}


@dataclass
class ModelInfo:
    path: Path
    size_gb: float
    quantisation: str
    family: str

    @property
    def name(self) -> str:
        return self.path.name


def discover_models(models_dir: Path) -> list[ModelInfo]:
    """Findet GGUF-Modelle im Modellverzeichnis der SSD."""
    if not models_dir.is_dir():
        return []
    found: list[ModelInfo] = []
    for path in sorted(models_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in MODEL_SUFFIXES:
            continue
        name = path.stem
        quant = ""
        match = re.search(r"(Q\d(?:_[A-Z0-9]+)*|F16|BF16|IQ\d[\w]*)", name, re.IGNORECASE)
        if match:
            quant = match.group(1).upper()
        family = re.split(r"[-_.]", name)[0]
        found.append(
            ModelInfo(path=path, size_gb=round(path.stat().st_size / 1024**3, 2),
                      quantisation=quant or "unbekannt", family=family)
        )
    return found


class LlmManager:
    """Waehlt den Anbieter und haelt den Zustand fuer die Oberflaeche bereit."""

    def __init__(
        self,
        primary: LlmProvider,
        online: LlmProvider | None = None,
        allow_online: bool = False,
    ):
        self.primary = primary
        self.online = online
        self.allow_online = bool(allow_online)
        self.last_error = ""
        self.notices: list[str] = []

    # -- Aufbau --------------------------------------------------------
    @classmethod
    def from_config(cls, config, paths, secret_lookup=None) -> "LlmManager":
        """Baut den Manager aus der Konfiguration - mit ehrlichem Rueckfall."""
        notices: list[str] = []
        provider_kind = str(config.get("llm.provider", "local")).lower()
        primary: LlmProvider

        if provider_kind == "echo":
            from .providers import ScriptedProvider
            primary = ScriptedProvider()
        else:
            primary, notice = cls._build_local(config, paths)
            if notice:
                notices.append(notice)

        online_provider: LlmProvider | None = None
        online_config = config.get("llm.online", {}) or {}
        if online_config.get("enabled") and online_config.get("base_url"):
            api_key = ""
            if secret_lookup is not None:
                api_key = secret_lookup(online_config.get("secret_key", "online_llm_api_key")) or ""
            online_provider = OpenAICompatibleProvider(
                base_url=str(online_config["base_url"]),
                model=str(online_config.get("model", "")),
                api_key=api_key, requires_internet=True, name="online-modell",
            )

        manager = cls(
            primary, online_provider,
            allow_online=bool(config.get("network.allow_online_llm", False)),
        )
        manager.notices = notices
        return manager

    @staticmethod
    def _build_local(config, paths) -> tuple[LlmProvider, str]:
        """Lokales Modell: erst Server auf 127.0.0.1, dann In-Process, sonst Notbetrieb."""
        model_setting = str(config.get("llm.model_path", "auto"))
        models_dir = paths.get("models")
        model_path: Path | None = None

        if model_setting and model_setting != "auto":
            candidate = Path(model_setting)
            if not candidate.is_absolute():
                candidate = paths.root / candidate
            model_path = candidate if candidate.is_file() else None
            if model_path is None:
                return (
                    RetrievalOnlyProvider(f"eingestelltes Modell nicht gefunden: {candidate}"),
                    f"Das eingestellte Modell wurde nicht gefunden: {candidate}",
                )
        else:
            models = discover_models(models_dir)
            if models:
                model_path = max(models, key=lambda m: m.size_gb).path

        server_url = str(config.get("llm.server_url", "") or "")
        if server_url:
            provider = OpenAICompatibleProvider(
                server_url, model=str(config.get("llm.server_model", "local")),
                requires_internet=False, name="local-server",
            )
            reachable, detail = provider.available()
            if reachable:
                return provider, ""
            return (
                RetrievalOnlyProvider(detail),
                f"Lokaler Modelldienst nicht erreichbar: {detail}",
            )

        if model_path is None:
            return (
                RetrievalOnlyProvider(f"kein GGUF-Modell in {models_dir}"),
                f"Es liegt kein Sprachmodell in {models_dir}. "
                "Die Anwendung laeuft im Notbetrieb (Recherche ohne Modellantwort). "
                "Einrichten mit: modell einrichten",
            )

        # Bevorzugt der mitgelieferte llama.cpp-Server: er braucht keine
        # Uebersetzung auf dem Rechner des Kunden. Fuer llama-cpp-python gibt
        # es keine fertigen Pakete - das waere fuer eine portable Anwendung
        # der falsche Weg.
        from .server import Llamaserver, finde_server

        programm = finde_server(paths.get("runtime"))
        if programm is not None:
            server = Llamaserver(
                programm=programm, modell=model_path,
                kontext=int(config.get("llm.context_tokens", 8192)),
                threads=int(config.get("llm.threads", 0)),
                gpu_layers=int(config.get("llm.gpu_layers", 0)),
            )
            anbieter = MitgelieferterServerProvider(server, protokollordner=paths.get("logs"))
            bereit, hinweis = anbieter.available()
            if bereit:
                return anbieter, ""
            return RetrievalOnlyProvider(hinweis), hinweis

        provider = LlamaCppProvider(
            model_path,
            context_tokens=int(config.get("llm.context_tokens", 8192)),
            threads=int(config.get("llm.threads", 0)),
            gpu_layers=int(config.get("llm.gpu_layers", 0)),
        )
        usable, detail = provider.available()
        if usable:
            return provider, ""
        hinweis = (
            f"{detail} Ausserdem fehlt der mitgelieferte Modelldienst in "
            f"{paths.relative(paths.get('runtime'))}. Einrichten mit: modell einrichten"
        )
        return RetrievalOnlyProvider(hinweis), hinweis

    # -- Betrieb -------------------------------------------------------
    def beenden(self) -> None:
        """Faehrt einen selbst gestarteten Modelldienst wieder herunter.

        Ohne das liefe der Dienst nach dem Schliessen der Anwendung weiter
        und hielte den Arbeitsspeicher des Modells belegt.
        """
        for anbieter in (self.primary, self.online):
            aufraeumen = getattr(anbieter, "beenden", None)
            if callable(aufraeumen):
                try:
                    aufraeumen()
                except Exception as fehler:      # pragma: no cover - defensiv
                    log.debug("Modelldienst liess sich nicht beenden: %s", fehler)

    @property
    def active(self) -> LlmProvider:
        if self.allow_online and self.online is not None:
            return self.online
        return self.primary

    def status(self) -> dict:
        usable, detail = self.primary.available()
        info = {
            "primaer": self.primary.describe(),
            "primaer_bereit": usable,
            "primaer_hinweis": detail,
            "online_verfuegbar": self.online is not None,
            "online_erlaubt": self.allow_online,
            "hinweise": list(self.notices),
        }
        if self.online is not None:
            info["online"] = self.online.describe()
        return info

    def generate(
        self,
        messages: Sequence[ChatMessage],
        max_tokens: int = 1024,
        temperature: float = 0.2,
        stop: Iterable[str] | None = None,
        prefer_online: bool = False,
        on_token: Callable[[str], None] | None = None,
    ) -> LlmResponse:
        """Erzeugt eine Antwort. Ein Online-Ausfall faellt auf lokal zurueck.

        ``on_token`` wird nur an Anbieter weitergereicht, die schrittweise
        erzeugen koennen (Abschnitt 21). Alle anderen antworten wie bisher am
        Stueck - eine schrittweise Ausgabe ist erwuenscht, eine richtige
        Antwort ist wichtiger.

        Bricht ein Anbieter mitten im Strom ab, sind bereits Stuecke bei der
        Oberflaeche angekommen. Der naechste Anbieter beginnt dann von vorn;
        deshalb meldet ``on_token`` den Neubeginn mit einer leeren Zeichenkette,
        und die Oberflaeche verwirft das bisher Angezeigte.
        """
        order: list[LlmProvider] = []
        if prefer_online and self.allow_online and self.online is not None:
            order.append(self.online)
        order.append(self.primary)
        if self.online is not None and self.allow_online and self.online not in order:
            order.append(self.online)

        errors: list[str] = []
        for provider in order:
            try:
                if on_token is not None and _kann_strom(provider):
                    if errors:
                        on_token("")
                    response = provider.generate(messages, max_tokens, temperature, stop,
                                                 on_token=on_token)
                else:
                    response = provider.generate(messages, max_tokens, temperature, stop)
                if errors:
                    response.meta["fallback_von"] = errors
                self.last_error = ""
                return response
            except LlmError as exc:
                errors.append(f"{provider.name}: {exc}")
                log.warning("Anbieter %s fehlgeschlagen: %s", provider.name, exc)

        self.last_error = " | ".join(errors)
        if on_token is not None:
            # Nichts von dem, was bereits durchlief, darf als Antwort
            # stehenbleiben: es kam von einem Anbieter, der abgebrochen hat.
            on_token("")
        fallback = RetrievalOnlyProvider(self.last_error)
        response = fallback.generate(messages, max_tokens, temperature, stop)
        response.meta["fallback_von"] = errors
        return response
