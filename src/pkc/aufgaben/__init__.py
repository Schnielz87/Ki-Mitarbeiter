"""Geplante Aufgaben und Automationen.

**Weg C, Vorgabe A.** PORTIVA laeuft nur, solange es geoeffnet ist -
das ist der Preis der Portabilitaet und keine Nachlaessigkeit. Aufgaben
laufen deshalb waehrend des Betriebs, und was ausgefallen ist, wird beim
naechsten Start **einmal** nachgeholt.

Wer mehr braucht, schaltet die Windows-Aufgabenplanung ausdruecklich
dazu und bekommt vorher zu lesen, was das auf dem Rechner hinterlaesst.

Die drei Saetze, die den Rest erklaeren:

* Eine Aufgabe, die nicht laufen konnte, gilt nicht als erledigt.
* Eine Aktion mit Aussenwirkung braucht bei **jeder** Ausfuehrung eine
  Bestaetigung - nicht nur beim Anlegen.
* Fuenf verpasste Sicherungen sind keine fuenf Sicherungen, sondern eine
  Sicherung und vier Wartezeiten.
"""

from .aktionen import Aktion, abmelden, alle, hole, registrieren
from .ausloeser import ARTEN, WOCHENTAGE, Ausloeser, AusloeserFehler
from .modell import Aufgabe, Lauf
from .planer import TAKT_SEKUNDEN, Planer
from .speicher import AufgabenFehler, Aufgabenspeicher
from .windows_planung import EINTRAG, SPUREN, WindowsPlanung, Zustand

__all__ = [
    "ARTEN", "Aktion", "Aufgabe", "AufgabenFehler", "Aufgabenspeicher",
    "Ausloeser", "AusloeserFehler", "EINTRAG", "Lauf", "Planer", "SPUREN",
    "TAKT_SEKUNDEN", "WOCHENTAGE", "WindowsPlanung", "Zustand",
    "abmelden", "alle", "hole", "registrieren",
]
