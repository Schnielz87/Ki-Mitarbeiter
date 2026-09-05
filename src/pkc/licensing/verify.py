"""Lizenzpruefung (Masterprompt 87, 91, 95).

Grundsaetze:

* **Offline pruefbar.** Der Start braucht keinen Lizenzserver und keine
  Internetverbindung (Abschnitt 87).
* **Kryptografisch, nicht per Textdatei.** Geprueft wird eine Ed25519-Signatur
  ueber die kanonische Darstellung der Lizenzdaten. Ein Eintrag wie
  ``licensed=true`` in einer Textdatei waere wirkungslos (Abschnitt 91).
* **Der private Schluessel ist niemals Teil der Anwendung.** Ausgeliefert wird
  ausschliesslich der oeffentliche Pruefschluessel (Abschnitt 86).
* **Niemals Daten beschaedigen.** Eine ungueltige Lizenz fuehrt zu einer
  verstaendlichen Meldung und einem eingeschraenkten Betrieb, in dem
  Lizenzinformationen und der **Datenexport** weiter moeglich bleiben - es
  werden keine Daten geloescht, gesperrt oder verschluesselt (Abschnitt 95).
"""

from __future__ import annotations

import json
from pathlib import Path

from ..logging_setup import get_logger
from .instance import CarrierIdentity, carrier_identity, instance_id_for
from .model import (
    License, LicenseError, LicenseState, LicenseStatus, canonical_bytes,
)

log = get_logger(__name__)

#: Oeffentlicher Pruefschluessel des Herausgebers.
#:
#: Fuer diese Vorabfassung ist noch kein Herausgeberschluessel hinterlegt - das
#: ist eine geschaeftliche Entscheidung und gehoert zur kommerziellen Freigabe.
#: Solange hier nichts steht, meldet die Pruefung ehrlich "nicht pruefbar",
#: statt eine Gueltigkeit vorzutaeuschen. Der Schluessel wird beim Bau der
#: kommerziellen Fassung eingesetzt; der private Gegenpart bleibt beim
#: Herausgeber.
PUBLIC_KEY_PEM: bytes = b""

#: Ablageort der Lizenz relativ zur Produktwurzel.
LICENSE_DIR = "license"
LICENSE_FILE = "license.json"
SIGNATURE_FILE = "license.sig"


def crypto_available() -> tuple[bool, str]:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: F401
            Ed25519PublicKey,
        )
    except ImportError:
        return False, (
            "Das Paket 'cryptography' fehlt. Ohne es kann eine Lizenzsignatur "
            "nicht geprueft werden."
        )
    return True, "Ed25519 verfuegbar"


def verify_signature(payload: dict, signature: bytes, public_key_pem: bytes) -> bool:
    """Prueft die Ed25519-Signatur ueber die kanonischen Lizenzdaten."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    schluessel = load_pem_public_key(public_key_pem)
    try:
        schluessel.verify(signature, canonical_bytes(payload))
        return True
    except InvalidSignature:
        return False


class LicenseChecker:
    """Prueft die Lizenz einer portablen Produktinstanz."""

    def __init__(
        self,
        root: Path,
        product: str = "portabler-ki-mitarbeiter",
        module: str = "buchhalter",
        required: bool = False,
        public_key_pem: bytes | None = None,
    ):
        self.root = Path(root)
        self.product = product
        self.module = module
        self.required = bool(required)
        self.public_key_pem = (
            public_key_pem if public_key_pem is not None else PUBLIC_KEY_PEM
        )

    # -- Ablage --------------------------------------------------------
    @property
    def directory(self) -> Path:
        return self.root / LICENSE_DIR

    @property
    def license_path(self) -> Path:
        return self.directory / LICENSE_FILE

    @property
    def signature_path(self) -> Path:
        return self.directory / SIGNATURE_FILE

    # -- Instanz -------------------------------------------------------
    def identity(self) -> CarrierIdentity:
        return carrier_identity(self.root)

    def instance_id(self, license_id: str = "") -> str:
        return instance_id_for(self.identity(), license_id)

    # -- Pruefung ------------------------------------------------------
    def check(self) -> LicenseStatus:
        """Fuehrt die vollstaendige Pruefung durch. Wirft nie."""
        kennung = self.identity()
        basis = {
            "required": self.required,
            "carrier": kennung.as_dict(),
            "instance_id": instance_id_for(kennung),
        }

        if not self.license_path.is_file():
            zustand = LicenseState.NICHT_ERFORDERLICH if not self.required else LicenseState.FEHLT
            meldung = (
                "Fuer diese Produktinstanz wurde keine Lizenzdatei gefunden."
                if self.required else
                "Diese Fassung laeuft ohne Lizenzpruefung (Vorab- bzw. Pilotfassung)."
            )
            return LicenseStatus(
                state=zustand, message=meldung,
                hints=self._hints_missing() if self.required else [],
                **basis,
            )

        ok, detail = crypto_available()
        if not ok:
            return LicenseStatus(
                state=LicenseState.NICHT_PRUEFBAR,
                message=f"Die Lizenz konnte nicht geprueft werden: {detail}",
                hints=["Bitte den Hersteller kontaktieren."], **basis,
            )

        try:
            daten = json.loads(self.license_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return LicenseStatus(
                state=LicenseState.BESCHAEDIGT,
                message=f"Die Lizenzdatei ist nicht lesbar: {exc}",
                hints=self._hints_missing(), **basis,
            )

        try:
            lizenz = License.from_payload(daten)
        except LicenseError as exc:
            return LicenseStatus(
                state=LicenseState.BESCHAEDIGT, message=str(exc),
                hints=self._hints_missing(), **basis,
            )

        if not self.signature_path.is_file():
            return LicenseStatus(
                state=LicenseState.UNGUELTIG_SIGNATUR,
                message="Zur Lizenzdatei fehlt die Signatur (license.sig).",
                license=lizenz, hints=self._hints_missing(), **basis,
            )
        if not self.public_key_pem:
            return LicenseStatus(
                state=LicenseState.NICHT_PRUEFBAR,
                message=(
                    "In dieser Fassung ist kein Pruefschluessel des Herausgebers "
                    "hinterlegt. Die Lizenz wird deshalb weder als gueltig noch "
                    "als ungueltig behandelt."
                ),
                license=lizenz, **basis,
            )

        signatur = self.signature_path.read_bytes().strip()
        try:
            signatur = bytes.fromhex(signatur.decode("ascii"))
        except (ValueError, UnicodeDecodeError):
            pass          # bereits binaer hinterlegt
        try:
            echt = verify_signature(lizenz.payload(), signatur, self.public_key_pem)
        except Exception as exc:
            return LicenseStatus(
                state=LicenseState.UNGUELTIG_SIGNATUR,
                message=f"Die Signatur der Lizenz ist nicht pruefbar: {exc}",
                license=lizenz, hints=self._hints_missing(), **basis,
            )
        if not echt:
            return LicenseStatus(
                state=LicenseState.UNGUELTIG_SIGNATUR,
                message=(
                    "Die Lizenzdatei wurde veraendert oder stammt nicht vom "
                    "Herausgeber. Die Signatur passt nicht zu ihrem Inhalt."
                ),
                license=lizenz, hints=self._hints_missing(), **basis,
            )

        # Ab hier ist die Lizenz echt - jetzt zaehlt, ob sie zu DIESER Instanz passt.
        if lizenz.product != self.product:
            return LicenseStatus(
                state=LicenseState.FALSCHES_PRODUKT,
                message=(
                    f"Die Lizenz gilt fuer '{lizenz.product}', diese Anwendung ist "
                    f"'{self.product}'."
                ),
                license=lizenz, **basis,
            )
        if not lizenz.covers_module(self.module):
            return LicenseStatus(
                state=LicenseState.MODUL_NICHT_LIZENZIERT,
                message=(
                    f"Das Fachmodul '{self.module}' ist in dieser Lizenz nicht "
                    f"enthalten (enthalten: {', '.join(lizenz.modules) or 'keines'})."
                ),
                license=lizenz, **basis,
            )
        if lizenz.expired():
            return LicenseStatus(
                state=LicenseState.ABGELAUFEN,
                message=f"Die Lizenz ist am {lizenz.expiry_date} abgelaufen.",
                license=lizenz,
                hints=["Bitte den Hersteller wegen einer Verlaengerung ansprechen."],
                **basis,
            )

        erwartet = kennung.fingerprint()
        if lizenz.carrier_fingerprint and lizenz.carrier_fingerprint != erwartet:
            return LicenseStatus(
                state=LicenseState.FALSCHE_INSTANZ,
                message=(
                    "Diese Lizenz gehoert zu einem anderen Datentraeger. "
                    "Vermutlich wurde der Programmordner auf einen weiteren "
                    "Datentraeger kopiert - dadurch entsteht keine zweite Lizenz."
                ),
                license=lizenz,
                hints=[
                    "Der urspruengliche lizenzierte Datentraeger laeuft weiterhin.",
                    "Bei Defekt oder Ersatz: Lizenzuebertragung beim Hersteller "
                    "beantragen (siehe LIZENZKONZEPT.md).",
                    f"Instanz-ID dieses Datentraegers: {instance_id_for(kennung, lizenz.license_id)}",
                ],
                **basis,
            )

        return LicenseStatus(
            state=LicenseState.GUELTIG,
            message=f"Lizenziert fuer {lizenz.customer} ({lizenz.license_id}).",
            license=lizenz, **basis,
        )

    def _hints_missing(self) -> list[str]:
        kennung = self.identity()
        hinweise = [
            "Die Anwendung laeuft eingeschraenkt weiter: Lizenzangaben ansehen "
            "und Unternehmensdaten exportieren bleiben moeglich.",
            "Es werden keine Daten geloescht, gesperrt oder veraendert.",
            f"Instanz-ID dieses Datentraegers: {instance_id_for(kennung)}",
        ]
        if not kennung.reliable:
            hinweise.append(
                "Achtung: Der Datentraeger liefert keine belastbare Kennung. "
                "Eine Lizenzbindung ist hier nur eingeschraenkt moeglich."
            )
        return hinweise

    # -- Aktivierung ---------------------------------------------------
    def install(self, license_json: Path, signature: Path) -> LicenseStatus:
        """Nimmt eine vom Hersteller ausgestellte Lizenz auf."""
        if not license_json.is_file():
            raise LicenseError(f"Lizenzdatei nicht gefunden: {license_json}")
        if not signature.is_file():
            raise LicenseError(f"Signaturdatei nicht gefunden: {signature}")
        self.directory.mkdir(parents=True, exist_ok=True)
        self.license_path.write_bytes(license_json.read_bytes())
        self.signature_path.write_bytes(signature.read_bytes())
        log.info("Lizenz aufgenommen: %s", self.license_path)
        return self.check()

    def activation_request(self, customer: str = "", note: str = "") -> dict:
        """Angaben, die der Hersteller zum Ausstellen einer Lizenz braucht."""
        kennung = self.identity()
        return {
            "produkt": self.product,
            "modul": self.module,
            "kunde": customer,
            "instanz_id": instance_id_for(kennung),
            "datentraeger_fingerabdruck": kennung.fingerprint(),
            "datentraeger_art": kennung.kind,
            "belastbar": kennung.reliable,
            "hinweis": note,
        }
