"""Aufnahme der mitgelieferten Vorlagen in den Kundenbereich.

Die Vorlagen liegen als lesbare Textdateien unter ``assets/vorlagen``
im Programmordner. Beim Start werden sie in den Vorlagenspeicher des
Kundenbereichs uebernommen - einmal, und danach nur noch, wenn sich die
mitgelieferte Fassung geaendert hat.

**Eigene Aenderungen werden nicht ueberschrieben.** Wer eine
mitgelieferte Vorlage anpasst, hat einen Grund dafuer. Die Anpassung
wieder wegzuraeumen waere aus Sicht des Anwenders ein Datenverlust,
auch wenn aus Sicht des Programms nur eine Vorgabe wiederhergestellt
wurde. Erkennbar ist die Aenderung an der Pruefsumme, die beim Aufnehmen
mitgeschrieben wird.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..logging_setup import get_logger
from .speicher import Vorlagenspeicher, kopfzeilen_lesen

log = get_logger(__name__)

#: Neben dem Verzeichnis: welche mitgelieferte Fassung schon da war.
STAND = "mitgeliefert.json"


@dataclass
class Aufnahme:
    """Was die Uebernahme getan hat."""

    neu: int = 0
    aktualisiert: int = 0
    unveraendert: int = 0
    #: Vorlagen, die der Anwender geaendert hat und die deshalb bleiben.
    geschont: list[str] = None      # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.geschont is None:
            self.geschont = []

    def als_satz(self) -> str:
        teile = []
        if self.neu:
            teile.append(f"{self.neu} neu")
        if self.aktualisiert:
            teile.append(f"{self.aktualisiert} aktualisiert")
        if self.geschont:
            teile.append(f"{len(self.geschont)} eigene Fassung behalten")
        if not teile:
            return "Vorlagen unveraendert."
        return "Mitgelieferte Vorlagen: " + ", ".join(teile) + "."


def _pruefsumme(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def quelle(paths) -> Path:
    return paths.get("assets") / "vorlagen"


def uebernehmen(speicher: Vorlagenspeicher, paths) -> Aufnahme:
    """Uebernimmt die mitgelieferten Vorlagen. Mehrfach aufrufbar."""
    ordner = quelle(paths)
    ergebnis = Aufnahme()
    if not ordner.is_dir():
        return ergebnis

    stand_datei = speicher.ordner / STAND
    stand = _stand_lesen(stand_datei)

    for datei in sorted(ordner.glob("*.md")):
        try:
            roh = datei.read_text(encoding="utf-8")
        except OSError as fehler:                       # pragma: no cover
            log.warning("Mitgelieferte Vorlage nicht lesbar: %s", fehler)
            continue
        kopf, rumpf = kopfzeilen_lesen(roh)
        kennung = datei.stem.lower()
        neue_summe = _pruefsumme(rumpf)
        alte_summe = stand.get(kennung, "")

        vorhanden = speicher.holen(kennung)
        if vorhanden is None:
            speicher.aufnehmen(
                name=kopf.get("name") or datei.stem,
                rumpf=rumpf,
                kategorie=kopf.get("kategorie") or "Allgemein",
                beschreibung=kopf.get("beschreibung") or "",
                format=kopf.get("format") or "docx",
                herkunft="mitgeliefert", kennung=kennung)
            stand[kennung] = neue_summe
            ergebnis.neu += 1
            continue

        if _pruefsumme(vorhanden.rumpf) != alte_summe and alte_summe:
            # Der Anwender hat die Vorlage geaendert. Sie bleibt, wie sie
            # ist - auch wenn eine neuere mitgelieferte Fassung vorliegt.
            ergebnis.geschont.append(vorhanden.name)
            continue

        if neue_summe == alte_summe:
            ergebnis.unveraendert += 1
            continue

        speicher.aufnehmen(
            name=kopf.get("name") or vorhanden.name,
            rumpf=rumpf,
            kategorie=kopf.get("kategorie") or vorhanden.kategorie,
            beschreibung=kopf.get("beschreibung") or vorhanden.beschreibung,
            format=kopf.get("format") or vorhanden.format,
            herkunft="mitgeliefert", kennung=kennung)
        stand[kennung] = neue_summe
        ergebnis.aktualisiert += 1

    _stand_schreiben(stand_datei, stand)
    if ergebnis.neu or ergebnis.aktualisiert or ergebnis.geschont:
        log.info("%s", ergebnis.als_satz())
    return ergebnis


def _stand_lesen(datei: Path) -> dict:
    if not datei.is_file():
        return {}
    try:
        inhalt = json.loads(datei.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return inhalt if isinstance(inhalt, dict) else {}


def _stand_schreiben(datei: Path, stand: dict) -> None:
    datei.parent.mkdir(parents=True, exist_ok=True)
    datei.write_text(json.dumps(stand, ensure_ascii=False, indent=2),
                     encoding="utf-8")
