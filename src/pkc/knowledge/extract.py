"""Extraktion von Fachtext aus Rohdokumenten (Masterprompt 28).

Ein gespeicherter Link ist keine Wissensbasis - hier entsteht aus dem
Originaldokument der normalisierte, durchsuchbare Text mit Struktur
(Ueberschrift, Fundstelle) und Metadaten.

Unterstuetzt ohne externe Abhaengigkeiten:
* HTML  (html.parser der Standardbibliothek)
* XML   (ElementTree), inklusive des Normen-XML von "Gesetze im Internet"
* ZIP   (z.B. xml.zip einer Norm)
* Text / Markdown

Optional (nur wenn ``pypdf`` installiert ist):
* PDF - fehlt die Bibliothek, wird das ehrlich als nicht unterstuetzt
  gemeldet, statt leeren Text vorzutaeuschen.
"""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any
from xml.etree import ElementTree as ET


class ExtractionError(RuntimeError):
    """Der Inhalt konnte nicht in Text ueberfuehrt werden."""


@dataclass
class Section:
    """Ein sinnvoll abgegrenzter Abschnitt (z.B. ein Paragraph)."""

    heading: str
    text: str
    citation: str = ""
    level: int = 1
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedDocument:
    title: str
    sections: list[Section]
    format: str
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        parts = []
        for section in self.sections:
            head = section.citation or section.heading
            parts.append(f"{head}\n{section.text}".strip() if head else section.text)
        return "\n\n".join(p for p in parts if p.strip())

    @property
    def char_count(self) -> int:
        return sum(len(s.text) for s in self.sections)


# --------------------------------------------------------------- Normalisierung
_WS = re.compile(r"[ \t   ]+")
_MULTI_NL = re.compile(r"\n{3,}")
_SOFT_HYPHEN = "­"


def normalize_text(text: str) -> str:
    """Vereinheitlicht Whitespace und Unicode - ohne den Inhalt zu veraendern."""
    text = unicodedata.normalize("NFC", text or "")
    text = text.replace(_SOFT_HYPHEN, "").replace("\r\n", "\n").replace("\r", "\n")
    text = _WS.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _MULTI_NL.sub("\n\n", text).strip()


# ----------------------------------------------------------------------- HTML
_SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "nav", "footer", "form", "iframe"}
_BLOCK_TAGS = {
    "p", "div", "section", "article", "br", "li", "tr", "td", "th", "table",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "dd", "dt",
}
_HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}


class _HtmlToText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title = ""
        self._skip = 0
        self._in_title = False
        self._heading: int | None = None
        self.headings: list[tuple[int, int]] = []  # (Position im parts-Index, Level)

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _SKIP_TAGS:
            self._skip += 1
            return
        if tag == "title":
            self._in_title = True
        if tag in _HEADING_TAGS:
            self._heading = _HEADING_TAGS[tag]
            self.parts.append("\n")
            self.headings.append((len(self.parts), self._heading))
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
            return
        if tag == "title":
            self._in_title = False
        if tag in _HEADING_TAGS:
            self._heading = None
            self.parts.append("\n")
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:          # <title> liegt in <head> und wird gebraucht
            self.title += data
            return
        if self._skip:
            return
        if data.strip():
            self.parts.append(data)


def extract_html(raw: bytes | str, charset_hint: str = "utf-8") -> ExtractedDocument:
    html = raw if isinstance(raw, str) else _decode(raw, charset_hint)
    parser = _HtmlToText()
    parser.feed(html)
    parser.close()

    heading_positions = dict(parser.headings)
    sections: list[Section] = []
    current_heading = ""
    current_level = 1
    buffer: list[str] = []

    for index, part in enumerate(parser.parts):
        if index in heading_positions:
            text = normalize_text("".join(buffer))
            if text:
                sections.append(Section(current_heading, text, level=current_level))
            buffer = []
            current_heading = normalize_text(part)
            current_level = heading_positions[index]
            continue
        buffer.append(part)

    text = normalize_text("".join(buffer))
    if text:
        sections.append(Section(current_heading, text, level=current_level))
    if not sections:
        # Beobachtet bei der EuGH-Rechtsprechungsrecherche: der Eintrag zeigte
        # auf eine Suchmaske, die ihren Inhalt erst per JavaScript nachlaedt.
        # Ein reiner HTML-Abruf sieht dort nichts. Das ist kein Fehler des
        # Abrufs, sondern ein falsch gewaehlter Einstiegspunkt - und die
        # Meldung soll das sagen, statt nur "kein Text".
        hinweis = ""
        if "<script" in html.lower() and len(html) > 2000:
            hinweis = (" Die Seite besteht im Wesentlichen aus Skripten - sie "
                       "baut ihren Inhalt vermutlich erst im Browser auf "
                       "(etwa eine Suchmaske). Der Eintrag im Quellenregister "
                       "sollte auf eine Seite mit dem eigentlichen Inhalt "
                       "zeigen, nicht auf das Suchformular.")
        raise ExtractionError("HTML enthielt keinen verwertbaren Text." + hinweis)

    title = normalize_text(parser.title) or (sections[0].heading if sections[0].heading else "")
    return ExtractedDocument(title=title, sections=sections, format="html")


def _decode(raw: bytes, charset_hint: str = "utf-8") -> str:
    match = re.search(rb'charset=["\']?([\w\-]+)', raw[:4096], re.IGNORECASE)
    candidates = []
    if match:
        candidates.append(match.group(1).decode("ascii", "ignore"))
    candidates += [charset_hint, "utf-8", "cp1252", "latin-1"]
    for encoding in candidates:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


# ------------------------------------------------------------------ Normen-XML
def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _element_text(element: ET.Element) -> str:
    return normalize_text("".join(element.itertext()))


def extract_gii_xml(raw: bytes) -> ExtractedDocument:
    """Normen-XML von 'Gesetze im Internet' (ein <norm> je Paragraph)."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ExtractionError(f"XML nicht lesbar: {exc}") from exc

    norms = [e for e in root.iter() if _local(e.tag) == "norm"]
    if not norms:
        raise ExtractionError("XML enthaelt keine <norm>-Elemente.")

    doc_title = ""
    abbreviation = ""
    sections: list[Section] = []

    for norm in norms:
        meta_el = next((c for c in norm if _local(c.tag) == "metadaten"), None)
        enbez = titel = jurabk = amtabk = ""
        if meta_el is not None:
            for child in meta_el.iter():
                name = _local(child.tag)
                value = normalize_text("".join(child.itertext()))
                if name == "enbez" and not enbez:
                    enbez = value
                elif name == "titel" and not titel:
                    titel = value
                elif name == "jurabk" and not jurabk:
                    jurabk = value
                elif name == "amtabk" and not amtabk:
                    amtabk = value
        abbreviation = abbreviation or amtabk or jurabk
        if not doc_title and titel and not enbez:
            doc_title = titel

        body_el = next((c for c in norm if _local(c.tag) == "textdaten"), None)
        body = _element_text(body_el) if body_el is not None else ""
        if not body.strip():
            continue

        citation = ""
        if enbez:
            citation = f"{enbez} {abbreviation}".strip()
        heading = " ".join(p for p in (enbez, titel) if p).strip()
        sections.append(
            Section(heading=heading or citation, text=body, citation=citation,
                    meta={"enbez": enbez, "abk": abbreviation})
        )

    if not sections:
        raise ExtractionError("Normen-XML enthielt keinen Textkoerper.")
    return ExtractedDocument(
        title=doc_title or abbreviation or "Norm",
        sections=sections,
        format="gii_xml",
        meta={"abbreviation": abbreviation, "norm_count": len(sections)},
    )


def extract_xml(raw: bytes) -> ExtractedDocument:
    """Allgemeines XML: erst Normen-XML versuchen, sonst Volltext."""
    try:
        return extract_gii_xml(raw)
    except ExtractionError:
        pass
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ExtractionError(f"XML nicht lesbar: {exc}") from exc
    text = _element_text(root)
    if not text:
        raise ExtractionError("XML enthielt keinen Text.")
    return ExtractedDocument(title=_local(root.tag), sections=[Section("", text)], format="xml")


# ------------------------------------------------------------------------ ZIP
def extract_zip(raw: bytes) -> ExtractedDocument:
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as exc:
        raise ExtractionError(f"ZIP nicht lesbar: {exc}") from exc
    names = [n for n in archive.namelist() if not n.endswith("/")]
    preferred = [n for n in names if n.lower().endswith((".xml", ".html", ".htm", ".txt"))]
    if not preferred:
        raise ExtractionError(f"ZIP enthielt keine verwertbare Datei ({len(names)} Eintraege).")
    member = preferred[0]
    payload = archive.read(member)
    document = extract(payload, fmt=_format_from_name(member))
    document.meta.setdefault("zip_member", member)
    return document


# ------------------------------------------------------------------------ PDF
def extract_pdf(raw: bytes) -> ExtractedDocument:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise ExtractionError(
            "PDF-Extraktion nicht moeglich: das optionale Paket 'pypdf' ist in dieser "
            "Installation nicht vorhanden. Das Dokument wurde NICHT ausgewertet."
        ) from exc
    try:
        reader = PdfReader(io.BytesIO(raw))
    except Exception as exc:  # pypdf wirft verschiedene Fehlertypen
        raise ExtractionError(f"PDF nicht lesbar: {exc}") from exc
    sections: list[Section] = []
    for number, page in enumerate(reader.pages, start=1):
        try:
            text = normalize_text(page.extract_text() or "")
        except Exception:  # pragma: no cover - beschaedigte Seite
            text = ""
        if text:
            sections.append(Section(heading=f"Seite {number}", text=text, meta={"page": number}))
    if not sections:
        raise ExtractionError(
            "PDF enthielt keinen extrahierbaren Text (vermutlich ein Scan ohne OCR)."
        )
    title = ""
    try:
        title = normalize_text(str((reader.metadata or {}).get("/Title", "")))
    except Exception:  # pragma: no cover
        title = ""
    return ExtractedDocument(title=title, sections=sections, format="pdf",
                             meta={"pages": len(reader.pages)})


# ----------------------------------------------------------------------- Text
def extract_plain(raw: bytes | str) -> ExtractedDocument:
    text = raw if isinstance(raw, str) else _decode(raw)
    text = normalize_text(text)
    if not text:
        raise ExtractionError("Datei enthielt keinen Text.")
    sections: list[Section] = []
    heading = ""
    level = 1
    title = ""
    buffer: list[str] = []
    for line in text.split("\n"):
        if line.startswith("#"):
            body = "\n".join(buffer).strip()
            if body:
                sections.append(Section(heading, body, level=level))
            buffer = []
            level = len(line) - len(line.lstrip("#"))
            heading = line.lstrip("#").strip()
            if not title and level == 1:
                title = heading
            continue
        buffer.append(line)
    body = "\n".join(buffer).strip()
    if body or not sections:
        sections.append(Section(heading, body, level=level))
    kept = [s for s in sections if s.text.strip()]
    return ExtractedDocument(
        title=title or (kept[0].heading if kept else ""), sections=kept, format="text"
    )


# ------------------------------------------------------------------ Verteiler
def _format_from_name(name: str) -> str:
    low = name.lower()
    if low.endswith(".zip"):
        return "zip"
    if low.endswith((".xml", ".rss")):
        return "xml"
    if low.endswith((".html", ".htm")):
        return "html"
    if low.endswith(".pdf"):
        return "pdf"
    return "text"


def sniff_format(raw: bytes, content_type: str = "", url: str = "") -> str:
    head = raw[:512].lstrip()
    if raw[:4] == b"PK\x03\x04":
        return "zip"
    if raw[:5] == b"%PDF-":
        return "pdf"
    lower_ct = (content_type or "").lower()
    if "pdf" in lower_ct:
        return "pdf"
    if "zip" in lower_ct:
        return "zip"
    if "xml" in lower_ct or head[:5] == b"<?xml":
        return "xml"
    if "html" in lower_ct or re.match(rb"<!doctype html|<html", head, re.IGNORECASE):
        return "html"
    if url:
        guess = _format_from_name(url.split("?", 1)[0])
        if guess != "text":
            return guess
    if b"<" in head and b">" in head:
        return "html"
    return "text"


def extract(
    raw: bytes | str,
    content_type: str = "",
    fmt: str = "auto",
    url: str = "",
) -> ExtractedDocument:
    """Waehlt den passenden Extraktor und liefert normalisierten Text."""
    if isinstance(raw, str):
        raw_bytes = raw.encode("utf-8")
    else:
        raw_bytes = raw
    if not raw_bytes.strip():
        raise ExtractionError("Leeres Dokument.")

    chosen = fmt if fmt not in ("auto", "", None) else sniff_format(raw_bytes, content_type, url)
    if chosen == "xml_zip":
        chosen = "zip"
    dispatch = {
        "zip": extract_zip,
        "pdf": extract_pdf,
        "xml": extract_xml,
        "gii_xml": extract_gii_xml,
        "html": extract_html,
        "text": extract_plain,
    }
    handler = dispatch.get(chosen)
    if handler is None:
        raise ExtractionError(f"Unbekanntes Format: {chosen!r}")
    document = handler(raw_bytes)
    _reject_if_not_text(document)
    document.meta.setdefault("detected_format", chosen)
    return document


#: Anteil unlesbarer Zeichen, ab dem ein "Text" keiner mehr ist.
_MAX_JUNK_RATIO = 0.2


def _reject_if_not_text(document: ExtractedDocument, sample: int = 4000) -> None:
    """Verhindert, dass Binaerdaten als Fachwissen in den Index geraten.

    Erkennt eine Datei weder ZIP noch PDF noch XML, landet sie beim
    HTML-Extraktor und ergaebe dort scheinbaren "Text". Ein solcher Eintrag
    waere in der Recherche wertlos und in der Quellenanzeige irrefuehrend.
    """
    text = document.text[:sample]
    if not text.strip():
        raise ExtractionError("Nach der Aufbereitung blieb kein Text uebrig.")
    junk = sum(
        1 for char in text
        if not (char.isprintable() or char in "\n\t ")
        or char in "\ufffd"
    )
    ratio = junk / len(text)
    if ratio > _MAX_JUNK_RATIO:
        raise ExtractionError(
            f"Der Inhalt ist kein lesbarer Text ({ratio:.0%} unlesbare Zeichen) - "
            "vermutlich eine Binaerdatei oder ein nicht unterstuetztes Format. "
            "Es wurde nichts uebernommen."
        )
