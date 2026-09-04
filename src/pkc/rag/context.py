"""Zusammenstellung des Kontexts fuer eine Anfrage.

Drei Wissensarten werden getrennt gehalten und getrennt gekennzeichnet
(Masterprompt 14 und 30):

1. **Unternehmenswissen** - gilt fuer dieses Unternehmen, hat Vorrang vor
   allgemeinen Annahmen
2. **Fachwissen** - Gesetze, Verwaltungsanweisungen, Rechtsprechung,
   Fachmodule; geordnet nach Quellenhierarchie
3. **Belege des Nutzers** - hochgeladene Dokumente

Der Kontext ist token-budgetiert: Primaerquellen werden zuerst aufgenommen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from ..knowledge.chunker import estimate_tokens
from ..memory.store import MemoryEntry
from ..retrieval.search import Hit

PRIORITY_NAMES = {
    1: "Gesetz / amtliche Rechtsquelle",
    2: "Amtliche Verwaltungsanweisung",
    3: "Rechtsprechung",
    4: "Behoerdeninformation",
    5: "Fachquelle (sekundaer)",
}


@dataclass
class SourceReference:
    """Ein Quellennachweis, wie er dem Nutzer angezeigt und gespeichert wird."""

    number: int
    origin: str                # knowledge | company | document
    reference: str
    title: str
    excerpt: str
    url: str = ""
    priority: int = 5
    ref_id: str = ""
    score: float = 0.0
    valid_from: str | None = None
    valid_to: str | None = None
    fetched_at: str | None = None

    @property
    def priority_label(self) -> str:
        return PRIORITY_NAMES.get(self.priority, "unbestimmt")

    def as_dict(self) -> dict:
        return {
            "nummer": self.number, "art": self.origin, "fundstelle": self.reference,
            "titel": self.title, "auszug": self.excerpt, "url": self.url,
            "prioritaet": self.priority, "prioritaet_text": self.priority_label,
            "ref_id": self.ref_id, "score": self.score,
            "gueltig_ab": self.valid_from, "gueltig_bis": self.valid_to,
            "abgerufen_am": self.fetched_at,
        }

    def as_line(self) -> str:
        parts = [f"[{self.number}] {self.reference}"]
        if self.title and self.title.lower() not in self.reference.lower():
            parts.append(self.title)
        parts.append(f"({self.priority_label})")
        if self.url:
            parts.append(self.url)
        return " · ".join(parts)


@dataclass
class ContextBundle:
    company_block: str = ""
    knowledge_block: str = ""
    document_block: str = ""
    references: list[SourceReference] = field(default_factory=list)
    used_tokens: int = 0
    company_entries: list[MemoryEntry] = field(default_factory=list)
    knowledge_hits: list[Hit] = field(default_factory=list)

    @property
    def has_knowledge(self) -> bool:
        return bool(self.knowledge_hits)

    def as_system_block(self) -> str:
        parts: list[str] = []
        if self.company_block:
            parts.append(
                "## UNTERNEHMENSWISSEN (gilt fuer dieses Unternehmen, Vorrang vor "
                "allgemeinen Annahmen)\n\n" + self.company_block
            )
        if self.document_block:
            parts.append("## BELEGE DES NUTZERS\n\n" + self.document_block)
        if self.knowledge_block:
            parts.append(
                "## FUNDSTELLEN AUS DER LOKALEN FACHWISSENSBASIS\n\n"
                "Nutze ausschliesslich diese Fundstellen als Belege. Zitiere sie mit "
                "ihrer Nummer in eckigen Klammern, zum Beispiel [1]. Erfinde keine "
                "weiteren Fundstellen.\n\n" + self.knowledge_block
            )
        else:
            parts.append(
                "## FUNDSTELLEN AUS DER LOKALEN FACHWISSENSBASIS\n\n"
                "Zu dieser Frage wurde lokal **keine** passende Fundstelle gefunden. "
                "Sage das offen, stuetze dich erkennbar auf allgemeines Fachwissen und "
                "empfiehl die Pruefung an der Primaerquelle."
            )
        return "\n\n".join(parts)


class ContextBuilder:
    """Baut aus Treffern und Gedaechtnis den Modellkontext."""

    def __init__(self, max_context_tokens: int = 3200, max_company_tokens: int = 900):
        self.max_context_tokens = int(max_context_tokens)
        self.max_company_tokens = int(max_company_tokens)

    def build(
        self,
        hits: Sequence[Hit],
        company_entries: Sequence[MemoryEntry] = (),
        document_hits: Sequence[dict] = (),
    ) -> ContextBundle:
        bundle = ContextBundle()
        number = 0
        used = 0

        # 1. Unternehmenswissen - immer zuerst, es ist kurz und entscheidend
        company_lines: list[str] = []
        company_used = 0
        for entry in company_entries:
            line = entry.as_prompt_line()
            cost = estimate_tokens(line)
            if company_used + cost > self.max_company_tokens:
                break
            company_lines.append(line)
            company_used += cost
        if company_lines:
            bundle.company_block = "\n".join(company_lines)
            bundle.company_entries = list(company_entries[: len(company_lines)])
            used += company_used

        # 2. Belege des Nutzers
        document_lines: list[str] = []
        for item in document_hits:
            number += 1
            text = str(item.get("text", ""))
            title = str(item.get("title", "Beleg"))
            cost = estimate_tokens(text) + 20
            if used + cost > self.max_context_tokens:
                number -= 1
                break
            document_lines.append(f"[{number}] Beleg „{title}“\n{text}")
            bundle.references.append(
                SourceReference(
                    number=number, origin="document", reference=f"Beleg: {title}",
                    title=title, excerpt=_shorten(text), ref_id=str(item.get("doc_uid", "")),
                )
            )
            used += cost
        if document_lines:
            bundle.document_block = "\n\n".join(document_lines)

        # 3. Fachwissen nach Quellenhierarchie
        knowledge_lines: list[str] = []
        for hit in sorted(hits, key=lambda h: (h.priority, -h.score)):
            cost = estimate_tokens(hit.text) + 30
            if used + cost > self.max_context_tokens:
                break
            number += 1
            header = f"[{number}] {hit.reference}"
            if hit.heading and hit.heading.lower() not in header.lower():
                header += f" - {hit.heading}"
            header += f" ({PRIORITY_NAMES.get(hit.priority, 'unbestimmt')})"
            if hit.valid_from or hit.valid_to:
                header += f" [gueltig {hit.valid_from or '?'} bis {hit.valid_to or 'offen'}]"
            knowledge_lines.append(f"{header}\n{hit.text}")
            bundle.references.append(
                SourceReference(
                    number=number, origin="knowledge", reference=hit.reference,
                    title=hit.title, excerpt=hit.excerpt(), url=hit.url,
                    priority=hit.priority, ref_id=hit.doc_uid, score=hit.score,
                    valid_from=hit.valid_from, valid_to=hit.valid_to,
                    fetched_at=hit.fetched_at,
                )
            )
            bundle.knowledge_hits.append(hit)
            used += cost
        if knowledge_lines:
            bundle.knowledge_block = "\n\n".join(knowledge_lines)

        bundle.used_tokens = used
        return bundle


def _shorten(text: str, length: int = 320) -> str:
    flat = " ".join((text or "").split())
    return flat if len(flat) <= length else flat[: length - 1].rstrip() + "…"


_CITATION = re.compile(r"\[(\d{1,2})\]")


def cited_numbers(text: str) -> set[int]:
    """Welche Fundstellennummern hat das Modell tatsaechlich zitiert?"""
    return {int(m) for m in _CITATION.findall(text or "")}
