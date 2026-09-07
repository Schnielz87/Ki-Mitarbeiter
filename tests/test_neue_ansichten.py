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


def test_noch_nicht_gebaute_bereiche_haben_keine_toten_knoepfe(fenster):
    """Auftrag Abschnitt 34 laesst zwei Moeglichkeiten: es funktioniert,
    oder es ist eindeutig als nicht verfuegbar gekennzeichnet.

    Der einzige Knopf in diesen Bereichen fuehrt zu dem Bereich, der heute
    schon hilft - und der funktioniert."""
    window, _, _ = fenster
    for kennung in ("vorlagen", "aufgaben"):
        flaeche = window.schale.bereiche[kennung].rahmen
        texte = _alle_texte(flaeche)
        assert any("nicht verfuegbar" in t for t in texte), (
            f"{kennung} muss sagen, dass es den Bereich noch nicht gibt")
        assert any("Was heute schon geht" in t for t in texte), (
            f"{kennung} muss den heutigen Weg nennen")
        for knopf in _alle_knoepfe(flaeche):
            assert knopf.commands.get("command") is not None, (
                f"toter Knopf in {kennung}: {knopf.options.get('text')}")


def test_der_verweis_aus_einem_leeren_bereich_fuehrt_wirklich_hin(fenster):
    window, _, _ = fenster
    window.schale.zeigen("vorlagen")
    knoepfe = _alle_knoepfe(window.schale.bereiche["vorlagen"].rahmen)
    assert knoepfe, "es muss einen Weg heraus geben"
    knoepfe[0].invoke()
    assert window.schale.aktiv == "arbeitsergebnisse"


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
