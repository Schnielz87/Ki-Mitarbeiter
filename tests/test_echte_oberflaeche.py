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

    # Keine echten Meldungsfenster. Ein echtes ``messagebox.showinfo``
    # wartet auf einen Klick; in einem Test, den niemand anklickt, steht
    # damit alles - der erste Anlauf blieb genau daran haengen.
    #
    # Der Ersatz muss **hier** gesetzt werden und nicht in einer eigenen
    # Fixture davor: diese Fixture laedt das Paket ``ui`` frisch, und ein
    # vorher gesetzter Ersatz haengt dann am alten Modul. Genau so ist
    # der erste Versuch gescheitert - der Ersatz war da und wirkte nicht.
    tk_app.messagebox = _Meldungen()

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


class _Meldungen:
    """Ein Ersatz fuer ``messagebox`` - merkt sich, statt zu fragen.

    Geprueft wird hier das Aussehen und das Verhalten der Flaechen. Den
    Wortlaut der Meldungen prueft ``test_neue_ansichten.py`` gegen das
    Doppel.
    """

    def __init__(self):
        self.gemeldet: list[tuple[str, str]] = []

    def showinfo(self, titel="", text="", **k):
        self.gemeldet.append((titel, text))

    showwarning = showinfo
    showerror = showinfo

    def askyesno(self, titel="", text="", **k):
        self.gemeldet.append((titel, text))
        return True


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


def test_das_fenstersymbol_wird_wirklich_gesetzt(fenster):
    """In der Titelleiste stand die Feder von Tk statt des PORTIVA-P.

    Die vorherige Fassung rief ``iconbitmap(default=...)`` auf und war
    damit zufrieden. ``default`` setzt aber das Symbol fuer Fenster, die
    *danach* entstehen; das schon offene Fenster behaelt seines. Der
    Aufruf meldete keinen Fehler - er tat nur etwas anderes als gemeint.

    Geprueft wird deshalb nicht "es gab keine Ausnahme", sondern dass
    mindestens ein Weg das Symbol wirklich gesetzt hat, und dass der Weg
    fuer *dieses* Fenster dabei ist.
    """
    from ui import tk_app

    geschafft = tk_app._fenstericon(fenster.root, fenster.brand)
    assert geschafft, (
        "Kein Weg hat funktioniert - in der Titelleiste stuende das "
        "Standardbild von Tk.")
    fuer_dieses_fenster = {"iconbitmap", "iconphoto"} & set(geschafft)
    assert fuer_dieses_fenster, (
        f"Nur {geschafft} - das setzt das Symbol erst fuer spaetere "
        "Fenster, nicht fuer dieses.")


def test_die_symboldateien_gibt_es_und_sie_sind_lesbar():
    """Ein Symbolweg kann nur greifen, wenn die Datei auch da ist."""
    from pkc.branding import load_brand
    from pkc.config import Config
    from pkc.paths import Paths
    import tempfile

    wurzel = Path(tempfile.mkdtemp())
    pfade = Paths(wurzel)
    pfade.ensure_runtime_dirs()
    pfade.write_marker()
    brand = load_brand(pfade, Config.load(pfade))

    ico = brand.icon_pfad
    assert ico is not None and ico.exists(), "portiva_icon.ico fehlt"
    png = brand.variante("icon")
    assert png is not None and png.exists(), "portiva_icon.png fehlt"

    # Die .ico muss die kleinen Groessen enthalten - Windows nimmt fuer
    # die Titelleiste 16x16. Fehlen sie, skaliert Windows die grosse
    # Fassung herunter, und das sieht matschig aus.
    kopf = ico.read_bytes()[:6]
    assert kopf[:4] == b"\x00\x00\x01\x00", "das ist keine gueltige .ico-Datei"
    anzahl = int.from_bytes(kopf[4:6], "little")
    assert anzahl >= 4, f"die .ico enthaelt nur {anzahl} Groessen"


def test_der_vorlagenbereich_schneidet_nichts_ab(fenster):
    """Ein neuer Bereich mit zwei Spalten ist der klassische Ort dafuer.

    Gemessen wird jedes sichtbare Element des Bereichs, nicht nur die
    Knoepfe: abgeschnitten wird zuerst eine Beschriftung neben einem
    Eingabefeld.
    """
    fenster.schale.zeigen("vorlagen")
    _durchatmen(fenster.root, 4)

    zu_breit = []

    def messen(element) -> None:
        if _abgeschnitten(element):
            beschriftung = ""
            try:
                beschriftung = str(element.cget("text"))
            except Exception:
                beschriftung = element.winfo_class()
            zu_breit.append(
                f"{beschriftung!r}: braucht {element.winfo_reqwidth()}, "
                f"hat {element.winfo_width()}")
        for kind in element.winfo_children():
            messen(kind)

    messen(fenster.schale.bereiche["vorlagen"].rahmen)
    assert not zu_breit, "Im Vorlagenbereich fehlt Text:\n" + "\n".join(zu_breit)


def test_eine_vorlage_laesst_sich_im_echten_fenster_waehlen(fenster):
    """Die Liste traegt ihre Kennungen - im echten Tk, nicht im Doppel."""
    fenster.schale.zeigen("vorlagen")
    _durchatmen(fenster.root, 3)

    kennungen = fenster.vorlagen_tree.get_children()
    assert "mandantenbrief" in kennungen, \
        f"die mitgelieferten Vorlagen fehlen: {kennungen}"

    fenster.vorlagen_tree.selection_set("mandantenbrief")
    fenster._vorlage_zeigen()
    _durchatmen(fenster.root, 2)

    assert fenster.vorlage_titel.cget("text") == "Mandantenbrief"
    assert fenster.vorlage_felder, "es muss nach den offenen Stellen fragen"
    assert "{{" not in fenster.vorlage_vorschau_text.get("1.0", "end")


def test_die_vorlagenliste_beschneidet_keinen_namen(fenster):
    """Eine Tabellenspalte beschneidet anders als ein Knopf.

    Ein zu schmaler Knopf braucht mehr Breite, als er hat - das misst
    ``winfo_reqwidth``. Eine Treeview-Spalte dagegen ist nie "zu schmal":
    sie schneidet den Zelltext ab und meldet nichts. Auf dem ersten Bild
    des fertigen Bereichs stand "Umsatzsteuer-Voranmeldung - Abgab", und
    der Breitentest daneben war gruen.

    Deshalb hier von Hand: die Textbreite in der tatsaechlichen Schrift
    gegen die Spaltenbreite.
    """
    from tkinter import font as tkfont
    from tkinter import ttk

    fenster.schale.zeigen("vorlagen")
    _durchatmen(fenster.root, 3)

    baum = fenster.vorlagen_tree
    # Das Fenster dieses Tests ausdruecklich mitgeben. Ohne ``root``
    # sucht Tk das "Standardfenster" - und wenn ein frueherer Test seines
    # schon zerstoert hat, bricht die Schriftabfrage ab. Der Test war
    # damit allein gruen und im Verbund rot.
    # ``lookup`` liefert je nach Thema einen Namen ("TkDefaultFont") oder
    # eine Beschreibung ("{DejaVu Sans} 9"). ``Font(font=...)`` nimmt
    # beides; ``nametofont`` nur das erste.
    spec = ttk.Style(fenster.root).lookup("Treeview", "font") or "TkDefaultFont"
    schrift = tkfont.Font(root=fenster.root, font=spec)
    # Tk laesst links und rechts in einer Zelle etwas Luft.
    LUFT = 12

    zu_lang = []
    for kennung in baum.get_children():
        werte = baum.item(kennung)["values"]
        for spalte, wert in zip(("name", "kategorie", "format"), werte):
            breite = int(baum.column(spalte, "width"))
            gebraucht = schrift.measure(str(wert)) + LUFT
            if gebraucht > breite:
                zu_lang.append(
                    f"{spalte}: {wert!r} braucht {gebraucht}, "
                    f"Spalte ist {breite}")
    assert not zu_lang, "In der Vorlagenliste fehlt Text:\n" + "\n".join(zu_lang)


def test_der_aufgabenbereich_schneidet_nichts_ab(fenster):
    """Ein Formular mit Beschriftungen neben Feldern - der klassische Ort.

    Zusaetzlich zum Breitentest wird hier auch die Hoehe geprueft: der
    Bereich stapelt Liste, Formular und den Windows-Kasten untereinander.
    Passt das zusammen nicht ins Fenster, faellt der unterste Teil
    heraus, ohne dass ein einzelnes Element zu klein waere.
    """
    fenster.schale.zeigen("aufgaben")
    _durchatmen(fenster.root, 4)

    zu_breit = []

    def messen(element) -> None:
        if _abgeschnitten(element):
            try:
                beschriftung = str(element.cget("text"))
            except Exception:
                beschriftung = element.winfo_class()
            zu_breit.append(
                f"{beschriftung!r}: braucht {element.winfo_reqwidth()}, "
                f"hat {element.winfo_width()}")
        for kind in element.winfo_children():
            messen(kind)

    rahmen = fenster.schale.bereiche["aufgaben"].rahmen
    messen(rahmen)
    assert not zu_breit, "Im Aufgabenbereich fehlt Text:\n" + "\n".join(zu_breit)

    assert fenster.windows_planung_text.winfo_ismapped(), (
        "Der Hinweis zur Windows-Aufgabenplanung ist aus dem Fenster "
        "gefallen - er steht ganz unten und wird als erstes abgeschnitten.")


def test_eine_aufgabe_entsteht_im_echten_fenster(fenster):
    """Der ganze Weg mit echten Bedienelementen, nicht gegen ein Doppel."""
    fenster.schale.zeigen("aufgaben")
    _durchatmen(fenster.root, 2)

    fenster.aufgabe_name.set("Naechtliche Sicherung")
    fenster.aufgabe_aktion.set("Sicherung anlegen")
    fenster.aufgabe_wann.set("taeglich")
    fenster.aufgabe_uhrzeit.set("23:00")
    fenster._aufgabe_anlegen()
    _durchatmen(fenster.root, 2)

    kennungen = fenster.aufgaben_tree.get_children()
    assert kennungen, "die Aufgabe muss in der Liste stehen"
    werte = fenster.aufgaben_tree.item(kennungen[0])["values"]
    assert werte[0] == "Naechtliche Sicherung"
    assert werte[1] == "Taeglich um 23:00"
    assert werte[3] == "aktiv"


def test_die_aufgabenliste_beschneidet_keinen_text(fenster):
    """Wie bei den Vorlagen: eine Tabellenspalte meldet nicht, dass sie
    zu schmal ist - sie schneidet einfach ab."""
    from tkinter import font as tkfont
    from tkinter import ttk

    fenster.schale.zeigen("aufgaben")
    fenster.aufgabe_name.set("Wissen jede Woche aktualisieren")
    fenster.aufgabe_aktion.set("Wissen aktualisieren")
    fenster.aufgabe_wann.set("intervall")
    fenster.aufgabe_stunden.set("168")
    fenster._aufgabe_anlegen()
    _durchatmen(fenster.root, 3)

    baum = fenster.aufgaben_tree
    spec = ttk.Style(fenster.root).lookup("Treeview", "font") or "TkDefaultFont"
    schrift = tkfont.Font(root=fenster.root, font=spec)
    LUFT = 12

    zu_lang = []
    spalten = ("name", "wann", "aktion", "zustand", "letzter", "ergebnis")
    for kennung in baum.get_children():
        for spalte, wert in zip(spalten, baum.item(kennung)["values"]):
            breite = int(baum.column(spalte, "width"))
            gebraucht = schrift.measure(str(wert)) + LUFT
            if gebraucht > breite:
                zu_lang.append(f"{spalte}: {wert!r} braucht {gebraucht}, "
                               f"Spalte ist {breite}")
    assert not zu_lang, "In der Aufgabenliste fehlt Text:\n" + "\n".join(zu_lang)
