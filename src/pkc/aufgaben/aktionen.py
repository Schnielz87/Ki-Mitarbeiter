"""Was eine Aufgabe tun kann.

Eine Aktion ist eine benannte Arbeit mit vier Angaben, die dem Menschen
gesagt werden, **bevor** er sie einer Automation ueberlaesst:

* Was sie tut - in einem Satz.
* Ob sie Internet braucht.
* Ob sie Daten veraendert.
* Ob sie etwas nach aussen gibt.

Die letzte ist die wichtigste. Eine Automation, die ungefragt etwas nach
aussen schickt, ist genau das, was die Sicherheitsvorgaben ausschliessen.
Solche Aktionen brauchen deshalb **bei jeder einzelnen Ausfuehrung** eine
Bestaetigung - die Erlaubnis beim Anlegen genuegt nicht.

**Heute hat keine der mitgelieferten Aktionen diese Eigenschaft.** Das
Kennzeichen steht trotzdem hier, weil Plugins eigene Aktionen anmelden
koennen (Erweiterung E5) und ein Connector genau so etwas waere. Ein
Schutz, der erst eingebaut wird, wenn er gebraucht wird, ist zu spaet
eingebaut.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..logging_setup import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class Aktion:
    """Eine Arbeit, die eine Aufgabe ausloesen kann."""

    kennung: str
    name: str
    beschreibung: str
    #: Ruft die Arbeit auf. Bekommt den Controller, gibt einen Satz
    #: zurueck, der ins Protokoll kommt.
    funktion: Callable[..., str]
    braucht_netz: bool = False
    aendert_daten: bool = False
    #: Gibt etwas aus dem Haus - braucht bei JEDER Ausfuehrung eine
    #: Bestaetigung.
    nach_aussen: bool = False

    def as_dict(self) -> dict:
        return {"kennung": self.kennung, "name": self.name,
                "beschreibung": self.beschreibung,
                "braucht_netz": self.braucht_netz,
                "aendert_daten": self.aendert_daten,
                "nach_aussen": self.nach_aussen}


_AKTIONEN: dict[str, Aktion] = {}


def registrieren(aktion: Aktion) -> Aktion:
    """Meldet eine Aktion an. Auch fuer Plugins gedacht."""
    _AKTIONEN[aktion.kennung] = aktion
    return aktion


def abmelden(kennung: str) -> None:
    _AKTIONEN.pop(kennung, None)


def alle() -> list[Aktion]:
    return sorted(_AKTIONEN.values(), key=lambda a: a.name.lower())


def hole(kennung: str) -> Aktion | None:
    return _AKTIONEN.get(kennung)


# ----------------------------------------------------------------------
# Die mitgelieferten Aktionen
# ----------------------------------------------------------------------

def _wissen_aktualisieren(controller) -> str:
    """Holt die amtlichen Quellen, deren Intervall abgelaufen ist."""
    bericht = controller.run_update(trigger="aufgabe", nur_faellige=True)
    return (f"{bericht.updated} Quellen aktualisiert, "
            f"{bericht.failed} fehlgeschlagen (Lauf {bericht.run_id}).")


def _sicherung_anlegen(controller) -> str:
    """Sichert beide Datenbanken und die Konfiguration."""
    ergebnis = controller.backup(label="aufgabe")
    ordner = ergebnis.get("ordner") or ergebnis.get("directory") or ""
    dateien = ergebnis.get("dateien") or ergebnis.get("written") or []
    return f"Sicherung angelegt: {len(dateien)} Dateien in {ordner}."


def _wissensstand_pruefen(controller) -> str:
    """Sieht nach, wie alt das Fachwissen ist - ohne etwas zu aendern.

    Die harmloseste Aktion ueberhaupt und trotzdem nuetzlich: sie
    schreibt den Stand ins Protokoll, und wer hineinsieht, weiss, seit
    wann nichts mehr nachgeladen wurde.
    """
    stand = controller.knowledge.knowledge_date() or "unbekannt"
    faellig, grund = controller.update_due()
    return (f"Wissensstand: {stand}. "
            + ("Eine Aktualisierung steht an: " + grund if faellig
               else "Keine Aktualisierung faellig."))


registrieren(Aktion(
    kennung="wissen_aktualisieren",
    name="Wissen aktualisieren",
    beschreibung="Holt die amtlichen Quellen, deren Intervall abgelaufen "
                 "ist. Braucht Internet und laedt nur herunter - es "
                 "verlaesst nichts das Haus.",
    funktion=_wissen_aktualisieren,
    braucht_netz=True, aendert_daten=True,
))

registrieren(Aktion(
    kennung="sicherung_anlegen",
    name="Sicherung anlegen",
    beschreibung="Sichert Unternehmensgedaechtnis, Fachwissen und "
                 "Einstellungen auf den Datentraeger.",
    funktion=_sicherung_anlegen,
    aendert_daten=True,
))

registrieren(Aktion(
    kennung="wissensstand_pruefen",
    name="Wissensstand pruefen",
    beschreibung="Sieht nach, wie alt das Fachwissen ist, und vermerkt "
                 "es im Protokoll. Aendert nichts.",
    funktion=_wissensstand_pruefen,
))
