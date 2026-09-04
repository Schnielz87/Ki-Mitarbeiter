"""Geheimnistresor (Masterprompt 21).

Zugangsdaten, API-Schluessel und Tokens duerfen **nicht** unverschluesselt im
Unternehmensgedaechtnis liegen.  Sie gehen in diese separate, mit einem
Passwort verschluesselte Datei ``config/secrets.enc``.

Verfahren: Schluesselableitung mit **scrypt**, Verschluesselung mit
**AES-256-GCM** (authentifiziert).  Ohne das Paket ``cryptography`` wird der
Tresor **nicht** benutzt - dann gibt es eine klare Fehlermeldung statt einer
Scheinverschluesselung.

Wichtig fuer die Portabilitaet: Die Datei liegt auf der SSD und wandert mit.
Geht die SSD verloren, sind die Geheimnisse ohne Passwort nicht lesbar.
"""

from __future__ import annotations

import base64
import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..db import utc_now
from ..logging_setup import get_logger

log = get_logger(__name__)

MAGIC = "PKC-VAULT"
FORMAT_VERSION = 1
SCRYPT_N = 2 ** 15      # ~32 MiB Speicher, bewusst kostspielig
SCRYPT_R = 8
SCRYPT_P = 1
KEY_BYTES = 32


class VaultError(RuntimeError):
    """Der Tresor konnte nicht benutzt werden."""


class VaultLocked(VaultError):
    """Der Tresor ist verschlossen - es fehlt das Passwort."""


def crypto_available() -> tuple[bool, str]:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt  # noqa: F401
    except ImportError:
        return False, (
            "Das Paket 'cryptography' fehlt. Ohne es koennen Geheimnisse nicht "
            "verschluesselt gespeichert werden. Es wird nichts unverschluesselt "
            "abgelegt."
        )
    return True, "AES-256-GCM verfuegbar"


@dataclass
class VaultInfo:
    exists: bool
    unlocked: bool
    entries: int
    path: str
    algorithm: str
    created_at: str = ""
    updated_at: str = ""


class SecretVault:
    """Verschluesselter Schluesselspeicher auf dem portablen Datentraeger."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._data: dict[str, str] | None = None
        self._key: bytes | None = None
        self._salt: bytes | None = None
        self._meta: dict[str, Any] = {}

    # -- Zustand -------------------------------------------------------
    @property
    def exists(self) -> bool:
        return self.path.is_file()

    @property
    def unlocked(self) -> bool:
        return self._data is not None

    def info(self) -> VaultInfo:
        return VaultInfo(
            exists=self.exists, unlocked=self.unlocked,
            entries=len(self._data or {}), path=str(self.path),
            algorithm="AES-256-GCM / scrypt",
            created_at=self._meta.get("created_at", ""),
            updated_at=self._meta.get("updated_at", ""),
        )

    # -- Kryptografie --------------------------------------------------
    @staticmethod
    def _derive(passphrase: str, salt: bytes) -> bytes:
        ok, message = crypto_available()
        if not ok:
            raise VaultError(message)
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

        kdf = Scrypt(salt=salt, length=KEY_BYTES, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
        return kdf.derive(passphrase.encode("utf-8"))

    # -- Anlegen / Oeffnen ---------------------------------------------
    def create(self, passphrase: str, overwrite: bool = False) -> None:
        if self.exists and not overwrite:
            raise VaultError(f"Es existiert bereits ein Tresor: {self.path}")
        if len(passphrase) < 8:
            raise VaultError("Das Tresorpasswort muss mindestens 8 Zeichen haben.")
        self._salt = os.urandom(16)
        self._key = self._derive(passphrase, self._salt)
        self._data = {}
        self._meta = {"created_at": utc_now(), "updated_at": utc_now()}
        self._write()
        log.info("Geheimnistresor angelegt: %s", self.path)

    def unlock(self, passphrase: str) -> None:
        if not self.exists:
            raise VaultError(f"Kein Tresor vorhanden: {self.path}")
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise VaultError(f"Tresordatei nicht lesbar: {exc}") from exc
        if envelope.get("magic") != MAGIC:
            raise VaultError("Die Datei ist kein gueltiger Tresor.")
        if int(envelope.get("version", 0)) != FORMAT_VERSION:
            raise VaultError(f"Unbekannte Tresorversion: {envelope.get('version')}")

        salt = base64.b64decode(envelope["salt"])
        nonce = base64.b64decode(envelope["nonce"])
        blob = base64.b64decode(envelope["data"])
        key = self._derive(passphrase, salt)

        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        try:
            plaintext = AESGCM(key).decrypt(nonce, blob, MAGIC.encode("ascii"))
        except InvalidTag as exc:
            raise VaultError("Falsches Passwort oder beschaedigte Tresordatei.") from exc
        self._salt, self._key = salt, key
        self._data = json.loads(plaintext.decode("utf-8"))
        self._meta = envelope.get("meta", {})
        log.info("Geheimnistresor geoeffnet (%s Eintraege)", len(self._data))

    def lock(self) -> None:
        self._data = None
        self._key = None

    def change_passphrase(self, old: str, new: str) -> None:
        self.unlock(old)
        data = dict(self._data or {})
        self.create(new, overwrite=True)
        self._data = data
        self._write()

    # -- Zugriff -------------------------------------------------------
    def _require(self) -> dict[str, str]:
        if self._data is None:
            raise VaultLocked("Der Geheimnistresor ist verschlossen.")
        return self._data

    def set(self, key: str, value: str) -> None:
        self._require()[key] = value
        self._write()

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._require().get(key, default)

    def get_quiet(self, key: str) -> str | None:
        """Wie ``get``, aber ohne Fehler bei verschlossenem Tresor."""
        if self._data is None:
            return None
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        data = self._require()
        existed = key in data
        data.pop(key, None)
        self._write()
        return existed

    def keys(self) -> list[str]:
        return sorted(self._require())

    # -- Speichern -----------------------------------------------------
    def _write(self) -> None:
        if self._key is None or self._salt is None or self._data is None:
            raise VaultLocked("Der Tresor kann nicht geschrieben werden - er ist verschlossen.")
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = os.urandom(12)
        payload = json.dumps(self._data, ensure_ascii=False).encode("utf-8")
        blob = AESGCM(self._key).encrypt(nonce, payload, MAGIC.encode("ascii"))
        self._meta["updated_at"] = utc_now()
        envelope = {
            "magic": MAGIC,
            "version": FORMAT_VERSION,
            "kdf": {"name": "scrypt", "n": SCRYPT_N, "r": SCRYPT_R, "p": SCRYPT_P},
            "cipher": "AES-256-GCM",
            "salt": base64.b64encode(self._salt).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "data": base64.b64encode(blob).decode("ascii"),
            "meta": self._meta,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".enc.tmp")
        temporary.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)


def suggest_passphrase(words: int = 4) -> str:
    """Vorschlag fuer ein Passwort - nur als Hilfe, nie automatisch gesetzt."""
    alphabet = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "-".join(
        "".join(secrets.choice(alphabet) for _ in range(5)) for _ in range(words)
    )
