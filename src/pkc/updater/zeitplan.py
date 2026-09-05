"""Faelligkeit von Wissensupdates (Masterprompt-Erweiterung, Abschnitte 10-21).

Grundgedanke: Die lokale Wissensbasis soll regelmaessig aktuell gehalten
werden, ohne dass jemand daran denken muss. Vorgabe ist **woechentlich**.

Zwei Dinge sind dabei verbindlich:

* Im OFFLINE-Modus wird **nicht** synchronisiert - auch dann nicht, wenn
  physisch eine Verbindung besteht. Der Modus ist eine Entscheidung.
* Die Anwendung behauptet nie, ihr Wissen sei aktuell. Sie nennt den
  Zeitpunkt der letzten erfolgreichen Aktualisierung; ist keiner bekannt,
  sagt sie das.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from enum import Enum

from ..logging_setup import get_logger

log = get_logger(__name__)

#: Zeitplan -> Abstand in Tagen. ``manual`` und ``off`` haben keinen.
INTERVALLE: dict[str, int | None] = {
    "manual": None,
    "off": None,
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "custom": None,          # nimmt updates.custom_interval_days
}

#: Vorgabe laut Masterprompt-Ergaenzung.
VORGABE = "weekly"


class UpdateLage(str, Enum):
    AKTUELL = "AKTUELL"
    FAELLIG = "UPDATE FAELLIG"
    UEBERFAELLIG = "UPDATE UEBERFAELLIG"
    NIE_GELAUFEN = "NOCH NIE AKTUALISIERT"
    PAUSIERT = "OFFLINE - UPDATE PAUSIERT"
    ABGESCHALTET = "AUTOMATIK AUS"
    KEIN_NETZ = "KEINE VERBINDUNG"


@dataclass
class Faelligkeit:
    lage: UpdateLage
    letzte_pruefung: str = ""
    naechste_pruefung: str = ""
    tage_seit_letzter: int | None = None
    intervall_tage: int | None = None
    text: str = ""

    @property
    def faellig(self) -> bool:
        return self.lage in (UpdateLage.FAELLIG, UpdateLage.UEBERFAELLIG,
                             UpdateLage.NIE_GELAUFEN)

    def as_dict(self) -> dict:
        return {
            "lage": self.lage.value,
            "letzte_pruefung": self.letzte_pruefung,
            "naechste_pruefung": self.naechste_pruefung,
            "tage_seit_letzter": self.tage_seit_letzter,
            "intervall_tage": self.intervall_tage,
            "text": self.text,
        }


def intervall_tage(config) -> int | None:
    """Abstand in Tagen - oder None, wenn keine Automatik gewuenscht ist."""
    plan = str(config.get("updates.schedule", VORGABE) or VORGABE).strip().lower()
    if plan == "custom":
        try:
            tage = int(config.get("updates.custom_interval_days", 14))
        except (TypeError, ValueError):
            tage = 14
        return max(1, tage)
    return INTERVALLE.get(plan, INTERVALLE[VORGABE])


def _als_datum(wert: str) -> _dt.datetime | None:
    if not wert:
        return None
    text = str(wert).strip().replace("Z", "+00:00")
    try:
        zeitpunkt = _dt.datetime.fromisoformat(text)
    except ValueError:
        try:
            zeitpunkt = _dt.datetime.fromisoformat(text[:10])
        except ValueError:
            return None
    if zeitpunkt.tzinfo is None:
        zeitpunkt = zeitpunkt.replace(tzinfo=_dt.timezone.utc)
    return zeitpunkt


def pruefen(config, letzte_aktualisierung: str, online_moeglich: bool,
            modus_offline: bool, jetzt: _dt.datetime | None = None) -> Faelligkeit:
    """Ermittelt, ob eine Aktualisierung ansteht.

    ``letzte_aktualisierung`` ist der zuletzt erfolgreich erreichte
    Wissensstand als ISO-Zeitpunkt; leer bedeutet: noch nie gelaufen.
    """
    jetzt = jetzt or _dt.datetime.now(_dt.timezone.utc)
    tage = intervall_tage(config)
    letzte = _als_datum(letzte_aktualisierung)
    seit = (jetzt - letzte).days if letzte else None

    naechste = ""
    if letzte and tage:
        naechste = (letzte + _dt.timedelta(days=tage)).date().isoformat()

    grund = Faelligkeit(
        lage=UpdateLage.AKTUELL,
        letzte_pruefung=letzte.date().isoformat() if letzte else "",
        naechste_pruefung=naechste,
        tage_seit_letzter=seit,
        intervall_tage=tage,
    )

    if modus_offline:
        grund.lage = UpdateLage.PAUSIERT
        grund.text = ("Automatische Aktualisierung pausiert - Offline-Modus aktiv. "
                      "Der vorhandene Wissensstand bleibt unveraendert nutzbar.")
        return grund

    if tage is None:
        grund.lage = UpdateLage.ABGESCHALTET
        grund.text = "Es ist keine automatische Aktualisierung eingestellt."
        return grund

    if letzte is None:
        grund.lage = UpdateLage.NIE_GELAUFEN
        grund.text = ("Der lokale Wissensstand wurde noch nie aktualisiert. "
                      "Das mitgelieferte Fachwissen ist nutzbar.")
    elif seit is not None and seit >= tage * 2:
        grund.lage = UpdateLage.UEBERFAELLIG
        grund.text = (f"Der lokale Wissensstand wurde seit {seit} Tagen nicht "
                      f"aktualisiert (vorgesehen: alle {tage} Tage).")
    elif seit is not None and seit >= tage:
        grund.lage = UpdateLage.FAELLIG
        grund.text = (f"Die naechste Pruefung war fuer {naechste} vorgesehen. "
                      f"Letzte Aktualisierung vor {seit} Tagen.")
    else:
        grund.text = (f"Zuletzt aktualisiert vor {seit} Tag(en). "
                      f"Naechste Pruefung: {naechste}.")

    if grund.faellig and not online_moeglich:
        # Faellig ist es trotzdem - es geht nur gerade nicht.
        grund.lage = UpdateLage.KEIN_NETZ
        grund.text += " Derzeit besteht keine Verbindung."
    return grund
