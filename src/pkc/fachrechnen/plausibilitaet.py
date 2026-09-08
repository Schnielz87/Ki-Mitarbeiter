"""Prueft Zahlen einer Antwort auf offensichtliche Unmoeglichkeit.

**Warum das noetig ist.** Das Modell schrieb bei einer Ausgangsbasis von
24.000 EUR ein Ergebnis von 5.995.553,43 EUR - das 250-fache. Kein
Mensch, der die Aufgabe liest, wuerde das durchgehen lassen. Die
Anwendung tat es.

Dieses Modul ersetzt keine fachliche Pruefung. Es faengt das ab, was
ohne jedes Fachwissen erkennbar falsch ist:

* Ein Anteil eines Betrags kann nicht groesser sein als der Betrag.
* Ein Ergebnis, das um ein Vielfaches ueber allen genannten
  Ausgangsbetraegen liegt, ist ein Zahlendreher oder eine Halluzination.
* Ein Prozentsatz ueber 100 bei einer Aufteilung ist keiner.

**Was es ausdruecklich nicht tut:** entscheiden, ob eine Zahl fachlich
richtig ist. Eine Abgrenzung von 12.000 EUR statt 22.947,95 EUR ist
plausibel und trotzdem falsch. Dagegen hilft nur, richtig zu rechnen -
siehe die uebrigen Module dieses Pakets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

#: Ab dem Wievielfachen des groessten Ausgangsbetrags gilt ein Ergebnis
#: als unmoeglich. Bewusst grosszuegig: Summen ueber viele Posten duerfen
#: deutlich groesser sein als jeder Einzelposten. Es geht um Ausreisser
#: der Groessenordnung, nicht um knappe Faelle.
FAKTOR_UNMOEGLICH = Decimal("20")

#: Zahlen unterhalb dieser Grenze werden nicht geprueft. Jahreszahlen,
#: Paragrafen, Monatszahlen und Kontonummern sind keine Betraege.
KLEINSTBETRAG = Decimal("1000")

#: Deutsche Betragsschreibweise: 1.234.567,89 oder 1234,56 oder 24000
_ZAHL = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)(?![\d.,])")


@dataclass(frozen=True)
class Befund:
    """Ein Verdachtsfall - kein Urteil."""

    zahl: Decimal
    text: str
    art: str

    def __str__(self) -> str:                       # pragma: no cover - Anzeige
        return self.text


def zahlen_aus(text: str) -> list[Decimal]:
    """Liest alle Betraege aus einem Text - deutsche Schreibweise."""
    gefunden = []
    for treffer in _ZAHL.finditer(text or ""):
        roh = treffer.group(1).replace(".", "").replace(",", ".")
        try:
            gefunden.append(Decimal(roh))
        except InvalidOperation:                    # pragma: no cover - defensiv
            continue
    return gefunden


def pruefe_zahlen(frage: str, antwort: str) -> list[Befund]:
    """Vergleicht die Zahlen der Antwort mit denen der Frage.

    Der Massstab kommt aus der Frage: was dort an Betraegen steht, gibt
    die Groessenordnung vor. Steht in der Frage keine Zahl, wird nicht
    geprueft - dann fehlt der Massstab, und ein Verdacht ohne Massstab
    waere geraten.
    """
    aus_frage = [z for z in zahlen_aus(frage) if z >= KLEINSTBETRAG]
    if not aus_frage:
        return []

    groesster = max(aus_frage)
    grenze = groesster * FAKTOR_UNMOEGLICH

    befunde: list[Befund] = []
    gemeldet: set[Decimal] = set()
    for zahl in zahlen_aus(antwort):
        if zahl <= grenze or zahl in gemeldet:
            continue
        gemeldet.add(zahl)
        befunde.append(Befund(
            zahl=zahl,
            art="groessenordnung",
            text=(
                f"Die Antwort nennt {_de(zahl)} EUR. Der groesste Betrag in "
                f"der Aufgabe ist {_de(groesster)} EUR - das Ergebnis ist "
                f"mehr als das {int(FAKTOR_UNMOEGLICH)}-fache davon. Das ist "
                "sehr wahrscheinlich ein Rechenfehler."
            ),
        ))
    return befunde


def _de(zahl: Decimal) -> str:
    """Deutsche Schreibweise mit Tausenderpunkt."""
    ganz = f"{zahl:,.2f}"
    return ganz.replace(",", "#").replace(".", ",").replace("#", ".")
