"""Der Antwortspeicher - Hebel 4 aus ANTWORTZEIT_KONZEPT.md.

Dieselbe Frage zweimal zu stellen ist im Buero der Normalfall. Die zweite
Antwort dauert heute genauso lange wie die erste, obwohl sich nichts
geaendert hat. Das muss nicht sein.

**Die eine Regel, die alles andere traegt: eine wiederverwendete Antwort
wird als solche gekennzeichnet.** Eine gespeicherte Antwort als frisch
auszugeben waere eine Taeuschung - und zwar eine gefaehrliche: wer eine
Frage zum zweiten Mal stellt, tut das oft, weil sich etwas geaendert hat.

**Woran der Speicher erkennt, dass er nicht mehr gilt.** Der Schluessel
umfasst alles, was das Ergebnis veraendern kann:

* die Frage selbst,
* das Profil (ein Buchhalter antwortet anders als ein Jurist),
* den Wissensstand (neue amtliche Quellen),
* das Modell und die Tempostufe (andere Antwortlaenge, andere Tiefe),
* die Betriebsart,
* den **Stand des Unternehmensgedaechtnisses**.

Der letzte Punkt ist der wichtigste und am leichtesten zu uebersehen.
Wer seinen Kontenrahmen von SKR03 auf SKR04 umstellt, bekommt zu
derselben Frage eine andere Antwort. Ein Speicher, der das nicht merkt,
antwortet mit dem Stand von vorgestern.

**Was nicht gespeichert wird:** Antworten, bei denen kein Sprachmodell
geantwortet hat. Der Notbetrieb gibt eine Ersatzantwort aus; sie
festzuhalten hiesse, den Notbetrieb zu verewigen.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime

from ..logging_setup import get_logger

log = get_logger(__name__)

#: Wieviele Antworten hoechstens aufgehoben werden. Darueber faellt die
#: am laengsten unbenutzte heraus.
GRENZE = 200

#: Steht unter einer wiederverwendeten Antwort.
MARKE = ("*Aus dem Antwortspeicher - diese Antwort wurde am {wann} "
         "erstellt und seither nicht neu berechnet. Sie beruht auf "
         "demselben Wissensstand und denselben Unternehmensangaben wie "
         "damals; haette sich daran etwas geaendert, waere neu gerechnet "
         "worden.*")

_MEHRFACHER_RAUM = re.compile(r"\s+")


def frage_vereinheitlichen(frage: str) -> str:
    """"Was ist Buchhaltung?" und "was ist buchhaltung" sind dieselbe Frage.

    Bewusst zurueckhaltend: Gross- und Kleinschreibung und ueberzaehlige
    Leerzeichen. Nicht die Zeichensetzung - "Ist X zulaessig?" und "Ist X
    zulaessig" sind zwar dieselbe Frage, aber "10.000" und "10000" sind
    es nicht, und eine Regel, die das eine tut und das andere lassen
    soll, wird falsch.
    """
    return _MEHRFACHER_RAUM.sub(" ", (frage or "").strip().lower())


@dataclass(frozen=True)
class Treffer:
    """Eine wiederverwendete Antwort."""

    daten: dict
    erstellt: str
    treffer_nummer: int

    @property
    def erstellt_lesbar(self) -> str:
        try:
            wann = datetime.fromisoformat(self.erstellt)
        except ValueError:                      # pragma: no cover - defensiv
            return self.erstellt
        return wann.strftime("%d.%m.%Y um %H:%M")

    def marke(self) -> str:
        return MARKE.format(wann=self.erstellt_lesbar)


class Antwortspeicher:
    """Haelt fertige Antworten fest, solange sie noch gelten."""

    def __init__(self, db, grenze: int = GRENZE, aktiv: bool = True):
        self.db = db
        self.grenze = max(1, int(grenze))
        self.aktiv = bool(aktiv)

    # -- Der Schluessel ------------------------------------------------
    def schluessel(self, frage: str, *, profil: str = "",
                   wissensstand: str = "", modell: str = "",
                   tempo: str = "", betriebsart: str = "",
                   gedaechtnis: str = "") -> str:
        roh = "␟".join((
            frage_vereinheitlichen(frage), profil or "", wissensstand or "",
            modell or "", tempo or "", betriebsart or "", gedaechtnis or "",
        ))
        return hashlib.sha256(roh.encode("utf-8")).hexdigest()

    @staticmethod
    def gedaechtnisstand(memory) -> str:
        """Ein kurzer Fingerabdruck des Unternehmensgedaechtnisses.

        Anzahl der aktiven Eintraege und der juengste Aenderungszeitpunkt.
        Beides zusammen faengt sowohl neue und geloeschte als auch
        geaenderte Eintraege ab - ein Zaehler allein wuerde eine Aenderung
        uebersehen, ein Zeitstempel allein eine Loeschung.
        """
        if memory is None:
            return ""
        try:
            eintraege = memory.list(status="active")
        except Exception as fehler:             # pragma: no cover - defensiv
            log.debug("Gedaechtnisstand nicht lesbar: %s", fehler)
            # Im Zweifel nicht wiederverwenden: ein zufaelliger Wert
            # sorgt dafuer, dass neu gerechnet wird.
            return datetime.now().isoformat()
        juengste = max((getattr(e, "updated_at", "") or ""
                        for e in eintraege), default="")
        return f"{len(eintraege)}@{juengste}"

    # -- Lesen und Schreiben -------------------------------------------
    def holen(self, schluessel: str) -> Treffer | None:
        if not self.aktiv:
            return None
        zeile = self.db.one(
            "SELECT answer_json, created_at, hits FROM answer_cache"
            " WHERE cache_key = ?", (schluessel,))
        if zeile is None:
            return None
        try:
            daten = json.loads(zeile["answer_json"])
        except json.JSONDecodeError:            # pragma: no cover - defensiv
            self.db.execute("DELETE FROM answer_cache WHERE cache_key = ?",
                            (schluessel,))
            return None
        nummer = int(zeile["hits"] or 0) + 1
        self.db.execute(
            "UPDATE answer_cache SET used_at = ?, hits = ? WHERE cache_key = ?",
            (datetime.now().isoformat(timespec="seconds"), nummer, schluessel))
        log.info("Antwort aus dem Speicher (%d. Verwendung)", nummer)
        return Treffer(daten=daten, erstellt=zeile["created_at"],
                       treffer_nummer=nummer)

    def merken(self, schluessel: str, frage: str, daten: dict) -> None:
        if not self.aktiv:
            return
        jetzt = datetime.now().isoformat(timespec="seconds")
        self.db.execute(
            "INSERT OR REPLACE INTO answer_cache"
            " (cache_key, question, answer_json, created_at, used_at, hits)"
            " VALUES (?,?,?,?,?,0)",
            (schluessel, frage, json.dumps(daten, ensure_ascii=False),
             jetzt, jetzt))
        self._stutzen()

    def _stutzen(self) -> None:
        """Haelt den Speicher klein - die aeltesten Benutzungen fliegen."""
        anzahl = int(self.db.scalar(
            "SELECT COUNT(*) FROM answer_cache", default=0) or 0)
        if anzahl <= self.grenze:
            return
        self.db.execute(
            "DELETE FROM answer_cache WHERE cache_key IN ("
            " SELECT cache_key FROM answer_cache ORDER BY used_at ASC LIMIT ?)",
            (anzahl - self.grenze,))

    # -- Verwalten -----------------------------------------------------
    def leeren(self) -> int:
        anzahl = int(self.db.scalar(
            "SELECT COUNT(*) FROM answer_cache", default=0) or 0)
        self.db.execute("DELETE FROM answer_cache")
        log.info("Antwortspeicher geleert: %d Eintraege", anzahl)
        return anzahl

    def stand(self) -> dict:
        anzahl = int(self.db.scalar(
            "SELECT COUNT(*) FROM answer_cache", default=0) or 0)
        treffer = int(self.db.scalar(
            "SELECT COALESCE(SUM(hits), 0) FROM answer_cache", default=0) or 0)
        return {"eintraege": anzahl, "wiederverwendungen": treffer,
                "aktiv": self.aktiv, "grenze": self.grenze}
