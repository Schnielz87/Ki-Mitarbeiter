"""RAG-Orchestrierung: Frage -> Recherche -> Kontext -> Modell -> Antwort.

Was diese Schicht zusaetzlich leistet:

* Sie stellt sicher, dass jede Antwort einen **nachvollziehbaren
  Quellenteil** und den **Wissensstand** bekommt - auch wenn das Modell das
  vergisst.
* Sie erkennt **erfundene Fundstellennummern** und entfernt sie samt Hinweis.
* Sie kennzeichnet, wenn **keine** lokale Fundstelle vorlag.
* Sie haengt den **Freigabehinweis** an, wo das Profil ihn verlangt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

from ..llm.base import ChatMessage, LlmResponse
from ..llm.manager import LlmManager
from ..logging_setup import get_logger
from ..memory.store import MemoryEntry, MemoryStore
from ..profile import EmployeeProfile
from ..retrieval.search import Hit, HybridSearcher
from .context import ContextBuilder, ContextBundle, SourceReference, cited_numbers

log = get_logger(__name__)


@dataclass
class AnswerResult:
    text: str
    references: list[SourceReference] = field(default_factory=list)
    used_references: list[SourceReference] = field(default_factory=list)
    context: ContextBundle | None = None
    llm: LlmResponse | None = None
    mode: str = "OFFLINE"
    knowledge_date: str | None = None
    warnings: list[str] = field(default_factory=list)
    elapsed: float = 0.0

    @property
    def model_answered(self) -> bool:
        return bool(self.llm and self.llm.is_generated)


class RagEngine:
    """Verbindet Recherche, Gedaechtnis, Profil und Sprachmodell."""

    def __init__(
        self,
        profile: EmployeeProfile,
        searcher: HybridSearcher,
        memory: MemoryStore,
        llm: LlmManager,
        builder: ContextBuilder | None = None,
        top_k: int = 8,
        lexical_candidates: int = 40,
        vector_candidates: int = 40,
    ):
        self.profile = profile
        self.searcher = searcher
        self.memory = memory
        self.llm = llm
        self.builder = builder or ContextBuilder()
        self.top_k = int(top_k)
        self.lexical_candidates = int(lexical_candidates)
        self.vector_candidates = int(vector_candidates)

    # -- Kontext -------------------------------------------------------
    def retrieve(self, question: str, as_of: str | None = None) -> tuple[list[Hit], list[MemoryEntry]]:
        hits = self.searcher.search(
            question, top_k=self.top_k,
            lexical_candidates=self.lexical_candidates,
            vector_candidates=self.vector_candidates,
            as_of=as_of,
        )
        # Unternehmenswissen: gezielte Treffer plus die Stammdaten
        targeted = self.memory.search(question, limit=6)
        base = self.memory.all_active_for_prompt(max_entries=25)
        seen: set[str] = set()
        entries: list[MemoryEntry] = []
        for entry in list(targeted) + list(base):
            if entry.mem_key in seen:
                continue
            seen.add(entry.mem_key)
            entries.append(entry)
        return hits, entries

    def build_messages(
        self,
        question: str,
        bundle: ContextBundle,
        history: Sequence[ChatMessage] = (),
        mode: str = "OFFLINE",
        knowledge_date: str | None = None,
    ) -> list[ChatMessage]:
        header = [
            self.profile.system_prompt,
            "",
            "---",
            "",
            "## LAUFZEITLAGE",
            "",
            f"* Betriebsart: **{mode}**",
            f"* Lokaler Wissensstand: **{knowledge_date or 'unbekannt'}**",
            "* Es wurde ausschliesslich lokal recherchiert."
            if mode == "OFFLINE"
            else "* Lokale Recherche; Online-Funktionen stehen zusaetzlich zur Verfuegung.",
        ]
        if self.profile.limits:
            header += ["", "## GRENZEN DIESER ROLLE", ""]
            header += [f"* {limit}" for limit in self.profile.limits]
        messages = [ChatMessage("system", "\n".join(header))]
        messages.append(ChatMessage("system", bundle.as_system_block()))
        messages.extend(history)
        messages.append(ChatMessage("user", question))
        return messages

    # -- Hauptweg ------------------------------------------------------
    def answer(
        self,
        question: str,
        history: Sequence[ChatMessage] = (),
        mode: str = "OFFLINE",
        knowledge_date: str | None = None,
        as_of: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        prefer_online: bool = False,
    ) -> AnswerResult:
        hits, entries = self.retrieve(question, as_of=as_of)
        bundle = self.builder.build(hits, entries)
        messages = self.build_messages(question, bundle, history, mode, knowledge_date)

        response = self.llm.generate(
            messages, max_tokens=max_tokens, temperature=temperature,
            prefer_online=prefer_online,
        )

        text = response.text
        warnings: list[str] = []
        valid = {ref.number for ref in bundle.references}
        cited = cited_numbers(text)
        invented = sorted(cited - valid)
        if invented:
            warnings.append(
                "Das Modell hat Fundstellennummern genannt, die es nicht gab "
                f"({', '.join(f'[{n}]' for n in invented)}). Sie wurden entfernt."
            )
            text = _strip_numbers(text, invented)
            cited = cited_numbers(text)

        used = [ref for ref in bundle.references if ref.number in cited]
        if response.is_generated and bundle.references and not used:
            warnings.append(
                "Die Antwort nennt keine der gefundenen Fundstellen. Bitte besonders "
                "sorgfaeltig pruefen."
            )
        if not bundle.has_knowledge:
            warnings.append(
                "Zu dieser Frage lag lokal keine Fachfundstelle vor. Die Antwort stuetzt "
                "sich nicht auf eine lokale Quelle."
            )

        text = self._append_footer(
            text, bundle, used, mode, knowledge_date, response, warnings
        )
        return AnswerResult(
            text=text, references=bundle.references, used_references=used,
            context=bundle, llm=response, mode=mode, knowledge_date=knowledge_date,
            warnings=warnings, elapsed=response.elapsed,
        )

    # -- Nachbereitung -------------------------------------------------
    def _append_footer(
        self, text: str, bundle: ContextBundle, used: Sequence[SourceReference],
        mode: str, knowledge_date: str | None, response: LlmResponse,
        warnings: Sequence[str],
    ) -> str:
        parts = [text.rstrip()]
        upper = text.upper()

        shown = list(used) or list(bundle.references)
        if shown and "QUELLEN" not in upper:
            parts.append("**QUELLEN**\n" + "\n".join(ref.as_line() for ref in shown))
        elif not shown:
            parts.append(
                "**QUELLEN**\nKeine lokale Fundstelle verwendet. Diese Antwort ist nicht "
                "durch eine lokale Quelle belegt."
            )

        if "WISSENSSTAND" not in upper:
            parts.append(
                "**WISSENSSTAND**\n"
                f"Lokaler Wissensstand: {knowledge_date or 'unbekannt'} · "
                f"Betriebsart: {mode} · "
                f"Antwort erzeugt durch: {response.provider}"
                f"{'' if response.is_generated else ' (kein Sprachmodell verfuegbar)'}"
            )

        if response.is_generated and "FREIGABEBEDARF" not in upper:
            parts.append(
                "**FREIGABEBEDARF**\n"
                "Fachliche Zuarbeit ohne Gewaehr. Buchungen, Meldungen und Zahlungen "
                "beduerfen der Pruefung und Freigabe durch einen verantwortlichen "
                "Menschen."
            )

        if warnings:
            parts.append("**HINWEISE DER ANWENDUNG**\n" + "\n".join(f"* {w}" for w in warnings))
        return "\n\n".join(parts)


def _strip_numbers(text: str, numbers: Sequence[int]) -> str:
    for number in numbers:
        text = re.sub(rf"\s*\[{number}\]", "", text)
    return text
