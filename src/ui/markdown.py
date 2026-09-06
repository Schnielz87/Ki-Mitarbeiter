"""Markdown fuer ein Tkinter-Textfeld aufbereiten.

Das Sprachmodell antwortet in Markdown. Ungerendert stehen dann Zeichen wie
``**`` und ``#`` mitten im Text - der Auftrag (Abschnitt 7) verlangt
ausdruecklich, das entweder richtig darzustellen oder umzuwandeln.

Tkinter kann kein Markdown. Es kann aber Textbereiche mit Stilkennzeichen
versehen. Dieses Modul zerlegt den Text deshalb in Stuecke mit Stilangabe;
die Oberflaeche fuegt sie mit den passenden Kennzeichen ein.

Bewusst klein gehalten: unterstuetzt wird, was in Fachantworten vorkommt -
Ueberschriften, Aufzaehlungen, nummerierte Listen, Fettdruck, Kursiv,
Code und Tabellen. Kein vollstaendiger Markdown-Umfang, dafuer
nachvollziehbar und ohne Fremdpaket.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Stilkennzeichen, die die Oberflaeche kennen muss.
STILE = ("ueberschrift1", "ueberschrift2", "fett", "kursiv", "code",
         "aufzaehlung", "tabelle", "normal")


@dataclass
class Stueck:
    """Ein Textstueck mit seinem Stil."""

    text: str
    stil: str = "normal"


_FETT = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_KURSIV = re.compile(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", re.DOTALL)
_CODE = re.compile(r"`([^`]+)`")
_UEBERSCHRIFT = re.compile(r"^(#{1,6})\s+(.*)$")
_AUFZAEHLUNG = re.compile(r"^\s*[-*+]\s+(.*)$")
_NUMMERIERT = re.compile(r"^\s*(\d+)[\.\)]\s+(.*)$")
_TABELLENTRENNER = re.compile(r"^\s*\|?[\s:\-\|]+\|[\s:\-\|]*$")


def _inline(text: str, grundstil: str = "normal") -> list[Stueck]:
    """Zerlegt eine Zeile in Fett-, Kursiv-, Code- und Normalstuecke."""
    stuecke: list[Stueck] = []
    rest = text
    muster = [(_FETT, "fett"), (_CODE, "code"), (_KURSIV, "kursiv")]

    while rest:
        treffer = None
        stil = ""
        for regex, name in muster:
            gefunden = regex.search(rest)
            if gefunden and (treffer is None or gefunden.start() < treffer.start()):
                treffer, stil = gefunden, name
        if treffer is None:
            stuecke.append(Stueck(rest, grundstil))
            break
        if treffer.start():
            stuecke.append(Stueck(rest[:treffer.start()], grundstil))
        inhalt = treffer.group(1)
        # Fett innerhalb einer Ueberschrift bleibt Ueberschrift - sonst
        # wuerde die Zeile mitten im Wort die Schriftgroesse wechseln.
        stuecke.append(Stueck(inhalt, grundstil if grundstil.startswith("ueberschrift") else stil))
        rest = rest[treffer.end():]
    return [s for s in stuecke if s.text]


def zerlegen(text: str) -> list[Stueck]:
    """Wandelt Markdown in Stuecke mit Stilangabe um.

    Jedes Stueck endet dort, wo der Stil wechselt. Zeilenumbrueche bleiben
    erhalten, damit die Oberflaeche den Text unveraendert einfuegen kann.
    """
    if not text:
        return []

    stuecke: list[Stueck] = []
    zeilen = text.replace("\r\n", "\n").split("\n")
    in_codeblock = False

    for zeile in zeilen:
        if zeile.strip().startswith("```"):
            in_codeblock = not in_codeblock
            continue
        if in_codeblock:
            stuecke += [Stueck(zeile, "code"), Stueck("\n")]
            continue

        # Trennlinie einer Tabelle wegwerfen - sie traegt keine Information
        # und saehe als Text nur nach Zeichensalat aus.
        if _TABELLENTRENNER.match(zeile) and "|" in zeile:
            continue

        ueberschrift = _UEBERSCHRIFT.match(zeile)
        if ueberschrift:
            ebene = len(ueberschrift.group(1))
            stil = "ueberschrift1" if ebene <= 2 else "ueberschrift2"
            stuecke += _inline(ueberschrift.group(2), stil) + [Stueck("\n")]
            continue

        aufzaehlung = _AUFZAEHLUNG.match(zeile)
        if aufzaehlung:
            stuecke.append(Stueck("  •  ", "aufzaehlung"))
            stuecke += _inline(aufzaehlung.group(1)) + [Stueck("\n")]
            continue

        nummeriert = _NUMMERIERT.match(zeile)
        if nummeriert:
            stuecke.append(Stueck(f"  {nummeriert.group(1)}.  ", "aufzaehlung"))
            stuecke += _inline(nummeriert.group(2)) + [Stueck("\n")]
            continue

        if zeile.count("|") >= 2:
            felder = [f.strip() for f in zeile.strip().strip("|").split("|")]
            stuecke.append(Stueck("  " + "   ".join(felder), "tabelle"))
            stuecke.append(Stueck("\n"))
            continue

        stuecke += _inline(zeile) + [Stueck("\n")]

    while stuecke and stuecke[-1].text == "\n":
        stuecke.pop()
    return stuecke


def als_klartext(text: str) -> str:
    """Markdown ohne Auszeichnung - fuer Ausgaben ohne Stilunterstuetzung."""
    return "".join(s.text for s in zerlegen(text))
