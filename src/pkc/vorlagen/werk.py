"""Das Vorlagenwerk: Vorschau zeigen und Datei erzeugen.

Der Weg einer Vorlage zur Datei hat drei Schritte, und der mittlere ist
der wichtigste:

1. **Fuellen.** Platzhalter durch Werte ersetzen. Was fehlt, bleibt
   stehen.
2. **Vorschau.** Der Mensch sieht, was herauskaeme - einschliesslich der
   Stellen, die leer geblieben sind.
3. **Erzeugen.** Erst danach entsteht eine Datei, ueber die
   Artefakt-Engine, mit Fassungsnummer, Pruefsumme und Verzeichniseintrag
   wie jede andere erzeugte Datei auch.

Schritt 2 ist nicht Bequemlichkeit. Eine gefuellte Vorlage sieht aus wie
ein fertiges Dokument; sie traegt Briefkopf, Anrede und Unterschrift. Wer
sie ungesehen erzeugt, verschickt auch das, was nicht gefuellt werden
konnte.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..artefakte.modell import aus_markdown
from ..logging_setup import get_logger
from .modell import Vorlage, Vorschau
from .platzhalter import fuellen
from .speicher import VorlagenFehler
from .werte import sammeln

log = get_logger(__name__)

#: Steht unter jeder aus einer Vorlage erzeugten Datei.
FREIGABEHINWEIS = (
    "Aus einer Vorlage erzeugt. Fachliche Zuarbeit - vor der Verwendung "
    "durch einen Menschen zu pruefen und freizugeben.")


@dataclass
class Erzeugnis:
    """Die erzeugte Datei und was beim Fuellen offen blieb."""

    artefakt: object
    offen: list[str] = field(default_factory=list)
    hinweis: str = ""

    @property
    def vollstaendig(self) -> bool:
        return not self.offen


class Vorlagenwerk:
    """Verbindet Vorlagenspeicher, Werte und Artefakt-Engine."""

    def __init__(self, speicher, artefaktwerk, memory=None):
        self.speicher = speicher
        self.artefaktwerk = artefaktwerk
        self.memory = memory

    # -- Schritt 1 und 2 -----------------------------------------------
    def vorschau(self, kennung: str, zusatz: dict | None = None,
                 heute: date | None = None) -> Vorschau:
        """Fuellt die Vorlage, erzeugt aber noch keine Datei."""
        vorlage = self._holen(kennung)
        werte = sammeln(self.memory, zusatz, heute)
        fuellung = fuellen(vorlage.rumpf, werte)
        return Vorschau(
            vorlage=vorlage,
            text=fuellung.text,
            angezeigt=fuellung.vorschau(),
            gefuellt=fuellung.gefuellt,
            offen=fuellung.offen,
            hinweis=fuellung.bericht(),
        )

    def offene_felder(self, kennung: str, zusatz: dict | None = None) -> list[str]:
        """Was der Mensch noch eintragen muss, bevor es vollstaendig ist."""
        return self.vorschau(kennung, zusatz).offen

    # -- Schritt 3 -----------------------------------------------------
    def erzeugen(self, kennung: str, *, format: str = "",
                 zusatz: dict | None = None, name: str = "",
                 heute: date | None = None) -> Erzeugnis:
        """Erzeugt die Datei ueber die Artefakt-Engine.

        Offene Platzhalter verhindern das Erzeugen **nicht**. Sie
        stehen sichtbar in der Datei, werden zurueckgemeldet und
        in den Dateiangaben vermerkt. Das Erzeugen zu verweigern waere
        bevormundend: ein Entwurf, in dem drei Stellen von Hand
        auszufuellen sind, ist ein gebraeuchliches Arbeitsergebnis.
        """
        vorschau = self.vorschau(kennung, zusatz, heute)
        vorlage = vorschau.vorlage
        ziel = (format or vorlage.format or "docx").strip().lower()

        dokument = aus_markdown(vorschau.text, titel=name or vorlage.name)
        dokument.absatz(FREIGABEHINWEIS)

        angaben = {
            "vorlage": vorlage.name,
            "vorlage_kennung": vorlage.kennung,
        }
        if vorschau.offen:
            angaben["offene_platzhalter"] = ", ".join(
                dict.fromkeys(vorschau.offen))

        artefakt = self.artefaktwerk.erzeugen(
            dokument, ziel, name=name or vorlage.name, angaben=angaben)
        log.info("Aus Vorlage erzeugt: %s -> %s", vorlage.kennung,
                 artefakt.name)
        return Erzeugnis(artefakt=artefakt, offen=vorschau.offen,
                         hinweis=vorschau.hinweis)

    # -- Hilfen --------------------------------------------------------
    def _holen(self, kennung: str) -> Vorlage:
        vorlage = self.speicher.holen(kennung)
        if vorlage is None:
            raise VorlagenFehler(f"Diese Vorlage gibt es nicht: {kennung}")
        if not (vorlage.rumpf or "").strip():
            raise VorlagenFehler(
                f"Die Vorlage „{vorlage.name}“ hat keinen Inhalt mehr. "
                "Ihre Datei fehlt oder ist leer.")
        return vorlage
