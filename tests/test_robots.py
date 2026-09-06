"""robots.txt darf den Wissensabgleich nicht anhalten.

Die Anwendung fragt vor jedem Abruf, ob robots.txt ihn erlaubt. Das ist
richtig so - amtliche Server sollen nicht ueberrannt werden.

Nur wurde dafuer ``RobotFileParser.read()`` benutzt, und das ruft
``urlopen`` **ohne Zeitgrenze** auf. Ein Server, der die Verbindung annimmt
und dann schweigt, haelt den Abgleich damit endlos an: kein Fehler, keine
Meldung, kein Ende - und noch bevor ein einziges Dokument geladen ist.

Aufgefallen ist das nicht im Test, sondern im Windows-Bauablauf: die
Pruefung des Quellenregisters stand nach neun Minuten immer noch beim
ersten Server. Diese Datei schliesst die Luecke.
"""

from __future__ import annotations

import socket
import threading
import time

import pytest

from pkc.updater.http_client import ROBOTS_ZEITGRENZE, HttpClient


class SchweigenderServer:
    """Nimmt die Verbindung an und antwortet nie.

    Genau der Fall, den eine Zeitgrenze abfangen muss - ein abgelehnter
    Verbindungsversuch waere sofort zurueck und wuerde nichts beweisen.
    """

    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(4)
        self.port = self._sock.getsockname()[1]
        self._offen: list[socket.socket] = []
        self._laeuft = True
        self._faden = threading.Thread(target=self._annehmen, daemon=True)
        self._faden.start()

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def _annehmen(self):
        while self._laeuft:
            try:
                verbindung, _ = self._sock.accept()
            except OSError:
                return
            self._offen.append(verbindung)      # halten, nicht antworten

    def beenden(self):
        self._laeuft = False
        try:
            self._sock.close()
        except OSError:
            pass
        for verbindung in self._offen:
            try:
                verbindung.close()
            except OSError:
                pass


@pytest.fixture
def schweigend():
    server = SchweigenderServer()
    try:
        yield server
    finally:
        server.beenden()


def test_stummer_server_haelt_den_abgleich_nicht_an(schweigend):
    """Nach der Zeitgrenze muss es weitergehen - nicht irgendwann."""
    client = HttpClient(timeout=3.0, min_delay=0.0, respect_robots=True)

    begonnen = time.monotonic()
    erlaubt = client.allowed(f"{schweigend.base}/ustg/xml.zip")
    gedauert = time.monotonic() - begonnen

    assert gedauert < 20.0, (
        f"die Abfrage von robots.txt hing {gedauert:.0f} s - ohne Zeitgrenze "
        "haengt hier der ganze Wissensabgleich")
    assert erlaubt is True, (
        "ein nicht erreichbares robots.txt darf nicht als Verbot gelten")


def test_zeitgrenze_ist_kleiner_als_die_des_abrufs():
    """robots.txt ist eine kleine Textdatei - sie braucht nicht so lange."""
    assert 0 < ROBOTS_ZEITGRENZE <= 15.0


def test_robots_wird_nur_einmal_je_server_geholt(schweigend):
    """Sonst wartet jeder Abruf erneut die volle Zeitgrenze ab."""
    client = HttpClient(timeout=3.0, min_delay=0.0, respect_robots=True)
    client.allowed(f"{schweigend.base}/eins.html")

    begonnen = time.monotonic()
    client.allowed(f"{schweigend.base}/zwei.html")
    assert time.monotonic() - begonnen < 1.0, (
        "das Ergebnis muss gemerkt werden, auch ein fehlgeschlagenes")


def test_verbot_in_robots_wird_beachtet(http_server):
    """Die Zeitgrenze darf die eigentliche Aufgabe nicht aushebeln."""
    http_server.add("/robots.txt",
                    b"User-agent: *\nDisallow: /gesperrt/\n",
                    "text/plain")
    client = HttpClient(timeout=3.0, min_delay=0.0, respect_robots=True)

    assert client.allowed(f"{http_server.base}/gesperrt/akte.html") is False
    assert client.allowed(f"{http_server.base}/offen/akte.html") is True
