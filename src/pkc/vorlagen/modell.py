"""Was eine Vorlage ist.

Eine Vorlage ist ein **Text mit Platzhaltern** plus die Angaben, die man
braucht, um sie wiederzufinden: Name, Kategorie, Beschreibung und das
Format, in dem sie ueblicherweise erzeugt wird.

Bewusst ein Text und keine fertige Word-Datei. Der Grund ist praktisch:
die Artefakt-Engine erzeugt aus einem Text bereits neun Formate. Eine
Vorlage, die als Text vorliegt, kann deshalb ohne Mehrarbeit als docx,
pdf, xlsx oder md herauskommen - dieselbe Vorlage, verschiedene Wege.
Eine Vorlage, die als docx vorliegt, koennte nur docx.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .platzhalter import finden


@dataclass
class Vorlage:
    """Eine wiederverwendbare Vorlage."""

    kennung: str
    name: str
    rumpf: str = ""
    kategorie: str = "Allgemein"
    beschreibung: str = ""
    #: Das Format, das beim Erzeugen vorgeschlagen wird.
    format: str = "docx"
    #: "mitgeliefert" oder "eigen". Mitgelieferte Vorlagen lassen sich
    #: nicht loeschen - sie kaemen beim naechsten Start ohnehin wieder.
    herkunft: str = "mitgeliefert"
    angelegt: str = ""

    @property
    def platzhalter(self) -> list[str]:
        """Welche Stellen gefuellt werden muessen."""
        return finden(self.rumpf)

    def as_dict(self) -> dict:
        """Ohne den Rumpf - der liegt als eigene Datei daneben."""
        return {
            "kennung": self.kennung, "name": self.name,
            "kategorie": self.kategorie, "beschreibung": self.beschreibung,
            "format": self.format, "herkunft": self.herkunft,
            "angelegt": self.angelegt,
        }


@dataclass
class Vorschau:
    """Was vor dem Erzeugen angezeigt wird.

    Der Auftrag verlangt eine Vorschau ausdruecklich, und sie hat einen
    Zweck: eine gefuellte Vorlage sieht aus wie ein fertiges Dokument.
    Wer sie ungesehen erzeugt und verschickt, verschickt auch die
    Stellen, die nicht gefuellt werden konnten.
    """

    vorlage: Vorlage
    text: str
    #: Derselbe Text mit hervorgehobenen offenen Stellen.
    angezeigt: str = ""
    gefuellt: dict[str, str] = field(default_factory=dict)
    offen: list[str] = field(default_factory=list)
    hinweis: str = ""

    @property
    def vollstaendig(self) -> bool:
        return not self.offen
