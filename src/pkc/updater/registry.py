"""Maschinenlesbares Quellenregister (Masterprompt 27).

Das Register beschreibt *woher* Fachwissen stammt, mit welcher Prioritaet es
gilt (Quellenhierarchie nach Abschnitt 26) und wie es abgerufen wird.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import re

from ..config import load_mapping

class RegistryError(ValueError):
    """Das Quellenregister ist fehlerhaft oder unsicher."""


#: Kennungen werden zu Verzeichnis- und Dateinamen. Sie duerfen deshalb weder
#: Pfadtrenner noch ".." enthalten - sonst koennte ein weitergegebenes
#: Quellenregister Dateien ausserhalb des vorgesehenen Bereichs anlegen.
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,120}$")


def check_identifier(value: str, feld: str) -> str:
    """Prueft eine Kennung, die spaeter als Dateiname dient."""
    if not _SAFE_ID.match(value or "") or ".." in value:
        raise RegistryError(
            f"Unzulaessige {feld}: {value!r}. Erlaubt sind Buchstaben, Ziffern, "
            "Punkt, Bindestrich und Unterstrich - keine Pfadangaben."
        )
    return value

#: Quellenhierarchie nach Masterprompt 26 (1 = hoechste Prioritaet).
PRIORITY_LABELS = {
    1: "Gesetze, Verordnungen, amtliche Rechtsquellen",
    2: "Amtliche Verwaltungsanweisungen",
    3: "Hoechstrichterliche Rechtsprechung",
    4: "Behoerdeninformationen",
    5: "Seriöse Fachsekundaerquellen",
}


@dataclass
class DocumentRef:
    """Ein konkret abrufbares Dokument einer Quelle."""

    doc_uid: str
    url: str
    title: str
    kind: str = "law"
    citation: str = ""
    format: str = "auto"          # auto | xml | xml_zip | html | pdf | text
    licence: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Source:
    source_id: str
    name: str
    publisher: str
    priority: int
    kind: str
    base_url: str
    fetcher: str = "static"        # static | toc_xml | rss | sitemap
    licence: str = ""
    enabled: bool = True
    notes: str = ""
    verified: bool = False         # URL in dieser Umgebung nicht geprueft?
    documents: list[DocumentRef] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def priority_label(self) -> str:
        return PRIORITY_LABELS.get(self.priority, "unbestimmt")

    @classmethod
    def from_dict(cls, data: dict) -> "Source":
        docs = [
            DocumentRef(
                doc_uid=d["doc_uid"], url=d["url"], title=d["title"],
                kind=d.get("kind", data.get("kind", "law")),
                citation=d.get("citation", ""), format=d.get("format", "auto"),
                licence=d.get("licence", data.get("licence", "")),
                meta=d.get("meta", {}),
            )
            for d in data.get("documents", [])
        ]
        return cls(
            source_id=data["source_id"], name=data["name"],
            publisher=data.get("publisher", ""), priority=int(data.get("priority", 5)),
            kind=data.get("kind", "secondary"), base_url=data.get("base_url", ""),
            fetcher=data.get("fetcher", "static"), licence=data.get("licence", ""),
            enabled=bool(data.get("enabled", True)), notes=data.get("notes", ""),
            verified=bool(data.get("verified", False)), documents=docs,
            meta=data.get("meta", {}),
        )

    def as_dict(self) -> dict:
        return {
            "source_id": self.source_id, "name": self.name, "publisher": self.publisher,
            "priority": self.priority, "kind": self.kind, "base_url": self.base_url,
            "fetcher": self.fetcher, "licence": self.licence, "enabled": self.enabled,
            "notes": self.notes, "verified": self.verified, "meta": self.meta,
            "documents": [
                {
                    "doc_uid": d.doc_uid, "url": d.url, "title": d.title, "kind": d.kind,
                    "citation": d.citation, "format": d.format, "licence": d.licence,
                    "meta": d.meta,
                }
                for d in self.documents
            ],
        }


class SourceRegistry:
    """Laedt und validiert das Quellenregister."""

    def __init__(self, sources: Iterable[Source], path: Path | None = None, meta: dict | None = None):
        self.sources = list(sources)
        self.path = path
        self.meta = meta or {}
        self._validate()

    @classmethod
    def load(cls, path: Path) -> "SourceRegistry":
        if not path.is_file():
            raise RegistryError(f"Quellenregister nicht gefunden: {path}")
        data = load_mapping(path)
        raw = data.get("sources")
        if not isinstance(raw, list):
            raise RegistryError("Quellenregister enthaelt keine Liste 'sources'.")
        meta = {k: v for k, v in data.items() if k != "sources"}
        return cls([Source.from_dict(s) for s in raw], path, meta)

    def _validate(self) -> None:
        seen_sources: set[str] = set()
        seen_docs: set[str] = set()
        for source in self.sources:
            if not source.source_id:
                raise RegistryError("Quelle ohne source_id.")
            check_identifier(source.source_id, "source_id")
            if source.source_id in seen_sources:
                raise RegistryError(f"Doppelte source_id: {source.source_id}")
            seen_sources.add(source.source_id)
            if source.priority not in PRIORITY_LABELS:
                raise RegistryError(
                    f"{source.source_id}: Prioritaet {source.priority} liegt ausserhalb 1-5."
                )
            for doc in source.documents:
                check_identifier(doc.doc_uid, "doc_uid")
                if doc.doc_uid in seen_docs:
                    raise RegistryError(f"Doppelte doc_uid: {doc.doc_uid}")
                seen_docs.add(doc.doc_uid)
                if not doc.url.startswith(("http://", "https://")):
                    raise RegistryError(f"{doc.doc_uid}: unzulaessige URL {doc.url!r}")

    # -- Zugriff -------------------------------------------------------
    def __iter__(self):
        return iter(self.sources)

    def __len__(self) -> int:
        return len(self.sources)

    def get(self, source_id: str) -> Source | None:
        for source in self.sources:
            if source.source_id == source_id:
                return source
        return None

    def enabled_sources(self) -> list[Source]:
        return [s for s in self.sources if s.enabled]

    def all_documents(self) -> list[tuple[Source, DocumentRef]]:
        return [(s, d) for s in self.enabled_sources() for d in s.documents]

    def document_count(self) -> int:
        return sum(len(s.documents) for s in self.sources)

    def save(self, path: Path | None = None) -> Path:
        target = path or self.path
        if target is None:
            raise RegistryError("Kein Zielpfad fuer das Quellenregister angegeben.")
        payload = dict(self.meta)
        payload["sources"] = [s.as_dict() for s in self.sources]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return target
