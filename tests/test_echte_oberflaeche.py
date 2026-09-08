"""Prueft die Oberflaeche mit **echtem** Tkinter, nicht gegen ein Doppel.

Warum es das gibt: Das Testdoppel sagt, dass ein Knopf angelegt wurde und
eine Funktion hinterlegt ist. Es sagt nicht, ob der Knopf breit genug ist
fuer seine Beschriftung. Genau daran ist die erste Fassung der neuen
Oberflaeche gescheitert: aus "Senden" wurde "Send", aus "Sicherung
erstellen" ein "S", und in der Seitenleiste stand "Plugins &
Erweiterunge". 745 gruene Tests haben davon nichts gemerkt.

Diese Tests brauchen einen Bildschirm. Sie laufen

* unter Windows (dort hat auch der Bauablauf einen),
* unter Linux mit ``xvfb-run`` oder einem gesetzten ``DISPLAY``.

Sonst werden sie uebersprungen - ausdruecklich und mit Begruendung, nicht
still. Ein uebersprungener Test, von dem niemand weiss, ist schlimmer als
gar keiner.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]

tk = pytest.importorskip("tkinter", reason="Tkinter ist nicht installiert")

if os.name != "nt" and not os.environ.get("DISPLAY"):
    pytest.skip("kein Bildschirm - unter Linux mit xvfb-run starten",
                allow_module_level=True)


@pytest.fixture(autouse=True)
def ohne_dateiablage(monkeypatch):
    """Kein Eingriff in die Fensterprozedur waehrend der Tests.

    Unter Windows richtet die Anwendung Drag & Drop ein, indem sie die
    Fensterprozedur durch eine Python-Funktion ersetzt. Fuer den Betrieb
    ist das richtig. In einem Test ist es gefaehrlich: das Fenster wird am
    Ende zerstoert, die Rueckruffunktion lebt in Python, und in welcher
    Reihenfolge beides passiert, ist nichts, worauf man bauen sollte.
    Geprueft wird hier das Aussehen, nicht die Dateiablage.
    """
    from ui import dateiablage

    monkeypatch.setenv(dateiablage.ABSCHALTER, "1")


@pytest.fixture
def fenster(portable_root):
    """Ein echtes Hauptfenster auf einem echten Bildschirm.

    Vor dem Aufbau wird das Tkinter-Doppel entfernt. Es ersetzt ``tkinter``
    fuer den ganzen Prozess; lief vorher ein Test gegen das Doppel, bekaeme
    dieser Test hier ebenfalls das Doppel - und wuerde nichts von dem
    pruefen, wofuer er da ist.
    """
    import tk_double

    tk_double.entfernen()
    from test_controller import make_controller
    from ui import tk_app

    steuerung = make_controller(portable_root)
    bericht = steuerung.bootstrap()
    try:
        fenster = tk_app.MainWindow(steuerung, bericht)
    except tk.TclError as fehler:                # pragma: no cover
        pytest.skip(f"Tk laesst sich nicht oeffnen: {fehler}")
    fenster.root.geometry("1500x940+0+0")
    _durchatmen(fenster.root)
    yield fenster
    try:
        fenster.root.destroy()
    except Exception:                            # pragma: no cover
        pass
    steuerung.shutdown()
    # Die Module wieder freigeben, damit der naechste Test sie frisch
    # gegen das Doppel laden kann - das Paket "ui" eingeschlossen.
    tk_double.ui_module_freigeben()


def _durchatmen(dach, runden: int = 5) -> None:
    for _ in range(runden):
        dach.update_idletasks()
        dach.update()


def _abgeschnitten(widget) -> bool:
    """Braucht das Element mehr Breite, als es bekommen hat?

    ``winfo_reqwidth`` ist die Breite, die der Inhalt braucht;
    ``winfo_width`` die, die er hat. Ist die erste groesser, fehlt Text.
    Zwei Bildpunkte Nachsicht, damit Rundungen keinen Fehlalarm ausloesen.
    """
    if not widget.winfo_ismapped():
        return False
    return widget.winfo_reqwidth() > widget.winfo_width() + 2


def test_kein_eintrag_der_seitenleiste_wird_abgeschnitten(fenster):
    """In der Leiste stand "Plugins & Erweiterunge" - ohne das n.

    Die Leiste hat eine feste Breite. Ein Eintrag, der nicht hineinpasst,
    wird von Tk stillschweigend beschnitten - kein Fehler, keine Meldung,
    nur ein halbes Wort.
    """
    zu_breit = []
    gemessen = 0
    for kennung in fenster.schale.reihenfolge:
        # Jeden Eintrag **aktiv** messen. Der aktive Eintrag wird fett
        # gesetzt, und fett ist breiter. Die erste Fassung dieses Tests
        # hat nur den nicht-aktiven Zustand gemessen und deshalb nichts
        # gefunden - obwohl auf dem Bildschirmfoto "Plugins &
        # Erweiterunge" stand. Aufgefallen an einer Gegenprobe, die nicht
        # ansprang.
        fenster.schale.zeigen(kennung)
        _durchatmen(fenster.root, 2)
        knopf = fenster.schale.bereiche[kennung].knopf
        if knopf is None:
            continue
        assert knopf.winfo_ismapped(), f"Eintrag {kennung} ist nicht sichtbar"
        gemessen += 1
        if _abgeschnitten(knopf):
            zu_breit.append(
                f"{kennung}: {knopf.cget('text').strip()!r} braucht "
                f"{knopf.winfo_reqwidth()}, hat {knopf.winfo_width()}")
    assert gemessen >= 5, f"nur {gemessen} Eintraege gemessen - zu wenige"
    assert not zu_breit, "Beschriftungen passen nicht in die Leiste:\n" + \
        "\n".join(zu_breit)


def test_die_knoepfe_der_unterhaltung_zeigen_ihre_volle_beschriftung(fenster):
    """Aus "Senden" war "Send" geworden, aus "Stoppen" ein "Stopp"."""
    fenster.schale.zeigen("unterhaltung")
    _durchatmen(fenster.root)
    zu_breit = [f"{k.cget('text')!r}: braucht {k.winfo_reqwidth()}, "
                f"hat {k.winfo_width()}"
                for k in (fenster.send_button, fenster.stop_button)
                if _abgeschnitten(k)]
    assert not zu_breit, "\n".join(zu_breit)


def test_der_betriebsmodus_ist_im_auswahlfeld_lesbar(fenster):
    """Das Feld sah leer aus, obwohl "OFFLINE" darinstand.

    Ursache war die Markierungsfarbe: ein Auswahlfeld mit
    ``state="readonly"`` zeichnet seinen Text markiert, und die
    Markierungsschrift des Themas war weiss - auf weissem Feld.

    Geprueft wird deshalb nicht der Wert (den gab es die ganze Zeit),
    sondern dass sich Schrift- und Hintergrundfarbe unterscheiden.
    """
    from tkinter import ttk

    assert fenster.mode_box.get(), "im Feld muss ein Betriebsmodus stehen"
    stil = ttk.Style(fenster.root)
    schrift = stil.lookup("TCombobox", "selectforeground")
    grund = stil.lookup("TCombobox", "selectbackground")
    assert schrift and grund, "beide Farben muessen gesetzt sein"
    assert str(schrift).lower() != str(grund).lower(), (
        f"Schrift und Hintergrund sind gleich ({schrift}) - der Text waere "
        "unsichtbar")


def test_alle_bereiche_lassen_sich_wirklich_oeffnen(fenster):
    """Jeder Bereich muss sich zeigen lassen, ohne dass Tk sich beschwert.

    Gegen das Doppel lief das immer durch. Auf einem echten Bildschirm
    faellt auf, wenn eine Ansicht beim Aufbauen in einen Fehler laeuft
    oder gar nicht sichtbar wird.
    """
    for kennung in fenster.schale.reihenfolge:
        fenster.schale.zeigen(kennung)
        _durchatmen(fenster.root, 2)
        bereich = fenster.schale.bereiche[kennung]
        assert bereich.rahmen.winfo_ismapped(), (
            f"Bereich {kennung} wird nicht angezeigt")
        assert bereich.rahmen.winfo_width() > 200, (
            f"Bereich {kennung} ist nur {bereich.rahmen.winfo_width()} "
            "Bildpunkte breit")


def test_die_statusspalte_schneidet_ihre_werte_nicht_ab(fenster):
    """"Lokales Modell" und "nicht eingerichtet" lagen uebereinander."""
    fenster.schale.zeigen("einstellungen")
    _durchatmen(fenster.root)
    zu_breit = []
    for name, (namelabel, wertlabel) in fenster._statuszeilen.items():
        for label in (namelabel, wertlabel):
            if _abgeschnitten(label):
                zu_breit.append(
                    f"{name}: {label.cget('text')!r} braucht "
                    f"{label.winfo_reqwidth()}, hat {label.winfo_width()}")
    assert not zu_breit, "\n".join(zu_breit)


def _alles_abgeschnittene(widget, treffer=None):
    """Sucht das ganze Fenster nach beschnittenem Text ab."""
    treffer = [] if treffer is None else treffer
    try:
        kinder = widget.winfo_children()
    except Exception:                                # pragma: no cover
        return treffer
    for kind in kinder:
        try:
            if _abgeschnitten(kind):
                text = ""
                try:
                    text = str(kind.cget("text"))
                except Exception:                    # kein Textelement
                    text = ""
                if text.strip():
                    treffer.append(
                        f"{kind.winfo_class()} {text[:50]!r}: braucht "
                        f"{kind.winfo_reqwidth()}, hat {kind.winfo_width()}")
        except Exception:                            # pragma: no cover
            pass
        _alles_abgeschnittene(kind, treffer)
    return treffer


def test_auf_einem_kleinen_fenster_wird_nichts_abgeschnitten(fenster):
    """Die Mindestgroesse muss benutzbar sein, nicht nur die Wunschgroesse.

    Bei 900 mal 600 war die Unterhaltung ein Streifen von 130
    Bildpunkten: Seitenleiste, Quellenspalte und Knopfspalte hatten den
    Platz unter sich aufgeteilt. Die Oberflaeche raeumt jetzt selbst auf -
    Quellenspalte weg, Navigation auf die Sinnbilder, kurzer
    Tastenhinweis.

    Geprueft wird das ganze Fenster, nicht einzelne Elemente. Was hier
    durchrutscht, sieht der Anwender.
    """
    fenster.schale.zeigen("unterhaltung")
    fenster.root.geometry("900x600")
    _durchatmen(fenster.root, 6)
    zu_breit = _alles_abgeschnittene(fenster.root)
    assert not zu_breit, ("Auf 900x600 wird Text abgeschnitten:\n"
                          + "\n".join(zu_breit))


def _breite_setzen(fenster, breite: int, hoehe: int) -> int:
    """Setzt die Fenstergroesse und gibt die zurueck, die es bekommen hat.

    Nicht dasselbe: ein Fenstermanager darf eine Wunschgroesse kuerzen,
    und auf einem Bildschirm, der schmaler ist als der Wunsch, tut er das
    auch. Wer die Wunschgroesse fuer bare Muenze nimmt, prueft am Ende
    eine Lage, die es gar nicht gibt.
    """
    fenster.root.geometry(f"{breite}x{hoehe}")
    _durchatmen(fenster.root, 6)
    return int(fenster.root.winfo_width())


def test_die_quellenspalte_folgt_der_fensterbreite(fenster):
    """Ausblenden ist nur richtig, wenn es sich auch wieder umkehrt.

    Geprueft wird gegen die Breite, die das Fenster **tatsaechlich** hat -
    nicht gegen die, die angefordert wurde. Auf dem Windows-Baurechner
    schlug die erste Fassung dieses Tests fehl: dort blieb das Fenster
    schmaler als die angeforderten 1500 Bildpunkte, die Quellenspalte
    blieb folgerichtig ausgeblendet, und der Test verlangte trotzdem, dass
    sie da ist. Der Fehler lag im Test, nicht in der Anwendung - aber das
    war erst zu sehen, nachdem gemessen statt angenommen wurde.
    """
    fenster.schale.zeigen("unterhaltung")

    lagen = []
    for breite, hoehe in ((900, 600), (1500, 940), (1000, 700)):
        ist = _breite_setzen(fenster, breite, hoehe)
        erwartet_quellen = ist >= tk_app_modul(fenster).SCHWELLE_QUELLEN
        erwartet_leiste = ist < tk_app_modul(fenster).SCHWELLE_LEISTE
        assert fenster._quellenspalte_ist_da is erwartet_quellen, (
            f"Bei {ist} Bildpunkten Breite muesste die Quellenspalte "
            f"{'sichtbar' if erwartet_quellen else 'ausgeblendet'} sein.")
        assert fenster.schale.eingeklappt is erwartet_leiste, (
            f"Bei {ist} Bildpunkten Breite muesste die Navigation "
            f"{'eingeklappt' if erwartet_leiste else 'offen'} sein.")
        lagen.append((ist, erwartet_quellen))

    # Der Test taugt nur etwas, wenn beide Lagen wirklich vorkamen. Sonst
    # hat er dreimal dasselbe geprueft und nichts ueber das Umschalten
    # ausgesagt.
    if len({sichtbar for _breite, sichtbar in lagen}) < 2:
        pytest.skip(
            "Auf diesem Bildschirm liessen sich keine zwei verschiedenen "
            f"Lagen herstellen (gemessene Breiten: "
            f"{[b for b, _ in lagen]}). Das Umschalten ist damit hier "
            "nicht pruefbar.")


def tk_app_modul(fenster):
    """Das Modul, aus dem dieses Fenster stammt - fuer die Schwellenwerte."""
    import sys

    return sys.modules[type(fenster).__module__]
