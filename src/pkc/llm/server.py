"""Den mitgelieferten llama.cpp-Server starten und wieder beenden.

Warum es dieses Modul gibt: fuer ``llama-cpp-python`` gibt es auf PyPI
**keine** fertigen Pakete - es muesste auf dem Rechner des Kunden uebersetzt
werden, mit Compiler und CMake. Fuer eine portable Anwendung, die per
Doppelklick laufen soll, ist das kein gangbarer Weg.

Das offizielle Projekt llama.cpp liefert dagegen fertige Programmdateien aus.
Eine davon, ``llama-server``, spricht dasselbe Protokoll wie ein
Online-Dienst. Sie liegt im portablen Ordner unter ``runtime/llama/`` und
wird von der Anwendung selbst gestartet - der Benutzer merkt davon nichts.

Drei Festlegungen, die aus dem uebrigen Auftrag folgen:

* Der Server hoert **nur** auf 127.0.0.1. Er ist kein Netzwerkdienst, und
  ausser der Anwendung selbst erreicht ihn niemand (Masterprompt 5, 69).
* Unter Windows wird kein zusaetzliches Fenster geoeffnet. Ein schwarzes
  Konsolenfenster neben der Anwendung waere ein Fehler, kein Merkmal.
* Beim Beenden der Anwendung wird der Server beendet. Ein weiterlaufender
  Vorgang, der still 5 GB Arbeitsspeicher haelt, ist nicht hinnehmbar.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from ..logging_setup import get_logger

log = get_logger(__name__)

#: Unterverzeichnis im portablen Ordner, in dem die Programmdatei erwartet wird.
LAUFZEIT_UNTERORDNER = ("llama", "llama.cpp", ".")

#: Die mitgelieferten Fassungen des Modelldienstes, in der Reihenfolge, in
#: der sie versucht werden, wenn eine Grafikkarte erkannt wurde.
#:
#: Der Unterschied ist nicht klein: die CPU-Fassung rechnet auf dem
#: Prozessor, die Vulkan-Fassung auf der Grafikkarte. Auf einem Rechner mit
#: GPU liegen dazwischen Faktoren, nicht Prozente. Vulkan und nicht CUDA,
#: weil es mit Karten von NVIDIA, AMD und Intel gleichermassen laeuft und
#: keine zusaetzliche Installation braucht.
FASSUNGEN = ("vulkan", "cpu")

#: Wie lange auf das Hochfahren gewartet wird. Ein grosses Modell braucht auf
#: einer aelteren CPU durchaus eine Minute, bis es geladen ist.
STARTGRENZE_S = 180.0


def _programmname() -> str:
    return "llama-server.exe" if os.name == "nt" else "llama-server"


def fassungen(runtime_dir: Path) -> dict[str, Path]:
    """Welche Fassungen des Modelldienstes liegen bei?

    Erwartet werden sie unter ``runtime/llama/<fassung>/llama-server``.
    Aeltere Pakete haben nur eine Datei ohne Unterordner - die zaehlt als
    ``cpu``, denn genau das war sie.

    Gesucht wird nur unterhalb des portablen Ordners - nie im System. Was
    nicht auf dem Datentraeger liegt, ist beim naechsten Rechner nicht da
    (Masterprompt 19, 20).
    """
    runtime_dir = Path(runtime_dir)
    name = _programmname()
    gefunden: dict[str, Path] = {}
    for unter in LAUFZEIT_UNTERORDNER:
        basis = (runtime_dir / unter) if unter != "." else runtime_dir
        for fassung in FASSUNGEN:
            kandidat = basis / fassung / name
            if kandidat.is_file():
                gefunden.setdefault(fassung, kandidat)
        schlicht = basis / name
        if schlicht.is_file():
            gefunden.setdefault("cpu", schlicht)
    return gefunden


def waehle_server(runtime_dir: Path, grafikkarte: bool = False) -> tuple[Path | None, str]:
    """Waehlt die Fassung, die auf diesem Rechner am schnellsten ist.

    Mit erkannter Grafikkarte zuerst Vulkan, sonst die CPU-Fassung. Ob die
    Wahl auch traegt, zeigt sich erst beim Start - dafuer gibt es den
    Rueckfall in ``Llamaserver.starten``.
    """
    verfuegbar = fassungen(runtime_dir)
    reihenfolge = FASSUNGEN if grafikkarte else ("cpu", "vulkan")
    for fassung in reihenfolge:
        if fassung in verfuegbar:
            return verfuegbar[fassung], fassung
    # Unbekannte Ablage: irgendwo darunter suchen, statt aufzugeben.
    runtime_dir = Path(runtime_dir)
    if runtime_dir.is_dir():
        for pfad in sorted(runtime_dir.rglob(_programmname())):
            if pfad.is_file():
                return pfad, "unbekannt"
    return None, ""


def finde_server(runtime_dir: Path) -> Path | None:
    """Die Programmdatei des Servers - ohne Ruecksicht auf die Fassung.

    Fuer alle Stellen, die nur wissen wollen, **ob** ein Modelldienst
    beiliegt (Systempruefung, Lagebericht).
    """
    return waehle_server(runtime_dir)[0]


def _freier_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@dataclass
class Llamaserver:
    """Ein llama.cpp-Server als Kindvorgang der Anwendung."""

    programm: Path
    modell: Path
    kontext: int = 8192
    threads: int = 0
    gpu_layers: int = 0
    port: int = 0
    startgrenze: float = STARTGRENZE_S
    #: Befehl, der dem Programm vorangestellt wird. Gebraucht wird das an
    #: zwei Stellen: wenn der Dienst ueber ein Startskript laufen soll (etwa
    #: um Kerne zu binden), und in den Tests, die den Dienst gegen einen
    #: Stellvertreter pruefen - eine Textdatei kann Windows nicht ausfuehren.
    vorlauf: list[str] = field(default_factory=list)
    #: Zusaetzliche Schalter fuer Geschwindigkeit. Wird beim Fehlstart
    #: automatisch abgeschaltet, siehe ``_tempoflags``.
    tempoflags: bool = True
    #: Programmdatei, die genommen wird, wenn ``programm`` nicht hochkommt.
    #: Gebraucht fuer die Grafikfassung: fehlt der Treiber, muss die
    #: CPU-Fassung uebernehmen - lieber langsam als gar kein Sprachmodell.
    rueckfall: Path | None = None
    #: Ob der letzte Start die Tempoflags verwenden konnte, und welche
    #: Programmdatei wirklich lief. Nur zum Nachlesen.
    tempoflags_aktiv: bool = field(default=False, repr=False)
    benutzt: Path | None = field(default=None, repr=False)
    _vorgang: subprocess.Popen | None = field(default=None, repr=False)
    _protokoll: Path | None = field(default=None, repr=False)

    @property
    def adresse(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def laeuft(self) -> bool:
        return self._vorgang is not None and self._vorgang.poll() is None

    # -- Start ---------------------------------------------------------
    def _grundbefehl(self, programm: Path | None = None) -> list[str]:
        """Nur Schalter, die es seit jeher in llama.cpp gibt."""
        befehl = [
            *self.vorlauf,
            str(programm or self.programm),
            "-m", str(self.modell),
            "--host", "127.0.0.1",
            "--port", str(self.port),
            "-c", str(self.kontext),
        ]
        if self.threads:
            befehl += ["-t", str(self.threads)]
        if self.gpu_layers:
            befehl += ["-ngl", str(self.gpu_layers)]
        return befehl

    def _tempoflags(self) -> list[list[str]]:
        """Schalter, die messbar Zeit sparen - aber nicht in jeder Fassung.

        * ``-fa`` (Flash Attention) beschleunigt vor allem die Verarbeitung
          des Kontextes, also die Zeit bis zum ersten Wort.
        * ``--cache-type-k/-v q8_0`` halbiert den Speicher des Kontextes.
          Auf einem knappen Rechner entscheidet das darueber, ob ausgelagert
          wird - und Auslagern kostet nicht Prozente, sondern das Zehnfache.
        * ``-tb`` gibt der Kontextverarbeitung alle Kerne.

        Zurueckgegeben wird eine **Liste** von Saetzen, absteigend nach
        Wirkung: llama.cpp aendert seine Schalter zwischen Fassungen, und
        wer einen unbekannten uebergibt, bekommt eine Hilfeseite statt eines
        Dienstes. Beim Fehlstart wird deshalb der naechste Satz versucht,
        zuletzt gar keiner. Lieber langsamer als gar nicht.
        """
        kerne = self.threads or (os.cpu_count() or 0)
        kern = ["-tb", str(kerne)] if kerne else []
        kontext = ["--cache-type-k", "q8_0", "--cache-type-v", "q8_0"]
        # Absteigend nach Wirkung. Der Bauablauf hat gezeigt, warum es eine
        # Liste sein muss und kein fester Satz: die vorliegende Fassung
        # verlangte "-fa on", eine aeltere kennt nur "-fa" ohne Wert, und wer
        # den falschen nimmt, bekommt eine Hilfeseite statt eines Dienstes.
        return [
            ["-fa", "on", *kontext, *kern],
            ["-fa", *kontext, *kern],
            [*kontext, *kern],
            kern,
        ]

    def _befehl(self, programm: Path | None = None) -> list[str]:
        """Der Aufruf, der zuerst versucht wird - mit dem besten Schaltersatz."""
        befehl = self._grundbefehl(programm)
        if self.tempoflags:
            befehl += self._tempoflags()[0]
        return befehl

    def starten(self, protokollordner: Path | None = None) -> str:
        """Startet den Server und wartet, bis er antwortet.

        Gibt die Adresse zurueck. Kommt der Server nicht hoch, wird eine
        ``RuntimeError`` mit der letzten Ausgabe des Programms ausgeloest -
        ohne diese Ausgabe waere ein Fehlstart nicht nachvollziehbar.
        """
        if self.laeuft:
            return self.adresse
        if not self.programm.is_file():
            raise RuntimeError(f"Die Programmdatei fehlt: {self.programm}")
        if not self.modell.is_file():
            raise RuntimeError(f"Die Modelldatei fehlt: {self.modell}")

        self.port = self.port or _freier_port()
        ausgabe = subprocess.DEVNULL
        if protokollordner is not None:
            protokollordner = Path(protokollordner)
            protokollordner.mkdir(parents=True, exist_ok=True)
            self._protokoll = protokollordner / "llama-server.log"
            ausgabe = self._protokoll.open("ab")

        # Unter Windows kein zusaetzliches Konsolenfenster oeffnen.
        zusatz = {}
        if os.name == "nt":                                  # pragma: no cover
            zusatz["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        else:
            zusatz["start_new_session"] = True

        log.info("Starte Modelldienst: %s (Modell %s)", self.programm.name, self.modell.name)
        # Zwei Achsen, absteigend nach Geschwindigkeit: erst die gewaehlte
        # Programmdatei mit den Tempoflags, dann ohne, dann - falls es eine
        # gibt - die Rueckfalldatei. Jeder Schritt ist langsamer als der
        # vorige und immer noch unendlich viel besser als kein Modell.
        programme = [self.programm]
        if self.rueckfall is not None and Path(self.rueckfall).is_file():
            programme.append(Path(self.rueckfall))

        saetze = self._tempoflags() if self.tempoflags else []
        saetze = [*saetze, []]                 # zuletzt ganz ohne Zusatz

        letzte = ""
        for programm in programme:
            for satz in saetze:
                self.tempoflags_aktiv = bool(satz)
                self.benutzt = programm
                befehl = self._grundbefehl(programm) + satz
                self._vorgang = subprocess.Popen(
                    befehl, stdout=ausgabe, stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL, cwd=str(programm.parent), **zusatz,
                )
                if self._warten():
                    log.info("Modelldienst bereit auf %s (%s, Zusatzschalter: %s)",
                             self.adresse, programm.parent.name,
                             " ".join(satz) if satz else "keine")
                    return self.adresse

                letzte = self.letzte_ausgabe()
                self.beenden()
                log.warning("Modelldienst kam nicht hoch (%s, Zusatzschalter: %s). "
                            "Letzte Ausgabe: %s", programm.parent.name,
                            " ".join(satz) if satz else "keine", letzte)
                self.port = _freier_port()

        self.tempoflags_aktiv = False
        self.benutzt = None
        raise RuntimeError(
            "Der Modelldienst ist nicht hochgekommen"
            f"{': ' + letzte if letzte else '.'}"
        )

    def _warten(self) -> bool:
        """Wartet, bis der Server antwortet - oder der Vorgang endet."""
        ende = time.monotonic() + self.startgrenze
        while time.monotonic() < ende:
            if self._vorgang is not None and self._vorgang.poll() is not None:
                return False                     # vorzeitig beendet
            if self.bereit():
                return True
            time.sleep(0.5)
        return False

    def bereit(self) -> bool:
        """Antwortet der Server schon?

        Geprueft wird ``/health`` und - fuer aeltere Fassungen - ``/v1/models``.
        """
        for pfad in ("/health", "/v1/models"):
            try:
                with urllib.request.urlopen(f"{self.adresse}{pfad}", timeout=2) as antwort:
                    if 200 <= antwort.status < 300:
                        return True
            except urllib.error.HTTPError as fehler:
                if fehler.code in (503,):        # laedt noch
                    return False
                return True                      # antwortet, also erreichbar
            except (urllib.error.URLError, OSError, TimeoutError):
                continue
        return False

    def letzte_ausgabe(self, zeilen: int = 5) -> str:
        if self._protokoll is None or not self._protokoll.is_file():
            return ""
        try:
            text = self._protokoll.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        return " | ".join(text.strip().splitlines()[-zeilen:])

    # -- Ende ----------------------------------------------------------
    def beenden(self, frist: float = 10.0) -> None:
        """Beendet den Server. Mehrfach aufrufbar."""
        vorgang, self._vorgang = self._vorgang, None
        if vorgang is None:
            return
        if vorgang.poll() is None:
            vorgang.terminate()
            try:
                vorgang.wait(timeout=frist)
            except subprocess.TimeoutExpired:    # pragma: no cover - Notfall
                log.warning("Modelldienst reagiert nicht, wird abgebrochen.")
                vorgang.kill()
                vorgang.wait(timeout=frist)
        for strom in (vorgang.stdout, vorgang.stderr):
            try:
                if strom is not None:
                    strom.close()
            except Exception:                    # pragma: no cover - defensiv
                pass
        log.info("Modelldienst beendet.")

    def __del__(self):                           # pragma: no cover - Aufraeumen
        try:
            self.beenden(frist=2.0)
        except Exception:
            pass


def beschreibung(programm: Path | None) -> str:
    """Kurze Auskunft ueber die vorhandene Programmdatei."""
    if programm is None:
        return "nicht vorhanden"
    try:
        groesse = programm.stat().st_size / 1024**2
    except OSError:                              # pragma: no cover - defensiv
        return str(programm)
    return f"{programm.name} ({groesse:.1f} MB)"


def python_version_hinweis() -> str:             # pragma: no cover - Auskunft
    return f"Python {sys.version_info.major}.{sys.version_info.minor}"
