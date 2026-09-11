"""Fotografiert die echte Oberflaeche - jede Ansicht einzeln.

Warum es das gibt: Bis hierher wurde die Oberflaeche nur gegen ein
Testdoppel geprueft. Ein Doppel sagt, dass ein Knopf angelegt wurde. Es
sagt nicht, ob er sichtbar ist, ob seine Beschriftung abgeschnitten wird
oder ob zwei Bereiche uebereinanderliegen. Genau das war der Fall - und es
fiel erst auf, als das Fenster zum ersten Mal wirklich geoeffnet wurde.

Dieses Werkzeug oeffnet das echte Tk-Fenster auf einem Bildschirm (unter
Linux genuegt ein virtueller: ``xvfb-run``), schaltet der Reihe nach alle
Bereiche durch und legt von jedem ein Bild ab. Die Bilder dienen zwei
Zwecken:

1. **Pruefung** - man sieht, was der Anwender sieht.
2. **Anleitung** - dieselben Bilder werden in die Betriebsanleitung
   eingebaut, damit sich niemand die Oberflaeche aus Text zusammenreimen
   muss.

Aufruf::

    xvfb-run -a --server-args="-screen 0 1600x1000x24" \
        python tools/oberflaeche_fotografieren.py docs/Oberflaeche

Es braucht Tkinter und Pillow. Fehlt eines, sagt das Werkzeug das und
bricht ab - es erzeugt keine leeren Bilder.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

#: Groesse des aufgenommenen Fensters. Bewusst nicht die groesstmoegliche:
#: die Bilder sollen in einer Word-Seite noch lesbar sein.
BREITE, HOEHE = 1500, 940

#: Reihenfolge und Dateinamen. Der Schluessel ist der Bereichsschluessel
#: der Navigationsschale.
ANSICHTEN = [
    ("unterhaltung", "01_Unterhaltung"),
    ("unternehmenswissen", "02_Unternehmenswissen"),
    ("belege", "03_Belege_und_Dokumente"),
    ("arbeitsergebnisse", "04_Arbeitsergebnisse"),
    ("wissen_quellen", "05_Wissen_und_Quellen"),
    ("vorlagen", "06_Vorlagen"),
    ("aufgaben", "07_Aufgaben"),
    ("plugins", "08_Plugins"),
    ("dienste", "09_Verbundene_Dienste"),
    ("einstellungen", "10_Einstellungen_und_Status"),
]


def _pruefen() -> None:
    fehlend = []
    try:
        import tkinter                                  # noqa: F401
    except Exception:
        fehlend.append("tkinter (Paket python3-tk)")
    try:
        from PIL import ImageGrab                       # noqa: F401
    except Exception:
        fehlend.append("Pillow")
    if not os.environ.get("DISPLAY"):
        fehlend.append("ein Bildschirm (DISPLAY) - unter Linux: xvfb-run")
    if fehlend:
        print("Es fehlt: " + ", ".join(fehlend))
        raise SystemExit(2)


def _controller(wurzel: Path):
    """Eine frische portable Wurzel mit Testantwort statt echtem Modell."""
    from app.controller import AppController
    from pkc.config import Config
    from pkc.llm.manager import LlmManager
    from pkc.llm.providers import ScriptedProvider
    from pkc.netstate import Mode, NetworkMonitor
    from pkc.paths import Paths

    pfade = Paths(wurzel)
    pfade.ensure_runtime_dirs()
    pfade.write_marker()
    config = Config.load(pfade)
    config.set("llm.provider", "echo")
    config.set("retrieval.embedding_dim", 256)
    config.set("network.mode", "OFFLINE")
    monitor = NetworkMonitor([], enabled=False)
    monitor.force(False, "Bildaufnahme")
    steuerung = AppController(pfade, config, monitor, console_logging=False)
    steuerung.llm = LlmManager(ScriptedProvider(_beispielantwort))
    steuerung.rag.llm = steuerung.llm
    return steuerung


def _beispielantwort(messages) -> str:
    """Eine Beispielantwort, damit die Bilder nicht leer wirken.

    Sie ist als Beispiel erkennbar und behauptet keine Rechtsfolge, die
    nicht geprueft waere - in einer Anleitung darf kein Bild stehen, das
    wie eine verbindliche Auskunft aussieht.
    """
    return (
        "**ERGEBNIS**\n"
        "Fuer eine belastbare Beurteilung brauche ich zuerst zwei Angaben:\n\n"
        "1. Sitzt der Lieferant in Frankreich und handelt er als Unternehmer?\n"
        "2. Handelt es sich um eine Warenlieferung oder eine sonstige Leistung?\n\n"
        "Danach pruefe ich Umsatzsteuer, Reverse Charge und den passenden "
        "Buchungsvorschlag [1].\n\n"
        "*Beispielantwort zur Veranschaulichung der Oberflaeche.*"
    )


def aufnehmen(ziel: Path, mit_frage: bool = True) -> list[Path]:
    """Nimmt alle Ansichten auf und gibt die geschriebenen Pfade zurueck."""
    from PIL import ImageGrab
    from ui import tk_app

    ziel.mkdir(parents=True, exist_ok=True)
    wurzel = Path(tempfile.mkdtemp(prefix="portiva_bilder_"))
    os.environ["KIM_ROOT"] = str(wurzel)
    steuerung = _controller(wurzel)
    bericht = steuerung.bootstrap()
    fenster = tk_app.MainWindow(steuerung, bericht)
    dach = fenster.root
    dach.geometry(f"{BREITE}x{HOEHE}+0+0")
    _durchatmen(dach)

    if mit_frage:
        # Eine leere Unterhaltung zeigt nichts von dem, was die Ansicht
        # ausmacht. Also erst eine Frage stellen, dann fotografieren.
        # Bewusst eine Frage, zu der es im Fachwissen wirklich Fundstellen
        # gibt. Ein Bild mit leerer Quellenspalte erklaert nichts - und
        # die Quellenspalte ist der Teil, den die Anleitung zeigen soll.
        fenster.entry.insert("end", "Welche Pflichtangaben muss eine "
                                    "Rechnung enthalten?")
        fenster._send()
        _durchatmen(dach)

    geschrieben = []
    for schluessel, name in ANSICHTEN:
        if schluessel not in fenster.schale.bereiche:
            print(f"  uebersprungen (kein Bereich): {schluessel}")
            continue
        fenster.schale.zeigen(schluessel)
        _vorbereiten(fenster, schluessel)
        _durchatmen(dach)
        bild = ImageGrab.grab(xdisplay=os.environ.get("DISPLAY"))
        bild = bild.crop((0, 0, min(BREITE, bild.width), min(HOEHE, bild.height)))
        pfad = ziel / f"{name}.png"
        bild.save(pfad)
        geschrieben.append(pfad)
        print(f"  {pfad.name}  {bild.size[0]}x{bild.size[1]}")

    steuerung.shutdown()
    try:
        dach.destroy()
    except Exception:                                   # pragma: no cover
        pass
    return geschrieben


def _vorbereiten(fenster, schluessel: str) -> None:
    """Fuellt eine Ansicht, damit das Bild etwas zeigt.

    Der Vorlagenbereich ohne gewaehlte Zeile ist eine leere Flaeche mit
    der Aufschrift "Keine Vorlage gewaehlt". Als Bild in einer Anleitung
    erklaert das nichts. Also wird eine Vorlage ausgewaehlt - dieselbe,
    die im Text beschrieben ist.
    """
    if schluessel != "vorlagen":
        return
    baum = getattr(fenster, "vorlagen_tree", None)
    if baum is None or "mandantenbrief" not in baum.get_children():
        return
    baum.selection_set("mandantenbrief")
    baum.focus("mandantenbrief")
    fenster._vorlage_zeigen()


def _durchatmen(dach, runden: int = 6) -> None:
    """Laesst Tk zeichnen. Ohne das entstehen halb gemalte Bilder."""
    for _ in range(runden):
        try:
            dach.update_idletasks()
            dach.update()
        except Exception:                               # pragma: no cover
            return
        time.sleep(0.08)


def startbild_aufnehmen(ziel: Path) -> Path | None:
    """Fotografiert das Begruessungsbild - es ist nur drei Sekunden da."""
    from PIL import ImageGrab
    from pkc.branding import load_brand
    from ui.startbild import Startbild
    from pkc.config import Config
    from pkc.paths import Paths

    wurzel = Path(tempfile.mkdtemp(prefix="portiva_start_"))
    pfade = Paths(wurzel)
    pfade.ensure_runtime_dirs()
    pfade.write_marker()
    bild = Startbild(load_brand(pfade, Config.load(pfade)), "Buchhalter")
    fenster = bild.oeffnen()                # zeigt, ohne zu warten
    if fenster is None:
        print("  Begruessungsbild liess sich nicht oeffnen")
        return None
    _durchatmen(fenster, runden=8)
    aufnahme = ImageGrab.grab(xdisplay=os.environ.get("DISPLAY"))
    pfad = ziel / "00_Begruessungsbild.png"
    aufnahme.save(pfad)
    bild.schliessen()
    print(f"  {pfad.name}  {aufnahme.size[0]}x{aufnahme.size[1]}")
    return pfad


def main(argv: list[str]) -> int:
    _pruefen()
    ziel = Path(argv[1]) if len(argv) > 1 else WURZEL / "docs" / "Oberflaeche"
    ziel.mkdir(parents=True, exist_ok=True)
    print(f"Bilder nach {ziel}")
    startbild_aufnehmen(ziel)
    aufnehmen(ziel)
    return 0


if __name__ == "__main__":                              # pragma: no cover
    raise SystemExit(main(sys.argv))
