"""Buchhalterische Berechnungen - ausgerechnet, nicht geraten.

**Warum es dieses Paket gibt.** Ein Sprachmodell rechnet nicht. Es sagt
das naechste Wort vorher, und eine Zahl ist fuer es ein Wort wie jedes
andere. Bei einfachen Zahlen geht das oft gut. Bei einer
Abgrenzungsrechnung ueber zwei Kalenderjahre geht es schief, und zwar
lautlos: es kommt eine Zahl heraus, die aussieht wie ein Ergebnis.

Der belegte Fall, der zu diesem Paket gefuehrt hat:

* Aufgabe: 24.000 EUR Jahreslizenz, bezahlt am 15.09.2026, Stichtag
  30.09.2026. Gefragt war der abzugrenzende Betrag.
* Antwort des Modells: **5.995.553,43 EUR**. Aus 24.000 EUR wurden
  fast sechs Millionen. Das Modell hatte ausserdem mit dem 91. Tag des
  Kalenderjahres gerechnet statt mit dem 16. Tag der Vertragslaufzeit.
* Richtig sind 22.947,95 EUR.

Ein zweiter Versuch derselben Aufgabe rechnete die Abschreibung eines im
Maerz angeschafften Fahrzeugs ueber neun Monate ab, weil der Stichtag im
neunten Monat des Jahres liegt. Richtig sind sieben Monate.

**Die Schlussfolgerung ist nicht "das Modell muss besser rechnen".** Sie
lautet: das Modell darf gar nicht rechnen. Was sich ausrechnen laesst,
wird hier ausgerechnet - in Python, mit ``Decimal``, nachvollziehbar und
gegen bekannte Faelle geprueft. Das Modell bekommt die fertigen Zahlen
und formuliert daraus einen Text.

**Was hier bewusst nicht passiert:** Dieses Paket faellt keine
steuerliche Entscheidung. Es rechnet aus, was jemand entschieden hat -
welche Methode, welcher Zeitraum, welche Nutzungsdauer. Die Entscheidung
trifft ein Mensch, und die Antwort sagt das auch weiterhin.
"""

from .geld import euro, netto_aus_brutto, umsatzsteuer_aus_brutto
from .abschreibung import Abschreibung, lineare_afa
from .abgrenzung import Abgrenzung, abgrenzen
from .plausibilitaet import Befund, pruefe_zahlen

__all__ = [
    "euro",
    "netto_aus_brutto",
    "umsatzsteuer_aus_brutto",
    "Abschreibung",
    "lineare_afa",
    "Abgrenzung",
    "abgrenzen",
    "Befund",
    "pruefe_zahlen",
]
