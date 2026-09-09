"""Liest rechenbare Angaben aus einer Aufgabe - und rechnet sie aus.

**Der Zweck.** Das Sprachmodell soll formulieren, nicht rechnen. Damit
das geht, muessen die Zahlen schon dastehen, bevor es anfaengt. Dieses
Modul sucht in der Frage nach Angaben, die sich eindeutig ausrechnen
lassen, und rechnet sie mit den geprueften Funktionen dieses Pakets aus.

**Der Grundsatz: lieber nichts als etwas Geratenes.** Es wird nur
gerechnet, wenn alle noetigen Angaben in *einem* Abschnitt stehen. Fehlt
das Anschaffungsdatum, die Nutzungsdauer oder der Stichtag, entsteht
kein Ergebnis - und die Antwort bleibt beim Text des Modells. Ein
falsches Ergebnis mit Rechenweg waere schlimmer als gar keines: es sieht
geprueft aus.

**Was hier nicht entschieden wird.** Ob taggenau oder monatsgenau
abgegrenzt wird, ist eine Entscheidung des Betriebs, keine Rechenfrage.
Beide Wege werden ausgerechnet und beide genannt. Ebenso die Richtung
ARAP oder PRAP: wo sie sich nicht eindeutig aus dem Text ergibt, steht
die Frage in der Antwort statt einer Vermutung.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from .abgrenzung import abgrenzen, ganze_monate
from .abschreibung import lineare_afa
from .geld import deutsch, euro, netto_aus_brutto

#: Datum als 15.03.2026 oder 15.3.2026
_DATUM = re.compile(r"\b(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})\b")

#: Datum als "30. September 2026"
_MONATSNAMEN = {
    "januar": 1, "februar": 2, "maerz": 3, "märz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}
_DATUM_LANG = re.compile(
    r"\b(\d{1,2})\.\s*(" + "|".join(_MONATSNAMEN) + r")\s*(\d{4})\b",
    re.IGNORECASE)

#: Betrag mit Euro dahinter: "53.550 €", "14.400 EUR", "12.000,00 Euro"
_BETRAG = re.compile(
    r"(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)\s*(?:€|EUR\b|Euro\b)",
    re.IGNORECASE)

_NUTZUNGSDAUER = re.compile(
    r"Nutzungsdauer\s*[:\-]?\s*(\d{1,2})\s*Jahr", re.IGNORECASE)

_STICHTAG = re.compile(
    r"(?:Stichtag|per|zum|bis\s+zum)\s*[:\-]?\s*"
    r"(\d{1,2}\.\s?\d{1,2}\.\s?\d{4}|\d{1,2}\.\s*[A-Za-zäöüÄÖÜ]+\s*\d{4})",
    re.IGNORECASE)

_ZEITRAUM = re.compile(
    r"(?:Zeitraum|Laufzeit)?\s*[:\-]?\s*"
    r"(\d{1,2}\.\s?\d{1,2}\.\s?\d{4})\s*(?:bis|-|–)\s*"
    r"(\d{1,2}\.\s?\d{1,2}\.\s?\d{4})",
    re.IGNORECASE)

_BRUTTO = re.compile(r"\bbrutto|inkl\.?\s*\d{1,2}\s*%|inklusive\s*\d{1,2}\s*%",
                     re.IGNORECASE)
_STEUERSATZ = re.compile(r"(\d{1,2})\s*%")

#: Woran ein vereinnahmter Ertrag zu erkennen ist (PRAP).
_ERTRAG = re.compile(
    r"\b(erloes|erlös|erträge|ertraege|kunde|kunden|umsatz|lizenz|"
    r"vereinnahmt|erhalten|abonnement)\w*", re.IGNORECASE)
#: Woran ein vorausgezahlter Aufwand zu erkennen ist (ARAP).
# "im Voraus bezahlt" stand hier zuerst mit drin. Das war falsch: in
# "Ein Kunde hat im Voraus bezahlt" haben WIR kassiert. Die Wendung sagt
# nichts ueber die Richtung, nur ueber den Zeitpunkt. Uebrig bleiben
# Begriffe, die wirklich einen Aufwand bezeichnen.
_AUFWAND = re.compile(
    r"\b(versicherung|miete|aufwand|praemie|prämie|beitrag|"
    r"wartungsvertrag|vorausgezahlt|leasing|pacht)\w*", re.IGNORECASE)


@dataclass
class Rechnung:
    """Ein ausgerechnetes Teilergebnis mit Rechenweg."""

    art: str                    # "AfA" oder "Abgrenzung"
    bezeichnung: str
    zeilen: list[str] = field(default_factory=list)
    ergebnis: str = ""
    offene_frage: str = ""      # was der Mensch entscheiden muss
    #: Dieselben Werte noch einmal als Paare - fuer eine Tabelle in einer
    #: Datei. Aus dem Rechenweg-Text die Werte wieder herauszuloesen waere
    #: moeglich und falsch: eine Zahl zweimal zu erzeugen heisst, dass
    #: sie irgendwann auseinanderlaeuft.
    felder: list[tuple[str, str]] = field(default_factory=list)


def _datum(text: str) -> date | None:
    treffer = _DATUM.search(text)
    if treffer:
        tag, monat, jahr = (int(g) for g in treffer.groups())
        try:
            return date(jahr, monat, tag)
        except ValueError:
            return None
    lang = _DATUM_LANG.search(text)
    if lang:
        tag, name, jahr = lang.groups()
        monat = _MONATSNAMEN.get(name.lower())
        if monat:
            try:
                return date(int(jahr), monat, int(tag))
            except ValueError:
                return None
    return None


def _betraege(text: str) -> list[Decimal]:
    werte = []
    for treffer in _BETRAG.finditer(text):
        roh = treffer.group(1).replace(".", "").replace(",", ".")
        try:
            werte.append(Decimal(roh))
        except Exception:                       # pragma: no cover - defensiv
            continue
    return werte


def stichtag_finden(text: str) -> date | None:
    """Der Stichtag gilt fuer die ganze Aufgabe, nicht je Abschnitt."""
    treffer = _STICHTAG.search(text or "")
    return _datum(treffer.group(1)) if treffer else None


def _abschnitte(text: str) -> list[str]:
    """Zerlegt die Aufgabe in Abschnitte - Zeilen und Aufzaehlungspunkte.

    Gerechnet wird nur innerhalb eines Abschnitts. Ein Betrag aus Zeile
    drei und ein Datum aus Zeile sieben gehoeren nicht zwingend zusammen;
    sie zusammenzurechnen waere geraten.
    """
    # Getrennt wird an Zeilenenden und an Aufzaehlungszeichen - nicht an
    # Satzpunkten. Der erste Entwurf trennte auch nach einem Punkt vor
    # einer Ziffer; damit zerriss "(inkl. 19% MwSt.)" den Abschnitt
    # mitten in einer Anlage, und der Kaufpreis stand plotzlich ohne
    # Anschaffungsdatum da. Die Anlage fiel stillschweigend heraus.
    roh = re.split(r"[\n\r]+|\s+(?=\u2022)", text or "")
    return [teil.strip() for teil in roh if teil and teil.strip()]


def lesen(frage: str) -> list[Rechnung]:
    """Sucht rechenbare Angaben und rechnet sie aus.

    Gibt eine leere Liste zurueck, wenn nichts eindeutig rechenbar ist -
    das ist der Normalfall und kein Fehler.
    """
    text = frage or ""
    stichtag = stichtag_finden(text)
    if stichtag is None:
        # Ohne Stichtag ist weder eine AfA noch eine Abgrenzung bestimmt.
        return []

    ergebnisse: list[Rechnung] = []
    for abschnitt in _abschnitte(text):
        rechnung = _afa_aus(abschnitt, stichtag)
        if rechnung is not None:
            ergebnisse.append(rechnung)
            continue
        rechnung = _abgrenzung_aus(abschnitt, stichtag)
        if rechnung is not None:
            ergebnisse.append(rechnung)
    return ergebnisse


def _afa_aus(abschnitt: str, stichtag: date) -> Rechnung | None:
    """Braucht: Nutzungsdauer, Anschaffungsdatum und einen Betrag."""
    dauer = _NUTZUNGSDAUER.search(abschnitt)
    if not dauer:
        return None
    anschaffung = _datum(abschnitt)
    betraege = _betraege(abschnitt)
    if anschaffung is None or not betraege:
        return None

    jahre = int(dauer.group(1))
    if jahre <= 0:
        return None

    roh = max(betraege)                 # der Kaufpreis ist der groesste Wert
    zeilen: list[str] = []
    if _BRUTTO.search(abschnitt):
        satz_treffer = _STEUERSATZ.search(abschnitt)
        satz = int(satz_treffer.group(1)) if satz_treffer else 19
        netto = netto_aus_brutto(roh, satz)
        zeilen.append(
            f"Netto aus brutto: {deutsch(roh)} / (1 + {satz}%) = "
            f"{deutsch(netto)} EUR (geteilt, nicht abgezogen)")
    else:
        netto = euro(roh)

    afa = lineare_afa(netto, jahre, anschaffung, stichtag)
    zeilen.extend(afa.rechenweg())
    return Rechnung(
        art="AfA",
        bezeichnung=_bezeichnung(abschnitt),
        zeilen=zeilen,
        ergebnis=(f"AfA bis {stichtag.strftime('%d.%m.%Y')}: "
                  f"{deutsch(afa.afa_kumuliert)} EUR, Buchwert "
                  f"{deutsch(afa.buchwert)} EUR"),
        # Die Betraege in deutscher Schreibweise, damit sie in einer
        # erzeugten Tabelle als Zahl und nicht als Text ankommen. Die
        # Stueckzahlen (Jahre, Monate) bleiben schlichte Ziffern.
        felder=[
            ("Anschaffungsdatum", anschaffung.strftime("%d.%m.%Y")),
            ("Anschaffungswert netto (EUR)", deutsch(afa.anschaffungswert)),
            ("Nutzungsdauer (Jahre)", str(jahre)),
            ("AfA pro Jahr (EUR)", deutsch(afa.afa_pro_jahr)),
            ("Abschreibungsmonate", str(afa.monate)),
            ("AfA kumuliert (EUR)", deutsch(afa.afa_kumuliert)),
            ("Buchwert am Stichtag (EUR)", deutsch(afa.buchwert)),
        ],
    )


def _abgrenzung_aus(abschnitt: str, stichtag: date) -> Rechnung | None:
    """Braucht: einen Zeitraum (von-bis) und einen Betrag."""
    zeitraum = _ZEITRAUM.search(abschnitt)
    if not zeitraum:
        return None
    beginn = _datum(zeitraum.group(1))
    ende = _datum(zeitraum.group(2))
    betraege = _betraege(abschnitt)
    if beginn is None or ende is None or not betraege or ende < beginn:
        return None

    betrag = max(betraege)
    art, offen = _richtung(abschnitt)

    tag = abgrenzen(betrag, beginn, ende, stichtag, art=art, basis="tag")
    zeilen = ["Taggenau:"]
    zeilen += ["  " + z for z in tag.rechenweg()]

    # Monatsweise nur, wenn der Zeitraum volle Kalendermonate abdeckt.
    # Sonst kommt Unsinn heraus: 15.09. bis 14.09. des Folgejahres ist
    # ein Jahr, beruehrt aber dreizehn Kalendermonate. Genau das stand
    # zuerst in der Antwort - "13 Monate" fuer eine Jahreslizenz.
    if ganze_monate(beginn, ende):
        monat = abgrenzen(betrag, beginn, ende, stichtag, art=art,
                          basis="monat")
        zeilen += ["Monatsgenau:"]
        zeilen += ["  " + z for z in monat.rechenweg()]
        zeilen.append(
            "Welche Basis gilt, entscheidet der Betrieb. Beide Wege sind "
            "zulaessig; die Ergebnisse weichen voneinander ab.")
        ergebnis = (f"Abzugrenzen zum {stichtag.strftime('%d.%m.%Y')}: "
                    f"{deutsch(tag.betrag_abgrenzung)} EUR taggenau / "
                    f"{deutsch(monat.betrag_abgrenzung)} EUR monatsgenau")
    else:
        zeilen.append(
            "Eine monatsweise Aufteilung ist hier nicht sinnvoll: der "
            "Zeitraum beginnt nicht am Monatsersten und endet nicht am "
            "Monatsletzten. Er deckt keine vollen Kalendermonate ab.")
        ergebnis = (f"Abzugrenzen zum {stichtag.strftime('%d.%m.%Y')}: "
                    f"{deutsch(tag.betrag_abgrenzung)} EUR (taggenau)")

    felder = [
        ("Betrag (EUR)", deutsch(tag.betrag)),
        ("Zeitraum", f"{beginn.strftime('%d.%m.%Y')} bis "
                     f"{ende.strftime('%d.%m.%Y')}"),
        ("Posten", tag.art),
        ("Tage gesamt", str(tag.einheiten_gesamt)),
        ("Tage bis Stichtag", str(tag.einheiten_verbraucht)),
        ("Laufende Periode taggenau (EUR)", deutsch(tag.betrag_periode)),
        ("Abzugrenzen taggenau (EUR)", deutsch(tag.betrag_abgrenzung)),
    ]
    if ganze_monate(beginn, ende):
        felder.append(("Abzugrenzen monatsgenau (EUR)",
                       deutsch(monat.betrag_abgrenzung)))

    return Rechnung(
        art="Abgrenzung",
        bezeichnung=_bezeichnung(abschnitt),
        zeilen=zeilen,
        ergebnis=ergebnis,
        offene_frage=offen,
        felder=felder,
    )


def _richtung(abschnitt: str) -> tuple[str, str]:
    """ARAP oder PRAP - und wenn unklar, wird das gesagt statt geraten."""
    ertrag = bool(_ERTRAG.search(abschnitt))
    aufwand = bool(_AUFWAND.search(abschnitt))
    if ertrag and not aufwand:
        return "PRAP", ""
    if aufwand and not ertrag:
        return "ARAP", ""
    return "ARAP", (
        "Die Richtung ist aus dem Text nicht eindeutig. Haben wir gezahlt, "
        "ist es ein ARAP (Aktivposten, mindert den Aufwand). Haben wir "
        "kassiert, ist es ein PRAP (Passivposten, mindert den Ertrag). Der "
        "Betrag ist in beiden Faellen derselbe.")


def _bezeichnung(abschnitt: str) -> str:
    """Ein kurzer Name fuer die Zeile - aus dem Anfang des Abschnitts."""
    roh = re.sub(r"^[\s•\-\*\d\.\)]+", "", abschnitt).strip()
    roh = re.split(r"[:\|\.]", roh)[0].strip()
    return (roh[:60] or "Posten")
