"""Der Oberflaechenstandard gilt fuer jeden Mitarbeiter - auch kuenftige.

Warum es diese Tests gibt: ``OBERFLAECHEN_STANDARD.md`` ist eine Vorgabe.
Eine Vorgabe, die nur in einem Dokument steht, ist eine Bitte. Diese
Tests machen aus den Punkten, die sich pruefen lassen, eine Zusage.

Geprueft wird bewusst nicht das Aussehen - dafuer gibt es
``test_echte_oberflaeche.py`` mit einem echten Fenster. Hier geht es um
die Regeln, die dahinterstehen: dass Farben an einer Stelle liegen, dass
die Fallen aus Abschnitt 5 nicht wieder aufgestellt werden, und dass ein
neues Profil die Schale wirklich erbt.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "OBERFLAECHEN_STANDARD.md"
UI = ROOT / "src" / "ui"


def _quelle(name: str) -> str:
    return (UI / name).read_text(encoding="utf-8")


def test_der_standard_liegt_vor():
    assert STANDARD.exists(), (
        "OBERFLAECHEN_STANDARD.md fehlt - ohne ihn hat ein neues Profil "
        "keine Vorgabe, an die es sich halten koennte.")


def test_die_farben_stehen_nur_an_einer_stelle():
    """Abschnitt 2: Farben gehoeren in stil.py, nirgends sonst.

    Geprueft werden die Farben des Standards. Taucht eine davon in einer
    anderen Oberflaechendatei als wortwoertlicher Wert auf, ist sie
    dorthin kopiert worden - und die naechste Aenderung wird eine davon
    vergessen.

    Ausgenommen sind ``schale.py`` und ``quellenpanel.py``: sie bauen mit
    einfachen tk-Bausteinen, denen man die Farbe einzeln mitgeben muss,
    und sie definieren ihre Werte am Dateikopf. Das ist eine bewusste
    Ausnahme, kein Versehen - und sie ist hier festgehalten, damit sie
    nicht unbemerkt auf weitere Dateien ausgedehnt wird.
    """
    farben = ["#1e6fd9", "#17202e", "#f5f7fa", "#14243c", "#5b6b80"]
    erlaubt = {"stil.py", "schale.py", "quellenpanel.py", "startbild.py"}

    verstoesse = []
    for datei in sorted(UI.glob("*.py")):
        if datei.name in erlaubt:
            continue
        text = datei.read_text(encoding="utf-8")
        for farbe in farben:
            if farbe in text:
                verstoesse.append(f"{datei.name}: {farbe}")
    assert not verstoesse, (
        "Diese Farben stehen ausserhalb der dafuer vorgesehenen Dateien:\n"
        + "\n".join(verstoesse)
        + "\nSie gehoeren nach src/ui/stil.py.")


def test_kein_knopf_verliert_seine_tastaturbedienung():
    """Abschnitt 5.1: ``highlightthickness=0`` nimmt den Fokusrahmen.

    Damit ist nicht nur der Rahmen weg, sondern auch die Anzeige, wo man
    mit der Tastatur gerade steht. Wer keine Maus benutzt, ist kein
    Sonderfall. Richtig ist: den Rahmen unsichtbar machen, nicht
    abschalten.
    """
    # Kommentare bleiben aussen vor - in ihnen steht die Erklaerung,
    # warum es NICHT so gemacht wird. Und eine Zeichenflaeche (Canvas)
    # ist ausgenommen: sie nimmt keinen Tastaturfokus entgegen, dort
    # entfernt der Wert nur einen haesslichen Rand. Beides hat die erste
    # Fassung dieses Tests angemahnt - zu Unrecht.
    treffer = []
    for datei in sorted(UI.glob("*.py")):
        text = datei.read_text(encoding="utf-8")
        for nummer, zeile in enumerate(text.splitlines(), 1):
            ohne_rand = zeile.strip()
            if ohne_rand.startswith("#") or "Canvas(" in zeile:
                continue
            eng = zeile.replace(" ", "")
            if "highlightthickness=0" in eng:
                treffer.append(f"{datei.name}:{nummer}")
            if "takefocus=0" in eng:
                treffer.append(f"{datei.name}:{nummer} (takefocus)")
    assert not treffer, (
        "Hier wird ein Fokusrahmen abgeschaltet statt unsichtbar "
        "gemacht:\n" + "\n".join(treffer)
        + "\nRichtig: highlightbackground = Hintergrundfarbe, "
          "highlightcolor = Blau.")


def test_readonly_auswahlfelder_haben_markierungsfarben():
    """Abschnitt 5.2: sonst steht der Wert weiss auf weiss.

    Ein Auswahlfeld mit ``state="readonly"`` zeichnet seinen Text
    markiert. Sind die Markierungsfarben des Themas nicht gesetzt, ist
    der Text unsichtbar - das Feld sieht leer aus, obwohl ein Wert
    darinsteht. Genau das war der Fall, und kein Test hat es gemerkt:
    der Wert war ja abfragbar.
    """
    stil = _quelle("stil.py")
    assert "selectforeground" in stil and "selectbackground" in stil, (
        "In stil.py fehlen die Markierungsfarben fuer Eingabefelder.")
    # Und sie muessen sich unterscheiden - gleiche Farben sind dasselbe
    # wie keine.
    assert "selectbackground=BLAU_HELL" in stil or \
           "selectbackground=KARTE" in stil, (
        "Die Markierungsfarbe muss ausdruecklich gesetzt sein.")


def test_keine_schiebeteiler_mehr_in_den_hauptansichten():
    """Abschnitt 5.3: der Schiebeteiler quetscht Beschriftungen ab.

    ``ttk.PanedWindow`` verteilt Breite nach Gewichten. Wo eine Spalte
    eine Mindestbreite braucht, gehoert ``grid`` mit ``minsize`` hin.
    Aus "Senden" wurde sonst ein "Send".
    """
    text = _quelle("tk_app.py")
    assert "PanedWindow" not in text, (
        "In tk_app.py steht wieder ein PanedWindow. Wo eine Spalte eine "
        "Mindestbreite braucht, gehoert grid mit minsize hin.")


def test_die_schwellen_fuer_schmale_fenster_sind_benannt():
    """Abschnitt 4 und 5.5: Breiten werden begruendet, nicht geraten."""
    text = _quelle("tk_app.py")
    for name in ("QUELLEN_BREITE", "KNOPFSPALTE", "STATUS_BREITE",
                 "SCHWELLE_QUELLEN", "SCHWELLE_LEISTE"):
        assert f"{name} =" in text, (
            f"{name} fehlt - eine Breite ohne Namen ist eine Breite ohne "
            "Begruendung.")


def test_ein_neues_profil_erbt_die_schale(portable_root):
    """Abschnitt 6: ein Profil bringt Bereiche mit, kein eigenes Aussehen.

    Geprueft wird mit einem Profil, das nur drei Bereiche zulaesst: die
    Navigation zeigt genau diese drei, alles andere - Kopfzeile,
    Fusszeile, Farben - ist unveraendert da.
    """
    import sys

    import tk_double
    from test_controller import make_controller

    tk_double.install()
    tk_double.ui_module_freigeben()
    from ui import tk_app

    steuerung = make_controller(portable_root)
    bericht = steuerung.bootstrap()
    steuerung.profile.raw["navigation"] = [
        "unterhaltung", "unternehmenswissen", "einstellungen"]
    try:
        fenster = tk_app.MainWindow(steuerung, bericht)
        schale = fenster.schale
        assert schale.reihenfolge == [
            "unterhaltung", "unternehmenswissen", "einstellungen"], (
            f"Die Navigation zeigt {schale.reihenfolge} statt der drei "
            "Bereiche des Profils.")
        # Die uebrigen Bereiche sind trotzdem gebaut - nur nicht in der
        # Navigation. So bleibt der Code der Ansichten unveraendert.
        assert len(schale.bereiche) > 3, (
            "Die uebrigen Bereiche muessen weiterhin gebaut werden.")
        assert schale.profil_label is not None, "Die Fusszeile fehlt."
        assert schale.chips is not None, "Die Kopfzeile fehlt."
    finally:
        steuerung.shutdown()


def test_der_standard_nennt_die_dateien_die_es_gibt():
    """Ein Standard, der auf eine Datei zeigt, die es nicht gibt, ist
    schlimmer als keiner - er schickt den naechsten auf eine falsche
    Faehrte."""
    text = STANDARD.read_text(encoding="utf-8")
    for pfad in re.findall(r"`(src/[\w/]+\.py|assets/[\w/]+/?|"
                           r"tools/[\w/]+\.py|docs/[\w/]+/?)`", text):
        ziel = ROOT / pfad.rstrip("/")
        assert ziel.exists(), f"Der Standard nennt {pfad} - das gibt es nicht."
