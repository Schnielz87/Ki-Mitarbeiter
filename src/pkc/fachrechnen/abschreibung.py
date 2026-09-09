"""Lineare Abschreibung, monatsgenau.

Der Fehler, der zu diesem Modul gefuehrt hat: Ein Fahrzeug wurde am
15.03.2026 angeschafft, Stichtag war der 30.09.2026. Das Modell rechnete
**neun** Monate ab - weil September der neunte Monat des Kalenderjahres
ist. Richtig sind **sieben** Monate: Maerz bis September.

Die Regel ist nicht schwer, aber sie muss angewandt und nicht erraten
werden:

* Gezaehlt wird ab dem **Anschaffungsmonat**, nicht ab Jahresbeginn.
* Der Anschaffungsmonat zaehlt **voll** mit, auch wenn am 31. angeschafft
  wurde (§ 7 Abs. 1 EStG, monatsgenaue Aufteilung).
* Mehr als die Nutzungsdauer wird nicht abgeschrieben; danach steht das
  Wirtschaftsgut mit null in den Buechern.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .geld import deutsch, euro


@dataclass(frozen=True)
class Abschreibung:
    """Das Ergebnis einer Abschreibungsrechnung - mit Rechenweg."""

    anschaffungswert: Decimal
    nutzungsdauer_jahre: int
    anschaffung: date
    stichtag: date
    monate: int
    afa_pro_jahr: Decimal
    afa_pro_monat: Decimal
    afa_kumuliert: Decimal
    buchwert: Decimal

    def rechenweg(self) -> list[str]:
        """Der Weg zum Ergebnis, Zeile fuer Zeile.

        Steht so in der Antwort. Ein Ergebnis ohne Rechenweg kann man
        nicht pruefen - und pruefen muss es ein Mensch.
        """
        return [
            f"Anschaffungswert (netto): {deutsch(self.anschaffungswert)} EUR",
            f"Nutzungsdauer: {self.nutzungsdauer_jahre} Jahre",
            f"AfA pro Jahr: {deutsch(self.anschaffungswert)} / "
            f"{self.nutzungsdauer_jahre} = {deutsch(self.afa_pro_jahr)} EUR",
            f"AfA pro Monat: {deutsch(self.afa_pro_jahr)} / 12 = "
            f"{deutsch(self.afa_pro_monat)} EUR "
            "(gerundet; gerechnet wird ungerundet)",
            f"Monate von {self.anschaffung.strftime('%m/%Y')} bis "
            f"{self.stichtag.strftime('%m/%Y')} (Anschaffungsmonat zaehlt voll): "
            f"{self.monate}",
            f"AfA kumuliert: {self.monate} x {deutsch(self.afa_pro_monat)} "
            f"= {deutsch(self.afa_kumuliert)} EUR",
            f"Buchwert am {self.stichtag.strftime('%d.%m.%Y')}: "
            f"{deutsch(self.anschaffungswert)} - {deutsch(self.afa_kumuliert)} "
            f"= {deutsch(self.buchwert)} EUR",
        ]


def monate_zwischen(anschaffung: date, stichtag: date) -> int:
    """Volle Abschreibungsmonate vom Anschaffungsmonat bis zum Stichtag.

    Der Anschaffungsmonat zaehlt mit, deshalb das ``+ 1``. Vor der
    Anschaffung wird nicht abgeschrieben, deshalb nie unter null.
    """
    if stichtag < anschaffung:
        return 0
    monate = ((stichtag.year - anschaffung.year) * 12
              + (stichtag.month - anschaffung.month) + 1)
    return max(monate, 0)


def lineare_afa(anschaffungswert, nutzungsdauer_jahre: int,
                anschaffung: date, stichtag: date) -> Abschreibung:
    """Berechnet die lineare AfA bis zum Stichtag.

    ``anschaffungswert`` ist der **Nettowert**. Wer einen Bruttobetrag
    hat, rechnet ihn vorher mit ``netto_aus_brutto`` heraus - das ist
    eine eigene Entscheidung und gehoert nicht stillschweigend hierhin.
    """
    if nutzungsdauer_jahre <= 0:
        raise ValueError("Die Nutzungsdauer muss groesser als null sein.")

    wert = euro(anschaffungswert)
    pro_jahr = euro(wert / Decimal(nutzungsdauer_jahre))
    pro_monat = euro(pro_jahr / Decimal(12))

    monate = monate_zwischen(anschaffung, stichtag)
    # Nicht ueber die Nutzungsdauer hinaus abschreiben.
    monate = min(monate, nutzungsdauer_jahre * 12)

    # Erst am Ende runden, nicht zwischendurch. Wer den Monatswert
    # zuerst auf den Cent rundet und dann multipliziert, bekommt bei
    # 4.000 EUR / 3 Jahre und drei Monaten 999,99 EUR statt 1.000,00 EUR
    # - der Monatswert ist 333,3333... und nicht 333,33. Der Cent klingt
    # egal, ist es in der Buchhaltung aber nicht: er wandert in die
    # Bilanz und stimmt dort mit nichts mehr ueberein.
    kumuliert = euro(pro_jahr * Decimal(monate) / Decimal(12))
    # Der Buchwert kann nicht unter null fallen. Bei voller Nutzungsdauer
    # ergaebe die Monatsrundung sonst einen Cent Differenz.
    if kumuliert > wert:
        kumuliert = wert
    buchwert = euro(wert - kumuliert)

    return Abschreibung(
        anschaffungswert=wert,
        nutzungsdauer_jahre=nutzungsdauer_jahre,
        anschaffung=anschaffung,
        stichtag=stichtag,
        monate=monate,
        afa_pro_jahr=pro_jahr,
        afa_pro_monat=pro_monat,
        afa_kumuliert=kumuliert,
        buchwert=buchwert,
    )
