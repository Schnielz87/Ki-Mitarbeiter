"""Marke und Erscheinungsbild der Plattform (PORTIVA).

Grundgedanke: **Marke und Berufsprofil sind getrennt.** PORTIVA ist fest,
der Mitarbeitername kommt aus dem aktiven Profil. Daraus entsteht der
Fenstertitel:

    PORTIVA - Buchhalter
    PORTIVA - Controller

Der Profilname steht deshalb nirgends fest im Programmcode.

Alle Brandingdateien werden ueber **relative** Pfade unterhalb der
Programmwurzel gefunden. Damit funktioniert das Erscheinungsbild
unveraendert, wenn der Datentraeger einmal als D:, ein andermal als E:
eingebunden wird - und ohne jede Internetverbindung, weil alles auf dem
Datentraeger liegt.

Fehlt eine Brandingdatei, faellt die Anwendung auf eine Textdarstellung
zurueck. Sie stuerzt nicht ab, und sie erfindet kein Ersatzlogo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .logging_setup import get_logger

log = get_logger(__name__)

#: Fester Markenname. Aendert sich nicht mit dem Berufsprofil.
MARKE = "PORTIVA"
CLAIM = "Portable KI-Mitarbeiter-Plattform"

#: Trennzeichen zwischen Marke und Profil im Fenstertitel.
TRENNER = " - "

#: Ablageorte, alle relativ zur Programmwurzel.
BRANDING_DIR = "branding"
ORIGINAL_DIR = "branding/original"
ORIGINAL_DATEI = "branding/original/portiva_logo_original.png"
#: Optionales eigenes Quadratsymbol. Fehlt es, wird das Symbol aus dem
#: breiten Logo abgeleitet - das ist zulaessig, sieht aber in kleinen
#: Groessen weniger gut aus, weil der Schriftzug dann winzig wird.
ORIGINAL_ICON = "branding/original/portiva_icon_original.png"

VARIANTEN = {
    "primary": "branding/portiva_logo_primary.png",
    "light": "branding/portiva_logo_light.png",
    "dark": "branding/portiva_logo_dark.png",
    "icon": "branding/portiva_icon.png",
    "ico": "branding/portiva_icon.ico",
}


@dataclass
class Brand:
    """Die Marke - unabhaengig vom Berufsprofil."""

    name: str = MARKE
    claim: str = CLAIM
    logo: str = VARIANTEN["primary"]
    icon: str = VARIANTEN["ico"]
    #: Wurzel, unter der die relativen Pfade aufgeloest werden.
    asset_root: Path | None = field(default=None, repr=False)

    # -- Aufloesung ----------------------------------------------------
    def pfad(self, relativ: str) -> Path | None:
        """Absoluter Pfad zu einer Brandingdatei - oder None, wenn sie fehlt.

        Bewusst None statt einer Ausnahme: ein fehlendes Logo ist ein
        Schoenheitsfehler, kein Grund, die Anwendung nicht zu starten.
        """
        if self.asset_root is None:
            return None
        if Path(relativ).is_absolute():
            # Absolute Pfade sind ausgeschlossen: sie ueberleben den Wechsel
            # des Laufwerksbuchstabens nicht.
            log.warning("Brandingpfad muss relativ sein, war: %s", relativ)
            return None
        ziel = (self.asset_root / relativ).resolve()
        try:
            ziel.relative_to(self.asset_root.resolve())
        except ValueError:
            log.warning("Brandingpfad zeigt aus dem Assetbereich heraus: %s", relativ)
            return None
        return ziel if ziel.is_file() else None

    @property
    def logo_pfad(self) -> Path | None:
        return self.pfad(self.logo)

    @property
    def icon_pfad(self) -> Path | None:
        return self.pfad(self.icon)

    @property
    def original_pfad(self) -> Path | None:
        return self.pfad(ORIGINAL_DATEI)

    def variante(self, name: str) -> Path | None:
        return self.pfad(VARIANTEN[name]) if name in VARIANTEN else None

    # -- Titel ---------------------------------------------------------
    def titel(self, profilname: str = "") -> str:
        """``PORTIVA - Buchhalter``; ohne Profil nur ``PORTIVA``."""
        profilname = (profilname or "").strip()
        return f"{self.name}{TRENNER}{profilname}" if profilname else self.name

    def fehlende_dateien(self) -> list[str]:
        """Welche Brandingdateien fehlen? Fuer die Systempruefung."""
        return [rel for rel in VARIANTEN.values() if self.pfad(rel) is None]


def _bundle_assets() -> Path | None:
    """Assetordner im Innenleben einer gepackten EXE, falls vorhanden.

    PyInstaller entpackt mitgelieferte Datendateien nach ``sys._MEIPASS``
    (bei onedir: der Unterordner ``_internal``). Die Anwendung loest ihre
    Pfade sonst von der portablen Wurzel aus auf - das ist richtig so, denn
    der Betreiber soll das Logo austauschen koennen, ohne neu zu bauen.
    Diese Funktion ist nur der Rueckfall, falls neben der EXE nichts liegt.
    """
    import sys

    basis = getattr(sys, "_MEIPASS", None)
    if not basis:
        return None
    ordner = Path(basis) / "assets"
    return ordner if ordner.is_dir() else None


def load_brand(paths, config=None) -> Brand:
    """Laedt die Markenangaben.

    Reihenfolge: ``config/brand.json`` auf dem Datentraeger, sonst die
    Vorgaben aus diesem Modul. Der Markenname laesst sich damit nicht
    versehentlich durch ein Berufsprofil ueberschreiben - Marke und Profil
    bleiben getrennt.
    """
    asset_root = paths.get("assets")
    # Liegt neben der EXE kein Branding, im Paket aber schon, dann von dort.
    if not (asset_root / BRANDING_DIR).is_dir():
        ersatz = _bundle_assets()
        if ersatz is not None:
            log.info("Branding aus dem Programmpaket geladen: %s", ersatz)
            asset_root = ersatz
    brand = Brand(asset_root=asset_root)

    datei = paths.get("config") / "brand.json"
    if datei.is_file():
        try:
            daten = json.loads(datei.read_text(encoding="utf-8"))
            marke = daten.get("brand", daten)
            brand.name = str(marke.get("name", brand.name)) or MARKE
            brand.claim = str(marke.get("claim", brand.claim))
            brand.logo = str(marke.get("logo", brand.logo))
            brand.icon = str(marke.get("icon", brand.icon))
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            log.warning("brand.json nicht lesbar (%s) - Vorgaben werden verwendet", exc)
    return brand


def profilname(profile) -> str:
    """Der Anzeigename des Berufsprofils - nie fest im Code.

    Bevorzugt ``short_name`` (``Buchhalter``), sonst ``name``, sonst die
    Profilkennung. So heisst das Fenster nach einem Profilwechsel
    automatisch anders, ohne Programmaenderung.
    """
    for feld in ("short_name", "display_name", "name", "profile_id"):
        wert = getattr(profile, feld, None)
        if isinstance(wert, str) and wert.strip():
            return wert.strip()
    daten = getattr(profile, "data", None)
    if isinstance(daten, dict):
        for feld in ("short_name", "display_name", "name", "profile_id"):
            wert = daten.get(feld)
            if isinstance(wert, str) and wert.strip():
                return wert.strip()
    return ""
