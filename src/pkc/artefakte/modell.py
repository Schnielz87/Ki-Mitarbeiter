"""Ein Dokument, unabhaengig vom spaeteren Dateiformat (Erweiterung E4).

Warum ein eigenes Modell: dieselbe Auswertung soll als PDF-Bericht, als
Word-Dokumentation und als Excel-Liste herauskommen koennen, ohne dass der
Fachcode drei Mal geschrieben wird. Die Formatschreiber bekommen deshalb
nicht Text, sondern **Bloecke**: Ueberschrift, Absatz, Aufzaehlung, Tabelle,
Code.

Bewusst klein: das Modell deckt ab, was in Antworten und Auswertungen eines
Buchhalters vorkommt. Es ist kein Satzsystem.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Zulaessige Blockarten.
ARTEN = ("ueberschrift", "absatz", "aufzaehlung", "tabelle", "code")


@dataclass
class Block:
    """Ein Abschnitt des Dokuments."""

    art: str
    text: str = ""
    #: Nur bei ``ueberschrift``: 1 bis 3.
    ebene: int = 1
    #: Nur bei ``aufzaehlung``: die Punkte.
    punkte: list[str] = field(default_factory=list)
    #: Nur bei ``tabelle``: erste Zeile ist die Kopfzeile.
    zeilen: list[list[str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.art not in ARTEN:
            raise ValueError(f"Unbekannte Blockart: {self.art}")


@dataclass
class Dokument:
    """Titel, Bloecke und beschreibende Angaben."""

    titel: str = ""
    bloecke: list[Block] = field(default_factory=list)
    #: Freie Angaben, die in die Dateimetadaten uebernommen werden.
    angaben: dict[str, str] = field(default_factory=dict)

    def ueberschrift(self, text: str, ebene: int = 1) -> "Dokument":
        self.bloecke.append(Block("ueberschrift", text=text, ebene=max(1, min(3, ebene))))
        return self

    def absatz(self, text: str) -> "Dokument":
        self.bloecke.append(Block("absatz", text=text))
        return self

    def aufzaehlung(self, punkte) -> "Dokument":
        self.bloecke.append(Block("aufzaehlung", punkte=[str(p) for p in punkte]))
        return self

    def tabelle(self, zeilen) -> "Dokument":
        self.bloecke.append(Block("tabelle", zeilen=[[str(z) for z in zeile] for zeile in zeilen]))
        return self

    @property
    def tabellen(self) -> list[list[list[str]]]:
        return [b.zeilen for b in self.bloecke if b.art == "tabelle"]

    def als_text(self) -> str:
        """Fuer TXT und als Grundlage der Vorschau."""
        teile: list[str] = []
        if self.titel:
            teile.append(self.titel)
            teile.append("=" * len(self.titel))
        for block in self.bloecke:
            if block.art == "ueberschrift":
                teile.append("")
                teile.append(block.text)
                teile.append(("-" if block.ebene > 1 else "=") * len(block.text))
            elif block.art == "absatz":
                teile.append("")
                teile.append(block.text)
            elif block.art == "aufzaehlung":
                teile.append("")
                teile.extend(f"* {punkt}" for punkt in block.punkte)
            elif block.art == "code":
                teile.append("")
                teile.extend(f"    {zeile}" for zeile in block.text.splitlines())
            elif block.art == "tabelle":
                teile.append("")
                teile.extend(_tabelle_als_text(block.zeilen))
        return "\n".join(teile).strip() + "\n"

    def als_markdown(self) -> str:
        teile: list[str] = []
        if self.titel:
            teile.append(f"# {self.titel}")
        for block in self.bloecke:
            if block.art == "ueberschrift":
                teile.append("")
                teile.append("#" * (block.ebene + 1) + f" {block.text}")
            elif block.art == "absatz":
                teile.append("")
                teile.append(block.text)
            elif block.art == "aufzaehlung":
                teile.append("")
                teile.extend(f"- {punkt}" for punkt in block.punkte)
            elif block.art == "code":
                teile.append("")
                teile.append("```")
                teile.append(block.text)
                teile.append("```")
            elif block.art == "tabelle" and block.zeilen:
                teile.append("")
                kopf, *rest = block.zeilen
                teile.append("| " + " | ".join(kopf) + " |")
                teile.append("|" + "|".join(["---"] * len(kopf)) + "|")
                teile.extend("| " + " | ".join(zeile) + " |" for zeile in rest)
        return "\n".join(teile).strip() + "\n"


def _tabelle_als_text(zeilen: list[list[str]]) -> list[str]:
    if not zeilen:
        return []
    spalten = max(len(z) for z in zeilen)
    breiten = [0] * spalten
    for zeile in zeilen:
        for i, wert in enumerate(zeile):
            breiten[i] = max(breiten[i], len(wert))
    raus = []
    for nummer, zeile in enumerate(zeilen):
        gefuellt = list(zeile) + [""] * (spalten - len(zeile))
        raus.append("  ".join(wert.ljust(breiten[i]) for i, wert in enumerate(gefuellt)).rstrip())
        if nummer == 0:
            raus.append("  ".join("-" * breite for breite in breiten))
    return raus


# -- Markdown -> Dokument ------------------------------------------------

_UEBERSCHRIFT = re.compile(r"^(#{1,6})\s+(.*)$")
_FETTZEILE = re.compile(r"^\*\*(.+?)\*\*:?\s*$")
_PUNKT = re.compile(r"^\s*[-*+]\s+(.*)$")
_NUMMER = re.compile(r"^\s*\d+[\.\)]\s+(.*)$")
_TABELLENZEILE = re.compile(r"^\s*\|.*\|\s*$")
#: "[1] UStG ..." - eine Fundstelle je Zeile, nicht zu einem Absatz verschmelzen.
_FUNDSTELLE = re.compile(r"^\[\d+\]\s")
_TRENNZEILE = re.compile(r"^\s*\|?[\s:\-\|]+\|[\s:\-\|]*$")
_AUSZEICHNUNG = re.compile(r"\*\*(.+?)\*\*|__(.+?)__|`([^`]+)`")


def klartext(text: str) -> str:
    """Entfernt die Auszeichnungszeichen - der Text bleibt."""
    return _AUSZEICHNUNG.sub(lambda t: t.group(1) or t.group(2) or t.group(3) or "", text)


def aus_markdown(text: str, titel: str = "") -> Dokument:
    """Wandelt eine Antwort in ein Dokument um.

    Damit laesst sich genau das speichern, was im Fenster steht - mit
    Ueberschriften, Aufzaehlungen und Tabellen, nicht als eine Wand aus Text.
    """
    dokument = Dokument(titel=titel)
    zeilen = (text or "").splitlines()
    i = 0
    absatz: list[str] = []
    punkte: list[str] = []

    def absatz_schliessen() -> None:
        nonlocal absatz
        if absatz:
            dokument.absatz(klartext(" ".join(absatz).strip()))
            absatz = []

    def punkte_schliessen() -> None:
        nonlocal punkte
        if punkte:
            dokument.aufzaehlung(punkte)
            punkte = []

    while i < len(zeilen):
        zeile = zeilen[i]
        roh = zeile.strip()

        if not roh:
            absatz_schliessen(); punkte_schliessen(); i += 1; continue

        if roh.startswith("```"):
            absatz_schliessen(); punkte_schliessen()
            i += 1
            gesammelt = []
            while i < len(zeilen) and not zeilen[i].strip().startswith("```"):
                gesammelt.append(zeilen[i]); i += 1
            i += 1
            dokument.bloecke.append(Block("code", text="\n".join(gesammelt)))
            continue

        treffer = _UEBERSCHRIFT.match(roh)
        if treffer:
            absatz_schliessen(); punkte_schliessen()
            dokument.ueberschrift(klartext(treffer.group(2).strip()), len(treffer.group(1)))
            i += 1; continue

        treffer = _FETTZEILE.match(roh)
        if treffer:
            # "**QUELLEN**" allein auf einer Zeile ist eine Ueberschrift,
            # kein fett gesetzter Absatz.
            absatz_schliessen(); punkte_schliessen()
            dokument.ueberschrift(treffer.group(1).strip(), 2)
            i += 1; continue

        if _TABELLENZEILE.match(roh):
            absatz_schliessen(); punkte_schliessen()
            zeilenblock: list[list[str]] = []
            while i < len(zeilen) and _TABELLENZEILE.match(zeilen[i].strip()):
                rohzeile = zeilen[i].strip()
                if not _TRENNZEILE.match(rohzeile):
                    felder = [klartext(f.strip()) for f in rohzeile.strip("|").split("|")]
                    zeilenblock.append(felder)
                i += 1
            if zeilenblock:
                dokument.tabelle(zeilenblock)
            continue

        if _FUNDSTELLE.match(roh):
            # Quellenangaben stehen zeilenweise untereinander. Wuerden sie zu
            # einem Absatz zusammenlaufen, waere nicht mehr zu erkennen, wo
            # eine Fundstelle endet und die naechste beginnt.
            absatz_schliessen(); punkte_schliessen()
            dokument.absatz(klartext(roh))
            i += 1; continue

        treffer = _PUNKT.match(roh) or _NUMMER.match(roh)
        if treffer:
            absatz_schliessen()
            punkte.append(klartext(treffer.group(1).strip()))
            i += 1; continue

        punkte_schliessen()
        absatz.append(roh)
        i += 1

    absatz_schliessen(); punkte_schliessen()
    return dokument
