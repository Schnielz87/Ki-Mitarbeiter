"""Prueft Kontonummern gegen den Kontenrahmen - ohne selbst welche zu erfinden.

**Der gemeldete Fehler.** Das Modell schrieb: *"Die Umsatzsteuer wird an
der Umsatzsteuerkonto 4400 abgerechnet. Die Vorsteuer wird an der
Vorsteuerkonto 4410 abgerechnet."* Beide Nummern sind in keinem der
beiden gebraeuchlichen deutschen Kontenrahmen Steuerkonten.

**Wie hier geprueft wird - und warum in zwei Stufen.**

1. **Der Bereich.** Beide Kontenrahmen sind nach Kontenklassen geordnet,
   und diese Ordnung ist eindeutig. Im SKR03 sind die 4000er
   *betriebliche Aufwendungen*, im SKR04 sind sie *Ertraege*. Eine
   Umsatzsteuerschuld ist weder das eine noch das andere - sie ist eine
   Verbindlichkeit. Eine als Steuerkonto bezeichnete 4000er-Nummer ist
   deshalb in beiden Rahmen falsch, ohne dass man ein einziges
   Einzelkonto kennen muesste. **Das ist die belastbare Pruefung.**

2. **Der Hinweis auf das richtige Konto.** Dafuer liegt unten eine
   Auswahl gebraeuchlicher Konten. Sie ist **kein vollstaendiger
   Kontenrahmen** und wird auch nie als solcher ausgegeben: Eine Nummer
   gilt hier niemals als falsch, nur weil sie in dieser Auswahl fehlt.
   Massgeblich ist der Kontenrahmen des Betriebs.

Diese Zurueckhaltung ist Absicht. Eine Anwendung, die erfundene
Kontonummern anmahnt, indem sie selbst welche erfindet, waere genau der
Fehler, den sie verhindern soll.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Kontenklassen je Rahmen: erste Ziffer -> (Bezeichnung, Art).
#: Die Ordnung der Klassen ist der belastbare Teil dieses Moduls.
KLASSEN: dict[str, dict[str, tuple[str, str]]] = {
    # SKR03 ist nach dem Prozessgliederungsprinzip geordnet.
    "SKR03": {
        "0": ("Anlagevermoegen und Kapital", "bestand"),
        "1": ("Finanz- und Privatkonten (inkl. Steuerkonten)", "bestand"),
        "2": ("Abgrenzungskonten", "gemischt"),
        "3": ("Wareneingang und Bestaende", "aufwand"),
        "4": ("Betriebliche Aufwendungen", "aufwand"),
        "5": ("Weitere Aufwendungen", "aufwand"),
        "6": ("Weitere Aufwendungen", "aufwand"),
        "7": ("Bestaende an Erzeugnissen", "bestand"),
        "8": ("Erloeskonten", "ertrag"),
        "9": ("Vortrags- und statistische Konten", "gemischt"),
    },
    # SKR04 ist nach dem Abschlussgliederungsprinzip geordnet.
    "SKR04": {
        "0": ("Anlagevermoegen", "bestand"),
        "1": ("Umlaufvermoegen (inkl. Vorsteuer)", "bestand"),
        "2": ("Eigenkapital", "bestand"),
        "3": ("Fremdkapital (inkl. Umsatzsteuer, Rueckstellungen)", "bestand"),
        "4": ("Betriebliche Ertraege", "ertrag"),
        "5": ("Betriebliche Aufwendungen", "aufwand"),
        "6": ("Betriebliche Aufwendungen", "aufwand"),
        "7": ("Weitere Ertraege und Aufwendungen", "gemischt"),
        "9": ("Vortrags- und statistische Konten", "gemischt"),
    },
}

#: Eine **Auswahl** gebraeuchlicher Konten - kein vollstaendiger Rahmen.
#: Nur fuer den Hinweis "gemeint ist vermutlich ...", nie fuer ein Urteil.
KONTEN: dict[str, dict[str, str]] = {
    "SKR03": {
        "1576": "Abziehbare Vorsteuer 19 %",
        "1571": "Abziehbare Vorsteuer 7 %",
        "1776": "Umsatzsteuer 19 %",
        "1771": "Umsatzsteuer 7 %",
        "0980": "Aktive Rechnungsabgrenzung",
        "0990": "Passive Rechnungsabgrenzung",
        "8400": "Erloese 19 % Umsatzsteuer",
        "8300": "Erloese 7 % Umsatzsteuer",
    },
    "SKR04": {
        "1406": "Abziehbare Vorsteuer 19 %",
        "1401": "Abziehbare Vorsteuer 7 %",
        "3806": "Umsatzsteuer 19 %",
        "3801": "Umsatzsteuer 7 %",
        "1900": "Aktive Rechnungsabgrenzung",
        "3900": "Passive Rechnungsabgrenzung",
        "4400": "Erloese 19 % Umsatzsteuer",
        "4300": "Erloese 7 % Umsatzsteuer",
    },
}

#: Welcher Zweck welche Kontenart verlangt. Nur Zwecke, bei denen die
#: Zuordnung ausser Frage steht.
ZWECKE: dict[str, tuple[re.Pattern, tuple[str, ...], str]] = {
    "umsatzsteuer": (
        re.compile(r"umsatzsteuer(?:konto)?|ust[-\s]?konto", re.IGNORECASE),
        ("bestand",),
        "Die Umsatzsteuerschuld ist eine Verbindlichkeit - ein Bestandskonto, "
        "kein Aufwands- oder Ertragskonto.",
    ),
    "vorsteuer": (
        re.compile(r"vorsteuer(?:konto)?|vst[-\s]?konto", re.IGNORECASE),
        ("bestand",),
        "Die abziehbare Vorsteuer ist eine Forderung gegen das Finanzamt - "
        "ein Bestandskonto, kein Aufwandskonto.",
    ),
}

#: Eine Kontonummer wird nur geprueft, wenn sie ausdruecklich als Konto
#: bezeichnet ist. Sonst waere jede Jahreszahl ein Konto.
_KONTO = re.compile(
    r"(?:konto|kontonummer|sachkonto|gegenkonto)\s*(?:nr\.?|nummer)?\s*[:\-]?\s*"
    r"(\d{4})\b",
    re.IGNORECASE)


@dataclass(frozen=True)
class Kontobefund:
    nummer: str
    zweck: str
    text: str


def rahmen_erkennen(angabe: str | None) -> str | None:
    """Liest "SKR03" oder "SKR04" aus einer Angabe des Unternehmens."""
    if not angabe:
        return None
    treffer = re.search(r"SKR\s*0?(3|4)", str(angabe), re.IGNORECASE)
    if not treffer:
        return None
    return "SKR03" if treffer.group(1) == "3" else "SKR04"


def pruefe_konten(text: str, rahmen: str | None = None) -> list[Kontobefund]:
    """Sucht Kontonummern mit erkennbarem Zweck und prueft ihren Bereich.

    Ist ``rahmen`` unbekannt, wird gegen **beide** Rahmen geprueft und nur
    dann bemaengelt, wenn die Nummer in beiden nicht passt. Ein Vorwurf,
    der nur unter einer Annahme stimmt, ist kein Vorwurf.
    """
    befunde: list[Kontobefund] = []
    gesehen: set[tuple[str, str]] = set()

    zu_pruefen = [rahmen] if rahmen in KLASSEN else list(KLASSEN)

    for satz in re.split(r"(?<=[.;!?])\s+|\n", text or ""):
        for treffer in _KONTO.finditer(satz):
            nummer = treffer.group(1)
            for zweck, (muster, erlaubt, begruendung) in ZWECKE.items():
                if not muster.search(satz):
                    continue
                if (nummer, zweck) in gesehen:
                    continue
                passt_irgendwo = False
                lagen: list[str] = []
                for name in zu_pruefen:
                    klasse = KLASSEN[name].get(nummer[0])
                    if klasse is None:
                        passt_irgendwo = True     # unbekannte Klasse: nichts behaupten
                        break
                    bezeichnung, art = klasse
                    if art in erlaubt or art == "gemischt":
                        passt_irgendwo = True
                        break
                    lagen.append(f"im {name} liegt {nummer} in \"{bezeichnung}\"")
                if passt_irgendwo:
                    continue

                gesehen.add((nummer, zweck))
                hinweis = _richtiges_konto(zweck, zu_pruefen)
                befunde.append(Kontobefund(
                    nummer=nummer, zweck=zweck,
                    text=(
                        f"Die Antwort nennt {nummer} als {zweck.capitalize()}konto. "
                        f"{begruendung} Aber: {' und '.join(lagen)}."
                        + (f" {hinweis}" if hinweis else "")
                    ),
                ))
    return befunde


def _richtiges_konto(zweck: str, rahmen: list[str]) -> str:
    """Nennt das uebliche Konto - als Hinweis, nicht als Vorschrift.

    Die Formulierung ist mit Absicht zurueckhaltend. Diese Auswahl ist
    kein vollstaendiger Kontenrahmen; massgeblich bleibt der des
    Betriebs.
    """
    suche = "Umsatzsteuer 19 %" if zweck == "umsatzsteuer" else "Abziehbare Vorsteuer 19 %"
    teile = []
    for name in rahmen:
        for nummer, bezeichnung in KONTEN.get(name, {}).items():
            if bezeichnung == suche:
                teile.append(f"{name}: {nummer}")
    if not teile:
        return ""
    return (f"Ueblich ist dafuer {', '.join(teile)} - massgeblich ist aber "
            "der Kontenrahmen Ihres Betriebs.")
