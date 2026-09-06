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

#: Wie lange auf das Hochfahren gewartet wird. Ein grosses Modell braucht auf
#: einer aelteren CPU durchaus eine Minute, bis es geladen ist.
STARTGRENZE_S = 180.0


def _programmname() -> str:
    return "llama-server.exe" if os.name == "nt" else "llama-server"


def finde_server(runtime_dir: Path) -> Path | None:
    """Sucht die Programmdatei des Servers im Laufzeitordner.

    Gesucht wird nur unterhalb des portablen Ordners - nie im System. Was
    nicht auf dem Datentraeger liegt, ist beim naechsten Rechner nicht da
    (Masterprompt 19, 20).
    """
    runtime_dir = Path(runtime_dir)
    name = _programmname()
    for unter in LAUFZEIT_UNTERORDNER:
        kandidat = (runtime_dir / unter / name) if unter != "." else runtime_dir / name
        if kandidat.is_file():
            return kandidat
    # Manche Pakete legen die Datei in einen Unterordner mit Versionsnamen.
    if runtime_dir.is_dir():
        for pfad in sorted(runtime_dir.rglob(name)):
            if pfad.is_file():
                return pfad
    return None


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
    _vorgang: subprocess.Popen | None = field(default=None, repr=False)
    _protokoll: Path | None = field(default=None, repr=False)

    @property
    def adresse(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def laeuft(self) -> bool:
        return self._vorgang is not None and self._vorgang.poll() is None

    # -- Start ---------------------------------------------------------
    def _befehl(self) -> list[str]:
        befehl = [
            str(self.programm),
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
        self._vorgang = subprocess.Popen(
            self._befehl(), stdout=ausgabe, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, cwd=str(self.programm.parent), **zusatz,
        )

        if not self._warten():
            letzte = self.letzte_ausgabe()
            self.beenden()
            raise RuntimeError(
                "Der Modelldienst ist nicht hochgekommen"
                f"{': ' + letzte if letzte else '.'}"
            )
        log.info("Modelldienst bereit auf %s", self.adresse)
        return self.adresse

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
