"""Gemeinsame Schnittstelle aller Sprachmodell-Anbieter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol, Sequence, runtime_checkable


class LlmError(RuntimeError):
    """Das Modell konnte die Anfrage nicht beantworten."""


@dataclass
class ChatMessage:
    role: str          # system | user | assistant
    content: str

    def as_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class LlmResponse:
    text: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    elapsed: float = 0.0
    #: Sekunden bis zum **ersten** Textstueck. Das ist die Zahl, die der
    #: Benutzer als Wartezeit erlebt: danach laeuft die Antwort sichtbar
    #: weiter. Ohne schrittweise Ausgabe bleibt sie 0.
    erstes_token_s: float = 0.0
    truncated: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def is_generated(self) -> bool:
        """False, wenn kein echtes Sprachmodell geantwortet hat."""
        return bool(self.meta.get("generated", True))


@runtime_checkable
class LlmProvider(Protocol):
    name: str
    model: str

    def available(self) -> tuple[bool, str]: ...

    def generate(
        self,
        messages: Sequence[ChatMessage],
        max_tokens: int = 1024,
        temperature: float = 0.2,
        stop: Iterable[str] | None = None,
    ) -> LlmResponse: ...

    def describe(self) -> dict: ...
