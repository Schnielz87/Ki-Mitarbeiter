"""Erkennung dauerhaft relevanter Unternehmensinformationen (Masterprompt 15).

Zwei Stufen:

1. **Regelbasiert** (immer verfuegbar, auch offline, deterministisch und
   testbar).  Erkennt typische deutsche Formulierungen fuer Dauerregeln.
2. **Modellgestuetzt** (optional): ein LLM kann zusaetzliche Kandidaten
   vorschlagen.  Die Regelstufe bleibt die Grundlage, damit die Funktion nie
   vom Modell abhaengt.

Grundsatz: Bei Unsicherheit wird *gefragt*, nicht stillschweigend gespeichert.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .schema_keys import CATEGORIES

#: Formulierungen, die auf Dauerhaftigkeit hindeuten.
DURABLE_MARKERS = (
    "grundsaetzlich", "grundsätzlich", "immer", "stets", "in der regel",
    "standardmaessig", "standardmäßig", "generell", "kuenftig", "künftig",
    "ab sofort", "wir verwenden", "wir nutzen", "wir arbeiten mit",
    "unsere regel", "unsere vorgabe", "bei uns gilt", "es gilt",
    "merke dir", "merk dir", "bitte merken", "dauerhaft", "unser unternehmen",
    "wir buchen", "wir sind", "unser", "unsere", "muessen", "müssen",
)

#: Formulierungen, die auf einen Einzelfall hindeuten.
TEMPORARY_MARKERS = (
    "diese rechnung", "dieser beleg", "diesen vorgang", "einmalig",
    "pruefe mal", "prüfe mal", "kurz nachschauen", "heute nur", "testweise",
    "was waere", "was wäre", "beispiel:", "angenommen",
)

QUESTION_STARTERS = (
    "wie", "was", "warum", "wieso", "welche", "welcher", "welches", "wann",
    "wo", "kann", "koennen", "können", "darf", "duerfen", "dürfen", "ist",
    "sind", "muss", "gibt es", "erklaere", "erkläre", "pruefe", "prüfe",
    "berechne", "erstelle", "zeige", "buche",
)


@dataclass
class CaptureCandidate:
    """Ein Vorschlag, etwas dauerhaft zu speichern."""

    mem_key: str
    category: str
    title: str
    content: str
    confidence: float
    rationale: str
    source_text: str = ""

    def question(self) -> str:
        return (
            f"Soll ich dauerhaft merken: „{self.content}“ "
            f"(Kategorie: {CATEGORIES.get(self.category, self.category)})?"
        )


@dataclass
class _Rule:
    name: str
    pattern: re.Pattern[str]
    mem_key: str
    category: str
    title: str
    confidence: float
    template: str = "{match}"
    #: Zusaetzliche Bedingung an den Satz (verhindert Fehlzuordnungen).
    requires: re.Pattern[str] | None = None
    #: Praefixe, die aus dem Treffer entfernt werden.
    strip_prefix: re.Pattern[str] | None = None


def _r(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.UNICODE)


RULES: tuple[_Rule, ...] = (
    _Rule(
        "kontenrahmen",
        _r(r"\b(SKR\s?-?\s?(03|04|07|14|49|51|81))\b"),
        "company.chart_of_accounts", "accounting", "Kontenrahmen", 0.9,
        "Das Unternehmen verwendet den Kontenrahmen {match}.",
    ),
    _Rule(
        "erp",
        _r(r"\b(SAP(?:\s+S/?4\s*HANA)?|DATEV(?:\s+\w+)?|Wilken(?:\s+\w+)?|Lexware|Navision|"
           r"Business\s?Central|Odoo|Sage|Addison|Agenda|JTL|Microsoft\s+Dynamics)\b"),
        "company.erp", "erp", "ERP-/Buchhaltungssystem", 0.75,
        "Eingesetztes System: {match}.",
    ),
    _Rule(
        "ust_id",
        _r(r"\bDE\s?\d{9}\b"),
        "company.vat_id", "tax", "USt-IdNr.", 0.9,
        "Die USt-IdNr. des Unternehmens lautet {match}.",
    ),
    _Rule(
        "kleinunternehmer",
        _r(r"\bKleinunternehmer(regelung)?\b"),
        "company.vat_status", "tax", "Umsatzsteuerstatus", 0.7,
        "Umsatzsteuerlicher Status betrifft die Kleinunternehmerregelung (§ 19 UStG).",
    ),
    _Rule(
        "freigabegrenze",
        _r(r"(?:ab|ueber|über|groesser|größer)\s*(?:als\s*)?([\d.\s]{1,12}(?:,\d{1,2})?)\s*"
           r"(?:EUR|Euro|€)[^.]{0,80}?(freigabe|freigegeben|genehmig\w*|unterschrift)"),
        "company.approval_rules", "approval", "Freigaberegel", 0.85,
        "{sentence}",
    ),
    _Rule(
        "wirtschaftsjahr",
        _r(r"(Wirtschaftsjahr|Geschaeftsjahr|Geschäftsjahr)\b[^.]{0,80}"),
        "company.fiscal_year", "accounting", "Wirtschaftsjahr", 0.7,
        "{sentence}",
    ),
    _Rule(
        "rechtsform",
        _r(r"\b([A-ZÄÖÜ][\wÄÖÜäöüß&.\- ]{1,40}?\s(?:GmbH\s*&\s*Co\.\s*KG|GmbH|AG|UG(?:\s*\(haftungsbeschraenkt\))?|"
           r"KG|OHG|GbR|e\.K\.|SE))\b"),
        "company.name", "profile", "Unternehmensname und Rechtsform", 0.7,
        "Unternehmen: {match}.",
        # nur wenn sich der Satz erkennbar auf das eigene Unternehmen bezieht
        requires=_r(r"\b(wir\s+sind|wir\s+hei(?:ss|ß)en|unser(?:e)?\s+(?:firma|unternehmen|gesellschaft)|"
                    r"firmier\w*|unser\s+betrieb)\b"),
        strip_prefix=_r(r"^(?:wir\s+sind|unser(?:e)?\s+(?:firma|unternehmen|gesellschaft|betrieb)"
                        r"(?:\s+(?:ist|hei(?:ss|ß)t))?)?\s*(?:die|der|das)?\s*"),
    ),
    _Rule(
        "kostenstelle",
        _r(r"\bKostenstelle[n]?\b[^.]{0,80}"),
        "company.cost_centers", "accounting", "Kostenstellen", 0.65,
        "{sentence}",
    ),
    _Rule(
        "steuerschluessel",
        _r(r"\bSteuerschl(?:ue|ü)ssel\b[^.]{0,80}"),
        "company.tax_keys", "accounting", "Steuerschluessel", 0.7,
        "{sentence}",
    ),
)

EXPLICIT_PATTERN = _r(
    r"(?:merke\s+dir|merk\s+dir|bitte\s+merken|speichere|notiere)\s*[:,]?\s*(?P<body>.+)"
)


#: Abkuerzungen, nach denen ein Punkt *kein* Satzende ist.
ABBREVIATIONS = (
    "co", "nr", "abs", "art", "bzw", "ca", "ggf", "evtl", "inkl", "exkl",
    "z", "b", "u", "a", "d", "h", "i", "s", "v", "vgl", "etc", "usw", "mio",
    "mrd", "tsd", "str", "az", "rz", "bfh", "bmf", "ust", "estg", "hgb",
    "gmbh", "ohg", "kg", "ek", "ziff", "lit", "buchst", "s", "f", "ff",
)
_ABBR_RE = re.compile(
    r"(?:^|[\s(])(?:" + "|".join(ABBREVIATIONS) + r")\.$", re.IGNORECASE | re.UNICODE
)


def split_sentences(text: str) -> list[str]:
    """Satztrennung mit Schutz gaengiger deutscher Abkuerzungen.

    "Beispiel Bau GmbH & Co. KG." bleibt ein Satz, "Wir nutzen SKR03. Bitte
    buchen." wird getrennt.
    """
    text = (text or "").strip()
    if not text:
        return []
    parts: list[str] = []
    buffer: list[str] = []
    for piece in re.split(r"(?<=[.!?;\n])(\s+)", text):
        if piece.isspace():
            candidate = "".join(buffer)
            stripped = candidate.rstrip()
            single_letter = re.search(r"(?:^|\s)[A-Za-zÄÖÜäöü]\.$", stripped)
            if stripped.endswith((".",)) and (_ABBR_RE.search(stripped) or single_letter):
                buffer.append(piece)
                continue
            if stripped:
                parts.append(stripped)
            buffer = []
            continue
        buffer.append(piece)
    tail = "".join(buffer).strip()
    if tail:
        parts.append(tail)
    return parts


def _looks_like_question(sentence: str) -> bool:
    low = sentence.strip().lower()
    if low.endswith("?"):
        return True
    first = low.split(" ", 1)[0] if low else ""
    return first in QUESTION_STARTERS


def _slug(text: str, limit: int = 40) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", text.lower().strip())
    return cleaned.strip("_")[:limit] or "notiz"


class MemoryCapture:
    """Erzeugt Speicherkandidaten aus einer Benutzernachricht."""

    def __init__(self, min_confidence: float = 0.55):
        self.min_confidence = float(min_confidence)

    def analyse(self, text: str, existing_keys: Iterable[str] = ()) -> list[CaptureCandidate]:
        text = (text or "").strip()
        if len(text) < 8:
            return []
        existing = set(existing_keys)
        candidates: dict[str, CaptureCandidate] = {}

        explicit = EXPLICIT_PATTERN.search(text)
        if explicit:
            body = explicit.group("body").strip().rstrip(".")
            if body:
                key = f"company.note.{_slug(body)}"
                candidates[key] = CaptureCandidate(
                    mem_key=key, category="rule",
                    title=body[:60] if len(body) > 8 else "Merkposten",
                    content=body, confidence=0.95,
                    rationale="Ausdrueckliche Anweisung, sich etwas zu merken.",
                    source_text=text,
                )

        for sentence in split_sentences(text):
            low = sentence.lower()
            if any(marker in low for marker in TEMPORARY_MARKERS):
                continue
            if _looks_like_question(sentence) and not explicit:
                continue
            durable = any(marker in low for marker in DURABLE_MARKERS)
            for rule in RULES:
                match = rule.pattern.search(sentence)
                if not match:
                    continue
                if rule.requires is not None and not rule.requires.search(sentence):
                    continue
                confidence = rule.confidence + (0.05 if durable else -0.2)
                if rule.mem_key in existing:
                    confidence -= 0.05
                confidence = max(0.0, min(0.99, confidence))
                if confidence < self.min_confidence:
                    continue
                value = match.group(1) if match.groups() else match.group(0)
                if rule.strip_prefix is not None:
                    value = rule.strip_prefix.sub("", value.strip())
                content = rule.template.format(
                    match=value.strip(), sentence=sentence.strip().rstrip(".") + "."
                )
                previous = candidates.get(rule.mem_key)
                if previous is None or previous.confidence < confidence:
                    candidates[rule.mem_key] = CaptureCandidate(
                        mem_key=rule.mem_key, category=rule.category, title=rule.title,
                        content=content, confidence=round(confidence, 2),
                        rationale=f"Regel '{rule.name}' erkannt"
                                  + (" mit Dauerhaftigkeitsmerkmal." if durable else "."),
                        source_text=sentence,
                    )

        return sorted(candidates.values(), key=lambda c: -c.confidence)
