"""Die Unterhaltung: Quellenpanel, Recherche-Details, Tastenbelegung.

Auftrag Abschnitt 11, 18, 19 und 33.
"""

from __future__ import annotations

import sys

import pytest

import tk_double
from test_controller import make_controller


@pytest.fixture
def fenster(portable_root):
    dialoge = tk_double.install()
    for modul in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[modul]
    from ui import tk_app

    controller = make_controller(portable_root)
    bericht = controller.bootstrap()
    window = tk_app.MainWindow(controller, bericht)
    yield window, controller, dialoge
    controller.shutdown()


class Ereignis:
    """Ein Tastendruck, wie Tk ihn meldet. ``state`` traegt die Sondertasten."""

    def __init__(self, state=0):
        self.state = state


# ------------------------------------------------------ Tastenbelegung
def test_eingabetaste_sendet(fenster):
    """Auftrag Abschnitt 33. Bisher war es Strg+Eingabe - das kennt aus
    anderen Anwendungen niemand."""
    window, controller, _ = fenster
    window.entry.insert("end", "Welche Pflichtangaben braucht eine Rechnung?")
    ergebnis = window._auf_eingabetaste(Ereignis(state=0))

    assert ergebnis == "break", "ohne 'break' kaeme zusaetzlich ein Zeilenumbruch"
    assert len(controller.messages()) == 2, "die Frage muss abgeschickt worden sein"


def test_umschalt_eingabe_sendet_nicht(fenster):
    """Umschalt+Eingabe bricht die Zeile um - Bit 0 im Zustand."""
    window, controller, _ = fenster
    window.entry.insert("end", "Erste Zeile")
    ergebnis = window._auf_eingabetaste(Ereignis(state=0x0001))

    assert ergebnis == "", "Tk soll den Zeilenumbruch selbst einfuegen"
    assert controller.messages() == [], "es darf nichts abgeschickt worden sein"


def test_ohne_zustandsangabe_wird_gesendet(fenster):
    """Meldet ein System die Sondertasten nicht, ist Senden der haeufigere
    Wunsch - und die Frage bleibt im Feld erhalten, falls es falsch war."""
    window, controller, _ = fenster
    window.entry.insert("end", "Eine Frage")
    window._auf_eingabetaste(None)
    assert len(controller.messages()) == 2


def test_strg_n_und_escape_sind_belegt(fenster):
    window, _, _ = fenster
    for taste in ("<Control-n>", "<Control-N>", "<Escape>"):
        assert taste in window.root.bindings, f"{taste} fehlt"


def test_escape_ohne_laufende_erzeugung_tut_nichts(fenster):
    """Escape darf keine Unterhaltung schliessen und nichts verwerfen."""
    window, controller, _ = fenster
    window.entry.insert("end", "Eine Frage")
    window._send()
    vorher = len(controller.messages())

    window._laufende_aufgabe = None
    assert window._auf_escape(None) == "break"
    assert len(controller.messages()) == vorher


def test_strg_n_beginnt_eine_neue_unterhaltung(fenster):
    window, controller, _ = fenster
    window.entry.insert("end", "Eine Frage")
    window._send()
    erste = controller.conversation_uid

    window.root.bindings["<Control-n>"](Ereignis())
    assert controller.conversation_uid != erste


# -------------------------------------------------------- Quellenpanel
def test_quellen_erscheinen_als_karten(fenster):
    window, _, _ = fenster
    window.entry.insert("end", "Welche Pflichtangaben braucht eine Rechnung?")
    window._send()

    panel = window.quellenpanel
    assert panel.anzahl > 0, "es muessen Karten entstehen"
    assert "Fundstellen" in panel.untertitel.options["text"]


def test_ohne_fundstelle_sagt_das_panel_das_auch(fenster):
    """Ein leeres Panel ohne Erklaerung sieht aus wie ein Fehler."""
    window, _, _ = fenster
    window.quellenpanel.setzen([], [])
    assert window.quellenpanel.anzahl == 0
    assert "keine Fundstelle" in window.quellenpanel.untertitel.options["text"]


def test_das_panel_laesst_sich_ausblenden(fenster):
    """Auftrag Abschnitt 18: einklappbar - dann hat die Antwort die ganze
    Breite."""
    window, _, _ = fenster
    panel = window.quellenpanel
    assert panel.eingeklappt is False
    panel.klapp_knopf.invoke()
    assert panel.eingeklappt is True
    assert panel.klapp_knopf.options["text"] == "einblenden"
    panel.klapp_knopf.invoke()
    assert panel.eingeklappt is False


# --------------------------------------------------- Recherche-Details
def test_recherche_details_sind_zuerst_geschlossen(fenster):
    """Auftrag Abschnitt 19: technische Angaben gehoeren nicht in die
    normale Ansicht."""
    window, _, _ = fenster
    panel = window.quellenpanel
    assert panel.details_offen is False
    assert "anzeigen" in panel.details_knopf.options["text"]
    # Nicht nur das Merkmal, sondern die Wirkung: das Feld darf nicht
    # angezeigt werden. Eine Gegenprobe, die das Feld sichtbar machte,
    # ohne das Merkmal zu aendern, lief sonst unbemerkt durch.
    assert panel.details_feld.sichtbar is False, (
        "die Recherche-Details duerfen nicht von Anfang an dastehen")


def test_bewertungen_stehen_nur_in_den_details(fenster):
    """Eine Bewertungszahl neben einer Gesetzesangabe sieht aus, als
    gehoere sie zur fachlichen Aussage. Sie tut es nicht."""
    window, _, _ = fenster
    window.entry.insert("end", "Welche Pflichtangaben braucht eine Rechnung?")
    window._send()

    panel = window.quellenpanel
    assert "Bewertung" in panel.detailtext, "die Details nennen die Bewertung"
    assert "gefunden:" in panel.detailtext and "verwendet:" in panel.detailtext

    # In der sichtbaren Antwort darf davon nichts stehen. Geprueft werden
    # die technischen Merkmale, nicht das Wort "Bewertung": das kommt in
    # einer Fachantwort voellig zu Recht vor ("steuerliche Bewertung").
    # Diese Unterscheidung ist der ganze Punkt von Abschnitt 19.
    sichtbar = window.chat.buffer + panel.untertitel.options["text"]
    for kennzeichen in ("gefunden:", "verwendet:", "Kennung / Herkunft"):
        assert kennzeichen not in sichtbar, (
            f"{kennzeichen!r} gehoert nur in die Recherche-Details")
    # Auch die Kennungen der Fundstellen bleiben draussen.
    kennungen = [q.ref_id for q in
                 (window._letzte_quellen or []) if getattr(q, "ref_id", "")]
    for kennung in kennungen:
        assert kennung not in window.chat.buffer, (
            "Dokument-Kennungen gehoeren nicht in die Antwort (E6 §18)")


def test_details_lassen_sich_auf_und_zuklappen(fenster):
    window, _, _ = fenster
    panel = window.quellenpanel
    panel.details_knopf.invoke()
    assert panel.details_offen is True
    assert panel.details_feld.sichtbar is True
    assert "ausblenden" in panel.details_knopf.options["text"]
    panel.details_knopf.invoke()
    assert panel.details_offen is False
    assert panel.details_feld.sichtbar is False


# ------------------------------------------------------ Datei anhaengen
def test_ziehen_und_auswaehlen_gehen_denselben_weg(fenster, tmp_path):
    """Zwei Wege haetten frueher oder spaeter zwei Verhalten - und dann
    klappt es beim Auswaehlen und beim Ziehen nicht."""
    window, controller, _ = fenster
    beleg = tmp_path / "rechnung.txt"
    beleg.write_text("# Rechnung 2026-7\nNetto 200,00 EUR zzgl. Umsatzsteuer.\n",
                     encoding="utf-8")

    window._datei_abgelegt([str(beleg)])

    assert controller.documents(), "der hergezogene Beleg muss aufgenommen sein"
    assert "Beleg aufgenommen" in window.chat.buffer


def test_die_ablageflaeche_ist_immer_ein_klickziel(fenster):
    """Kommt die Ablage nicht zustande, bleibt der Bereich benutzbar -
    statt eine Aufforderung zu zeigen, die nicht funktioniert."""
    window, _, _ = fenster
    assert "<Button-1>" in window.drop_hinweis.bindings
    if not window.ablage_moeglich:
        assert "nicht verfuegbar" in window.drop_hinweis.options["text"]


def test_die_dateiablage_meldet_ehrlich_wenn_sie_nicht_geht():
    """Auf Linux gibt es sie nicht - und das wird gesagt, nicht behauptet."""
    from ui import dateiablage

    if dateiablage.verfuegbar():
        pytest.skip("laeuft unter Windows - dort wird sie eingerichtet")
    assert dateiablage.einrichten(object(), lambda _p: None) is False
