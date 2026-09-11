"""Wiederverwendbare Vorlagen - verwalten, fuellen, erzeugen.

Der Unterschied zu den Arbeitsergebnissen: dort liegt, was einmal
erzeugt wurde. Hier liegt, woraus sich immer wieder etwas erzeugen
laesst.

Eine Vorlage ist ein Text mit Platzhaltern (``{{firma.name}}``). Gefuellt
wird aus dem Unternehmensgedaechtnis des aktiven Kundenbereichs und aus
dem, was der Mensch beim Erzeugen eingibt. Was sich nicht aufloesen
laesst, bleibt sichtbar stehen und wird gemeldet - nie stillschweigend
weggelassen.
"""

from .mitgeliefert import Aufnahme, uebernehmen
from .modell import Vorlage, Vorschau
from .platzhalter import Fuellung, beschriftung, finden, fuellen
from .speicher import VorlagenFehler, Vorlagenspeicher, kopfzeilen_lesen
from .werk import FREIGABEHINWEIS, Erzeugnis, Vorlagenwerk
from .werte import sammeln

__all__ = [
    "Aufnahme", "Erzeugnis", "FREIGABEHINWEIS", "Fuellung", "Vorlage",
    "Vorlagenspeicher", "Vorlagenwerk", "VorlagenFehler", "Vorschau",
    "beschriftung", "finden", "fuellen", "kopfzeilen_lesen",
    "sammeln", "uebernehmen",
]
