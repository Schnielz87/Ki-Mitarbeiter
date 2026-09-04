"""Generischer REST-Connector.

Deckt jedes System ab, das eine HTTP/JSON-Schnittstelle anbietet.  Zugangs-
daten kommen ausschliesslich aus dem Geheimnistresor, nie aus der
Konfigurationsdatei.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .base import Connector, ConnectorError, ConnectorMode, ConnectorResult, NotConfigured


class GenericRestConnector(Connector):
    connector_id = "generic_rest"
    name = "Generische REST-Schnittstelle"
    system = "HTTP/JSON"
    capabilities = ("read", "preview", "write")
    open_questions = (
        "Welche Basisadresse und welche Endpunkte werden verwendet?",
        "Welches Anmeldeverfahren (Bearer-Token, Basic, API-Key im Header)?",
        "Ist ein VPN oder eine Freischaltung der IP notwendig?",
        "Welche Berechtigungen hat das verwendete technische Konto?",
        "Gibt es eine Testumgebung, in der Schreibvorgaenge geprueft werden koennen?",
    )

    def configured(self) -> tuple[bool, str]:
        base = self.config.get("base_url")
        if not base:
            return False, "Keine Basisadresse konfiguriert (Schluessel 'base_url')."
        if not str(base).startswith(("http://", "https://")):
            return False, f"Basisadresse ist keine HTTP-Adresse: {base}"
        return True, f"Konfiguriert: {base}"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        headers.update(self.config.get("headers", {}) or {})
        secret_key = self.config.get("secret_key")
        if secret_key and self.secret_lookup is not None:
            token = self.secret_lookup(secret_key)
            if token:
                scheme = self.config.get("auth_scheme", "Bearer")
                header_name = self.config.get("auth_header", "Authorization")
                headers[header_name] = f"{scheme} {token}".strip()
        return headers

    def _request(self, method: str, path: str, body: dict | None = None,
                 params: dict | None = None) -> Any:
        ok, detail = self.configured()
        if not ok:
            raise NotConfigured(f"{self.name}: {detail}")
        base = str(self.config["base_url"]).rstrip("/")
        url = f"{base}/{path.lstrip('/')}" if path else base
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        for key, value in self._headers().items():
            request.add_header(key, value)
        timeout = float(self.config.get("timeout", 30))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise ConnectorError(f"{self.name}: HTTP {exc.code} von {url} - {detail}") from exc
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise ConnectorError(f"{self.name}: {url} nicht erreichbar - {exc}") from exc
        if not payload.strip():
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ConnectorError(f"{self.name}: Antwort ist kein JSON ({exc}).") from exc

    def test(self) -> ConnectorResult:
        ok, detail = self.configured()
        if not ok:
            return ConnectorResult(ok=False, message=detail)
        path = self.config.get("health_path", "")
        try:
            self._request("GET", path)
        except ConnectorError as exc:
            return ConnectorResult(ok=False, message=str(exc))
        return ConnectorResult(ok=True, message=f"Verbindung erfolgreich: {self.config['base_url']}")

    def read(self, query: str = "", params: dict | None = None, **kwargs) -> ConnectorResult:
        data = self._request("GET", query, params=params)
        rows = _as_rows(data, self.config.get("rows_key"))
        return ConnectorResult(ok=True, rows=rows, message=f"{len(rows)} Datensaetze gelesen.",
                               meta={"pfad": query})

    def _perform_write(self, payload: dict, approval_uid: str) -> ConnectorResult:
        path = payload.get("path") or self.config.get("write_path", "")
        method = str(payload.get("method", "POST")).upper()
        body = payload.get("body", {})
        data = self._request(method, path, body=body)
        rows = _as_rows(data, self.config.get("rows_key"))
        return ConnectorResult(
            ok=True, rows=rows,
            message=f"Schreibvorgang ausgefuehrt ({method} {path}) auf Grundlage der "
                    f"Freigabe {approval_uid}.",
        )


def _as_rows(data: Any, rows_key: str | None = None) -> list[dict]:
    if data is None:
        return []
    if rows_key and isinstance(data, dict) and rows_key in data:
        data = data[rows_key]
    if isinstance(data, list):
        return [item if isinstance(item, dict) else {"wert": item} for item in data]
    if isinstance(data, dict):
        return [data]
    return [{"wert": data}]
