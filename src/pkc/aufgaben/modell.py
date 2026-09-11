"""Eine Aufgabe und was von ihren Laeufen uebrig bleibt."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .ausloeser import Ausloeser

#: Wieviele Laeufe je Aufgabe aufgehoben werden. Mehr braucht niemand,
#: und eine Protokolldatei, die unbegrenzt waechst, ist auf einem
#: Datentraeger die falsche Antwort.
LAEUFE_BEHALTEN = 30


@dataclass(frozen=True)
class Lauf:
    """Was bei einer Ausfuehrung herauskam."""

    zeitpunkt: str
    ergebnis: str               # "ok", "fehler" oder "uebersprungen"
    meldung: str = ""
    dauer: float = 0.0

    def as_dict(self) -> dict:
        return {"zeitpunkt": self.zeitpunkt, "ergebnis": self.ergebnis,
                "meldung": self.meldung, "dauer": round(self.dauer, 2)}

    @classmethod
    def aus_dict(cls, daten: dict) -> "Lauf":
        return cls(
            zeitpunkt=daten.get("zeitpunkt") or "",
            ergebnis=daten.get("ergebnis") or "fehler",
            meldung=daten.get("meldung") or "",
            dauer=float(daten.get("dauer") or 0.0),
        )


@dataclass
class Aufgabe:
    """Eine geplante Arbeit."""

    kennung: str
    name: str
    aktion: str
    ausloeser: Ausloeser
    aktiv: bool = True
    angelegt: str = ""
    #: Wann sie zuletzt **wirklich gelaufen** ist (ISO, ohne Zeitzone).
    #: Ein uebersprungener Lauf zaehlt nicht - sonst waere eine Aufgabe,
    #: die mangels Internet ausfiel, bis zum naechsten Termin erledigt.
    letzter_lauf: str = ""
    protokoll: list[Lauf] = field(default_factory=list)

    # -- Zeiten --------------------------------------------------------
    @property
    def letzte_zeit(self) -> datetime | None:
        if not self.letzter_lauf:
            return None
        try:
            return datetime.fromisoformat(self.letzter_lauf)
        except ValueError:                      # pragma: no cover - defensiv
            return None

    def naechste(self, jetzt: datetime | None = None) -> datetime | None:
        if not self.aktiv:
            return None
        return self.ausloeser.naechste(self.letzte_zeit, jetzt or datetime.now())

    def faellig(self, jetzt: datetime | None = None,
                start: bool = False) -> bool:
        if not self.aktiv:
            return False
        return self.ausloeser.faellig(self.letzte_zeit,
                                      jetzt or datetime.now(), start=start)

    # -- Protokoll -----------------------------------------------------
    def vermerken(self, lauf: Lauf) -> None:
        self.protokoll.append(lauf)
        if len(self.protokoll) > LAEUFE_BEHALTEN:
            del self.protokoll[:-LAEUFE_BEHALTEN]

    @property
    def letzte_meldung(self) -> str:
        return self.protokoll[-1].meldung if self.protokoll else ""

    @property
    def letztes_ergebnis(self) -> str:
        return self.protokoll[-1].ergebnis if self.protokoll else ""

    # -- Speichern -----------------------------------------------------
    def as_dict(self) -> dict:
        return {
            "kennung": self.kennung, "name": self.name,
            "aktion": self.aktion, "ausloeser": self.ausloeser.as_dict(),
            "aktiv": self.aktiv, "angelegt": self.angelegt,
            "letzter_lauf": self.letzter_lauf,
            "protokoll": [lauf.as_dict() for lauf in self.protokoll],
        }

    @classmethod
    def aus_dict(cls, daten: dict) -> "Aufgabe":
        return cls(
            kennung=daten.get("kennung") or "",
            name=daten.get("name") or "",
            aktion=daten.get("aktion") or "",
            ausloeser=Ausloeser.aus_dict(daten.get("ausloeser") or {}),
            aktiv=bool(daten.get("aktiv", True)),
            angelegt=daten.get("angelegt") or "",
            letzter_lauf=daten.get("letzter_lauf") or "",
            protokoll=[Lauf.aus_dict(l) for l in daten.get("protokoll") or []],
        )
