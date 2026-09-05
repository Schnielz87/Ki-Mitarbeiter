"""Erkennung des Internetstatus und Umschaltung OFFLINE <-> HYBRID.

Wichtig: Es gibt genau *eine* Anwendung.  Der Netzstatus schaltet lediglich
Zusatzfunktionen frei bzw. wieder ab; der Offline-Kern laeuft unveraendert
weiter.  Ein Verbindungsverlust darf nie zum Abbruch fuehren.
"""

from __future__ import annotations

import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable

from .logging_setup import get_logger

log = get_logger(__name__)


class Mode(str, Enum):
    """Der **vom Benutzer gewaehlte** Betriebsmodus.

    Nicht zu verwechseln mit dem Internetstatus. Das sind zwei getrennte
    Zustaende, und genau darin liegt der Sinn:

        Betriebsmodus OFFLINE + Internet VERFUEGBAR
            -> es wird trotzdem nichts abgerufen. Eine bewusste
               Entscheidung des Benutzers hebt die Anwendung nicht auf.

        Betriebsmodus HYBRID + Internet NICHT VERFUEGBAR
            -> die Anwendung arbeitet lokal weiter, ohne Datenverlust.
    """

    OFFLINE = "OFFLINE"
    HYBRID = "HYBRID"
    ONLINE = "ONLINE"

    @property
    def label(self) -> str:
        return {
            Mode.OFFLINE: "OFFLINE (nur lokal)",
            Mode.HYBRID: "HYBRID (lokal, online zusaetzlich)",
            Mode.ONLINE: "ONLINE (online bevorzugt, lokal weiterhin verfuegbar)",
        }[self]

    @property
    def erlaubt_online(self) -> bool:
        """Darf in diesem Modus ueberhaupt nach draussen zugegriffen werden?"""
        return self is not Mode.OFFLINE

    @property
    def beschreibung(self) -> str:
        """Text fuer die Bestaetigung beim Moduswechsel."""
        if self is Mode.OFFLINE:
            return ("Offline-Modus aktiv.\n\n"
                    "Die Anwendung verwendet ausschliesslich lokale Modelle, "
                    "Daten, Dokumente, Plugins und Wissensbestaende.\n\n"
                    "Es werden keine externen Online-Dienste verwendet - auch "
                    "dann nicht, wenn eine Internetverbindung besteht.")
        if self is Mode.ONLINE:
            return ("Online-Modus aktiv.\n\n"
                    "Onlinequellen, Wissensupdates und - soweit freigegeben - "
                    "eine Online-KI duerfen verwendet werden.\n\n"
                    "Ihre lokalen Daten, das Unternehmensgedaechtnis und das "
                    "lokale Fachwissen bleiben unveraendert verfuegbar.")
        return ("Hybrid-Modus aktiv.\n\n"
                "Die lokale Arbeit ist die Grundlage; Onlinequellen und "
                "Wissensupdates duerfen zusaetzlich verwendet werden.\n\n"
                "Faellt die Verbindung aus, arbeitet die Anwendung ohne "
                "Unterbrechung lokal weiter.")

    @classmethod
    def parse(cls, wert: object, vorgabe: "Mode" = None) -> "Mode":
        """Liest einen Modus aus Konfiguration oder Eingabe - grosszuegig.

        ``offline``, ``OFFLINE`` und ``Offline`` bezeichnen dasselbe. Ein
        unbekannter Wert fuehrt nie zu einem Absturz, sondern zur Vorgabe -
        aber niemals stillschweigend zu mehr Rechten: die Vorgabe ist
        HYBRID, und wer OFFLINE gewaehlt hatte, dessen Wahl steht in der
        Konfiguration und wird gelesen.
        """
        vorgabe = vorgabe if vorgabe is not None else cls.HYBRID
        if isinstance(wert, cls):
            return wert
        text = str(wert or "").strip().upper()
        for modus in cls:
            if modus.value == text:
                return modus
        return vorgabe


@dataclass
class NetStatus:
    online: bool
    checked_at: float
    reachable: tuple[str, ...] = ()
    detail: str = ""

    @property
    def mode(self) -> Mode:
        """Welcher Modus sich allein aus dem Netzbefund ergaebe.

        Nur ein Vorschlag - die Wahl des Benutzers hat Vorrang. Siehe
        ``Betriebsart``.
        """
        return Mode.HYBRID if self.online else Mode.OFFLINE


def probe(url: str, timeout: float) -> bool:
    """Einzelner HEAD/GET-Versuch. Jeder Fehler bedeutet 'nicht erreichbar'."""
    request = urllib.request.Request(url, method="HEAD")
    request.add_header("User-Agent", "Portabler-KI-Mitarbeiter/0.1 (Konnektivitaetspruefung)")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 500
    except urllib.error.HTTPError as exc:
        # Server antwortet -> Verbindung existiert.
        return exc.code < 500
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return False


class NetworkMonitor:
    """Prueft den Netzstatus und meldet Wechsel per Callback.

    Der Monitor ist optional: ohne ``start()`` bleibt alles synchron.
    """

    def __init__(
        self,
        hosts: Iterable[str],
        timeout: float = 4.0,
        interval: float = 60.0,
        enabled: bool = True,
    ):
        self.hosts = tuple(hosts)
        self.timeout = float(timeout)
        self.interval = float(interval)
        self.enabled = bool(enabled)
        self._status = NetStatus(False, 0.0, (), "noch nicht geprueft")
        self._listeners: list[Callable[[NetStatus], None]] = []
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    # -- Status --------------------------------------------------------
    @property
    def status(self) -> NetStatus:
        with self._lock:
            return self._status

    @property
    def mode(self) -> Mode:
        return self.status.mode

    def check(self) -> NetStatus:
        """Synchrone Pruefung. Erster Erfolg genuegt.

        Ist die Pruefung abgeschaltet, wird ein bereits gesetzter Status
        **nicht** ueberschrieben: "nicht pruefen" heisst nicht "kein Netz".
        Sonst wuerde eine ausdrueckliche Vorgabe des Nutzers stillschweigend
        verworfen.
        """
        if not self.enabled:
            with self._lock:
                bekannt = self._status.checked_at > 0.0
            if bekannt:
                return self.status
            return self._apply(
                NetStatus(False, time.time(), (), "Netzpruefung deaktiviert")
            )
        reachable: list[str] = []
        detail = "keine Testadresse erreichbar"
        for host in self.hosts:
            if probe(host, self.timeout):
                reachable.append(host)
                detail = f"erreichbar: {host}"
                break
        status = NetStatus(bool(reachable), time.time(), tuple(reachable), detail)
        return self._apply(status)

    def _apply(self, status: NetStatus) -> NetStatus:
        with self._lock:
            previous = self._status
            self._status = status
        if previous.online != status.online or previous.checked_at == 0.0:
            log.info("Betriebsart: %s (%s)", status.mode.value, status.detail)
            for listener in list(self._listeners):
                try:
                    listener(status)
                except Exception:  # pragma: no cover - Listener duerfen nie stoeren
                    log.exception("Netzstatus-Listener fehlgeschlagen")
        return status

    def on_change(self, callback: Callable[[NetStatus], None]) -> None:
        self._listeners.append(callback)

    # -- Hintergrunduebwachung ----------------------------------------
    def start(self) -> None:
        if self._thread is not None or not self.enabled:
            return
        self._stop.clear()

        def loop() -> None:
            while not self._stop.wait(self.interval):
                try:
                    self.check()
                except Exception:  # pragma: no cover
                    log.exception("Netzpruefung fehlgeschlagen")

        self._thread = threading.Thread(target=loop, name="netmonitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=2.0)

    def force(self, online: bool, detail: str = "manuell gesetzt") -> NetStatus:
        """Erzwingt einen Status (Tests, Benutzerwunsch 'offline arbeiten')."""
        return self._apply(NetStatus(online, time.time(), (), detail))


@dataclass
class Betriebslage:
    """Was gerade gilt - Wahl und Wirklichkeit nebeneinander."""

    modus: Mode
    internet: bool
    #: Ergebnis aus beidem: Darf jetzt tatsaechlich online zugegriffen werden?
    online_moeglich: bool
    grund: str = ""

    @property
    def internet_text(self) -> str:
        return "verfuegbar" if self.internet else "nicht verfuegbar"

    def as_dict(self) -> dict:
        return {
            "betriebsmodus": self.modus.value,
            "internet": self.internet_text,
            "online_moeglich": self.online_moeglich,
            "grund": self.grund,
        }


class Betriebsart:
    """Verwaltet den gewaehlten Betriebsmodus - getrennt vom Netzbefund.

    Der Benutzer waehlt HYBRID, OFFLINE oder ONLINE. Diese Wahl:

    * wird gespeichert und ueberlebt einen Neustart
    * wird von der Anwendung **nie** selbsttaetig aufgehoben
    * entscheidet zusammen mit dem Netzbefund, ob online zugegriffen wird

    Der haeufigste Denkfehler waere, den Modus aus dem Netzbefund
    abzuleiten. Dann waere OFFLINE keine Entscheidung, sondern nur die
    Beschreibung eines Zustands - und ein wiederkehrendes Netz wuerde den
    Benutzer unbemerkt zurueck in den Onlinebetrieb versetzen.
    """

    SCHLUESSEL = "network.mode"

    def __init__(self, config, monitor: "NetworkMonitor", audit=None):
        self.config = config
        self.monitor = monitor
        self.audit = audit
        self._modus = Mode.parse(config.get(self.SCHLUESSEL, Mode.HYBRID.value))
        log.info("Betriebsmodus (gewaehlt): %s", self._modus.value)

    @property
    def modus(self) -> Mode:
        return self._modus

    def lage(self, pruefen: bool = False) -> Betriebslage:
        """Aktuelle Lage. ``pruefen`` erzwingt eine Netzpruefung.

        Im OFFLINE-Modus wird **nicht** geprueft: eine Netzpruefung ist
        selbst ein Netzzugriff. Der Internetstatus wird dann als unbekannt
        und damit als nicht verfuegbar gefuehrt.
        """
        if self._modus is Mode.OFFLINE:
            return Betriebslage(
                self._modus, False, False,
                "Offline-Modus vom Benutzer gewaehlt - es wird nicht einmal "
                "geprueft, ob eine Verbindung besteht.",
            )
        status = self.monitor.check() if pruefen else self.monitor.status
        if not status.online:
            return Betriebslage(
                self._modus, False, False,
                "Keine Internetverbindung - die Anwendung arbeitet lokal weiter.",
            )
        return Betriebslage(self._modus, True, True, status.detail)

    def waehlen(self, neu: Mode | str, grund: str = "Benutzerwahl") -> Betriebslage:
        """Setzt den Modus, speichert ihn dauerhaft und protokolliert."""
        neu = Mode.parse(neu, self._modus)
        vorher = self._modus
        self._modus = neu
        self.config.set(self.SCHLUESSEL, neu.value)
        try:
            self.config.save()
        except Exception as exc:        # pragma: no cover - defensiv
            log.warning("Betriebsmodus konnte nicht gespeichert werden: %s", exc)
        if self.audit is not None and vorher is not neu:
            try:
                self.audit.record(
                    "betriebsmodus", "mode", neu.value,
                    vorher=vorher.value, nachher=neu.value, grund=grund,
                    internet="verfuegbar" if self.monitor.status.online else "nicht verfuegbar",
                )
            except Exception:           # pragma: no cover - defensiv
                log.debug("Moduswechsel nicht protokollierbar", exc_info=True)
        log.info("Betriebsmodus gewechselt: %s -> %s (%s)", vorher.value, neu.value, grund)
        return self.lage()
