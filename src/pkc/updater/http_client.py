"""HTTP-Zugriff fuer den Wissensabruf.

Eigenschaften:
* nur Standardbibliothek (kein ``requests``) - erleichtert das EXE-Packaging
* bedingte Anfragen ueber ETag / If-Modified-Since (inkrementelle Updates)
* Wartezeit pro Host (hoefliches Verhalten gegenueber amtlichen Servern)
* robots.txt wird beachtet
* jeder Fehler wird als Ergebnis zurueckgegeben, nie als Absturz
"""

from __future__ import annotations

import gzip
import hashlib
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import zlib
from dataclasses import dataclass, field

from ..logging_setup import get_logger

log = get_logger(__name__)

USER_AGENT = (
    "Portabler-KI-Mitarbeiter/0.1 (lokaler Wissensabgleich; "
    "kontaktieren Sie den Betreiber der Installation)"
)


@dataclass
class FetchResult:
    url: str
    status: int
    ok: bool
    not_modified: bool = False
    content: bytes = b""
    content_type: str = ""
    etag: str | None = None
    last_modified: str | None = None
    error: str = ""
    elapsed: float = 0.0
    final_url: str = ""

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest() if self.content else ""

    @property
    def size(self) -> int:
        return len(self.content)

    def text(self, fallback: str = "utf-8") -> str:
        charset = fallback
        if "charset=" in self.content_type.lower():
            charset = self.content_type.lower().split("charset=", 1)[1].split(";")[0].strip()
        for encoding in (charset, "utf-8", "cp1252", "latin-1"):
            try:
                return self.content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return self.content.decode("utf-8", errors="replace")


class HttpClient:
    """Schlanker, hoeflicher HTTP-Client mit Cache-Headern."""

    def __init__(
        self,
        timeout: float = 30.0,
        min_delay: float = 1.0,
        max_bytes: int = 60 * 1024 * 1024,
        respect_robots: bool = True,
        user_agent: str = USER_AGENT,
    ):
        self.timeout = float(timeout)
        self.min_delay = float(min_delay)
        self.max_bytes = int(max_bytes)
        self.respect_robots = bool(respect_robots)
        self.user_agent = user_agent
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    # -- Hoeflichkeit --------------------------------------------------
    def _throttle(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            wait = self.min_delay - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self._last_request[host] = time.monotonic()

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parsed = urllib.parse.urlsplit(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(base + "/robots.txt")
            try:
                parser.read()
                self._robots[base] = parser
            except Exception:  # robots nicht abrufbar -> nicht blockieren
                self._robots[base] = None
        parser = self._robots[base]
        if parser is None:
            return True
        try:
            return parser.can_fetch(self.user_agent, url)
        except Exception:  # pragma: no cover - defensiv
            return True

    # -- Abruf ---------------------------------------------------------
    def fetch(
        self,
        url: str,
        etag: str | None = None,
        last_modified: str | None = None,
        method: str = "GET",
    ) -> FetchResult:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https"):
            return FetchResult(url, 0, False, error=f"Nicht unterstuetztes Schema: {parsed.scheme!r}")
        if not self.allowed(url):
            return FetchResult(url, 0, False, error="Durch robots.txt untersagt")

        request = urllib.request.Request(url, method=method)
        request.add_header("User-Agent", self.user_agent)
        request.add_header("Accept-Encoding", "gzip, deflate")
        request.add_header("Accept", "*/*")
        if etag:
            request.add_header("If-None-Match", etag)
        if last_modified:
            request.add_header("If-Modified-Since", last_modified)

        self._throttle(parsed.netloc)
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(self.max_bytes + 1)
                if len(raw) > self.max_bytes:
                    return FetchResult(
                        url, response.status, False,
                        error=f"Antwort groesser als {self.max_bytes} Bytes",
                        elapsed=time.monotonic() - started,
                    )
                raw = _decompress(raw, response.headers.get("Content-Encoding", ""))
                return FetchResult(
                    url=url,
                    status=response.status,
                    ok=True,
                    content=raw,
                    content_type=response.headers.get("Content-Type", ""),
                    etag=response.headers.get("ETag"),
                    last_modified=response.headers.get("Last-Modified"),
                    elapsed=time.monotonic() - started,
                    final_url=response.geturl(),
                )
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                return FetchResult(url, 304, True, not_modified=True,
                                   elapsed=time.monotonic() - started)
            return FetchResult(url, exc.code, False, error=f"HTTP {exc.code}: {exc.reason}",
                               elapsed=time.monotonic() - started)
        except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
            return FetchResult(url, 0, False, error=f"{type(exc).__name__}: {exc}",
                               elapsed=time.monotonic() - started)


def _decompress(raw: bytes, encoding: str) -> bytes:
    encoding = (encoding or "").lower()
    try:
        if "gzip" in encoding:
            return gzip.decompress(raw)
        if "deflate" in encoding:
            try:
                return zlib.decompress(raw)
            except zlib.error:
                return zlib.decompress(raw, -zlib.MAX_WBITS)
    except (OSError, zlib.error) as exc:  # pragma: no cover - defensiv
        log.warning("Dekomprimierung fehlgeschlagen (%s), verwende Rohdaten", exc)
    return raw
