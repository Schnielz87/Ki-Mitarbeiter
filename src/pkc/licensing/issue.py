"""Ausstellen von Lizenzen - **Herstellerseite** (Masterprompt 86).

Dieses Modul gehoert nicht zur Kundenanwendung im engeren Sinn: es braucht
den **privaten** Signaturschluessel. Der darf niemals mit ausgeliefert werden.
Die Kundenanwendung enthaelt ausschliesslich den oeffentlichen Pruefschluessel.

Der Ablauf ist bewusst so gebaut, dass er auch offline funktioniert
(Abschnitt 88): Der Kunde schickt seine Aktivierungsanfrage, der Hersteller
stellt eine signierte Lizenzdatei aus, der Kunde nimmt sie auf.
"""

from __future__ import annotations

import datetime as _dt
import json
import uuid
from pathlib import Path

from .model import License, LicenseError, canonical_bytes


def generate_keypair(private_path: Path, public_path: Path, passphrase: str = "") -> tuple[Path, Path]:
    """Erzeugt ein Ed25519-Schluesselpaar fuer den Herausgeber.

    Der private Schluessel wird - sofern ein Passwort angegeben ist -
    verschluesselt abgelegt. Er gehoert in den Tresor des Herstellers, nicht
    in das Produkt.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    privat = Ed25519PrivateKey.generate()
    schutz = (
        serialization.BestAvailableEncryption(passphrase.encode("utf-8"))
        if passphrase else serialization.NoEncryption()
    )
    private_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(privat.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=schutz,
    ))
    try:
        private_path.chmod(0o600)
    except OSError:      # pragma: no cover - Windows kennt das nicht
        pass
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_bytes(privat.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    return private_path, public_path


def load_private_key(path: Path, passphrase: str = ""):
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    if not path.is_file():
        raise LicenseError(f"Privater Signaturschluessel nicht gefunden: {path}")
    return load_pem_private_key(
        path.read_bytes(), password=passphrase.encode("utf-8") if passphrase else None
    )


def issue_license(
    private_key_path: Path,
    *,
    customer: str,
    customer_id: str = "",
    instance_id: str,
    carrier_fingerprint: str,
    product: str = "portabler-ki-mitarbeiter",
    product_version: str = "0.1.0",
    modules: list[str] | None = None,
    license_type: str = "instanz",
    allowed_instances: int = 1,
    expiry_date: str | None = None,
    maintenance_until: str | None = None,
    issuer: str = "",
    notes: str = "",
    license_id: str = "",
    passphrase: str = "",
    target_dir: Path | None = None,
) -> tuple[License, bytes, Path | None]:
    """Erstellt und signiert eine Lizenz. Gibt (Lizenz, Signatur, Ablageort)."""
    schluessel = load_private_key(Path(private_key_path), passphrase)
    heute = _dt.date.today().isoformat()
    lizenz = License(
        license_id=license_id or f"LIZ-{uuid.uuid4().hex[:12].upper()}",
        customer=customer, customer_id=customer_id or uuid.uuid4().hex[:12].upper(),
        product=product, product_version=product_version,
        modules=modules or ["buchhalter"], license_type=license_type,
        allowed_instances=int(allowed_instances), instance_id=instance_id,
        carrier_fingerprint=carrier_fingerprint, activation_date=heute,
        expiry_date=expiry_date, maintenance_until=maintenance_until,
        issued_at=_dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        issuer=issuer, notes=notes,
    )
    signatur = schluessel.sign(canonical_bytes(lizenz.payload()))

    ablage = None
    if target_dir is not None:
        ablage = Path(target_dir)
        ablage.mkdir(parents=True, exist_ok=True)
        (ablage / "license.json").write_text(
            json.dumps(lizenz.payload(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (ablage / "license.sig").write_text(signatur.hex() + "\n", encoding="ascii")
    return lizenz, signatur, ablage
