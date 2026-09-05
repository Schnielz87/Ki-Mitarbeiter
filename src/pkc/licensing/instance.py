"""Identitaet der portablen Produktinstanz (Masterprompt 85, 86, 90).

Die Aufgabe ist zweischneidig:

* Der Datentraeger soll an **verschiedenen** Windows-Rechnern laufen - eine
  Bindung an einen einzelnen PC waere genau das, was Abschnitt 85 verbietet.
* Eine **Kopie der Programmdateien auf einen zweiten Datentraeger** darf
  jedoch keine zweite lizenzierte Instanz erzeugen.

Daraus folgt: gebunden wird an den **Datentraeger**, nicht an den Rechner.
Verwendet wird die Datentraegerkennung des Dateisystems - unter Windows die
Volume-Seriennummer, unter Linux die Dateisystem-UUID. Sie wandert mit dem
Datentraeger von PC zu PC, wird beim Kopieren auf einen anderen Datentraeger
aber nicht mitkopiert.

**Ehrliche Grenze:** Ein bitgenaues Abbild eines ganzen Datentraegers kann
diese Kennung reproduzieren. Das Kopieren von *Dateien* wird verhindert, das
Klonen eines ganzen Volumes nicht vollstaendig. Masterprompt 84 haelt das
bereits fest: eine absolute technische Verhinderung ist nicht moeglich.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..logging_setup import get_logger

log = get_logger(__name__)


@dataclass
class CarrierIdentity:
    """Kennung des Datentraegers, auf dem die Instanz liegt."""

    kind: str          # windows_volume_serial | linux_fs_uuid | device_id | unbekannt
    value: str
    detail: str = ""

    @property
    def reliable(self) -> bool:
        """Taugt die Kennung fuer eine Lizenzbindung?"""
        return self.kind in ("windows_volume_serial", "linux_fs_uuid") and bool(self.value)

    def fingerprint(self, salt: str = "portable-ki-mitarbeiter") -> str:
        """Gehashte Kennung - die Rohkennung muss nicht in der Lizenz stehen."""
        roh = f"{salt}|{self.kind}|{self.value}".encode("utf-8")
        return hashlib.sha256(roh).hexdigest()

    def as_dict(self) -> dict:
        return {"art": self.kind, "kennung": self.value, "hinweis": self.detail,
                "belastbar": self.reliable}


def _windows_volume_serial(path: Path) -> CarrierIdentity | None:  # pragma: no cover
    """Volume-Seriennummer des Laufwerks, auf dem ``path`` liegt."""
    try:
        laufwerk = os.path.splitdrive(str(path.resolve()))[0]
        if not laufwerk:
            return None
        wurzel = laufwerk + "\\"
        seriennummer = ctypes.c_ulong(0)
        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(wurzel), None, 0,
            ctypes.byref(seriennummer), None, None, None, 0,
        )
        if not ok or seriennummer.value == 0:
            return None
        return CarrierIdentity(
            "windows_volume_serial", f"{seriennummer.value:08X}",
            f"Laufwerk {laufwerk}",
        )
    except Exception as exc:
        log.warning("Volume-Seriennummer nicht lesbar: %s", exc)
        return None


def _linux_fs_uuid(path: Path) -> CarrierIdentity | None:
    """Dateisystem-UUID des Datentraegers, auf dem ``path`` liegt."""
    try:
        geraet = os.stat(path).st_dev
    except OSError:
        return None
    verzeichnis = Path("/dev/disk/by-uuid")
    if verzeichnis.is_dir():
        for eintrag in verzeichnis.iterdir():
            try:
                if os.stat(eintrag.resolve()).st_rdev == geraet:
                    return CarrierIdentity("linux_fs_uuid", eintrag.name,
                                           f"Geraet {eintrag.resolve()}")
            except OSError:
                continue
    # Ersatzweise ueber findmnt, falls vorhanden
    try:
        ausgabe = subprocess.run(
            ["findmnt", "-no", "UUID", "-T", str(path)],
            capture_output=True, text=True, timeout=5, check=False,
        )
        kennung = ausgabe.stdout.strip()
        if kennung:
            return CarrierIdentity("linux_fs_uuid", kennung, "ueber findmnt")
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def carrier_identity(path: Path) -> CarrierIdentity:
    """Ermittelt die Datentraegerkennung fuer den angegebenen Pfad."""
    erzwungen = os.environ.get("KIM_CARRIER_ID")
    if erzwungen:
        # Ausschliesslich fuer automatische Tests und die Fehlersuche.
        return CarrierIdentity("linux_fs_uuid", erzwungen, "durch Umgebung gesetzt")

    if platform.system() == "Windows":
        kennung = _windows_volume_serial(path)
    else:
        kennung = _linux_fs_uuid(path)
    if kennung is not None:
        return kennung

    # Letzter Ausweg: Geraetenummer. Sie ist nicht stabil genug fuer eine
    # Lizenzbindung und wird deshalb als nicht belastbar gekennzeichnet.
    try:
        return CarrierIdentity("device_id", str(os.stat(path).st_dev),
                               "Ersatzkennung - fuer eine Lizenzbindung zu schwach")
    except OSError:
        return CarrierIdentity("unbekannt", "", "Datentraeger nicht bestimmbar")


def instance_id_for(identity: CarrierIdentity, license_id: str = "") -> str:
    """Kurze, stabile Kennung dieser Produktinstanz."""
    roh = f"{identity.kind}|{identity.value}|{license_id}".encode("utf-8")
    return hashlib.sha256(roh).hexdigest()[:24].upper()
