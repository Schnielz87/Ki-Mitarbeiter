"""Trennt die eigentliche Antwort von den angehaengten Abschnitten.

Abschnitt 23 der Ergaenzung: die Unterhaltung soll sich wie ein Gespraech
lesen. Oben die Antwort, darunter - kleiner und ruhiger - Quellen,
Wissensstand, Freigabebedarf und Hinweise.

Der Text selbst wird dabei **nicht** veraendert. Es wird nur gesagt, wo die
Antwort endet und der Anhang beginnt; die Oberflaeche stellt beide Teile
unterschiedlich dar. Damit geht nichts verloren: wer die Antwort exportiert
oder in der Datenbank nachliest, sieht weiterhin den vollstaendigen Text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Abschnitte, die die Anwendung selbst unter jede Antwort setzt
#: (siehe ``RagEngine._append_footer``).
ANHANGSTEILE = (
    "QUELLEN",
    "WISSENSSTAND",
    "FREIGABEBEDARF",
    "HINWEISE DER ANWENDUNG",
    "RECHERCHE-DETAILS",
)

_UEBERSCHRIFT = re.compile(
    r"^[ \t]*(?:\*\*|__|##+[ \t]*)?(" + "|".join(re.escape(t) for t in ANHANGSTEILE) + r")\b",
    re.MULTILINE,
)


@dataclass
class Teile:
    """Antwort und Anhang - der Anhang darf leer sein."""

    antwort: str
    anhang: str = ""

    @property
    def hat_anhang(self) -> bool:
        return bool(self.anhang.strip())


def teilen(text: str) -> Teile:
    """Sucht die erste Anhangsueberschrift und trennt dort.

    Ohne Anhang bleibt die ganze Nachricht Antwort - das ist der Normalfall
    bei Smalltalk und bei allem, was nicht von der Antwortmaschine kommt.
    """
    if not text:
        return Teile("")
    treffer = _UEBERSCHRIFT.search(text)
    if treffer is None:
        return Teile(text.strip())
    return Teile(text[: treffer.start()].strip(), text[treffer.start():].strip())
