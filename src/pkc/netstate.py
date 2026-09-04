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
    OFFLINE = "OFFLINE"
    HYBRID = "HYBRID"

    @property
    def label(self) -> str:
        return "HYBRID (online + lokal)" if self is Mode.HYBRID else "OFFLINE (nur lokal)"


@dataclass
class NetStatus:
    online: bool
    checked_at: float
    reachable: tuple[str, ...] = ()
    detail: str = ""

    @property
    def mode(self) -> Mode:
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
