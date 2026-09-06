"""Welche Dateiformate erzeugt werden koennen (Erweiterung E4).

Alle hier eingetragenen Formate entstehen **offline** und ohne installiertes
Office. Neue Formate koennen ohne Aenderung am Kern hinzukommen: ein
Dateihandler wird angemeldet, mehr braucht es nicht (E4, Abschnitt
Plugin-Erweiterbarkeit).
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Callable

from .modell import Dokument
from .ooxml import docx_bytes, pptx_bytes, xlsx_bytes
from .pdf import pdf_bytes


class ArtefaktFehler(RuntimeError):
    """Die Datei konnte nicht erzeugt werden - mit verstaendlichem Grund."""


@dataclass(frozen=True)
class Schreiber:
    kuerzel: str
    endung: str
    bezeichnung: str
    funktion: Callable[[Dokument], bytes]
    #: Wofuer das Format gedacht ist - erscheint in der Auswahl.
    zweck: str = ""


def _txt(dokument: Dokument) -> bytes:
    return dokument.als_text().encode("utf-8")


def _md(dokument: Dokument) -> bytes:
    return dokument.als_markdown().encode("utf-8")


def _json(dokument: Dokument) -> bytes:
    daten = {
        "titel": dokument.titel,
        "angaben": dokument.angaben,
        "bloecke": [
            {k: v for k, v in {
                "art": b.art, "text": b.text, "ebene": b.ebene,
                "punkte": b.punkte, "zeilen": b.zeilen,
            }.items() if v not in ("", [], None)}
            for b in dokument.bloecke
        ],
    }
    return json.dumps(daten, ensure_ascii=False, indent=2).encode("utf-8")


def _csv(dokument: Dokument) -> bytes:
    """Erste Tabelle als CSV - sonst der Text zeilenweise.

    Trennzeichen ist das Semikolon und am Anfang steht eine Byte-Order-Marke:
    so oeffnet Excel in deutscher Einstellung die Datei richtig, statt alles
    in eine Spalte zu legen.
    """
    puffer = io.StringIO()
    schreiber = csv.writer(puffer, delimiter=";", lineterminator="\r\n")
    tabellen = dokument.tabellen
    if tabellen:
        for zeile in tabellen[0]:
            schreiber.writerow(zeile)
    else:
        if dokument.titel:
            schreiber.writerow([dokument.titel])
        for zeile in dokument.als_text().splitlines():
            schreiber.writerow([zeile])
    return "﻿".encode("utf-8") + puffer.getvalue().encode("utf-8")


#: Angemeldete Formate. Reihenfolge = Reihenfolge in der Auswahl.
_SCHREIBER: dict[str, Schreiber] = {}


def registrieren(schreiber: Schreiber, ersetzen: bool = False) -> None:
    """Meldet einen Dateihandler an (E4: FILE_HANDLER_...).

    Ein vorhandenes Format wird nicht stillschweigend ueberschrieben - sonst
    koennte ein Zusatzmodul die Ausgabe eines geprueften Formats aendern,
    ohne dass es jemand merkt.
    """
    kuerzel = schreiber.kuerzel.lower().strip()
    if not kuerzel:
        raise ValueError("Ein Dateihandler braucht ein Kuerzel.")
    if kuerzel in _SCHREIBER and not ersetzen:
        raise ValueError(f"Fuer '{kuerzel}' ist bereits ein Handler angemeldet.")
    _SCHREIBER[kuerzel] = schreiber


def abmelden(kuerzel: str) -> None:
    _SCHREIBER.pop(kuerzel.lower().strip(), None)


def formate() -> list[Schreiber]:
    return list(_SCHREIBER.values())


def hole(kuerzel: str) -> Schreiber:
    schreiber = _SCHREIBER.get((kuerzel or "").lower().strip().lstrip("."))
    if schreiber is None:
        moeglich = ", ".join(sorted(_SCHREIBER))
        raise ArtefaktFehler(
            f"Das Format '{kuerzel}' ist nicht bekannt. Moeglich sind: {moeglich}."
        )
    return schreiber


for _eintrag in (
    Schreiber("txt", ".txt", "Textdatei", _txt, "einfacher Text, ueberall lesbar"),
    Schreiber("md", ".md", "Markdown", _md, "Text mit Gliederung, versionierbar"),
    Schreiber("json", ".json", "JSON", _json, "maschinenlesbar, fuer Weiterverarbeitung"),
    Schreiber("csv", ".csv", "CSV-Tabelle", _csv, "Tabelle fuer Excel und Buchhaltung"),
    Schreiber("xlsx", ".xlsx", "Excel-Arbeitsmappe", xlsx_bytes, "Auswertungen, Buchungslisten"),
    Schreiber("docx", ".docx", "Word-Dokument", docx_bytes, "Berichte, Dokumentationen"),
    Schreiber("pptx", ".pptx", "PowerPoint-Praesentation", pptx_bytes, "Kurzberichte, Vorlagen"),
    Schreiber("pdf", ".pdf", "PDF-Bericht", pdf_bytes, "unveraenderlicher Bericht zum Weitergeben"),
):
    registrieren(_eintrag)
