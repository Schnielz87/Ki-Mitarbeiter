"""Arbeitsergebnisse, Plugins und Verbundene Dienste.

Diese drei Ansichten sind reine Oberflaeche zu Diensten, die es laengst
gab. Genau das wird hier geprueft: dass jeder sichtbare Knopf einen realen
Vorgang ausloest und nicht nur ein Ereignis (Auftrag Abschnitt 34 und 48).
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


def _artefakt_anlegen(controller, name="Probe"):
    return controller.datei_erzeugen("# Bericht\n\nEin Satz.", "txt", name)


# ------------------------------------------------- Arbeitsergebnisse
def test_die_zehn_bereiche_sind_erreichbar(fenster):
    """Der Zielentwurf nennt zehn Hauptbereiche."""
    window, _, _ = fenster
    vorhanden = set(window.schale.bereiche)
    for kennung in ("unterhaltung", "unternehmenswissen", "belege",
                    "arbeitsergebnisse", "wissen_quellen", "plugins",
                    "dienste", "einstellungen"):
        assert kennung in vorhanden, f"{kennung} fehlt"


def test_erzeugte_dateien_erscheinen_in_der_liste(fenster):
    window, controller, _ = fenster
    _artefakt_anlegen(controller)
    window._refresh_results()
    assert window.results_tree.rows, "das Arbeitsergebnis muss erscheinen"
    werte = list(window.results_tree.rows.values())[0]["values"]
    assert "Probe" in werte[0]
    assert werte[1] == "TXT"
    assert werte[5] == "vorhanden"


def test_ohne_auswahl_wird_gesagt_was_fehlt(fenster):
    """Kein stilles Nichtstun - wer drueckt, bekommt eine Antwort."""
    window, controller, dialoge = fenster
    _artefakt_anlegen(controller)
    window._refresh_results()
    window.results_tree._selection = ()
    window._result_oeffnen()
    assert any("auswaehlen" in text for _, _, text in dialoge.messages)


def test_exportieren_legt_wirklich_eine_kopie_an(fenster, tmp_path):
    """Ende zu Ende: Klick -> Dienst -> Datei liegt da (Abschnitt 48)."""
    window, controller, dialoge = fenster
    artefakt = _artefakt_anlegen(controller)
    window._refresh_results()
    window.results_tree.select_row(0)

    ziel = tmp_path / "export" / "Kopie.txt"
    dialoge.save_file = str(ziel)
    window._result_exportieren()

    assert ziel.is_file(), "die Kopie muss wirklich entstanden sein"
    assert ziel.read_text(encoding="utf-8")
    assert artefakt.pfad.is_file(), "das Original bleibt erhalten"


def test_abbrechen_beim_export_legt_nichts_an(fenster, tmp_path):
    window, controller, dialoge = fenster
    _artefakt_anlegen(controller)
    window._refresh_results()
    window.results_tree.select_row(0)

    # Ein eigener, leerer Ordner. Auf den Datentraeger zu schauen waere
    # sinnlos - dort liegt das Original ja schon.
    ausserhalb = tmp_path / "woanders"
    ausserhalb.mkdir()
    dialoge.save_file = None            # Benutzer bricht ab
    window._result_exportieren()
    assert list(ausserhalb.iterdir()) == []


def test_umbenennen_wirkt_auf_datei_und_liste(fenster):
    window, controller, dialoge = fenster
    _artefakt_anlegen(controller)
    window._refresh_results()
    window.results_tree.select_row(0)

    dialoge.answers = ["Monatsbericht"]
    window._result_umbenennen()

    namen = [z["values"][0] for z in window.results_tree.rows.values()]
    assert any("Monatsbericht" in n for n in namen), namen
    assert (controller.artefakte.ordner / "Monatsbericht.txt").is_file()


def test_die_endung_laesst_sich_nicht_ueberschreiben(fenster):
    """Eine XLSX-Datei "Bericht.txt" zu nennen erzeugt eine Datei, die kein
    Programm mehr oeffnet."""
    window, controller, dialoge = fenster
    _artefakt_anlegen(controller)
    window._refresh_results()
    window.results_tree.select_row(0)
    dialoge.answers = ["Bericht.pdf"]
    window._result_umbenennen()
    assert (controller.artefakte.ordner / "Bericht.txt").is_file()
    assert not (controller.artefakte.ordner / "Bericht.pdf").exists()


def test_loeschen_fragt_und_entfernt_die_datei(fenster):
    window, controller, dialoge = fenster
    artefakt = _artefakt_anlegen(controller)
    window._refresh_results()
    window.results_tree.select_row(0)

    dialoge.answers = [False]
    window._result_loeschen()
    assert artefakt.pfad.is_file(), "ohne Bestaetigung wird nichts geloescht"

    window.results_tree.select_row(0)
    dialoge.answers = [True]
    window._result_loeschen()
    assert not artefakt.pfad.exists()


def test_der_verzeichniseintrag_bleibt_als_nachweis(fenster):
    """Die Datei ist weg, der Nachweis bleibt - mit Pruefsumme und Zeit."""
    window, controller, dialoge = fenster
    _artefakt_anlegen(controller)
    window._refresh_results()
    window.results_tree.select_row(0)
    dialoge.answers = [True]
    window._result_loeschen()

    eintraege = controller.artefakt_liste()
    assert eintraege, "der Eintrag muss erhalten bleiben"
    assert eintraege[0]["vorhanden"] is False
    assert eintraege[0].get("pruefsumme"), "die Pruefsumme bleibt der Nachweis"


# ------------------------------------------------------------ Plugins
def test_pluginansicht_zeigt_den_leerzustand(fenster):
    """Ein leerer Bereich muss sagen, dass er leer ist - nicht nichts."""
    window, _, _ = fenster
    assert "Noch keine Plugins" in window.plugins_hint.options["text"]


def test_pluginansicht_listet_installierte_plugins(fenster, tmp_path):
    window, controller, _ = fenster
    beispiel = _beispielplugin(tmp_path)
    controller.plugins.installieren(beispiel, bestaetigt=True)
    window._refresh_plugins()
    assert window.plugins_tree.rows, "das Plugin muss in der Liste stehen"
    werte = list(window.plugins_tree.rows.values())[0]["values"]
    assert werte[0] == "html_export"
    assert werte[4] in ("installiert", "aktiv")
    assert werte[5] == "nicht signiert"


def test_plugin_aktivieren_wirkt_im_dienst(fenster, tmp_path):
    window, controller, _ = fenster
    controller.plugins.installieren(_beispielplugin(tmp_path), bestaetigt=True)
    window._refresh_plugins()
    window.plugins_tree.select_row(0)
    window._plugin_schalten(True)

    stand = controller.plugins.stand("html_export")
    assert stand is not None and stand.aktiv, "die Aenderung muss ankommen"
    assert "aktiv" in window.plugins_log.buffer


def test_deinstallieren_fragt_vorher(fenster, tmp_path):
    window, controller, dialoge = fenster
    controller.plugins.installieren(_beispielplugin(tmp_path), bestaetigt=True)
    window._refresh_plugins()
    window.plugins_tree.select_row(0)

    dialoge.answers = [False]
    window._plugin_entfernen()
    assert controller.plugins.stand("html_export") is not None

    window.plugins_tree.select_row(0)
    dialoge.answers = [True]
    window._plugin_entfernen()
    assert controller.plugins.stand("html_export") is None


def _beispielplugin(tmp_path):
    """Packt das mitgelieferte Beispielplugin zu einer Datei."""
    from pathlib import Path

    import pkc.plugins.paket as paketmodul

    wurzel = Path(__file__).resolve().parents[1]
    return Path(paketmodul.packen(wurzel / "examples" / "plugin_html",
                                  tmp_path / "html_export"))


# ------------------------------------------------- Verbundene Dienste
def test_diensteansicht_zeigt_alle_connectoren(fenster):
    window, controller, _ = fenster
    assert window.services_tree.rows, "die Connectoren muessen erscheinen"
    kennungen = {z["values"][0] for z in window.services_tree.rows.values()}
    assert {"datev", "sap"} <= kennungen
    assert "verbunden" in window.services_hint.options["text"]


def test_offline_wird_keine_verbindung_aufgebaut(fenster):
    """Ein Verbindungstest ist ein Netzzugriff - im Offlinebetrieb
    unterbleibt er (Auftrag Abschnitt 31)."""
    window, controller, dialoge = fenster
    from pkc.netstate import Mode

    controller.set_mode(Mode.OFFLINE)
    window.services_tree.select_row(0)
    window._dienst_testen()
    assert "OFFLINE" in window.services_log.buffer


def test_zugangsdaten_stehen_nirgends_im_klartext(fenster):
    """Auftrag Abschnitt 29 - und §21 des Masterprompts."""
    window, controller, _ = fenster
    controller.vault.create("EinSicheresPasswort2026")
    controller.vault.set("connector.datev", "streng-geheimes-kennwort")
    window._refresh_services()
    gesamt = window.services_log.buffer + str(window.services_tree.rows)
    assert "streng-geheimes-kennwort" not in gesamt


def test_trennen_entfernt_das_geheimnis(fenster):
    window, controller, dialoge = fenster
    controller.vault.create("EinSicheresPasswort2026")
    controller.vault.set("connector.datev", "geheim")
    window._refresh_services()
    zeile = next(k for k, v in window.services_tree.rows.items()
                 if v["values"][0] == "datev")
    window.services_tree._selection = (zeile,)

    dialoge.answers = [True]
    window._dienst_trennen()
    assert controller.vault.get_quiet("connector.datev") is None


# ------------------------------------------------- Zielentwurf gesamt
def test_die_navigation_zeigt_genau_die_zehn_bereiche(fenster):
    """Der Zielentwurf nennt zehn Hauptbereiche in fester Reihenfolge.

    Elf waeren einer zu viel, neun einer zu wenig - und die Reihenfolge
    ist Teil der Vorgabe, nicht Geschmackssache.
    """
    window, _, _ = fenster
    assert window.schale.reihenfolge == [
        "unterhaltung", "unternehmenswissen", "belege", "arbeitsergebnisse",
        "wissen_quellen", "vorlagen", "aufgaben", "plugins", "dienste",
        "einstellungen",
    ]


def test_das_sprachmodell_ist_kein_eigener_bereich_mehr(fenster):
    """Es ist eine Einstellung, kein Hauptbereich - und muss trotzdem
    vollstaendig erreichbar bleiben."""
    window, _, _ = fenster
    assert "sprachmodell" not in window.schale.bereiche
    # Die Bedienelemente muss es weiterhin geben, sonst waere die Funktion
    # beim Umbau verlorengegangen.
    # Die Beschriftung wechselt je nachdem, ob schon ein Modell da ist -
    # geprueft wird, dass der Knopf existiert und einen Vorgang hat.
    assert "Modell einrichten" in window.modell_button.options["text"]
    assert window.modell_button.commands.get("command") is not None
    assert hasattr(window, "modell_lage_label")
    assert hasattr(window, "gruppe_modelle")


def test_kein_bereich_ist_mehr_ein_blosses_schild(fenster):
    """Bis Fassung 19 gab es zwei Bereiche, die es nur dem Namen nach gab.

    Sie sagten das auch offen - "Dieser Bereich ist noch nicht
    verfuegbar" - und das war die richtige Loesung, solange sie leer
    waren. Jetzt sind beide gebaut, und der Satz darf nirgends mehr
    stehen. Er waere jetzt eine Falschaussage.
    """
    window, _, _ = fenster
    for kennung, bereich in window.schale.bereiche.items():
        texte = _alle_texte(bereich.rahmen)
        assert not any("noch nicht verfuegbar" in t for t in texte), (
            f"{kennung} gibt sich noch als unfertig aus")


def test_der_aufgabenbereich_kann_wirklich_etwas(fenster):
    window, _, _ = fenster
    flaeche = window.schale.bereiche["aufgaben"].rahmen
    beschriftungen = {k.options.get("text") for k in _alle_knoepfe(flaeche)}
    assert "Aufgabe anlegen" in beschriftungen
    assert "Jetzt ausfuehren" in beschriftungen
    for knopf in _alle_knoepfe(flaeche):
        assert knopf.commands.get("command") is not None, (
            f"toter Knopf: {knopf.options.get('text')}")


def test_eine_aufgabe_laesst_sich_aus_der_oberflaeche_anlegen(fenster):
    window, controller, _ = fenster
    window.aufgabe_name.set("Naechtliche Sicherung")
    window.aufgabe_aktion.set("Sicherung anlegen")
    window.aufgabe_wann.set("taeglich")
    window.aufgabe_uhrzeit.set("23:00")
    window._aufgabe_anlegen()

    aufgaben = controller.aufgaben_liste()
    assert [a.name for a in aufgaben] == ["Naechtliche Sicherung"]
    assert aufgaben[0].ausloeser.beschreibung() == "Taeglich um 23:00"
    assert aufgaben[0].kennung in window.aufgaben_tree.rows


def test_eine_unsinnige_uhrzeit_wird_abgefangen(fenster):
    """Sie kommt aus einem Eingabefeld - da steht irgendwann Unsinn."""
    window, controller, _ = fenster
    window.aufgabe_name.set("Kaputt")
    window.aufgabe_aktion.set("Sicherung anlegen")
    window.aufgabe_wann.set("taeglich")
    window.aufgabe_uhrzeit.set("halb acht")
    window._aufgabe_anlegen()
    assert controller.aufgaben_liste() == []


def test_die_gewaehlte_arbeit_erklaert_sich_vor_dem_anlegen(fenster):
    window, _, _ = fenster
    window.aufgabe_aktion.set("Wissen aktualisieren")
    text = window.aufgabe_aktionstext.options["text"]
    assert "Internet" in text, \
        "vor dem Anlegen muss dastehen, was die Arbeit tut"


def test_ohne_windows_sagt_der_bereich_das_auch(fenster):
    """Auf diesem Rechner gibt es keine Windows-Aufgabenplanung."""
    window, _, _ = fenster
    text = window.windows_planung_text.options["text"]
    assert "nur unter Windows" in text or "geoeffnet" in text


def test_der_vorlagenbereich_ist_kein_schild_mehr(fenster):
    """Er war eine beschriftete Tuer vor einem leeren Raum."""
    window, _, _ = fenster
    flaeche = window.schale.bereiche["vorlagen"].rahmen
    texte = _alle_texte(flaeche)
    assert not any("nicht verfuegbar" in t for t in texte), \
        "der Bereich ist gebaut - der Hinweis muss weg"
    beschriftungen = {k.options.get("text") for k in _alle_knoepfe(flaeche)}
    assert "Datei erzeugen" in beschriftungen
    assert "Vorschau" in beschriftungen
    for knopf in _alle_knoepfe(flaeche):
        assert knopf.commands.get("command") is not None, (
            f"toter Knopf: {knopf.options.get('text')}")


def test_die_mitgelieferten_vorlagen_stehen_in_der_liste(fenster):
    window, _, _ = fenster
    zeilen = window.vorlagen_tree.rows
    namen = [zeile["values"][0] for zeile in zeilen.values()]
    assert "Mandantenbrief" in namen, \
        "der Bereich muss ohne Zutun schon etwas anzubieten haben"
    assert "mandantenbrief" in zeilen, \
        "die Zeile muss ihre Kennung tragen - sonst weiss der Knopf nicht, "\
        "welche Vorlage gemeint ist"


def test_aus_der_oberflaeche_entsteht_eine_datei(fenster):
    """Der ganze Weg: Zeile waehlen, Angabe eintragen, Knopf druecken."""
    window, controller, _ = fenster
    window.vorlagen_tree._selection = ("mandantenbrief",)
    window._vorlage_zeigen()

    assert window.vorlage_felder, "es muss nach den offenen Stellen fragen"
    for name, feld in window.vorlage_felder.items():
        feld.set(f"Wert fuer {name}")
    window.vorlage_format.set("md")
    window._vorlage_erzeugen()

    dateien = controller.artefakt_liste()
    assert dateien, "es muss eine Datei entstanden sein"
    pfad = controller.artefakt_pfad(dateien[0]["name"])
    assert "Wert fuer betreff" in pfad.read_text(encoding="utf-8")


def test_die_vorschau_zeigt_die_offenen_stellen(fenster):
    window, _, _ = fenster
    window.vorlagen_tree._selection = ("mandantenbrief",)
    window._vorlage_zeigen()
    text = window.vorlage_vorschau_text.buffer
    assert "{{" not in text, "in der Vorschau werden sie hervorgehoben"
    assert "betreff" in text


def test_der_systemstatus_ist_eine_ampelliste(fenster):
    """Ein JSON-Block ist kein Systemstatus fuer einen Buchhalter."""
    window, _, _ = fenster
    window._refresh_status()
    assert "PORTIVA Core" in window._statuszeilen
    assert "Lokales Modell" in window._statuszeilen
    _, wert = window._statuszeilen["Lokales Modell"]
    assert wert.options["text"] in ("verfuegbar", "nicht eingerichtet")
    # Der vollstaendige Zustand bleibt kopierbar - er ist das, was bei
    # einer Stoerung weitergegeben wird.
    assert window.status_text.buffer


def test_die_statusliste_waechst_nicht_bei_jeder_aktualisierung(fenster):
    """Gezaehlt werden die sichtbaren Zeilen, nicht der Merkspeicher.

    Der Merkspeicher ist ein Verzeichnis nach Namen - er bleibt gleich
    gross, auch wenn bei jedem Aufruf neue Zeilen darunter entstehen. Eine
    Gegenprobe, die genau das tat, lief unbemerkt durch.
    """
    window, _, _ = fenster
    window._refresh_status()
    zeilen = len(window.statusliste.children)
    assert zeilen >= 5, "es muessen Statuszeilen entstanden sein"

    for _ in range(3):
        window._refresh_status()
    assert len(window.statusliste.children) == zeilen, (
        "die Liste darf bei jeder Aktualisierung nicht neu wachsen")


def _alle_texte(widget) -> list[str]:
    texte = [str(widget.options.get("text", ""))]
    for kind in widget.children:
        texte += _alle_texte(kind)
    return [t for t in texte if t]


def _alle_knoepfe(widget) -> list:
    knoepfe = [widget] if widget.commands.get("command") else []
    for kind in widget.children:
        knoepfe += _alle_knoepfe(kind)
    return knoepfe


def test_die_aufgabenuhr_holt_beim_start_nach(fenster):
    """Verpasstes laeuft beim naechsten Start - darum geht es bei Weg C.

    PORTIVA hat keinen Dienst im Hintergrund. Eine Aufgabe, die nachts um
    drei faellig war, kann also nur beim naechsten Start nachgeholt
    werden. Tut sie das nicht, ist der ganze Bereich Zierde.

    Wichtig ist hier, **wo** der Test ansetzt: an einem zweiten Fenster,
    das nach dem Anlegen der Aufgabe aufgemacht wird. Die erste Fassung
    rief ``_aufgabenuhr_schlag(start=True)`` von Hand auf - damit lief
    der Test auch dann durch, wenn das Fenster seinen Startdurchlauf gar
    nicht als solchen ausfuehrt. Eine Gegenprobe sprang nicht an, und
    das hat es aufgedeckt.
    """
    import time

    from pkc.aufgaben import Aktion, abmelden, registrieren
    from ui import tk_app

    gelaufen = []
    registrieren(Aktion(kennung="ui_probe", name="Probelauf",
                        beschreibung="Nur fuer Tests der Aufgabenuhr.",
                        funktion=lambda _c: gelaufen.append(1) or "Getan."))
    try:
        _, controller, _ = fenster
        controller.aufgabe_anlegen("Probelauf", "ui_probe",
                                   {"art": "beim_start"})

        zweites = tk_app.MainWindow(controller, None)
        ende = time.monotonic() + 5
        while zweites._aufgabenuhr_laeuft and time.monotonic() < ende:
            time.sleep(0.02)

        assert gelaufen == [1], (
            "die Startaufgabe muss beim Oeffnen des Fensters gelaufen sein")
        assert controller.aufgaben_liste()[0].letztes_ergebnis == "ok"
    finally:
        abmelden("ui_probe")


def test_die_aufgabenuhr_ueberschreibt_keine_laufende_frage(fenster):
    """Waehrend einer Frage steht in der Statuszeile, seit wann gewartet
    wird. Genau diese Anzeige hat Niels gefehlt, als er dachte, die
    Anwendung haenge."""
    window, _, _ = fenster
    window.busy = True
    window.statusbar.configure(text="Der Buchhalter denkt nach - seit 12 s")
    window._aufgabenuhr_melden("Geplante Aufgabe laeuft: Sicherung")
    assert "denkt nach" in window.statusbar.options["text"]

    window.busy = False
    window._aufgabenuhr_melden("Geplante Aufgabe laeuft: Sicherung")
    assert "Sicherung" in window.statusbar.options["text"]


def test_der_hinweis_unter_der_liste_sagt_nichts_falsches(fenster):
    """Er behauptete "Noch keine Aufgabe angelegt", waehrend zwei
    darueber standen. Aufgefallen auf dem ersten Bild des Bereichs."""
    window, controller, _ = fenster
    assert "Noch keine" in window.aufgabe_meldung.options["text"]

    controller.aufgabe_anlegen("Sicherung", "sicherung_anlegen",
                               {"art": "taeglich", "uhrzeit": "23:00"})
    window._refresh_aufgaben()
    text = window.aufgabe_meldung.options["text"]
    assert "Noch keine" not in text, text
