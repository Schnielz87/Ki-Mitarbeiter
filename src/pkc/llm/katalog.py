"""Bezugsquellen fuer Sprachmodelle - mit ehrlicher Kennzeichnung.

Der Auftrag (Abschnitt 14 der Erweiterung E6) verlangt einen gefuehrten Weg
zum Modell. Dafuer braucht die Anwendung Adressen. Zugleich gilt Abschnitt
42: keine Quelle behaupten, die nicht geprueft ist.

Beides zusammen geht so:

* Der Katalog liegt als Datei bei und ist ohne Programmaenderung zu pflegen.
* Jeder Eintrag traegt ein Feld ``pruefung``. Es wird **nicht** von Hand
  gesetzt, sondern vom Windows-Bauablauf, der die Adresse tatsaechlich
  abruft und die Pruefsumme bildet.
* Ein Eintrag ohne bestaetigte Pruefung wird der Anwendung gegenueber als
  ungeprueft ausgewiesen, und die Anwendung sagt das dem Benutzer, bevor
  etwas geladen wird.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..logging_setup import get_logger

log = get_logger(__name__)

KATALOGDATEI = "model_catalog.json"


@dataclass
class Modellquelle:
    """Ein Eintrag des Katalogs."""

    id: str
    profil: str
    name: str
    lizenz: str
    herkunft: str
    url: str
    datei: str
    groesse_gb: float = 0.0
    min_ram_gb: int = 0
    hinweis: str = ""
    produktiv: bool = True
    pruefung: dict = field(default_factory=dict)

    # -- Pruefstand ----------------------------------------------------
    @property
    def geprueft(self) -> bool:
        """Wurde die Adresse tatsaechlich abgerufen?"""
        return bool(self.pruefung.get("erreichbar")) and bool(self.pruefung.get("geprueft_am"))

    @property
    def sha256(self) -> str:
        """Nur eine im Bauablauf gebildete Pruefsumme zaehlt."""
        return str(self.pruefung.get("sha256", "") or "")

    @property
    def pruefstand(self) -> str:
        if not self.geprueft:
            return "nicht geprueft"
        teile = [f"Adresse geprueft am {self.pruefung.get('geprueft_am')}"]
        if self.sha256:
            teile.append("Pruefsumme liegt vor")
        else:
            teile.append("ohne Pruefsumme - die Datei wird beim Laden nicht auf "
                         "Unversehrtheit geprueft")
        return ", ".join(teile)

    def as_dict(self) -> dict:
        return {
            "id": self.id, "profil": self.profil, "name": self.name,
            "lizenz": self.lizenz, "herkunft": self.herkunft, "url": self.url,
            "datei": self.datei, "groesse_gb": self.groesse_gb,
            "min_ram_gb": self.min_ram_gb, "hinweis": self.hinweis,
            "produktiv": self.produktiv, "geprueft": self.geprueft,
            "sha256": self.sha256, "pruefstand": self.pruefstand,
        }


@dataclass
class Katalog:
    quellen: list[Modellquelle] = field(default_factory=list)
    stand: str = ""
    fehler: str = ""

    def __len__(self) -> int:
        return len(self.quellen)

    def __iter__(self):
        return iter(self.quellen)

    def fuer_profil(self, profil: str) -> Modellquelle | None:
        for quelle in self.quellen:
            if quelle.profil == profil:
                return quelle
        return None

    def nach_id(self, kennung: str) -> Modellquelle | None:
        kennung = (kennung or "").strip().lower()
        for quelle in self.quellen:
            if quelle.id.lower() == kennung:
                return quelle
        return None

    def waehlen(self, wunsch: str) -> Modellquelle | None:
        """Nimmt eine Kennung oder ein Profil - beides ist gebraeuchlich."""
        return self.nach_id(wunsch) or self.fuer_profil((wunsch or "").strip().lower())

    @property
    def produktiv(self) -> list[Modellquelle]:
        return [q for q in self.quellen if q.produktiv]


def laden(config_dir: Path) -> Katalog:
    """Liest den Katalog. Ein fehlender Katalog ist kein Startproblem."""
    pfad = Path(config_dir) / KATALOGDATEI
    if not pfad.is_file():
        return Katalog(fehler=f"Der Modellkatalog fehlt: {pfad}")
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as fehler:
        log.warning("Modellkatalog nicht lesbar: %s", fehler)
        return Katalog(fehler=f"Der Modellkatalog ist nicht lesbar: {fehler}")

    quellen: list[Modellquelle] = []
    for eintrag in daten.get("modelle", []):
        try:
            quellen.append(Modellquelle(
                id=str(eintrag["id"]), profil=str(eintrag.get("profil", "")),
                name=str(eintrag.get("name", eintrag["id"])),
                lizenz=str(eintrag.get("lizenz", "unbekannt")),
                herkunft=str(eintrag.get("herkunft", "")),
                url=str(eintrag.get("url", "")),
                datei=str(eintrag.get("datei", "")),
                groesse_gb=float(eintrag.get("groesse_gb", 0) or 0),
                min_ram_gb=int(eintrag.get("min_ram_gb", 0) or 0),
                hinweis=str(eintrag.get("hinweis", "")),
                produktiv=bool(eintrag.get("produktiv", True)),
                pruefung=dict(eintrag.get("pruefung", {}) or {}),
            ))
        except (KeyError, TypeError, ValueError) as fehler:
            log.warning("Katalogeintrag uebersprungen: %s", fehler)
    return Katalog(quellen=quellen, stand=str(daten.get("stand", "")))


def pruefung_eintragen(config_dir: Path, kennung: str, ergebnis: dict) -> bool:
    """Traegt ein Pruefergebnis in den Katalog ein (fuer den Bauablauf).

    Bewusst hier und nicht von Hand in der Datei: so ist die Herkunft der
    Angabe immer dieselbe, und es kann niemand versehentlich eine Pruefung
    behaupten, die nie stattgefunden hat.
    """
    pfad = Path(config_dir) / KATALOGDATEI
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    getroffen = False
    for eintrag in daten.get("modelle", []):
        if str(eintrag.get("id")) == kennung:
            eintrag["pruefung"] = ergebnis
            getroffen = True
    if getroffen:
        pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return getroffen
