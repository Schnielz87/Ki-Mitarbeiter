"""Datei- und Artefakterzeugung (Erweiterung E4).

Die Anwendung soll Arbeitsergebnisse nicht nur anzeigen, sondern als Datei
herausgeben - offline, ohne installiertes Office.
"""

from .modell import Block, Dokument, aus_markdown
from .schreiber import ArtefaktFehler, Schreiber, abmelden, formate, hole, registrieren
from .werk import Artefakt, Artefaktwerk, dateiname

__all__ = [
    "Block", "Dokument", "aus_markdown",
    "ArtefaktFehler", "Schreiber", "abmelden", "formate", "hole", "registrieren",
    "Artefakt", "Artefaktwerk", "dateiname",
]
