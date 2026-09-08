"""Drag & Drop unter Windows - ohne zusaetzliche Bibliothek.

Tkinter kann Drag & Drop nicht von sich aus. Der uebliche Weg waere die
Bibliothek ``tkinterdnd2``; sie bringt eigene Binaerdateien mit, die in ein
gepacktes Programm eingebettet werden muessen. Fuer eine Anwendung, die von
einem USB-Stick an fremden Rechnern laufen soll, ist jede weitere
Binaerdatei eine weitere Fehlerquelle.

Windows kann es aber selbst. Ein Fenster meldet mit ``DragAcceptFiles`` an,
dass es Dateien annimmt, und bekommt sie danach als Nachricht
``WM_DROPFILES``. Um an diese Nachricht heranzukommen, wird die
Fensterprozedur ersetzt und die urspruengliche danach wieder aufgerufen -
ein seit Jahrzehnten uebliches Verfahren.

**Was hier nie passieren darf:** dass ein Fehler beim Einrichten die
Anwendung stoert. Deshalb ist alles gekapselt, jede Ausnahme wird
abgefangen, und die Rueckgabe sagt schlicht, ob es geklappt hat. Klappt es
nicht - auf Linux, in einer ungewoehnlichen Windows-Fassung, bei fehlenden
Rechten -, bleibt es beim Auswaehlen ueber den Knopf.

**Nicht auf einem echten Windows-Rechner erprobt.** In der
Entwicklungsumgebung gibt es kein Windows und keinen Bildschirm. Der Code
ist so gebaut, dass ein Fehlschlag folgenlos bleibt; ob das Ziehen
tatsaechlich funktioniert, zeigt erst der Betrieb.
"""

from __future__ import annotations

import os
from typing import Callable

from pkc.logging_setup import get_logger

log = get_logger(__name__)

#: Nachricht, mit der Windows abgelegte Dateien meldet.
WM_DROPFILES = 0x0233
#: Zeigt an, dass die Fensterprozedur ersetzt werden soll.
GWL_WNDPROC = -4
#: Hoechstzahl der Dateien, die eine Ablage liefern darf. Wer 5000 Dateien
#: auf das Fenster zieht, meint es nicht ernst - und die Anwendung soll
#: daran nicht minutenlang haengen.
HOECHSTZAHL = 50

#: Merkt sich die eingerichteten Fenster. Ohne diese Bezuege raeumt der
#: Sammler die Rueckruffunktion weg, und Windows springt in eine Adresse,
#: an der nichts mehr steht - das ist ein Absturz, kein Fehler.
_EINGERICHTET: dict[int, object] = {}


#: Umgebungsvariable, mit der sich das Ziehen abschalten laesst. Zwei
#: Gruende dafuer: Erstens greift der Weg ueber ``WM_DROPFILES`` tief in
#: das Fenster ein - wer damit Aerger hat, soll die Anwendung ohne diesen
#: Eingriff starten koennen, ohne auf eine neue Fassung zu warten.
#: Zweitens sollen automatische Oberflaechentests das Fenster nicht mit
#: einer ersetzten Fensterprozedur aufbauen: die Rueckruffunktion lebt in
#: Python, das Fenster wird am Testende zerstoert, und die Reihenfolge
#: dieser beiden Dinge ist nichts, worauf man sich verlassen sollte.
ABSCHALTER = "PORTIVA_KEINE_DATEIABLAGE"


def verfuegbar() -> bool:
    """Kann auf diesem System ueberhaupt abgelegt werden?"""
    if os.environ.get(ABSCHALTER, "").strip() not in ("", "0", "nein", "false"):
        log.debug("Dateiablage per %s abgeschaltet", ABSCHALTER)
        return False
    return os.name == "nt"


def einrichten(fenster, rueckruf: Callable[[list[str]], None]) -> bool:
    """Meldet das Fenster fuer Dateiablage an.

    ``rueckruf`` bekommt eine Liste von Pfaden. Gibt zurueck, ob es
    geklappt hat - nie eine Ausnahme.
    """
    if not verfuegbar():
        log.debug("Dateiablage: kein Windows, wird uebersprungen")
        return False
    try:
        return _windows_einrichten(fenster, rueckruf)
    except Exception:                   # pragma: no cover - nur unter Windows
        log.debug("Dateiablage liess sich nicht einrichten", exc_info=True)
        return False


def _windows_einrichten(fenster, rueckruf) -> bool:   # pragma: no cover - Windows
    import ctypes
    from ctypes import wintypes

    hwnd = int(fenster.winfo_id())
    if hwnd in _EINGERICHTET:
        return True

    shell32 = ctypes.windll.shell32
    user32 = ctypes.windll.user32

    # Windows meldet die Ablage an das Fenster, das sie annimmt. Bei Tk ist
    # das Zeichenfenster ein Kind des eigentlichen Rahmens; angemeldet wird
    # deshalb der Rahmen, sonst kommen Ablagen am Rand nicht an.
    rahmen = user32.GetAncestor(hwnd, 2) or hwnd     # GA_ROOT
    shell32.DragAcceptFiles(rahmen, True)

    prozedur_typ = ctypes.WINFUNCTYPE(
        ctypes.c_long, wintypes.HWND, ctypes.c_uint,
        wintypes.WPARAM, wintypes.LPARAM)

    setzen = getattr(user32, "SetWindowLongPtrW", None) or user32.SetWindowLongW
    holen = getattr(user32, "GetWindowLongPtrW", None) or user32.GetWindowLongW
    aufrufen = getattr(user32, "CallWindowProcW", None)
    if aufrufen is None:
        return False

    # Rueckgabe- und Argumenttypen ausdruecklich setzen. Ohne das nimmt
    # ctypes ``c_int`` an - 32 Bit. Eine Fensterprozedur liegt auf einem
    # 64-Bit-Windows aber oberhalb dieser Grenze; die Adresse waere
    # abgeschnitten, und der Aufruf der alten Prozedur ginge ins Leere.
    # Das ist kein Schoenheitsfehler, das ist ein Absturz.
    setzen.restype = ctypes.c_void_p
    setzen.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
    holen.restype = ctypes.c_void_p
    holen.argtypes = [wintypes.HWND, ctypes.c_int]
    aufrufen.restype = ctypes.c_long
    aufrufen.argtypes = [ctypes.c_void_p, wintypes.HWND, ctypes.c_uint,
                         wintypes.WPARAM, wintypes.LPARAM]

    # Die bisherige Fensterprozedur nur LESEN. Die vorherige Fassung rief
    # dafuer ``SetWindowLongPtrW(..., GWL_WNDPROC, 0)`` auf - das liest
    # nicht, das SETZT die Fensterprozedur auf NULL. Zwischen diesem
    # Aufruf und dem spaeteren Wiedersetzen haette das Fenster keine
    # Prozedur gehabt; jede Nachricht in dieser Zeitspanne trifft eine
    # Adresse, an der nichts steht. Ein Kommentar "nur lesen" macht aus
    # einem Setzen kein Lesen.
    vorherige = holen(rahmen, GWL_WNDPROC)
    if not vorherige:
        log.debug("Fensterprozedur nicht lesbar - Dateiablage unterbleibt")
        return False

    def prozedur(h, nachricht, wparam, lparam):
        if nachricht == WM_DROPFILES:
            try:
                rueckruf(_pfade_lesen(shell32, wparam))
            except Exception:
                log.debug("Abgelegte Dateien konnten nicht verarbeitet werden",
                          exc_info=True)
            finally:
                shell32.DragFinish(wparam)
            return 0
        return aufrufen(vorherige, h, nachricht, wparam, lparam)

    neue = prozedur_typ(prozedur)
    if not setzen(rahmen, GWL_WNDPROC, ctypes.cast(neue, ctypes.c_void_p).value):
        # Auch ein Fehlschlag hier ist folgenlos: die alte Prozedur steht
        # noch, es gibt nur kein Ziehen.
        if ctypes.get_last_error() if hasattr(ctypes, "get_last_error") else 0:
            log.debug("Fensterprozedur liess sich nicht ersetzen")
    # Beide Bezuege festhalten - siehe Kommentar bei _EINGERICHTET.
    _EINGERICHTET[hwnd] = (neue, vorherige)
    log.info("Dateiablage eingerichtet (Fenster %s)", rahmen)
    return True


def _pfade_lesen(shell32, ablage) -> list[str]:       # pragma: no cover - Windows
    """Liest die Pfade aus einer Windows-Ablage."""
    import ctypes

    anzahl = shell32.DragQueryFileW(ablage, 0xFFFFFFFF, None, 0)
    pfade = []
    for nummer in range(min(int(anzahl), HOECHSTZAHL)):
        laenge = shell32.DragQueryFileW(ablage, nummer, None, 0)
        puffer = ctypes.create_unicode_buffer(laenge + 1)
        shell32.DragQueryFileW(ablage, nummer, puffer, laenge + 1)
        if puffer.value:
            pfade.append(puffer.value)
    return pfade
