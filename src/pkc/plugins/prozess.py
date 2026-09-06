"""Ein Plugin in einem eigenen Vorgang fuehren (E5.108).

Bisher lief ein Plugin im selben Vorgang wie die Anwendung. Die
Rechtepruefung war damit eine Absprache: wer eigenen Code ausfuehrt, kann
sie umgehen. Jetzt laeuft das Plugin daneben und hat gar nichts in der
Hand - keine Datenbank, keinen Tresor, kein Objekt der Anwendung. Es kann
nur fragen, und hier wird entschieden.

Was hier geprueft wird, ist damit die **einzige** Tuer zu den
Unternehmensdaten. Was hier nicht erlaubt ist, gibt es fuer das Plugin
nicht.

Ehrlich zur Grenze: der Vorgang laeuft mit denselben Benutzerrechten wie die
Anwendung. Eine Beschraenkung durch das Betriebssystem (eigenes Konto,
Job-Objekt, seccomp) ist damit **nicht** erreicht - ein Plugin koennte
weiterhin Dateien des Benutzers oeffnen. Der Gewinn ist, dass es die Daten
der Anwendung nicht mehr im Zugriff hat.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable

from ..logging_setup import get_logger
from . import protokoll
from .modell import BerechtigungFehlt, Manifest, PluginFehler

log = get_logger(__name__)

#: Schalter, mit dem sich die Anwendung selbst als Plugin-Vorgang startet.
#: In der gepackten EXE gibt es kein python.exe daneben - also ruft sich das
#: Programm selbst auf.
SCHALTER = "--plugin-worker"

#: Wie lange auf eine Antwort des Plugins gewartet wird.
ANTWORTGRENZE_S = 60.0


def worker_befehl() -> list[str]:
    """Der Befehl, mit dem ein Plugin-Vorgang gestartet wird."""
    if getattr(sys, "frozen", False):             # pragma: no cover - nur gepackt
        return [sys.executable, SCHALTER]
    return [sys.executable, "-m", "pkc.plugins.worker"]


class Pluginprozess:
    """Fuehrt genau ein Plugin in einem eigenen Vorgang."""

    def __init__(
        self,
        manifest: Manifest,
        ordner: Path,
        datenordner: Path,
        berechtigungen: list[str],
        dienste: dict[str, Callable[..., Any]] | None = None,
        befehl: list[str] | None = None,
        antwortgrenze: float = ANTWORTGRENZE_S,
    ):
        self.manifest = manifest
        self.ordner = Path(ordner)
        self.datenordner = Path(datenordner)
        self.berechtigungen = frozenset(berechtigungen)
        #: Was die Anwendung dem Plugin anbietet - jede Funktion prueft selbst.
        self.dienste = dienste or {}
        self.befehl = befehl or worker_befehl()
        self.antwortgrenze = float(antwortgrenze)
        self.werkzeuge: list[dict] = []
        self.formate: list[str] = []
        self._vorgang: subprocess.Popen | None = None
        self._zaehler = 0
        self._schloss = threading.Lock()

    @property
    def laeuft(self) -> bool:
        return self._vorgang is not None and self._vorgang.poll() is None

    # -- Start und Ende ------------------------------------------------
    def starten(self) -> None:
        if self.laeuft:
            return
        umgebung = dict(os.environ)
        # Der Vorgang soll nichts aus dem Elternprozess erben, was er nicht
        # braucht. Die Wurzel wird ausdruecklich gesetzt, damit ein Plugin
        # nicht ueber Umgebungsvariablen woanders hinschreibt.
        umgebung["KIM_PLUGIN"] = self.manifest.id
        umgebung["PYTHONIOENCODING"] = "utf-8"
        if not getattr(sys, "frozen", False):
            wurzel = Path(__file__).resolve().parents[2]
            vorher = umgebung.get("PYTHONPATH", "")
            umgebung["PYTHONPATH"] = str(wurzel) + (os.pathsep + vorher if vorher else "")

        zusatz = {}
        if os.name == "nt":                       # pragma: no cover - nur Windows
            zusatz["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            self._vorgang = subprocess.Popen(
                self.befehl, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, encoding="utf-8",
                env=umgebung, cwd=str(self.ordner), bufsize=1, **zusatz,
            )
        except OSError as fehler:
            raise PluginFehler(
                f"Der Plugin-Vorgang liess sich nicht starten: {fehler}"
            ) from fehler

        ergebnis = self._auftrag({
            "art": "anmelden",
            "manifest": self.manifest.as_dict(),
            "ordner": str(self.ordner),
            "datenordner": str(self.datenordner),
            "berechtigungen": sorted(self.berechtigungen),
        })
        self.werkzeuge = list(ergebnis.get("werkzeuge", []))
        self.formate = list(ergebnis.get("formate", []))
        log.info("Plugin %s laeuft in einem eigenen Vorgang (%s Werkzeug(e), "
                 "%s Format(e))", self.manifest.id, len(self.werkzeuge),
                 len(self.formate))

    def beenden(self, frist: float = 5.0) -> None:
        vorgang, self._vorgang = self._vorgang, None
        if vorgang is None:
            return
        try:
            if vorgang.poll() is None and vorgang.stdin is not None:
                protokoll.schreiben(vorgang.stdin, {"art": "ende"})
        except (OSError, ValueError):              # Leitung schon zu
            pass
        try:
            vorgang.wait(timeout=frist)
        except subprocess.TimeoutExpired:
            vorgang.terminate()
            try:
                vorgang.wait(timeout=frist)
            except subprocess.TimeoutExpired:      # pragma: no cover - Notfall
                vorgang.kill()
        for strom in (vorgang.stdin, vorgang.stdout, vorgang.stderr):
            try:
                if strom is not None:
                    strom.close()
            except Exception:                      # pragma: no cover - defensiv
                pass

    # -- Auftraege -----------------------------------------------------
    def werkzeug_rufen(self, name: str, *argumente, **schluessel):
        return self._auftrag({"art": "werkzeug", "name": name,
                              "argumente": protokoll.einfach(list(argumente)),
                              "schluessel": protokoll.einfach(schluessel)})

    def format_erzeugen(self, kuerzel: str, dokument) -> bytes:
        wert = self._auftrag({"art": "format", "kuerzel": kuerzel,
                              "dokument": protokoll.dokument_hinein(dokument)})
        return protokoll.bytes_heraus(str(wert))

    def _auftrag(self, nachricht: dict):
        """Schickt einen Auftrag und beantwortet Rueckfragen, bis er fertig ist."""
        if self._vorgang is None or self._vorgang.poll() is not None:
            raise PluginFehler(f"Der Vorgang des Plugins '{self.manifest.id}' laeuft nicht.")
        with self._schloss:
            self._zaehler += 1
            kennung = self._zaehler
            nachricht["id"] = kennung
            try:
                protokoll.schreiben(self._vorgang.stdin, nachricht)
            except (OSError, ValueError) as fehler:
                raise PluginFehler(
                    f"Das Plugin '{self.manifest.id}' nimmt nichts mehr entgegen: {fehler}"
                ) from fehler

            while True:
                antwort = protokoll.lesen(self._vorgang.stdout)
                if antwort is None:
                    rest = ""
                    if self._vorgang.stderr is not None:
                        try:
                            rest = self._vorgang.stderr.read()[-400:]
                        except Exception:          # pragma: no cover - defensiv
                            rest = ""
                    raise PluginFehler(
                        f"Der Vorgang des Plugins '{self.manifest.id}' ist beendet"
                        + (f": {rest.strip()}" if rest.strip() else ".")
                    )
                art = antwort.get("art")
                if art == "anfrage":
                    self._beantworten(antwort)
                    continue
                if antwort.get("id") != kennung:
                    continue
                if art == "fehler":
                    raise PluginFehler(
                        f"Plugin '{self.manifest.id}': {antwort.get('meldung', 'Fehler')}")
                if art == "ergebnis":
                    return antwort.get("wert")

    def _beantworten(self, anfrage: dict) -> None:
        """Beantwortet eine Rueckfrage des Plugins - nach Rechtepruefung."""
        funktion = str(anfrage.get("funktion", ""))
        argumente = anfrage.get("argumente", {}) or {}
        antwort: dict = {"art": "antwort", "id": anfrage.get("id")}
        dienst = self.dienste.get(funktion)
        if dienst is None:
            antwort["fehler"] = f"Die Anwendung bietet '{funktion}' nicht an."
        else:
            try:
                antwort["wert"] = protokoll.einfach(dienst(**argumente))
            except BerechtigungFehlt as fehler:
                antwort["fehler"] = str(fehler)
            except Exception as fehler:
                log.warning("Anfrage %s des Plugins %s fehlgeschlagen: %s",
                            funktion, self.manifest.id, fehler)
                antwort["fehler"] = f"{type(fehler).__name__}: {fehler}"
        try:
            protokoll.schreiben(self._vorgang.stdin, antwort)
        except (OSError, ValueError):              # pragma: no cover - Leitung zu
            pass
