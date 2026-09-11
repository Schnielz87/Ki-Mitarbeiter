"""Wann eine Aufgabe faellig ist.

Der Kern jeder Automation, und der Teil, an dem sich entscheidet, ob sie
brauchbar ist oder laestig.

**Die eine Festlegung, die man kennen muss:** PORTIVA laeuft nur, solange
es geoeffnet ist. Eine taegliche Aufgabe kann also einen Tag verpassen.
Beim naechsten Start wird sie **einmal** nachgeholt - nicht fuenfmal,
weil das Programm fuenf Tage aus war.

Der Grund: fuenf Sicherungen hintereinander sind keine fuenf Sicherungen,
sondern eine Sicherung und vier Wartezeiten. Und fuenf Wissensupdates
hintereinander laden fuenfmal dieselben Dateien. Was zaehlt, ist der
aktuelle Stand, nicht die Zahl der ausgefallenen Termine.

Das ist eine Entscheidung und keine Selbstverstaendlichkeit; deshalb
steht sie hier und nicht im Code versteckt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

ARTEN = ("intervall", "taeglich", "beim_start", "manuell")

WOCHENTAGE = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag",
              "Samstag", "Sonntag")

_UHRZEIT = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


class AusloeserFehler(ValueError):
    """Die Angabe ergibt keinen Auslöser - mit einem Satz fuer den Menschen."""


@dataclass(frozen=True)
class Ausloeser:
    """Wann eine Aufgabe laufen soll."""

    art: str
    #: Bei "intervall": Abstand in Stunden.
    stunden: int = 0
    #: Bei "taeglich": "HH:MM".
    uhrzeit: str = ""
    #: Bei "taeglich": 0 = Montag. Leer bedeutet jeden Tag.
    wochentage: tuple[int, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.art not in ARTEN:
            raise AusloeserFehler(
                f"Unbekannte Art: {self.art}. Moeglich sind: "
                + ", ".join(ARTEN))
        if self.art == "intervall" and self.stunden < 1:
            raise AusloeserFehler(
                "Ein Intervall braucht mindestens eine Stunde. Kuerzere "
                "Abstaende bringen nichts: PORTIVA prueft die Faelligkeit "
                "im Minutentakt, und keine der Aufgaben lohnt sich "
                "oefter.")
        if self.art == "taeglich":
            if not _UHRZEIT.match(self.uhrzeit or ""):
                raise AusloeserFehler(
                    f"„{self.uhrzeit}“ ist keine Uhrzeit. Erwartet wird "
                    "HH:MM, zum Beispiel 07:30.")
            for tag in self.wochentage:
                if not 0 <= tag <= 6:
                    raise AusloeserFehler(
                        f"{tag} ist kein Wochentag. 0 ist Montag, 6 ist "
                        "Sonntag.")

    # -- Klartext ------------------------------------------------------
    def beschreibung(self) -> str:
        """Ein Satz, den ein Buchhalter liest - keine Cron-Zeile."""
        if self.art == "intervall":
            if self.stunden == 1:
                return "Jede Stunde"
            if self.stunden == 24:
                return "Einmal am Tag"
            if self.stunden % 24 == 0:
                tage = self.stunden // 24
                return f"Alle {tage} Tage"
            return f"Alle {self.stunden} Stunden"
        if self.art == "taeglich":
            if not self.wochentage:
                return f"Taeglich um {self.uhrzeit}"
            namen = ", ".join(WOCHENTAGE[t] for t in sorted(self.wochentage))
            return f"{namen} um {self.uhrzeit}"
        if self.art == "beim_start":
            return "Bei jedem Programmstart"
        return "Nur von Hand"

    # -- Faelligkeit ---------------------------------------------------
    def naechste(self, letzte: datetime | None,
                 jetzt: datetime) -> datetime | None:
        """Wann ist die Aufgabe das naechste Mal dran?

        ``None`` bedeutet: gar nicht von selbst. Das ist bei "manuell"
        der Fall und bei "beim_start" - der Zeitpunkt steht dort nicht
        fest, er haengt am naechsten Start.
        """
        if self.art == "intervall":
            grundlage = letzte or jetzt
            return grundlage + timedelta(hours=self.stunden)
        if self.art == "taeglich":
            return self._naechster_termin(jetzt)
        return None

    def faellig(self, letzte: datetime | None, jetzt: datetime,
                start: bool = False) -> bool:
        """Ist die Aufgabe jetzt dran?

        ``start`` sagt, ob dies der Programmstart ist. Nur dann laeuft
        eine Startaufgabe - sonst liefe sie bei jeder Pruefung erneut.
        """
        if self.art == "manuell":
            return False
        if self.art == "beim_start":
            return start
        if self.art == "intervall":
            if letzte is None:
                return True
            return jetzt >= letzte + timedelta(hours=self.stunden)
        # taeglich
        termin = self._letzter_termin(jetzt)
        if termin is None:
            return False
        return letzte is None or letzte < termin

    def _passt(self, tag: datetime) -> bool:
        return not self.wochentage or tag.weekday() in self.wochentage

    def _stunde_minute(self) -> tuple[int, int]:
        stunde, minute = self.uhrzeit.split(":")
        return int(stunde), int(minute)

    def _letzter_termin(self, jetzt: datetime) -> datetime | None:
        """Der letzte Termin, der bis jetzt haette laufen sollen.

        Hier steckt das Nachholen: war das Programm drei Tage aus, ist
        der letzte faellige Termin der von heute (oder der letzte
        passende Wochentag davor) - nicht alle drei.
        """
        stunde, minute = self._stunde_minute()
        kandidat = jetzt.replace(hour=stunde, minute=minute, second=0,
                                 microsecond=0)
        if kandidat > jetzt:
            kandidat -= timedelta(days=1)
        # Hoechstens eine Woche zurueck - danach gibt es keinen passenden
        # Wochentag mehr, und eine Endlosschleife waere schlimmer als
        # eine ausgefallene Aufgabe.
        for _ in range(8):
            if self._passt(kandidat):
                return kandidat
            kandidat -= timedelta(days=1)
        return None

    def _naechster_termin(self, jetzt: datetime) -> datetime | None:
        stunde, minute = self._stunde_minute()
        kandidat = jetzt.replace(hour=stunde, minute=minute, second=0,
                                 microsecond=0)
        if kandidat <= jetzt:
            kandidat += timedelta(days=1)
        for _ in range(8):
            if self._passt(kandidat):
                return kandidat
            kandidat += timedelta(days=1)
        return None

    # -- Speichern -----------------------------------------------------
    def as_dict(self) -> dict:
        return {"art": self.art, "stunden": self.stunden,
                "uhrzeit": self.uhrzeit,
                "wochentage": list(self.wochentage)}

    @classmethod
    def aus_dict(cls, daten: dict) -> "Ausloeser":
        return cls(
            art=daten.get("art") or "manuell",
            stunden=int(daten.get("stunden") or 0),
            uhrzeit=daten.get("uhrzeit") or "",
            wochentage=tuple(int(t) for t in daten.get("wochentage") or ()),
        )
