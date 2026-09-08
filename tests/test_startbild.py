"""Das Begruessungsbild darf niemals den Start verhindern.

Ein Startbild ist eine Nettigkeit. Wenn eine Nettigkeit die Anwendung am
Starten hindert, ist sie ein Fehler. Diese Tests halten fest, dass jeder
denkbare Ausfall des Bildes folgenlos bleibt.
"""

from __future__ import annotations

import sys

import pytest

import tk_double


@pytest.fixture
def tk_ersatz(monkeypatch):
    """Setzt das Tk-Doppel ein und laedt das Modul frisch dagegen."""
    tk_double.install()
    for name in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[name]
    from ui import startbild

    return startbild


class Brandattrappe:
    name = "PORTIVA"
    claim = "Portable KI-Mitarbeiter-Plattform"

    def __init__(self, logo=None):
        self._logo = logo

    def variante(self, name):
        return self._logo

    @property
    def logo_pfad(self):
        return self._logo

    def titel(self, profil=""):
        return f"PORTIVA - {profil}" if profil else "PORTIVA"


def test_ohne_logo_wird_kein_leerer_kasten_gezeigt(tk_ersatz):
    """Ein blauer Kasten ohne Logo waere keine Begruessung, sondern eine
    Stoerung.

    Geprueft wird nicht nur der Rueckgabewert, sondern dass am Ende
    **kein** Fenster stehen bleibt. Die erste Fassung dieses Tests hat den
    Rueckgabewert geprueft und war deshalb wertlos: er war auch dann False,
    wenn das Fenster aufging und erst danach etwas schiefging. Aufgefallen
    an einer Gegenprobe, die nicht ansprang.
    """
    bild = tk_ersatz.Startbild(Brandattrappe(logo=None))
    assert bild.zeigen() is False
    assert bild.gezeigt is False
    offen = [f for f in tk_double._Toplevel.ERZEUGT if not f.destroyed]
    assert offen == [], "ohne Logo darf kein Fenster stehen bleiben"


def test_ein_fehler_beim_aufbau_verhindert_den_start_nicht(tk_ersatz, monkeypatch):
    """Was hier schiefgeht, darf nur das Bild kosten - nie die Anwendung."""
    def kaputt(self):
        raise RuntimeError("Grafikkarte weg")

    monkeypatch.setattr(tk_ersatz.Startbild, "_aufbauen", kaputt)
    assert tk_ersatz.Startbild(Brandattrappe(logo="egal.png")).zeigen() is False


def test_mit_logo_geht_ein_fenster_auf_und_wieder_zu(tk_ersatz):
    """Der eigentliche Zweck: es erscheint - und es verschwindet auch wieder.

    Ein Begruessungsbild, das stehen bleibt, waere schlimmer als keines: es
    verdeckt die Anwendung und laesst sich nicht wegklicken, wenn der
    Selbstschluss fehlt.
    """
    from pathlib import Path

    logo = (Path(__file__).resolve().parents[1]
            / "assets" / "branding" / "portiva_logo_dark.png")
    assert logo.is_file(), "die dunkle Logovariante muss abgeleitet sein"

    bild = tk_ersatz.Startbild(Brandattrappe(logo=str(logo)), profil="Buchhalter")
    assert bild.zeigen() is True
    assert bild.gezeigt is True

    fenster = tk_double._Toplevel.ERZEUGT
    assert fenster, "es muss ein Fenster aufgegangen sein"
    assert all(f.destroyed for f in fenster), (
        "das Begruessungsbild muss sich nach Ablauf selbst schliessen")


def test_ein_klick_schliesst_sofort(tk_ersatz):
    """Wer eilig ist, klickt - und ist drin."""
    from pathlib import Path

    logo = (Path(__file__).resolve().parents[1]
            / "assets" / "branding" / "portiva_logo_dark.png")
    bild = tk_ersatz.Startbild(Brandattrappe(logo=str(logo)), dauer_ms=999_000)
    # Kein zeigen() - das wuerde bei dieser Dauer warten. Nur aufbauen und
    # dann den Klick ausloesen, wie ihn Tk melden wuerde.
    assert bild._aufbauen() is True
    fenster = bild.fenster
    assert "<Button-1>" in fenster.bindings, "ein Klick muss schliessen koennen"
    fenster.bindings["<Button-1>"](None)
    assert fenster.destroyed
    assert bild.fenster is None


def test_die_dauer_kommt_aus_dem_auftrag():
    """Drei Sekunden - so vorgegeben."""
    from ui import startbild

    assert startbild.DAUER_MS == 3000


def test_schliessen_ist_mehrfach_gefahrlos(tk_ersatz):
    bild = tk_ersatz.Startbild(Brandattrappe(logo=None))
    bild.schliessen()
    bild.schliessen()          # darf nicht abstuerzen


def test_der_start_reicht_den_schalter_durch(monkeypatch, tmp_path):
    """--kein-startbild muss beim Fensterstart wirklich ankommen.

    Ein Schalter, der in der Hilfe steht und nichts tut, ist schlimmer als
    keiner.
    """
    import importlib.util
    from pathlib import Path

    wurzel = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "portable_buchhalter_start2", wurzel / "portable_buchhalter.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    monkeypatch.setattr(modul, "ROOT", tmp_path)

    gesehen = {}

    class Fensterdoppel:
        @staticmethod
        def run(startbild=True):
            gesehen["startbild"] = startbild
            return 0

    monkeypatch.setitem(sys.modules, "ui.tk_app", Fensterdoppel)

    assert modul.main(["--gui"]) == 0
    assert gesehen["startbild"] is True, "ohne Schalter wird begruesst"

    assert modul.main(["--gui", "--kein-startbild"]) == 0
    assert gesehen["startbild"] is False, "mit Schalter nicht"


def test_der_schalter_landet_nicht_in_der_kommandozeile(monkeypatch, tmp_path):
    """Sonst beschwerte sich die Konsolenfassung ueber ein unbekanntes Wort."""
    import importlib.util
    from pathlib import Path

    wurzel = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "portable_buchhalter_start3", wurzel / "portable_buchhalter.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    monkeypatch.setattr(modul, "ROOT", tmp_path)

    gesehen = {}

    class CliDoppel:
        @staticmethod
        def main(argv):
            gesehen["argv"] = argv
            return 0

    monkeypatch.setitem(sys.modules, "ui.cli", CliDoppel)
    assert modul.main(["check", "--kein-startbild"]) == 0
    assert gesehen["argv"] == ["check"], "der Schalter darf nicht durchgereicht werden"


def test_oeffnen_wartet_nicht_und_liefert_das_fenster(tk_ersatz):
    """Fuer die Bildaufnahme muss das Bild stehenbleiben duerfen.

    ``zeigen`` wartet, bis das Bild wieder weg ist - richtig fuer den
    Start, unbrauchbar fuer eine Aufnahme. ``oeffnen`` baut dasselbe Bild
    auf und kehrt sofort zurueck, damit es fotografiert werden kann.
    """
    bild = tk_ersatz.Startbild(Brandattrappe(logo="logo.png"), "Buchhalter")
    fenster = bild.oeffnen()
    assert fenster is not None, "das Fenster muss zurueckgegeben werden"
    assert bild.fenster is fenster, "es muss dasselbe Fenster sein"
    assert bild.gezeigt is True
    bild.schliessen()
    assert bild.fenster is None


def test_oeffnen_gibt_nichts_zurueck_wenn_es_kein_logo_gibt(tk_ersatz):
    """Kein Logo, kein Bild - auch hier kein leerer blauer Kasten."""
    bild = tk_ersatz.Startbild(Brandattrappe(logo=None), "Buchhalter")
    assert bild.oeffnen() is None
    assert bild.gezeigt is False


def test_schliessen_raeumt_das_selbst_erzeugte_wurzelfenster_ab(tk_ersatz):
    """Sonst haengen spaetere Variablen am falschen Fenster.

    Das Begruessungsbild erzeugt sich ein eigenes, unsichtbares
    Wurzelfenster. Blieb es nach ``oeffnen``/``schliessen`` stehen, hing
    alles, was danach ohne ausdrueckliches Elternteil erzeugt wurde - eine
    ``StringVar`` etwa -, an diesem alten Fenster. Im Hauptfenster zeigte
    das Auswahlfeld fuer den Betriebsmodus deshalb nichts an: der Wert
    stand in einer Variablen eines Fensters, das niemand mehr sah.

    Gefunden auf einem Bildschirmfoto der echten Oberflaeche, nicht in
    einem Test - der Test fragte den Wert ab und fand ihn.
    """
    bild = tk_ersatz.Startbild(Brandattrappe(logo="logo.png"), "Buchhalter")
    assert bild.oeffnen() is not None
    wurzel = bild._root
    assert wurzel is not None, "es muss ein eigenes Wurzelfenster geben"
    bild.schliessen()
    assert bild._root is None, "das Wurzelfenster muss abgeraeumt sein"
    assert wurzel.destroyed, "und zwar wirklich zerstoert"


def test_zeigen_raeumt_erst_nach_dem_warten_ab(tk_ersatz):
    """Waehrend ``zeigen`` wartet, darf das Wurzelfenster nicht fallen.

    ``zeigen`` plant den Selbstschluss ein und wartet dann auf das
    Fenster. Wuerde ``schliessen`` dabei gleich das Wurzelfenster
    mitnehmen, wartete ``wait_window`` auf etwas, das es nicht mehr gibt.
    """
    bild = tk_ersatz.Startbild(Brandattrappe(logo="logo.png"), "Buchhalter")
    assert bild.zeigen() is True
    assert bild._root is None, "am Ende ist trotzdem abgeraeumt"
    assert bild._wartet is False
