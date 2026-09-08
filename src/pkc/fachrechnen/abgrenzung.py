"""Rechnungsabgrenzung - taggenau oder monatsgenau.

Der Fehler, der zu diesem Modul gefuehrt hat: 24.000 EUR Jahreslizenz,
bezahlt am 15.09.2026, Stichtag 30.09.2026. Das Modell rechnete

    24.000 / 365 = 65,75 pro Tag,  mal 91 Tage = 5.995.553,43 EUR

Zwei Fehler in einer Zeile. Erstens die 91 Tage: das ist der Abstand vom
Jahresbeginn, nicht vom Vertragsbeginn - richtig sind 16 Tage
(15.09. bis 30.09.). Zweitens die Multiplikation selbst: 65,75 mal 91
ergibt 5.983,58 und nicht 5.995.553,43. Aus 24.000 EUR wurden fast sechs
Millionen, und niemand hat es gemerkt.

**Die beiden Richtungen, die man nicht verwechseln darf:**

* **ARAP** (aktiver Rechnungsabgrenzungsposten): Wir haben **gezahlt**
  und bekommen die Leistung erst spaeter. Der Teil, der ins naechste
  Jahr gehoert, mindert den Aufwand. Beispiel: vorausgezahlte
  Versicherung.
* **PRAP** (passiver Rechnungsabgrenzungsposten): Wir haben **kassiert**
  und erbringen die Leistung erst spaeter. Der Teil, der ins naechste
  Jahr gehoert, mindert den Ertrag. Beispiel: vorausbezahlte
  Jahreslizenz.

**Eine Rueckstellung ist kein ARAP.** Sie ist eine ungewisse
Verbindlichkeit und steht auf der Passivseite. Das Modell hatte auch das
verwechselt; deshalb steht es hier ausdruecklich.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from .geld import euro


@dataclass(frozen=True)
class Abgrenzung:
    """Das Ergebnis einer Abgrenzungsrechnung - mit Rechenweg."""

    betrag: Decimal
    beginn: date
    ende: date
    stichtag: date
    basis: str                      # "tag" oder "monat"
    art: str                        # "ARAP" oder "PRAP"
    einheiten_gesamt: int
    einheiten_verbraucht: int
    einheiten_offen: int
    betrag_periode: Decimal         # gehoert in die laufende Periode
    betrag_abgrenzung: Decimal      # wird abgegrenzt

    @property
    def einheit(self) -> str:
        return "Tage" if self.basis == "tag" else "Monate"

    def _mit_einheit(self, anzahl: int) -> str:
        """"1 Monat" statt "1 Monate" - Kleinigkeit, aber sie faellt auf."""
        if anzahl == 1:
            return f"1 {'Tag' if self.basis == 'tag' else 'Monat'}"
        return f"{anzahl} {self.einheit}"

    def rechenweg(self) -> list[str]:
        zeilen = [
            f"Betrag: {self.betrag} EUR",
            f"Zeitraum: {self.beginn.strftime('%d.%m.%Y')} bis "
            f"{self.ende.strftime('%d.%m.%Y')} = "
            f"{self._mit_einheit(self.einheiten_gesamt)}",
            f"Davon bis zum Stichtag {self.stichtag.strftime('%d.%m.%Y')} "
            f"verbraucht: {self._mit_einheit(self.einheiten_verbraucht)}",
            f"Offen (nach dem Stichtag): {self._mit_einheit(self.einheiten_offen)}",
            f"In der laufenden Periode: {self.betrag} x "
            f"{self.einheiten_verbraucht} / {self.einheiten_gesamt} "
            f"= {self.betrag_periode} EUR",
            f"Abzugrenzen ({self.art}): {self.betrag} x {self.einheiten_offen} "
            f"/ {self.einheiten_gesamt} = {self.betrag_abgrenzung} EUR",
        ]
        if self.art == "ARAP":
            zeilen.append(
                f"Buchungssatz: ARAP an Aufwand {self.betrag_abgrenzung} EUR "
                "(mindert den Aufwand der laufenden Periode)")
        else:
            zeilen.append(
                f"Buchungssatz: Ertrag an PRAP {self.betrag_abgrenzung} EUR "
                "(mindert den Ertrag der laufenden Periode)")
        return zeilen


def _monate_gesamt(beginn: date, ende: date) -> int:
    """Angefangene Monate eines Zeitraums, beide Enden eingeschlossen."""
    return ((ende.year - beginn.year) * 12 + (ende.month - beginn.month)) + 1


def _letzter_tag(tag: date) -> bool:
    """Ist das der letzte Tag seines Monats?"""
    naechster = (tag.replace(day=28) + timedelta(days=4)).replace(day=1)
    return (naechster - timedelta(days=1)) == tag


def ganze_monate(beginn: date, ende: date) -> bool:
    """Deckt der Zeitraum volle Kalendermonate ab?

    Nur dann ist eine monatsweise Aufteilung sinnvoll. Ein Zeitraum vom
    15.09. bis zum 14.09. des Folgejahres ist ein Jahr - beruehrt aber
    dreizehn Kalendermonate. Wer ihn durch dreizehn teilt, bekommt eine
    Zahl, die zu nichts passt; und genau das stand zuerst in der
    Antwort: "13 Monate" fuer eine Jahreslizenz.
    """
    return beginn.day == 1 and _letzter_tag(ende)


def abgrenzen(betrag, beginn: date, ende: date, stichtag: date,
              art: str = "ARAP", basis: str = "tag") -> Abgrenzung:
    """Teilt einen Betrag am Stichtag in verbrauchten und offenen Teil.

    ``art`` ist ``"ARAP"`` (vorausgezahlter Aufwand) oder ``"PRAP"``
    (vorausvereinnahmter Ertrag). ``basis`` ist ``"tag"`` oder
    ``"monat"``; beides ist zulaessig, die Ergebnisse weichen leicht
    voneinander ab. Welche Basis gilt, entscheidet der Betrieb - nicht
    dieses Modul.

    Gerechnet wird **ab Vertragsbeginn**, niemals ab Jahresbeginn. Genau
    daran ist das Modell gescheitert.
    """
    art = art.upper()
    if art not in ("ARAP", "PRAP"):
        raise ValueError('art muss "ARAP" oder "PRAP" sein.')
    basis = basis.lower()
    if basis not in ("tag", "monat"):
        raise ValueError('basis muss "tag" oder "monat" sein.')
    if ende < beginn:
        raise ValueError("Das Ende des Zeitraums liegt vor seinem Beginn.")

    wert = euro(betrag)

    if basis == "tag":
        # Beide Enden eingeschlossen: 15.09. bis 14.09. des Folgejahres
        # sind 365 Tage.
        gesamt = (ende - beginn).days + 1
        if stichtag < beginn:
            verbraucht = 0
        elif stichtag >= ende:
            verbraucht = gesamt
        else:
            verbraucht = (stichtag - beginn).days + 1
    else:
        gesamt = _monate_gesamt(beginn, ende)
        if stichtag < beginn:
            verbraucht = 0
        elif stichtag >= ende:
            verbraucht = gesamt
        else:
            verbraucht = _monate_gesamt(beginn, stichtag)

    offen = gesamt - verbraucht
    anteil_offen = Decimal(offen) / Decimal(gesamt)
    abgrenzung = euro(wert * anteil_offen)
    # Der Rest ergibt sich als Differenz, nicht als zweite Rundung -
    # sonst fehlt oder entsteht ein Cent.
    periode = euro(wert - abgrenzung)

    return Abgrenzung(
        betrag=wert, beginn=beginn, ende=ende, stichtag=stichtag,
        basis=basis, art=art, einheiten_gesamt=gesamt,
        einheiten_verbraucht=verbraucht, einheiten_offen=offen,
        betrag_periode=periode, betrag_abgrenzung=abgrenzung,
    )
