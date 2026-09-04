"""Zerlegung normalisierter Dokumente in durchsuchbare Abschnitte.

Leitgedanke: ein Chunk soll fachlich zitierfaehig bleiben.  Ein Paragraph
eines Gesetzes wird daher moeglichst *nicht* zerschnitten; nur zu lange
Abschnitte werden an Absatzgrenzen geteilt, mit Ueberlappung fuer den Kontext.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .extract import ExtractedDocument, Section


def estimate_tokens(text: str) -> int:
    """Grobe, aber stabile Schaetzung (deutsche Texte: ~3,7 Zeichen/Token)."""
    if not text:
        return 0
    return max(1, int(len(text) / 3.7))


@dataclass
class Chunk:
    ord: int
    text: str
    heading: str = ""
    citation: str = ""
    tokens: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _split_long(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    """Teilt zu langen Text an Absatz-, sonst an Satzgrenzen."""
    if len(text) <= max_chars:
        return [text]

    units = [u for u in _PARAGRAPH_SPLIT.split(text) if u.strip()]
    if len(units) == 1:
        units = [u for u in _SENTENCE_SPLIT.split(text) if u.strip()]
    if len(units) == 1:  # eine sehr lange Einheit: harter Schnitt
        return [
            text[i:i + max_chars]
            for i in range(0, len(text), max(1, max_chars - overlap_chars))
        ]

    parts: list[str] = []
    buffer = ""
    for unit in units:
        candidate = f"{buffer}\n\n{unit}".strip() if buffer else unit
        if len(candidate) <= max_chars or not buffer:
            buffer = candidate
            if len(buffer) > max_chars:      # einzelne Einheit zu gross
                parts.extend(_split_long(buffer, max_chars, overlap_chars))
                buffer = ""
            continue
        parts.append(buffer)
        tail = buffer[-overlap_chars:] if overlap_chars else ""
        buffer = f"{tail}\n\n{unit}".strip() if tail else unit
    if buffer.strip():
        parts.append(buffer)
    return parts


def chunk_sections(
    sections: Iterable[Section],
    max_tokens: int = 400,
    overlap_tokens: int = 60,
    min_chars: int = 40,
) -> list[Chunk]:
    max_chars = max(200, int(max_tokens * 3.7))
    overlap_chars = max(0, int(overlap_tokens * 3.7))
    chunks: list[Chunk] = []
    index = 0
    for section in sections:
        body = (section.text or "").strip()
        if len(body) < min_chars and not section.citation:
            continue
        for piece in _split_long(body, max_chars, overlap_chars):
            piece = piece.strip()
            if not piece:
                continue
            chunks.append(
                Chunk(
                    ord=index, text=piece, heading=section.heading,
                    citation=section.citation, tokens=estimate_tokens(piece),
                    meta=dict(section.meta),
                )
            )
            index += 1
    return chunks


def chunk_document(
    document: ExtractedDocument,
    max_tokens: int = 400,
    overlap_tokens: int = 60,
) -> list[Chunk]:
    return chunk_sections(document.sections, max_tokens, overlap_tokens)
