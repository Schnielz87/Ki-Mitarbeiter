"""Platzhalter in einer Vorlage finden und fuellen.

Eine Vorlage ohne Platzhalter ist nur eine Datei. Die Stellen, die
gefuellt werden, sehen so aus::

    Sehr geehrte Damen und Herren der {{firma.name}},

**Der wichtigste Grundsatz dieses Moduls: was sich nicht aufloesen
laesst, bleibt stehen.** Ein Platzhalter, fuer den es keinen Wert gibt,
wird nicht durch Leere ersetzt. Er bleibt sichtbar im Text und wird
zusaetzlich gemeldet.

Der Grund ist derselbe wie ueberall in dieser Anwendung: ein Brief, in
dem "Sehr geehrte Damen und Herren der ," steht, faellt auf. Einer, in
dem die Zeile stillschweigend fehlt, geht raus. Ein sichtbarer Fehler
ist besser als ein unsichtbarer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: ``{{name}}`` - der Name darf Buchstaben, Ziffern, Punkt, Strich und
#: Unterstrich enthalten. Leerzeichen um den Namen herum sind erlaubt,
#: damit ``{{ firma.name }}`` genauso funktioniert.
MUSTER = re.compile(r"\{\{\s*([A-Za-z0-9_.\-]+)\s*\}\}")

#: Wie ein offener Platzhalter in der Vorschau hervorgehoben wird.
#: Nur fuer die Anzeige - in die erzeugte Datei geht der Platzhalter
#: unveraendert, damit man ihn dort suchen und ersetzen kann.
MARKE = "▸ {name} ◂"


@dataclass
class Fuellung:
    """Das Ergebnis eines Fuellvorgangs."""

    text: str
    #: Welcher Platzhalter mit welchem Wert belegt wurde.
    gefuellt: dict[str, str] = field(default_factory=dict)
    #: Welche Platzhalter keinen Wert hatten - in der Reihenfolge des Texts.
    offen: list[str] = field(default_factory=list)

    @property
    def vollstaendig(self) -> bool:
        return not self.offen

    def vorschau(self) -> str:
        """Derselbe Text, offene Stellen sichtbar hervorgehoben."""
        def ersetzen(treffer: re.Match) -> str:
            return MARKE.format(name=treffer.group(1))

        return MUSTER.sub(ersetzen, self.text)

    def bericht(self) -> str:
        """Ein Satz fuer den Menschen davor - oder nichts."""
        if not self.offen:
            return ""
        namen = ", ".join(dict.fromkeys(self.offen))
        if len(set(self.offen)) == 1:
            return (f"Fuer den Platzhalter {namen} gibt es keinen Wert. "
                    "Er steht unveraendert in der Vorlage und muss von "
                    "Hand ergaenzt werden.")
        return (f"Fuer diese Platzhalter gibt es keinen Wert: {namen}. "
                "Sie stehen unveraendert in der Vorlage und muessen von "
                "Hand ergaenzt werden.")


def finden(text: str) -> list[str]:
    """Alle Platzhalternamen eines Texts, ohne Wiederholung, in Reihenfolge."""
    return list(dict.fromkeys(MUSTER.findall(text or "")))


def fuellen(text: str, werte: dict) -> Fuellung:
    """Setzt die Werte ein. Was fehlt, bleibt stehen und wird gemeldet.

    ``werte`` darf auch verschachtelt sein: ``{"firma": {"name": "X"}}``
    beantwortet ``{{firma.name}}``. Flache Schluessel mit Punkt
    (``{"firma.name": "X"}``) gehen ebenso; die flache Angabe hat
    Vorrang, weil sie die genauere ist.
    """
    gefuellt: dict[str, str] = {}
    offen: list[str] = []

    def ersetzen(treffer: re.Match) -> str:
        name = treffer.group(1)
        wert = _aufloesen(name, werte or {})
        if wert is None:
            offen.append(name)
            return treffer.group(0)         # unveraendert stehen lassen
        gefuellt[name] = wert
        return wert

    ergebnis = MUSTER.sub(ersetzen, text or "")
    return Fuellung(text=ergebnis, gefuellt=gefuellt, offen=offen)


def _aufloesen(name: str, werte: dict) -> str | None:
    """Sucht einen Wert - erst flach, dann ueber die Punkte hinweg."""
    if name in werte:
        return _als_text(werte[name])

    aktuell = werte
    for teil in name.split("."):
        if not isinstance(aktuell, dict) or teil not in aktuell:
            return None
        aktuell = aktuell[teil]
    return _als_text(aktuell)


def _als_text(wert) -> str | None:
    """Ein leerer Wert ist kein Wert.

    Sonst entstuende genau der stille Ausfall, den dieses Modul
    verhindern soll: der Platzhalter waere weg, die Stelle leer, und
    niemand haette es gemerkt.
    """
    if wert is None:
        return None
    if isinstance(wert, (dict, list, tuple, set)):
        return None
    text = str(wert).strip()
    return text or None


def beschriftung(name: str) -> str:
    """Aus "mandant.name" wird "Mandant · Name".

    Rein mechanisch und ohne Woerterbuch. Ein Woerterbuch waere fuer die
    bekannten Platzhalter huebscher und fuer jeden neuen falsch: wer eine
    eigene Vorlage mit ``{{projektnummer}}`` aufnimmt, soll keine
    Beschriftung "projektnummer" zwischen lauter ausgeschriebenen
    bekommen.
    """
    teile = [t for t in (name or "").split(".") if t]
    if not teile:
        return name or ""
    return " \u00b7 ".join(t[:1].upper() + t[1:] for t in teile)
