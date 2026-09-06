"""Das Modell muss nicht auf jedem Rechner neu geladen werden.

Rueckfrage aus dem Betrieb: "muss das so gemacht sein, dass ich das
Sprachmodell immer runterladen muss?"

Nein. Zwei Dinge gehoeren dafuer zusammen und werden hier beide geprueft:

* Das Modell liegt im Ordner ``models`` **auf dem Datentraeger**, nicht im
  Benutzerprofil des Rechners. Einmal geladen bleibt es dort - ueber
  Neustarts, ueber Laufwerksbuchstaben und ueber Kundenbereiche hinweg.
* Wer die Datei schon hat, kann sie uebernehmen statt sie erneut zu ziehen.
  Fuer einen zweiten Stick, fuer ein Buero mit gesperrtem Download, fuer
  eine Leitung, ueber die 4,7 GB nicht zweimal gehen.
"""

from __future__ import annotations

import pytest

from pkc.llm.bezug import uebernehmen
from pkc.paths import CUSTOMER_DIRS, PROGRAM_DIRS
from test_controller import make_controller

GGUF = b"GGUF" + bytes(6000)


@pytest.fixture
def anwendung(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap(build_embeddings=False)
    try:
        yield controller
    finally:
        controller.shutdown()


@pytest.fixture
def fremde_datei(tmp_path):
    """Ein Modell, das woanders liegt - etwa auf dem Stick einer Kollegin."""
    quelle = tmp_path / "anderswo"
    quelle.mkdir()
    datei = quelle / "qwen2.5-7b-instruct-q4_k_m.gguf"
    datei.write_bytes(GGUF)
    return datei


# -- Das Modell bleibt, wo es hingehoert ---------------------------------

def test_modelle_liegen_auf_dem_datentraeger(portable_root):
    """Nicht im Benutzerprofil - sonst waere die Anwendung nicht portabel."""
    assert portable_root.get("models") == portable_root.root / "models"


def test_modell_gehoert_nicht_einem_kundenbereich():
    """Sonst muesste jeder Kundenbereich dieselben Gigabyte erneut halten."""
    assert "models" not in CUSTOMER_DIRS
    assert "models" not in PROGRAM_DIRS


def test_einmal_uebernommen_wird_es_wiedergefunden(anwendung, fremde_datei):
    """Der eigentliche Punkt: einmal reicht."""
    ergebnis = anwendung.modell_uebernehmen(fremde_datei)
    assert ergebnis["ok"], ergebnis["meldung"]

    from pkc.llm.manager import discover_models

    gefunden = discover_models(anwendung.paths.get("models"))
    assert [m.name for m in gefunden] == [fremde_datei.name]
    # Und auch nach einem Neuaufbau der Anbindung ist es noch da.
    anwendung.modell_neu_laden()
    assert anwendung.modell_lage()["modelle"], "das Modell muss liegen bleiben"


# -- Die Uebernahme ------------------------------------------------------

def test_datei_wird_kopiert_nicht_nur_verwiesen(tmp_path, fremde_datei):
    """Ein Verweis waere kleiner - und wuerde die Portabilitaet zerstoeren."""
    ziel = tmp_path / "models"
    ergebnis = uebernehmen(fremde_datei, ziel)

    assert ergebnis.ok
    assert (ziel / fremde_datei.name).read_bytes() == GGUF
    fremde_datei.unlink()
    assert (ziel / fremde_datei.name).is_file(), (
        "nach dem Entfernen der Herkunft muss die Kopie noch da sein")


def test_fortschritt_wird_gemeldet(tmp_path, fremde_datei):
    schritte = []
    uebernehmen(fremde_datei, tmp_path / "models",
                fortschritt=lambda k, g, t: schritte.append((k, g)))
    assert schritte, "ohne Rueckmeldung sieht der Benutzer nur ein stehendes Fenster"
    assert schritte[-1][0] == schritte[-1][1] == len(GGUF)


def test_nur_gguf_wird_angenommen(tmp_path):
    andere = tmp_path / "modell.safetensors"
    andere.write_bytes(b"x" * 100)
    ergebnis = uebernehmen(andere, tmp_path / "models")

    assert not ergebnis.ok
    assert "GGUF" in ergebnis.meldung
    assert "safetensors" in ergebnis.meldung, "der Grund muss dastehen"


def test_fehlende_datei_wird_gemeldet(tmp_path):
    ergebnis = uebernehmen(tmp_path / "gibtsnicht.gguf", tmp_path / "models")
    assert not ergebnis.ok and "keine Datei" in ergebnis.meldung


def test_vorhandenes_wird_nicht_stillschweigend_ersetzt(tmp_path, fremde_datei):
    ziel = tmp_path / "models"
    assert uebernehmen(fremde_datei, ziel).ok
    zweite = uebernehmen(fremde_datei, ziel)

    assert not zweite.ok and "bereits" in zweite.meldung
    assert uebernehmen(fremde_datei, ziel, ueberschreiben=True).ok


def test_dieselbe_datei_ist_kein_fehler(tmp_path):
    """Wer die Datei aus dem Modellordner selbst waehlt, hat sie schon."""
    ziel = tmp_path / "models"
    ziel.mkdir()
    datei = ziel / "modell.gguf"
    datei.write_bytes(GGUF)

    ergebnis = uebernehmen(datei, ziel)
    assert ergebnis.ok and "liegt bereits hier" in ergebnis.meldung
    assert datei.read_bytes() == GGUF, "die Datei darf dabei nicht verlorengehen"


def test_zu_wenig_platz_wird_vorher_gemeldet(tmp_path, fremde_datei, monkeypatch):
    """Abbrechen, bevor etwas beginnt - nicht mittendrin."""
    import shutil

    class Wenig:
        total = free = 10
        used = 0

    monkeypatch.setattr(shutil, "disk_usage", lambda *a: Wenig())
    ergebnis = uebernehmen(fremde_datei, tmp_path / "models")
    assert not ergebnis.ok and "Speicherplatz" in ergebnis.meldung
    assert not (tmp_path / "models" / fremde_datei.name).exists()


def test_abbruch_hinterlaesst_keine_halbe_datei(tmp_path, fremde_datei, monkeypatch):
    """Eine halbe Datei waere schlimmer als keine - der Dienst haelt sie fuer ein Modell."""
    ziel = tmp_path / "models"
    echtes_open = type(fremde_datei).open

    def bricht_ab(self, *args, **kwargs):
        strom = echtes_open(self, *args, **kwargs)
        if "w" in (args[0] if args else kwargs.get("mode", "")):
            original = strom.write

            def kaputt(daten):
                original(daten[: len(daten) // 2])
                raise OSError("Datentraeger abgezogen")

            strom.write = kaputt
        return strom

    monkeypatch.setattr(type(fremde_datei), "open", bricht_ab)
    ergebnis = uebernehmen(fremde_datei, ziel)

    assert not ergebnis.ok and "fehlgeschlagen" in ergebnis.meldung
    assert list(ziel.glob("*")) == [], "weder Datei noch Bruchstueck duerfen bleiben"


# -- Ohne Internet -------------------------------------------------------

def test_uebernahme_geht_auch_offline(anwendung, fremde_datei):
    """Hier wird nichts geholt - die Sperre fuer OFFLINE darf nicht greifen."""
    from pkc.netstate import Mode

    anwendung.set_mode(Mode.OFFLINE)
    ergebnis = anwendung.modell_uebernehmen(fremde_datei)
    assert ergebnis["ok"], ergebnis["meldung"]


def test_uebernahme_steht_im_protokoll(anwendung, fremde_datei):
    """Was aufs Geraet kommt, muss nachvollziehbar sein."""
    anwendung.modell_uebernehmen(fremde_datei)
    aktionen = [e["action"] for e in anwendung.audit.entries(20)]
    assert "modell_uebernahme" in aktionen and "modell_uebernahme_ende" in aktionen
