"""Plugins installieren, aktivieren, laden, entfernen (E5.99, 112, 113, 117).

Ablauf einer Installation - genau die Reihenfolge aus E5.123:

    PAKET PRUEFEN -> BERECHTIGUNGEN ZEIGEN -> BENUTZER BESTAETIGT
    -> INSTALLIEREN -> AKTIVIEREN -> KI HAT EINE NEUE FAEHIGKEIT

Ohne Bestaetigung wird nichts installiert. Das ist kein Formalismus: ein
Plugin laeuft mit den Rechten der Anwendung, also muss der Mensch vorher
sehen, was es verlangt.

Ablage: der Code liegt unter ``plugins/<kennung>/`` in der Wurzel der
Installation - er ist fuer alle Kundenbereiche derselbe. **Aktiviert** wird
je Kundenbereich,
und die Daten eines Plugins liegen im Kundenbereich. Damit kann ein Plugin
im Bereich von Kunde A nicht an die Daten von Kunde B (Abschnitt 61,
E5.120).
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..logging_setup import get_logger
from . import paket as paketmodul
from .kontext import Pluginkontext, Werkzeug
from .modell import API_VERSION, BERECHTIGUNGEN, Manifest, PluginFehler

log = get_logger(__name__)

ZUSTAND = "zustand.json"


@dataclass
class Pluginstand:
    """Was die Anwendung ueber ein installiertes Plugin weiss."""

    manifest: Manifest
    ordner: Path
    aktiv: bool = False
    signiert: bool = False
    signatur_gueltig: bool = False
    erteilte_rechte: list[str] = field(default_factory=list)
    installiert_am: str = ""
    fehler: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.manifest.id, "name": self.manifest.name,
            "version": self.manifest.version, "kategorie": self.manifest.kategorie,
            "beschreibung": self.manifest.beschreibung, "autor": self.manifest.autor,
            "aktiv": self.aktiv, "signiert": self.signiert,
            "signatur_gueltig": self.signatur_gueltig,
            "berechtigungen": sorted(self.erteilte_rechte),
            "verlangt": sorted(self.manifest.berechtigungen),
            "installiert_am": self.installiert_am, "fehler": self.fehler,
        }


class Pluginverwaltung:
    """Verwaltet die installierten Plugins einer Installation."""

    def __init__(self, paths, config=None, audit=None, memory=None, knowledge=None,
                 artefakte=None, oeffentlicher_schluessel: bytes = b""):
        self.paths = paths
        self.config = config
        self.audit = audit
        self.memory = memory
        self.knowledge = knowledge
        self.artefakte = artefakte
        self.oeffentlicher_schluessel = oeffentlicher_schluessel
        self.geladen: dict[str, Pluginkontext] = {}

    # -- Orte ----------------------------------------------------------
    @property
    def ordner(self) -> Path:
        return self.paths.get("plugins")

    def plugin_ordner(self, kennung: str) -> Path:
        return self.ordner / kennung

    def datenordner(self, kennung: str) -> Path:
        """Daten eines Plugins - im Kundenbereich, getrennt je Kunde."""
        return self.paths.get("workspace") / "plugins" / kennung

    # -- Bestand -------------------------------------------------------
    def liste(self) -> list[Pluginstand]:
        staende: list[Pluginstand] = []
        if not self.ordner.is_dir():
            return staende
        for eintrag in sorted(self.ordner.iterdir()):
            if not eintrag.is_dir():
                continue
            stand = self._stand_lesen(eintrag)
            if stand is not None:
                staende.append(stand)
        return staende

    def stand(self, kennung: str) -> Pluginstand | None:
        for eintrag in self.liste():
            if eintrag.manifest.id == kennung:
                return eintrag
        return None

    def _stand_lesen(self, ordner: Path) -> Pluginstand | None:
        datei = ordner / paketmodul.MANIFEST
        if not datei.is_file():
            return None
        try:
            manifest = Manifest.from_dict(json.loads(datei.read_text(encoding="utf-8")))
        except (PluginFehler, json.JSONDecodeError) as fehler:
            log.warning("Plugin in %s ist unbrauchbar: %s", ordner, fehler)
            return None
        zustand = {}
        zustandsdatei = ordner / ZUSTAND
        if zustandsdatei.is_file():
            try:
                zustand = json.loads(zustandsdatei.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                zustand = {}
        return Pluginstand(
            manifest=manifest, ordner=ordner,
            aktiv=bool(zustand.get("aktiv", False)),
            signiert=bool(zustand.get("signiert", False)),
            signatur_gueltig=bool(zustand.get("signatur_gueltig", False)),
            erteilte_rechte=list(zustand.get("erteilte_rechte", [])),
            installiert_am=str(zustand.get("installiert_am", "")),
        )

    def _zustand_schreiben(self, stand: Pluginstand) -> None:
        (stand.ordner / ZUSTAND).write_text(json.dumps({
            "aktiv": stand.aktiv, "signiert": stand.signiert,
            "signatur_gueltig": stand.signatur_gueltig,
            "erteilte_rechte": sorted(stand.erteilte_rechte),
            "installiert_am": stand.installiert_am,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    # -- Installieren --------------------------------------------------
    def pruefen(self, paket: Path) -> paketmodul.Paketpruefung:
        """Prueft ein Paket, ohne etwas zu installieren (E5.117)."""
        pruefung = paketmodul.pruefen(Path(paket), self.oeffentlicher_schluessel)
        if pruefung.manifest.api != API_VERSION:
            raise PluginFehler(
                f"Das Plugin ist fuer die Schnittstellenfassung {pruefung.manifest.api} "
                f"gebaut, diese Anwendung bietet {API_VERSION}. Es wird nicht geladen."
            )
        return pruefung

    def installieren(self, paket: Path, bestaetigt: bool = False,
                     rechte: list[str] | None = None) -> Pluginstand:
        """Installiert ein geprueftes Paket - nur nach Bestaetigung."""
        pruefung = self.pruefen(Path(paket))
        manifest = pruefung.manifest
        if not bestaetigt:
            raise PluginFehler(
                "Vor der Installation muss bestaetigt werden, dass das Plugin die "
                "verlangten Berechtigungen bekommen soll: "
                + (", ".join(manifest.berechtigungen) or "keine")
            )
        erteilt = sorted(set(rechte if rechte is not None else manifest.berechtigungen))
        zuviel = [r for r in erteilt if r not in manifest.berechtigungen]
        if zuviel:
            raise PluginFehler(
                "Es sollen Rechte erteilt werden, die das Plugin gar nicht verlangt: "
                + ", ".join(zuviel)
            )

        fehlende = [p for p in manifest.benoetigt_plugins if self.stand(p) is None]
        if fehlende:
            raise PluginFehler(
                "Diese Plugins werden vorausgesetzt, fehlen aber: " + ", ".join(fehlende)
            )

        ziel = self.plugin_ordner(manifest.id)
        vorher = self.stand(manifest.id)
        if ziel.exists():
            shutil.rmtree(ziel)                 # Aktualisierung: E5.112
        ziel.mkdir(parents=True)

        _, _, dateien = paketmodul.lesen(Path(paket))
        for name, inhalt in dateien.items():
            datei = ziel / name
            datei.parent.mkdir(parents=True, exist_ok=True)
            datei.write_bytes(inhalt)
        (ziel / paketmodul.MANIFEST).write_text(
            json.dumps(manifest.as_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        from ..db import utc_now

        stand = Pluginstand(
            manifest=manifest, ordner=ziel, aktiv=False,
            signiert=pruefung.signiert, signatur_gueltig=pruefung.signatur_gueltig,
            erteilte_rechte=erteilt, installiert_am=utc_now(),
        )
        self._zustand_schreiben(stand)
        self._melden("plugin_installiert", manifest.id,
                     version=manifest.version, rechte=erteilt,
                     signiert=pruefung.signiert,
                     ersetzt=bool(vorher))
        log.info("Plugin installiert: %s %s", manifest.id, manifest.version)
        return stand

    def entfernen(self, kennung: str, daten_behalten: bool = True) -> None:
        """Entfernt ein Plugin (E5.113).

        Die Daten des Plugins bleiben standardmaessig erhalten - sie gehoeren
        dem Kunden, nicht dem Plugin.
        """
        stand = self.stand(kennung)
        if stand is None:
            raise PluginFehler(f"Es ist kein Plugin '{kennung}' installiert.")
        self.deaktivieren(kennung)
        shutil.rmtree(stand.ordner, ignore_errors=True)
        if not daten_behalten:
            shutil.rmtree(self.datenordner(kennung), ignore_errors=True)
        self._melden("plugin_entfernt", kennung, daten_behalten=daten_behalten)

    # -- Aktivieren ----------------------------------------------------
    def aktivieren(self, kennung: str) -> Pluginstand:
        stand = self.stand(kennung)
        if stand is None:
            raise PluginFehler(f"Es ist kein Plugin '{kennung}' installiert.")
        stand.aktiv = True
        self._zustand_schreiben(stand)
        self._melden("plugin_aktiviert", kennung)
        return stand

    def deaktivieren(self, kennung: str) -> Pluginstand | None:
        stand = self.stand(kennung)
        if stand is None:
            return None
        stand.aktiv = False
        self._zustand_schreiben(stand)
        self.geladen.pop(kennung, None)
        self._melden("plugin_deaktiviert", kennung)
        return stand

    # -- Laden ---------------------------------------------------------
    def laden(self, netz_erlaubt: bool = False) -> list[Pluginstand]:
        """Laedt alle aktiven Plugins. Ein Fehler haelt nur das Plugin auf."""
        geladen: list[Pluginstand] = []
        for stand in self.liste():
            if not stand.aktiv:
                continue
            try:
                self._laden(stand, netz_erlaubt)
                geladen.append(stand)
            except Exception as fehler:             # ein Plugin darf nie den Start verhindern
                stand.fehler = str(fehler)
                stand.aktiv = False
                self._zustand_schreiben(stand)
                log.error("Plugin %s konnte nicht geladen werden: %s",
                          stand.manifest.id, fehler)
                self._melden("plugin_ladefehler", stand.manifest.id,
                             status="fehler", grund=str(fehler))
                geladen.append(stand)
        return geladen

    def _laden(self, stand: Pluginstand, netz_erlaubt: bool) -> Pluginkontext:
        manifest = stand.manifest
        datei = stand.ordner / f"{manifest.modul}.py"
        if not datei.is_file():
            raise PluginFehler(f"Die Einstiegsdatei {datei.name} fehlt.")

        datenordner = self.datenordner(manifest.id)
        datenordner.mkdir(parents=True, exist_ok=True)
        kontext = Pluginkontext(
            manifest=manifest,
            berechtigungen=frozenset(stand.erteilte_rechte),
            datenordner=datenordner,
            _memory=self.memory, _knowledge=self.knowledge, _audit=self.audit,
            _artefakte=self.artefakte,
            _netz_erlaubt=bool(netz_erlaubt and "NETWORK_ACCESS" in stand.erteilte_rechte),
        )

        name = f"kim_plugin_{manifest.id}"
        spezifikation = importlib.util.spec_from_file_location(name, datei)
        if spezifikation is None or spezifikation.loader is None:
            raise PluginFehler(f"Das Modul {datei.name} laesst sich nicht laden.")
        modul = importlib.util.module_from_spec(spezifikation)
        sys.modules[name] = modul
        try:
            spezifikation.loader.exec_module(modul)
        except Exception as fehler:
            sys.modules.pop(name, None)
            raise PluginFehler(f"Beim Laden ist ein Fehler aufgetreten: {fehler}") from fehler

        einstieg = getattr(modul, manifest.funktion, None)
        if not callable(einstieg):
            raise PluginFehler(
                f"Im Modul {manifest.modul} gibt es keine Funktion "
                f"'{manifest.funktion}'."
            )
        einstieg(kontext)
        self.geladen[manifest.id] = kontext
        self._melden("plugin_geladen", manifest.id,
                     werkzeuge=[w.name for w in kontext.werkzeuge])
        return kontext

    # -- Auskunft ------------------------------------------------------
    def werkzeuge(self) -> list[Werkzeug]:
        return [w for kontext in self.geladen.values() for w in kontext.werkzeuge]

    def rechtebeschreibung(self, rechte) -> list[str]:
        return [f"{recht}: {BERECHTIGUNGEN.get(recht, 'unbekannt')}" for recht in rechte]

    def _melden(self, aktion: str, kennung: str, status: str = "ok", **angaben: Any) -> None:
        if self.audit is None:
            return
        try:
            self.audit.record(aktion, "plugin", kennung, status=status, **angaben)
        except Exception as fehler:
            log.debug("Plugin-Vorgang nicht protokolliert: %s", fehler)
