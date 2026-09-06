"""Das Plugin-Paket: lesen, pruefen, packen (E5.100, E5.109).

Ein Paket ist ein ZIP-Archiv mit der Endung ``.kimplug``. Darin liegen:

* ``manifest.json`` - die Selbstbeschreibung
* ``manifest.sig``  - die Signatur des Herausgebers (optional, siehe unten)
* der Programmcode des Plugins

Die Pruefsummen aller Codedateien stehen **im Manifest**. Signiert wird das
Manifest. Damit ist der Code mitsigniert: wird eine Datei ausgetauscht,
stimmt ihre Pruefsumme nicht mehr, und das Paket wird abgelehnt - auch wenn
die Signatur selbst gueltig waere.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ..licensing.model import canonical_bytes
from .modell import Manifest, PluginFehler

ENDUNG = ".kimplug"
MANIFEST = "manifest.json"
SIGNATUR = "manifest.sig"

#: Groessengrenze fuer ein einzelnes Paket. Ein Plugin ist Code, kein
#: Datenspeicher - so kann ein Paket den Datentraeger nicht vollschreiben.
HOECHSTGROESSE = 32 * 1024 * 1024

#: Nur diese Dateiendungen werden ausgepackt. Ausfuehrbare Dateien und
#: Bibliotheken sind ausgeschlossen: ein Plugin bringt Python mit, keine EXE.
ERLAUBTE_ENDUNGEN = {".py", ".json", ".md", ".txt", ".csv", ".html", ".css"}


@dataclass
class Paketpruefung:
    """Ergebnis der Pruefung eines Pakets."""

    manifest: Manifest
    signiert: bool
    signatur_gueltig: bool
    hinweise: list[str]

    @property
    def vertrauenswuerdig(self) -> bool:
        return self.signiert and self.signatur_gueltig


def _sicherer_name(name: str) -> str:
    """Verhindert, dass ein Paket ausserhalb seines Ordners schreibt."""
    reiner = name.replace("\\", "/")
    if reiner.startswith("/") or ".." in Path(reiner).parts or ":" in reiner:
        raise PluginFehler(f"Unzulaessiger Pfad im Paket: {name}")
    return reiner


def lesen(paket: Path) -> tuple[Manifest, bytes, dict[str, bytes]]:
    """Liest Manifest, Signatur und Dateien - ohne etwas auszupacken."""
    if not paket.is_file():
        raise PluginFehler(f"Es gibt keine Datei {paket}.")
    if paket.stat().st_size > HOECHSTGROESSE:
        raise PluginFehler(
            f"Das Paket ist groesser als {HOECHSTGROESSE // 1024 // 1024} MB "
            "und wird nicht angenommen."
        )
    try:
        with zipfile.ZipFile(paket) as archiv:
            if archiv.testzip() is not None:
                raise PluginFehler("Das Paket ist beschaedigt.")
            namen = archiv.namelist()
            if MANIFEST not in namen:
                raise PluginFehler(f"Im Paket fehlt {MANIFEST}.")
            manifest = Manifest.from_dict(json.loads(archiv.read(MANIFEST)))
            signatur = archiv.read(SIGNATUR) if SIGNATUR in namen else b""
            dateien: dict[str, bytes] = {}
            for name in namen:
                if name in (MANIFEST, SIGNATUR) or name.endswith("/"):
                    continue
                reiner = _sicherer_name(name)
                if Path(reiner).suffix.lower() not in ERLAUBTE_ENDUNGEN:
                    raise PluginFehler(
                        f"Das Paket enthaelt eine Datei, die nicht angenommen wird: "
                        f"{reiner}. Erlaubt sind: "
                        + ", ".join(sorted(ERLAUBTE_ENDUNGEN))
                    )
                dateien[reiner] = archiv.read(name)
    except zipfile.BadZipFile as fehler:
        raise PluginFehler(f"{paket.name} ist kein gueltiges Plugin-Paket.") from fehler
    except json.JSONDecodeError as fehler:
        raise PluginFehler(f"Das Manifest ist kein gueltiges JSON: {fehler}") from fehler
    return manifest, signatur, dateien


def pruefen(paket: Path, oeffentlicher_schluessel: bytes = b"") -> Paketpruefung:
    """Prueft Pruefsummen und - sofern moeglich - die Signatur."""
    manifest, signatur, dateien = lesen(paket)
    hinweise: list[str] = []

    fehlend = sorted(set(manifest.dateien) - set(dateien))
    zusatz = sorted(set(dateien) - set(manifest.dateien))
    if fehlend:
        raise PluginFehler("Im Paket fehlen angekuendigte Dateien: " + ", ".join(fehlend))
    if zusatz:
        raise PluginFehler(
            "Das Paket enthaelt Dateien, die nicht im Manifest stehen und damit "
            "nicht mitsigniert sind: " + ", ".join(zusatz)
        )
    for name, erwartet in manifest.dateien.items():
        tatsaechlich = hashlib.sha256(dateien[name]).hexdigest()
        if tatsaechlich != erwartet:
            raise PluginFehler(
                f"Die Datei {name} stimmt nicht mit dem Manifest ueberein. "
                "Das Paket wurde nach dem Erstellen veraendert."
            )
    if manifest.modul + ".py" not in dateien:
        raise PluginFehler(
            f"Der Einstieg nennt das Modul '{manifest.modul}', "
            f"aber {manifest.modul}.py liegt nicht im Paket."
        )

    signiert = bool(signatur)
    gueltig = False
    if signiert:
        if not oeffentlicher_schluessel:
            hinweise.append(
                "Das Paket ist signiert, aber in dieser Fassung ist kein "
                "Pruefschluessel des Herausgebers hinterlegt. Die Signatur kann "
                "deshalb nicht geprueft werden."
            )
        else:
            gueltig = _signatur_gueltig(manifest, signatur, oeffentlicher_schluessel)
            if not gueltig:
                raise PluginFehler(
                    "Die Signatur des Pakets ist ungueltig. Das Plugin wird nicht "
                    "installiert."
                )
    else:
        hinweise.append(
            "Das Paket ist nicht signiert. Es laeuft mit den Rechten der "
            "Anwendung - installieren Sie es nur, wenn Sie der Herkunft trauen."
        )
    return Paketpruefung(manifest, signiert, gueltig, hinweise)


def _signatur_gueltig(manifest: Manifest, signatur: bytes, schluessel: bytes) -> bool:
    from ..licensing.verify import crypto_available, verify_signature

    verfuegbar, grund = crypto_available()
    if not verfuegbar:
        raise PluginFehler(f"Die Signatur kann nicht geprueft werden: {grund}")
    return verify_signature(manifest.as_dict(), signatur, schluessel)


def signaturdaten(manifest: Manifest) -> bytes:
    """Die Bytes, ueber die signiert wird - fuer Herausgeber und Pruefung gleich."""
    return canonical_bytes(manifest.as_dict())


def packen(quelle: Path, ziel: Path, manifest_daten: dict | None = None,
           signatur: bytes = b"") -> Path:
    """Packt einen Ordner zu einem Plugin-Paket und traegt die Pruefsummen ein."""
    quelle = Path(quelle)
    daten = manifest_daten or json.loads((quelle / MANIFEST).read_text(encoding="utf-8"))
    dateien: dict[str, bytes] = {}
    for pfad in sorted(quelle.rglob("*")):
        if not pfad.is_file() or pfad.name in (MANIFEST, SIGNATUR):
            continue
        relativ = pfad.relative_to(quelle).as_posix()
        if pfad.suffix.lower() not in ERLAUBTE_ENDUNGEN:
            raise PluginFehler(f"Diese Datei gehoert nicht in ein Plugin-Paket: {relativ}")
        dateien[relativ] = pfad.read_bytes()

    daten["dateien"] = {
        name: hashlib.sha256(inhalt).hexdigest() for name, inhalt in sorted(dateien.items())
    }
    manifest = Manifest.from_dict(daten)

    ziel = ziel if ziel.suffix == ENDUNG else ziel.with_suffix(ENDUNG)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as archiv:
        archiv.writestr(MANIFEST, json.dumps(manifest.as_dict(), ensure_ascii=False,
                                             indent=2, sort_keys=True))
        if signatur:
            archiv.writestr(SIGNATUR, signatur)
        for name, inhalt in dateien.items():
            archiv.writestr(name, inhalt)
    return ziel
