"""Woher die Werte kommen, mit denen eine Vorlage gefuellt wird.

Drei Quellen, in dieser Rangfolge:

1. **Was der Mensch beim Erzeugen eingibt.** Hat immer Vorrang - er
   sieht den Einzelfall, das Gedaechtnis kennt nur den Regelfall.
2. **Das Unternehmensgedaechtnis.** Name, Rechtsform, Steuernummer,
   Kontenrahmen und alles Weitere, was dort gepflegt ist.
3. **Das Datum.** Heute, der laufende Monat, das laufende Jahr.

**Zur Mandantentrennung.** Dieses Modul liest ausschliesslich aus dem
Gedaechtnis, das ihm uebergeben wird. Das ist immer das des aktiven
Kundenbereichs - eine eigene Datenbank je Kunde. Es gibt hier keinen Weg,
an ein anderes Gedaechtnis zu kommen, und das ist Absicht: eine Vorlage,
die den Namen des falschen Unternehmens traegt, waere genau der Fehler,
den Abschnitt 61 ausschliesst.
"""

from __future__ import annotations

from datetime import date

from ..logging_setup import get_logger

log = get_logger(__name__)

#: Deutsche Platzhalternamen fuer die Schluessel des Gedaechtnisses.
#: ``{{firma.name}}`` ist lesbarer als ``{{company.name}}`` - beides
#: funktioniert, damit niemand raten muss.
DEUTSCH = {
    "company": "firma",
}

MONATE = ("Januar", "Februar", "Maerz", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember")


def sammeln(memory=None, zusatz: dict | None = None,
            heute: date | None = None) -> dict:
    """Traegt die Werte zusammen, mit denen gefuellt wird."""
    heute = heute or date.today()
    werte: dict[str, str] = {
        "datum": heute.strftime("%d.%m.%Y"),
        "jahr": str(heute.year),
        "monat": MONATE[heute.month - 1],
        "monat.nummer": f"{heute.month:02d}",
    }

    werte.update(_aus_gedaechtnis(memory))

    # Was der Mensch angibt, steht zuletzt und gewinnt damit.
    for schluessel, wert in (zusatz or {}).items():
        text = "" if wert is None else str(wert).strip()
        if text:
            werte[str(schluessel)] = text
    return werte


def _aus_gedaechtnis(memory) -> dict:
    """Alle aktiven Eintraege als Platzhalterwerte.

    Ein Eintrag hat einen Inhalt (``content``) und manchmal einen Wert
    (``value``). Genommen wird der Inhalt: er ist der Satz, den ein
    Mensch geschrieben hat, und genau der gehoert in einen Brief. Der
    Wert kann eine Liste oder eine Struktur sein - so etwas in eine
    Anrede zu setzen ergibt Unsinn.
    """
    if memory is None:
        return {}
    try:
        eintraege = memory.list(status="active")
    except Exception as fehler:                 # pragma: no cover - defensiv
        log.warning("Gedaechtnis fuer Vorlagen nicht lesbar: %s", fehler)
        return {}

    werte: dict[str, str] = {}
    for eintrag in eintraege:
        schluessel = getattr(eintrag, "mem_key", "") or ""
        inhalt = (getattr(eintrag, "content", "") or "").strip()
        if not schluessel or not inhalt:
            continue
        werte[schluessel] = inhalt
        kopf, _, rest = schluessel.partition(".")
        if rest and kopf in DEUTSCH:
            werte.setdefault(f"{DEUTSCH[kopf]}.{rest}", inhalt)
    return werte
