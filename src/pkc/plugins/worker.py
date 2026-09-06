"""Der Vorgang, in dem ein Plugin laeuft (E5.108).

Dieses Modul wird **nicht** von der Anwendung importiert, sondern in einem
eigenen Vorgang gestartet. Es laedt genau ein Plugin und wartet auf
Auftraege.

Der Unterschied zu vorher ist nicht kosmetisch: dieser Vorgang hat keine
Datenbankverbindung, keinen Tresor, keine Objekte der Anwendung. Er kann
nur fragen. Was er darf, entscheidet die Anwendung im anderen Vorgang.

Was das **nicht** leistet: eine Beschraenkung durch das Betriebssystem. Der
Vorgang laeuft mit denselben Benutzerrechten wie die Anwendung und koennte
Dateien oeffnen, die dem Benutzer gehoeren. Naeheres in PLUGIN_KONZEPT.md.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any

from . import protokoll
from .modell import BerechtigungFehlt, Manifest


class Fernkontext:
    """Was ein Plugin sieht - jeder Zugriff geht ueber die Leitung.

    Nach aussen bietet er dieselben Funktionen wie der Kontext im selben
    Vorgang. Innen ruft er nichts selbst auf, sondern fragt die Anwendung.
    """

    def __init__(self, manifest: Manifest, berechtigungen: list[str],
                 datenordner: str, bruecke: "Bruecke"):
        self.manifest = manifest
        self.berechtigungen = frozenset(berechtigungen)
        self.datenordner = Path(datenordner)
        self._bruecke = bruecke
        self.werkzeuge: list[dict] = []
        self.formate: list[dict] = []
        self._funktionen: dict[str, Any] = {}
        self._schreiber: dict[str, Any] = {}

    # -- Anmeldungen ---------------------------------------------------
    def werkzeug_anmelden(self, name: str, beschreibung: str, funktion):
        self._funktionen[name] = funktion
        self.werkzeuge.append({"name": name, "beschreibung": beschreibung})
        return funktion

    def dateiformat_anmelden(self, schreiber) -> None:
        self._schreiber[schreiber.kuerzel] = schreiber
        # Die Anwendung braucht die Angaben zum Format, um es in ihrer
        # eigenen Auswahl zu fuehren - die Datei selbst entsteht drueben.
        self.formate.append({
            "kuerzel": schreiber.kuerzel, "endung": schreiber.endung,
            "bezeichnung": schreiber.bezeichnung, "zweck": schreiber.zweck,
        })

    def darf(self, recht: str) -> bool:
        return recht in self.berechtigungen

    def _verlangt(self, recht: str) -> None:
        if recht not in self.berechtigungen:
            raise BerechtigungFehlt(
                f"Das Plugin '{self.manifest.id}' hat versucht, '{recht}' zu "
                "nutzen. Diese Berechtigung wurde nicht erteilt."
            )

    # -- Zugriffe ueber die Anwendung ----------------------------------
    def gedaechtnis_lesen(self, schluessel: str):
        self._verlangt("COMPANY_MEMORY_READ")
        return self._bruecke.anfragen("gedaechtnis_lesen", {"schluessel": schluessel})

    def gedaechtnis_liste(self, limit: int = 100):
        self._verlangt("COMPANY_MEMORY_READ")
        return self._bruecke.anfragen("gedaechtnis_liste", {"limit": limit})

    def gedaechtnis_schreiben(self, schluessel: str, titel: str, inhalt: str,
                              kategorie: str = "") -> None:
        self._verlangt("COMPANY_MEMORY_WRITE")
        self._bruecke.anfragen("gedaechtnis_schreiben", {
            "schluessel": schluessel, "titel": titel,
            "inhalt": inhalt, "kategorie": kategorie,
        })

    def wissen_suchen(self, frage: str, limit: int = 8):
        self._verlangt("KNOWLEDGE_READ")
        return self._bruecke.anfragen("wissen_suchen", {"frage": frage, "limit": limit})

    def datei_lesen(self, name: str) -> bytes:
        self._verlangt("FILE_READ")
        return protokoll.bytes_heraus(
            self._bruecke.anfragen("datei_lesen", {"name": name}))

    def datei_schreiben(self, name: str, inhalt) -> Path:
        self._verlangt("FILE_WRITE")
        if isinstance(inhalt, str):
            inhalt = inhalt.encode("utf-8")
        ziel = self._bruecke.anfragen("datei_schreiben", {
            "name": name, "inhalt": protokoll.bytes_hinein(inhalt)})
        return Path(ziel)

    def artefakt_erzeugen(self, inhalt, format: str, name: str = ""):
        self._verlangt("FILE_WRITE")
        if not isinstance(inhalt, str):
            inhalt = str(inhalt)
        return self._bruecke.anfragen("artefakt_erzeugen", {
            "inhalt": inhalt, "format": format, "name": name})

    def netz_abrufen(self, adresse: str, zeitgrenze: float = 30.0) -> bytes:
        self._verlangt("NETWORK_ACCESS")
        return protokoll.bytes_heraus(self._bruecke.anfragen(
            "netz_abrufen", {"adresse": adresse, "zeitgrenze": zeitgrenze}))

    def protokollieren(self, aktion: str, gegenstand: str = "", **angaben) -> None:
        self._bruecke.anfragen("protokollieren", {
            "aktion": aktion, "gegenstand": gegenstand,
            "angaben": protokoll.einfach(angaben)})


class Bruecke:
    """Die Leitung zur Anwendung."""

    def __init__(self, eingang, ausgang):
        self.eingang = eingang
        self.ausgang = ausgang
        self._zaehler = 0

    def anfragen(self, funktion: str, argumente: dict):
        """Fragt die Anwendung und wartet auf ihre Antwort."""
        self._zaehler += 1
        kennung = self._zaehler
        protokoll.schreiben(self.ausgang, {
            "art": "anfrage", "id": kennung, "funktion": funktion,
            "argumente": protokoll.einfach(argumente),
        })
        while True:
            nachricht = protokoll.lesen(self.eingang)
            if nachricht is None:
                raise RuntimeError("Die Anwendung hat die Verbindung beendet.")
            if nachricht.get("art") == "antwort" and nachricht.get("id") == kennung:
                if nachricht.get("fehler"):
                    raise BerechtigungFehlt(str(nachricht["fehler"]))
                return nachricht.get("wert")
            # Andere Nachrichten sind hier nicht vorgesehen; sie zu
            # uebergehen ist besser, als den Vorgang abzubrechen.


def _laden(ordner: Path, manifest: Manifest, kontext: Fernkontext) -> None:
    """Importiert das Plugin und ruft seinen Einstieg auf."""
    import importlib.util

    datei = ordner / f"{manifest.modul}.py"
    spezifikation = importlib.util.spec_from_file_location(
        f"kim_plugin_{manifest.id}", datei)
    if spezifikation is None or spezifikation.loader is None:
        raise RuntimeError(f"Das Modul {datei.name} laesst sich nicht laden.")
    modul = importlib.util.module_from_spec(spezifikation)
    sys.modules[spezifikation.name] = modul
    spezifikation.loader.exec_module(modul)

    einstieg = getattr(modul, manifest.funktion, None)
    if not callable(einstieg):
        raise RuntimeError(
            f"Im Modul {manifest.modul} gibt es keine Funktion '{manifest.funktion}'.")
    einstieg(kontext)


def hauptschleife(eingang=None, ausgang=None) -> int:
    """Nimmt Auftraege entgegen, bis die Anwendung Schluss sagt."""
    eingang = eingang or sys.stdin
    ausgang = ausgang or sys.stdout
    # Alles, was das Plugin selbst ausgibt, darf die Leitung nicht stoeren.
    sys.stdout = sys.stderr

    bruecke = Bruecke(eingang, ausgang)
    kontext: Fernkontext | None = None

    while True:
        try:
            auftrag = protokoll.lesen(eingang)
        except protokoll.ProtokollFehler as fehler:
            protokoll.schreiben(ausgang, {"art": "fehler", "id": 0,
                                          "meldung": str(fehler)})
            continue
        if auftrag is None or auftrag.get("art") == "ende":
            return 0

        kennung = auftrag.get("id", 0)
        try:
            if auftrag["art"] == "anmelden":
                manifest = Manifest.from_dict(auftrag["manifest"])
                kontext = Fernkontext(
                    manifest, auftrag.get("berechtigungen", []),
                    auftrag.get("datenordner", "."), bruecke,
                )
                _laden(Path(auftrag["ordner"]), manifest, kontext)
                protokoll.schreiben(ausgang, {
                    "art": "ergebnis", "id": kennung,
                    "wert": {"werkzeuge": kontext.werkzeuge,
                             "formate": kontext.formate},
                })
            elif auftrag["art"] == "werkzeug":
                if kontext is None:
                    raise RuntimeError("Das Plugin wurde noch nicht geladen.")
                funktion = kontext._funktionen.get(auftrag["name"])
                if funktion is None:
                    raise RuntimeError(f"Unbekanntes Werkzeug: {auftrag['name']}")
                wert = funktion(*auftrag.get("argumente", []),
                                **auftrag.get("schluessel", {}))
                protokoll.schreiben(ausgang, {"art": "ergebnis", "id": kennung,
                                              "wert": protokoll.einfach(wert)})
            elif auftrag["art"] == "format":
                if kontext is None:
                    raise RuntimeError("Das Plugin wurde noch nicht geladen.")
                schreiber = kontext._schreiber.get(auftrag["kuerzel"])
                if schreiber is None:
                    raise RuntimeError(f"Unbekanntes Format: {auftrag['kuerzel']}")
                dokument = protokoll.dokument_heraus(auftrag["dokument"])
                inhalt = schreiber.funktion(dokument)
                protokoll.schreiben(ausgang, {
                    "art": "ergebnis", "id": kennung,
                    "wert": protokoll.bytes_hinein(bytes(inhalt)),
                })
            else:
                raise RuntimeError(f"Unbekannter Auftrag: {auftrag.get('art')}")
        except Exception as fehler:
            protokoll.schreiben(ausgang, {
                "art": "fehler", "id": kennung, "meldung": str(fehler),
                "einzelheiten": traceback.format_exc(limit=4),
            })


def main(argv: list[str] | None = None) -> int:      # pragma: no cover - Einstieg
    return hauptschleife()


if __name__ == "__main__":                            # pragma: no cover
    raise SystemExit(main())
