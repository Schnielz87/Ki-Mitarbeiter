"""Erkennt, ob eine Frage eine Datei verlangt - und welche.

**Warum es das gibt.** Ein Anwender hat eine Fallstudie gestellt, in der
woertlich stand: *"Der Buchhalter soll eine Excel-Arbeitsmappe mit
mindestens vier verknuepften Tabellenblaettern erstellen."* Der
Buchhalter hat geantwortet - und keine Datei erzeugt. Die Faehigkeit war
da (neun Formate, im Bauablauf nachgewiesen), sie wurde nur nie
ausgeloest. Es gab einen Knopf dafuer, den man haette druecken muessen.

Ein Mitarbeiter, dem man sagt "erstell mir bitte eine Excel-Tabelle",
antwortet nicht mit einem Vortrag ueber Tabellen.

**Was hier bewusst nicht passiert.** Es wird nichts erzeugt, nur weil ein
Format erwaehnt wird. "Was ist der Unterschied zwischen CSV und Excel?"
ist eine Frage, keine Bestellung. Verlangt wird beides: ein Format **und**
eine Aufforderung, etwas zu erstellen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Wortformen je Format. Die Reihenfolge entscheidet bei Mehrfachnennung:
#: Wer "Excel oder CSV" sagt, bekommt Excel - das ist das reichere Format
#: und laesst sich in CSV weiterverarbeiten, nicht umgekehrt.
FORMATE: list[tuple[str, tuple[str, ...]]] = [
    ("xlsx", ("excel", "exceltabelle", "excel-tabelle", "arbeitsmappe",
              "tabellenblatt", "tabellenblaetter", "xlsx", "tabellenkalkulation")),
    ("docx", ("word", "word-dokument", "worddokument", "docx", "schriftsatz")),
    ("pptx", ("powerpoint", "praesentation", "präsentation", "pptx", "folien")),
    ("pdf", ("pdf", "pdf-bericht", "pdf-datei")),
    ("csv", ("csv", "csv-datei", "kommagetrennt")),
]

#: Woran eine Aufforderung zu erkennen ist. Bewusst knapp gehalten: jedes
#: zusaetzliche Wort erhoeht die Gefahr, eine Frage fuer eine Bestellung
#: zu halten.
_AUFFORDERUNG = re.compile(
    r"\b("
    r"erstell\w*|erzeug\w*|leg\w*\s+(?:mir\s+)?an|generier\w*|bau\w*|"
    r"schreib\w*|mach\w*|gib\s+mir|brauche|benoetige|benötige|"
    r"soll\w*\s+\w*\s*erstellen|exportier\w*|speicher\w*|liefer\w*"
    r")\b",
    re.IGNORECASE,
)

#: Wenn das dabeisteht, ist es eine Wissensfrage und keine Bestellung.
_FRAGE_UEBER = re.compile(
    r"\b(was ist|was sind|worin\s+besteht|unterschied\s+zwischen|"
    r"wofuer\s+steht|wofür\s+steht|erklaer\w*|erklär\w*|"
    r"wie\s+funktioniert|kann\s+man|kannst\s+du\s+(?:mir\s+)?erklaeren)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Dateiwunsch:
    """Eine erkannte Bestellung."""

    format: str
    ausloeser: str          # das Wort, das den Wunsch ausgeloest hat
    name: str = ""          # Vorschlag fuer den Dateinamen

    def __str__(self) -> str:                   # pragma: no cover - Anzeige
        return f"{self.format} (erkannt an: {self.ausloeser})"


def erkennen(frage: str, standardname: str = "Auswertung") -> Dateiwunsch | None:
    """Verlangt diese Frage eine Datei? Wenn ja: welche.

    Gibt ``None`` zurueck, wenn kein Format genannt wird, keine
    Aufforderung erkennbar ist, oder wenn die Frage erkennbar **ueber**
    ein Format handelt statt eine Datei zu bestellen.
    """
    text = (frage or "").strip()
    if not text:
        return None

    treffer = _format_finden(text)
    if treffer is None:
        return None
    format, ausloeser = treffer

    if not _AUFFORDERUNG.search(text):
        return None
    if _FRAGE_UEBER.search(text):
        return None

    return Dateiwunsch(format=format, ausloeser=ausloeser,
                       name=_namensvorschlag(text, standardname))


def _format_finden(text: str) -> tuple[str, str] | None:
    """Sucht das erste genannte Format - in der Reihenfolge von FORMATE."""
    klein = text.lower()
    for format, woerter in FORMATE:
        for wort in woerter:
            # Wortgrenzen, damit "pdf" nicht in "pdfs" oder einem Pfad
            # gefunden wird und "csv" nicht in einem Dateinamen.
            if re.search(rf"(?<![\w-]){re.escape(wort)}(?![\w])", klein):
                return format, wort
    return None


#: Ueberschriften, aus denen sich ein Dateiname ableiten laesst.
_TITEL = re.compile(
    r"(?:fallstudie|aufgabe|thema|betreff|titel)\s*[:\-]\s*([^\n\.;]{3,60})",
    re.IGNORECASE)


def _namensvorschlag(text: str, standard: str) -> str:
    """Ein sprechender Dateiname, wenn sich einer aus der Frage ergibt.

    Lieber ``Auswertung`` als ein aus dem Fliesstext zusammengeklaubter
    Name, der nichts sagt. Ein Dateiname, den niemand wiedererkennt, ist
    schlechter als ein neutraler.
    """
    treffer = _TITEL.search(text)
    if not treffer:
        return standard
    roh = treffer.group(1).strip(" \"'„“”»«")
    roh = re.sub(r"\s+", " ", roh)
    return roh[:60] or standard
