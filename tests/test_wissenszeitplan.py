"""Automatische Wissenssynchronisierung (Masterprompt-Ergaenzung 10 bis 21).

Vorgabe: woechentlich pruefen. Verbindlich dabei:

* Im OFFLINE-Modus wird nicht synchronisiert - auch nicht bei bestehender
  Verbindung. Der Modus ist eine Entscheidung des Benutzers.
* Ein ueberfaelliges Update wird nach einer laengeren Offlinephase erkannt.
* Die Anwendung behauptet nie, ihr Wissen sei aktuell.
"""

from __future__ import annotations

import datetime as _dt

import pytest

from pkc.config import Config
from pkc.updater.zeitplan import (INTERVALLE, VORGABE, Faelligkeit, UpdateLage,
                                  intervall_tage, pruefen)

JETZT = _dt.datetime(2026, 9, 15, 12, 0, tzinfo=_dt.timezone.utc)


def vor_tagen(tage: int) -> str:
    return (JETZT - _dt.timedelta(days=tage)).isoformat()


@pytest.fixture
def config(portable_root):
    return Config.load(portable_root)


def _pruefen(config, letzte, online=True, offline_modus=False):
    return pruefen(config, letzte, online_moeglich=online,
                   modus_offline=offline_modus, jetzt=JETZT)


# ------------------------------------------------------------- Intervall
def test_vorgabe_ist_woechentlich(config):
    assert VORGABE == "weekly"
    assert config.get("updates.schedule") == "weekly"
    assert intervall_tage(config) == 7


@pytest.mark.parametrize("plan, tage", [
    ("daily", 1), ("weekly", 7), ("monthly", 30),
    ("manual", None), ("off", None),
])
def test_alle_zeitplaene(config, plan, tage):
    config.set("updates.schedule", plan)
    assert intervall_tage(config) == tage


def test_benutzerdefiniertes_intervall(config):
    config.set("updates.schedule", "custom")
    config.set("updates.custom_interval_days", 3)
    assert intervall_tage(config) == 3


def test_unsinniges_intervall_fuehrt_nicht_zum_absturz(config):
    config.set("updates.schedule", "custom")
    config.set("updates.custom_interval_days", "keine Zahl")
    assert intervall_tage(config) == 14
    config.set("updates.schedule", "gibtesnicht")
    assert intervall_tage(config) == 7, "unbekannter Plan faellt auf die Vorgabe"


# ------------------------------------------------------------ Faelligkeit
def test_frisch_aktualisiert_ist_aktuell(config):
    lage = _pruefen(config, vor_tagen(2))
    assert lage.lage is UpdateLage.AKTUELL
    assert lage.faellig is False
    assert lage.naechste_pruefung == "2026-09-20"


def test_nach_einer_woche_faellig(config):
    lage = _pruefen(config, vor_tagen(8))
    assert lage.lage is UpdateLage.FAELLIG
    assert lage.faellig is True


def test_ueberfaellig_nach_langer_offlinephase(config):
    """Der Fall aus der Vorgabe: 14 Tage offline, Intervall woechentlich."""
    lage = _pruefen(config, vor_tagen(14))
    assert lage.lage is UpdateLage.UEBERFAELLIG
    assert lage.tage_seit_letzter == 14
    assert "14 Tagen" in lage.text


def test_noch_nie_aktualisiert(config):
    lage = _pruefen(config, "")
    assert lage.lage is UpdateLage.NIE_GELAUFEN
    assert lage.faellig is True
    # Keine falsche Aktualitaetsbehauptung
    assert "noch nie" in lage.text.lower()


def test_offline_modus_pausiert_die_automatik(config):
    """Auch bei bestehender Verbindung wird nicht synchronisiert."""
    lage = _pruefen(config, vor_tagen(30), online=True, offline_modus=True)
    assert lage.lage is UpdateLage.PAUSIERT
    assert "Offline-Modus aktiv" in lage.text
    assert "unveraendert nutzbar" in lage.text


def test_faellig_aber_kein_netz(config):
    lage = _pruefen(config, vor_tagen(10), online=False)
    assert lage.lage is UpdateLage.KEIN_NETZ
    assert "keine Verbindung" in lage.text


def test_abgeschaltete_automatik(config):
    config.set("updates.schedule", "manual")
    lage = _pruefen(config, vor_tagen(90))
    assert lage.lage is UpdateLage.ABGESCHALTET
    assert lage.faellig is False


def test_kaputtes_datum_bricht_nichts_ab(config):
    lage = _pruefen(config, "voellig kaputt")
    assert lage.lage is UpdateLage.NIE_GELAUFEN


def test_datum_ohne_zeitzone_wird_angenommen(config):
    lage = _pruefen(config, "2026-09-01")
    assert lage.tage_seit_letzter == 14
    assert lage.lage is UpdateLage.UEBERFAELLIG


# ----------------------------------------------------------- am Controller
def test_controller_beruecksichtigt_den_betriebsmodus(portable_root):
    from pkc.netstate import Mode
    from test_controller import make_controller

    controller = make_controller(portable_root)
    controller.bootstrap(build_embeddings=False)
    try:
        controller.set_mode(Mode.OFFLINE)
        assert controller.update_faelligkeit().lage is UpdateLage.PAUSIERT

        controller.set_mode(Mode.HYBRID)
        assert controller.update_faelligkeit().lage is not UpdateLage.PAUSIERT
    finally:
        controller.shutdown()


def test_as_dict_enthaelt_alles_fuer_die_anzeige(config):
    daten = _pruefen(config, vor_tagen(3)).as_dict()
    for schluessel in ("lage", "letzte_pruefung", "naechste_pruefung",
                       "tage_seit_letzter", "intervall_tage", "text"):
        assert schluessel in daten
