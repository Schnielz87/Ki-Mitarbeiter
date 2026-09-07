"""Der Fensterrahmen: linke Navigation, aktive Ansicht, einklappen.

Die Schale kennt keine Fachlogik. Sie nimmt Flaechen entgegen und zeigt
eine davon an. Genau das wird hier geprueft - und dass sie es auch dann
tut, wenn ein Profil nur einen Teil der Bereiche zulaesst.
"""

from __future__ import annotations

import sys

import pytest

import tk_double


@pytest.fixture
def schale_modul():
    tk_double.install()
    for name in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[name]
    from ui import schale

    return schale


class Brandattrappe:
    name = "PORTIVA"
    claim = "Portable KI-Mitarbeiter-Plattform"

    def variante(self, name):
        return None                     # kein Bild - der Schriftzug muss reichen

    @property
    def logo_pfad(self):
        return None

    def titel(self, profil=""):
        return f"PORTIVA - {profil}" if profil else "PORTIVA"


def _schale(modul, sichtbare=None, anzahl=4):
    import tkinter as tk

    s = modul.Navigationsschale(tk.Tk(), Brandattrappe(), "Buchhalter",
                                sichtbare=sichtbare)
    for i in range(anzahl):
        s.bereich_anlegen(f"b{i}", f"Bereich {i}", f"Untertitel {i}")
    return s


def test_ohne_logo_steht_der_schriftzug_da(schale_modul):
    """Ein leerer Kopf in der Seitenleiste waere schlimmer als kein Bild."""
    s = _schale(schale_modul)
    assert s.markenbild.options.get("text") == "PORTIVA"


def test_die_erste_ansicht_wird_gezeigt(schale_modul):
    s = _schale(schale_modul)
    assert s.aktiv == ""
    s.fertig()
    assert s.aktiv == "b0"
    assert s.titel_label.options["text"] == "Bereich 0"
    assert s.untertitel_label.options["text"] == "Untertitel 0"


def test_eine_unbekannte_kennung_aendert_nichts(schale_modul):
    """Ein Tippfehler darf nicht zu einem leeren Fenster fuehren."""
    s = _schale(schale_modul)
    s.fertig()
    assert s.zeigen("gibtsnicht") is False
    assert s.aktiv == "b0", "die bisherige Ansicht muss stehen bleiben"


def test_immer_genau_eine_ansicht_ist_hervorgehoben(schale_modul):
    s = _schale(schale_modul)
    s.fertig()
    for kennung in s.reihenfolge:
        s.zeigen(kennung)
        hervorgehoben = [k for k in s.reihenfolge
                         if s.bereiche[k].knopf.options["bg"] == schale_modul.AKTIV]
        assert hervorgehoben == [kennung], f"bei {kennung}: {hervorgehoben}"


def test_das_profil_bestimmt_die_navigation(schale_modul):
    """Auftrag Abschnitt 9: ein Profil darf Bereiche ausblenden.

    Ausgeblendet heisst nicht geloescht: die Flaeche wird trotzdem gebaut,
    damit der Code der Ansicht fuer jedes Profil derselbe bleibt. Sie
    erscheint nur nicht in der Navigation.
    """
    s = _schale(schale_modul, sichtbare=["b0", "b2"])
    assert s.reihenfolge == ["b0", "b2"]
    assert set(s.bereiche) == {"b0", "b1", "b2", "b3"}
    assert s.bereiche["b1"].knopf is None, "b1 darf keinen Knopf haben"
    assert s.bereiche["b1"].rahmen is not None, "die Flaeche wird trotzdem gebaut"

    s.fertig()
    assert s.aktiv == "b0"


def test_einklappen_laesst_die_bereiche_erreichbar(schale_modul):
    """Eingeklappt bleibt jeder Bereich anklickbar - nur der Text weicht
    dem Zeichen. Eine Leiste, die eingeklappt nichts mehr kann, waere
    keine Platzersparnis, sondern ein Verlust."""
    s = _schale(schale_modul)
    s.fertig()
    assert s.eingeklappt is False

    s.einklapp_knopf.invoke()
    assert s.eingeklappt is True
    for kennung in s.reihenfolge:
        knopf = s.bereiche[kennung].knopf
        assert s.bereiche[kennung].titel not in knopf.options["text"]
        knopf.invoke()
        assert s.aktiv == kennung, "eingeklappt muss jeder Bereich erreichbar bleiben"

    s.einklapp_knopf.invoke()
    assert s.eingeklappt is False
    assert "Bereich 0" in s.bereiche["b0"].knopf.options["text"]


def test_der_wechsel_meldet_sich_an(schale_modul):
    """Damit eine Ansicht ihre Daten erst laedt, wenn sie sichtbar wird -
    und nicht alle zehn beim Start."""
    s = _schale(schale_modul)
    gesehen = []
    s.beim_wechsel(gesehen.append)
    s.fertig()
    s.zeigen("b2")
    assert gesehen == ["b0", "b2"]


def test_ein_fehler_im_rueckruf_bricht_den_wechsel_nicht_ab(schale_modul):
    """Sonst haengt die Navigation an der schwaechsten Ansicht."""
    s = _schale(schale_modul)

    def kaputt(_kennung):
        raise RuntimeError("Ansicht defekt")

    s.beim_wechsel(kaputt)
    s.fertig()
    assert s.zeigen("b1") is True
    assert s.aktiv == "b1"


def test_die_lage_steht_in_der_fusszeile(schale_modul):
    s = _schale(schale_modul)
    s.lage_setzen("Profil: Controller", "HYBRID · Internet verfuegbar")
    assert s.profil_label.options["text"] == "Profil: Controller"
    assert "HYBRID" in s.lage_label.options["text"]
