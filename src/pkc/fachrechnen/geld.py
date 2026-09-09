"""Geldbetraege - kaufmaennisch gerundet, nicht als Fliesskommazahl.

``0.1 + 0.2`` ergibt in Fliesskomma nicht ``0.3``. Bei einem Betrag
faellt das irgendwann auf den Cent durch, und in der Buchhaltung ist ein
Cent ein Fehler. Deshalb ueberall ``Decimal``.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

#: Auf zwei Nachkommastellen, kaufmaennisch (0,005 wird zu 0,01).
CENT = Decimal("0.01")


def euro(wert) -> Decimal:
    """Macht aus einer Zahl einen auf den Cent gerundeten Betrag."""
    return Decimal(str(wert)).quantize(CENT, rounding=ROUND_HALF_UP)


def deutsch(betrag) -> str:
    """Deutsche Schreibweise: 45000.00 wird zu "45.000,00".

    Zwei Gruende. Erstens liest ein deutscher Buchhalter Betraege so.
    Zweitens erkennt der Tabellenschreiber eine Zahl an ihrem
    Dezimalkomma; ohne Komma landet der Betrag als Text in der Zelle und
    Excel kann nicht damit rechnen. Genau das war der Fall - in der
    erzeugten Arbeitsmappe standen alle Betraege als Text.

    Die Strenge des Tabellenschreibers ist dabei richtig und bleibt: sie
    schuetzt Kontonummern und Belegnummern davor, in Zahlen verwandelt
    zu werden und ihre fuehrende Null zu verlieren.
    """
    zahl = Decimal(str(betrag)).quantize(CENT, rounding=ROUND_HALF_UP)
    ganz = f"{zahl:,.2f}"
    return ganz.replace(",", "#").replace(".", ",").replace("#", ".")


def _satz(steuersatz) -> Decimal:
    """Nimmt 19, 0.19 oder "19%" und macht daraus 0.19."""
    if isinstance(steuersatz, str):
        steuersatz = steuersatz.strip().rstrip("%")
    wert = Decimal(str(steuersatz))
    return wert / Decimal(100) if wert >= 1 else wert


def netto_aus_brutto(brutto, steuersatz=19) -> Decimal:
    """Rechnet die Umsatzsteuer heraus.

    ``netto_aus_brutto("53550", 19)`` ergibt ``45000.00``.

    Bewusst nicht ``brutto * 0.81``: das waere ein Abzug von 19 Prozent
    vom Bruttobetrag und ergaebe 43.375,50 EUR. Der Unterschied von ueber
    1.600 EUR ist der haeufigste Rechenfehler ueberhaupt bei dieser
    Aufgabe.
    """
    return euro(Decimal(str(brutto)) / (Decimal(1) + _satz(steuersatz)))


def umsatzsteuer_aus_brutto(brutto, steuersatz=19) -> Decimal:
    """Der Steueranteil eines Bruttobetrags."""
    return euro(Decimal(str(brutto)) - netto_aus_brutto(brutto, steuersatz))
