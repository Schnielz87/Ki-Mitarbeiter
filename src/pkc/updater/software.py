"""Softwareupdates - getrennt vom Wissensupdate (Masterprompt 65).

Ein Wissensupdate taeuscht keine neue Programmfassung vor, und ein
Programmupdate darf den Wissensstand nicht anfassen. Deshalb sind es zwei
getrennte Wege mit getrennten Berichten.

Zusagen dieses Moduls:

* **Versioniert** - jedes Paket nennt seine Fassung.
* **Auf Integritaet pruefbar** - jede Datei mit SHA-256, das Verzeichnis
  zusaetzlich signiert, sofern ein Pruefschluessel hinterlegt ist.
* **Ruecksetzbar** - vor dem Einspielen wird der bisherige Stand gesichert.
* **Ein fehlerhaftes Update zerstoert keine Installation** - schlaegt die
  Pruefung nach dem Einspielen fehl, wird automatisch zurueckgesetzt.
* **Kundendaten bleiben unberuehrt** - ein Softwarepaket darf ausschliesslich
  Programmdateien enthalten; alles andere wird abgewiesen.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from ..db import utc_now
from ..logging_setup import get_logger

log = get_logger(__name__)

MANIFEST_NAME = "update_manifest.json"

#: Verzeichnisse, die ein Softwarepaket **niemals** anfassen darf.
#: Es geht um Programmdateien - Unternehmensdaten gehoeren dem Kunden.
PROTECTED = (
    "database/", "company/", "conversations/", "workspace/", "backups/",
    "customers/", "license/", "logs/", "config/secrets.enc", "models/",
)


class SoftwareUpdateError(RuntimeError):
    """Das Softwarepaket ist unbrauchbar oder unsicher."""


@dataclass
class PackageInfo:
    version: str
    released: str
    notes: str
    files: dict[str, str]          # Pfad -> SHA-256
    signed: bool = False
    signature_ok: bool | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def file_count(self) -> int:
        return len(self.files)

    def as_dict(self) -> dict:
        return {
            "version": self.version, "veroeffentlicht": self.released,
            "hinweise": self.notes, "dateien": self.file_count,
            "signiert": self.signed, "signatur_ok": self.signature_ok,
            "warnungen": self.warnings,
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(262144), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_protected(relativ: str) -> bool:
    normalisiert = relativ.replace("\\", "/")
    return any(
        normalisiert == p.rstrip("/") or normalisiert.startswith(p)
        for p in PROTECTED
    )


class SoftwareUpdater:
    """Prueft und spielt Programmupdates ein."""

    def __init__(self, program_root: Path, backup_dir: Path,
                 public_key_pem: bytes | None = None):
        self.program_root = Path(program_root)
        self.backup_dir = Path(backup_dir)
        self.public_key_pem = public_key_pem or b""

    # -- Pruefen -------------------------------------------------------
    def inspect(self, package: Path) -> PackageInfo:
        """Liest und prueft ein Paket, ohne etwas zu veraendern."""
        package = Path(package)
        if not package.is_file():
            raise SoftwareUpdateError(f"Paket nicht gefunden: {package}")
        try:
            archiv = zipfile.ZipFile(package)
        except zipfile.BadZipFile as exc:
            raise SoftwareUpdateError(f"Paket ist kein gueltiges ZIP: {exc}") from exc

        with archiv:
            if MANIFEST_NAME not in archiv.namelist():
                raise SoftwareUpdateError(
                    f"Im Paket fehlt {MANIFEST_NAME}. Ohne Verzeichnis der Dateien "
                    "und ihrer Pruefsummen wird nichts eingespielt."
                )
            try:
                manifest = json.loads(archiv.read(MANIFEST_NAME).decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise SoftwareUpdateError(f"{MANIFEST_NAME} ist nicht lesbar: {exc}") from exc

            dateien = dict(manifest.get("files", {}))
            info = PackageInfo(
                version=str(manifest.get("version", "")),
                released=str(manifest.get("released", "")),
                notes=str(manifest.get("notes", "")),
                files=dateien,
                signed="signature" in manifest,
            )
            if not info.version:
                raise SoftwareUpdateError("Das Paket nennt keine Version.")
            if not dateien:
                raise SoftwareUpdateError("Das Paket enthaelt keine Dateien.")

            # Kundendaten sind tabu
            verboten = [p for p in dateien if _is_protected(p)]
            if verboten:
                raise SoftwareUpdateError(
                    "Das Paket will geschuetzte Bereiche veraendern: "
                    + ", ".join(sorted(verboten)[:5])
                    + ". Ein Softwareupdate darf keine Kundendaten anfassen."
                )
            ausbruch = [
                p for p in dateien
                if p.startswith("/") or ".." in p.replace("\\", "/").split("/")
            ]
            if ausbruch:
                raise SoftwareUpdateError(
                    "Das Paket enthaelt Pfade ausserhalb des Programmverzeichnisses: "
                    + ", ".join(sorted(ausbruch)[:5])
                )

            # Jede angekuendigte Datei muss enthalten sein und passen
            vorhanden = set(archiv.namelist())
            for relativ, erwartet in dateien.items():
                if relativ not in vorhanden:
                    raise SoftwareUpdateError(f"Im Paket fehlt die Datei {relativ}.")
                tatsaechlich = hashlib.sha256(archiv.read(relativ)).hexdigest()
                if tatsaechlich != erwartet:
                    raise SoftwareUpdateError(
                        f"Pruefsumme von {relativ} passt nicht - das Paket ist "
                        "beschaedigt oder veraendert."
                    )

            if info.signed:
                info.signature_ok = self._check_signature(manifest)
                if info.signature_ok is False:
                    raise SoftwareUpdateError(
                        "Die Signatur des Pakets ist ungueltig. Es stammt nicht vom "
                        "Herausgeber oder wurde veraendert."
                    )
            elif self.public_key_pem:
                info.warnings.append(
                    "Das Paket ist nicht signiert, obwohl ein Pruefschluessel "
                    "vorhanden ist."
                )
            else:
                info.warnings.append(
                    "Das Paket ist nicht signiert und es ist kein Pruefschluessel "
                    "hinterlegt - die Herkunft ist nicht belegbar."
                )
        return info

    def _check_signature(self, manifest: dict) -> bool | None:
        if not self.public_key_pem:
            return None
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
        except ImportError:
            return None
        nutzdaten = {k: v for k, v in manifest.items() if k != "signature"}
        from ..licensing.model import canonical_bytes

        try:
            schluessel = load_pem_public_key(self.public_key_pem)
            schluessel.verify(bytes.fromhex(manifest["signature"]),
                              canonical_bytes(nutzdaten))
            return True
        except (InvalidSignature, ValueError):
            return False

    # -- Einspielen ----------------------------------------------------
    def apply(self, package: Path, dry_run: bool = False) -> dict:
        """Spielt ein geprueftes Paket ein. Bei Fehlern wird zurueckgesetzt."""
        info = self.inspect(package)
        if dry_run:
            return {"status": "trockenlauf", "paket": info.as_dict(),
                    "hinweis": "Es wurde nichts veraendert."}

        # Der Zeitstempel ist sekundengenau. Zwei Updates in derselben Sekunde
        # wuerden sich sonst die Sicherung ueberschreiben - und damit den
        # Ruecksetzpunkt vernichten. Deshalb wird ein freier Name gesucht.
        stempel = utc_now().replace(":", "").replace("-", "")
        sicherung = self.backup_dir / f"software-{stempel}"
        laufende_nummer = 1
        while sicherung.exists():
            laufende_nummer += 1
            sicherung = self.backup_dir / f"software-{stempel}-{laufende_nummer}"
        sicherung.mkdir(parents=True, exist_ok=True)

        gesichert: list[str] = []
        for relativ in info.files:
            ziel = self.program_root / relativ
            if ziel.is_file():
                kopie = sicherung / relativ
                kopie.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ziel, kopie)
                gesichert.append(relativ)
        (sicherung / "VORHER.json").write_text(json.dumps({
            "erstellt": utc_now(), "neue_version": info.version,
            "gesicherte_dateien": gesichert,
            "neu_hinzugekommen": [p for p in info.files if p not in gesichert],
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        eingespielt: list[str] = []
        try:
            with zipfile.ZipFile(package) as archiv:
                for relativ in info.files:
                    ziel = self.program_root / relativ
                    ziel.parent.mkdir(parents=True, exist_ok=True)
                    ziel.write_bytes(archiv.read(relativ))
                    eingespielt.append(relativ)
            # Nachpruefung: liegt wirklich das da, was drinstehen sollte?
            fehlerhaft = [
                relativ for relativ, erwartet in info.files.items()
                if _sha256(self.program_root / relativ) != erwartet
            ]
            if fehlerhaft:
                raise SoftwareUpdateError(
                    "Nach dem Einspielen stimmen Pruefsummen nicht: "
                    + ", ".join(fehlerhaft[:5])
                )
        except Exception as exc:
            log.error("Softwareupdate fehlgeschlagen, setze zurueck: %s", exc)
            zurueck = self.rollback(sicherung)
            return {
                "status": "zurueckgesetzt",
                "fehler": str(exc),
                "sicherung": str(sicherung),
                "wiederhergestellt": zurueck["wiederhergestellt"],
                "hinweis": "Die Installation ist auf dem bisherigen Stand.",
            }

        log.info("Softwareupdate auf %s eingespielt (%s Dateien)",
                 info.version, len(eingespielt))
        return {
            "status": "eingespielt", "version": info.version,
            "dateien": len(eingespielt), "sicherung": str(sicherung),
            "paket": info.as_dict(),
            "hinweis": "Ruecknahme moeglich ueber die Sicherung.",
        }

    def rollback(self, backup: Path) -> dict:
        """Stellt den Stand vor einem Update wieder her."""
        backup = Path(backup)
        beschreibung = backup / "VORHER.json"
        if not beschreibung.is_file():
            raise SoftwareUpdateError(f"Keine Sicherung gefunden: {backup}")
        daten = json.loads(beschreibung.read_text(encoding="utf-8"))

        wiederhergestellt: list[str] = []
        for relativ in daten.get("gesicherte_dateien", []):
            quelle = backup / relativ
            if quelle.is_file():
                ziel = self.program_root / relativ
                ziel.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(quelle, ziel)
                wiederhergestellt.append(relativ)
        entfernt: list[str] = []
        for relativ in daten.get("neu_hinzugekommen", []):
            ziel = self.program_root / relativ
            if ziel.is_file():
                ziel.unlink()
                entfernt.append(relativ)

        log.warning("Softwarestand zurueckgesetzt (%s Dateien)", len(wiederhergestellt))
        return {"wiederhergestellt": wiederhergestellt, "entfernt": entfernt,
                "sicherung": str(backup)}

    def history(self, limit: int = 20) -> list[dict]:
        if not self.backup_dir.is_dir():
            return []
        eintraege = []
        for ordner in sorted(self.backup_dir.glob("software-*"), reverse=True)[:limit]:
            beschreibung = ordner / "VORHER.json"
            if beschreibung.is_file():
                daten = json.loads(beschreibung.read_text(encoding="utf-8"))
                daten["sicherung"] = str(ordner)
                eintraege.append(daten)
        return eintraege


def build_package(
    source_root: Path, files: list[str], target: Path, version: str,
    notes: str = "", private_key_path: Path | None = None, passphrase: str = "",
) -> Path:
    """Baut ein Softwarepaket (Herstellerseite)."""
    source_root = Path(source_root)
    manifest = {
        "version": version,
        "released": utc_now(),
        "notes": notes,
        "files": {},
    }
    inhalte: dict[str, bytes] = {}
    for relativ in files:
        quelle = source_root / relativ
        if not quelle.is_file():
            raise SoftwareUpdateError(f"Datei fehlt: {quelle}")
        daten = quelle.read_bytes()
        inhalte[relativ] = daten
        manifest["files"][relativ] = hashlib.sha256(daten).hexdigest()

    if private_key_path is not None:
        from ..licensing.issue import load_private_key
        from ..licensing.model import canonical_bytes

        schluessel = load_private_key(Path(private_key_path), passphrase)
        manifest["signature"] = schluessel.sign(canonical_bytes(manifest)).hex()

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archiv:
        archiv.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2, ensure_ascii=False))
        for relativ, daten in inhalte.items():
            archiv.writestr(relativ, daten)
    return target
