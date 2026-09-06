"""Die Artefakt-Engine: Dateien erzeugen, benennen, ablegen, verzeichnen.

Erweiterung E4 verlangt vom Kern nicht nur das Schreiben einer Datei,
sondern den ganzen Vorgang: Dateiname, Speicherort, Versionierung,
Metadaten, Ueberschreibschutz, sichere Speicherung, Export und
Fehlerbehandlung. Das steht hier an einer Stelle - die Formatschreiber
kuemmern sich nur um Bytes.

Zwei Festlegungen, die aus dem uebrigen Auftrag folgen:

* Erzeugte Dateien sind **Kundendaten**. Sie liegen unter
  ``workspace/artefakte`` und damit im Kundenbereich (Abschnitt 61) - nie
  im Programmordner und nie auf dem Host-PC (Abschnitt 20).
* Nichts wird stillschweigend ueberschrieben. Gibt es die Datei schon,
  entsteht eine neue Fassung mit hochgezaehlter Nummer; nur auf
  ausdrueckliche Anweisung wird ersetzt.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..logging_setup import get_logger
from .modell import Dokument, aus_markdown
from .schreiber import ArtefaktFehler, Schreiber, formate, hole

log = get_logger(__name__)

#: Verzeichnisdatei neben den Artefakten - eine Zeile je erzeugter Datei.
VERZEICHNIS = "verzeichnis.jsonl"

#: Unter Windows belegte Dateinamen. Ein Artefakt "CON.pdf" waere auf dem
#: Zieldatentraeger nicht anlegbar - der Fehler kaeme erst beim Kunden.
_GESPERRT = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{n}" for n in range(1, 10)),
    *(f"LPT{n}" for n in range(1, 10)),
}
_UNZULAESSIG = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def dateiname(vorschlag: str, standard: str = "artefakt") -> str:
    """Macht aus einem Titel einen Dateinamen, der auf jedem System traegt."""
    roh = unicodedata.normalize("NFKD", vorschlag or "")
    roh = roh.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    roh = "".join(z for z in roh if not unicodedata.combining(z))
    roh = _UNZULAESSIG.sub(" ", roh)
    roh = re.sub(r"\s+", "_", roh.strip()).strip("._")
    roh = roh[:80].rstrip("._")
    if not roh or roh.upper().split(".")[0] in _GESPERRT:
        roh = standard
    return roh


@dataclass
class Artefakt:
    """Eine erzeugte Datei mit ihren Angaben."""

    pfad: Path
    format: str
    name: str
    version: int
    groesse: int
    pruefsumme: str
    erzeugt: str
    metadaten: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "pfad": str(self.pfad), "format": self.format, "name": self.name,
            "version": self.version, "groesse": self.groesse,
            "pruefsumme": self.pruefsumme, "erzeugt": self.erzeugt,
            "metadaten": self.metadaten,
        }


class Artefaktwerk:
    """Erzeugt Dateien aus einem Dokument."""

    def __init__(self, paths, audit=None, profil: str = "", marke: str = "PORTIVA"):
        self.paths = paths
        self.audit = audit
        self.profil = profil
        self.marke = marke

    # -- Auskunft ------------------------------------------------------
    @property
    def ordner(self) -> Path:
        return self.paths.get("artefakte")

    def formate(self) -> list[dict]:
        return [
            {"format": s.kuerzel, "endung": s.endung,
             "bezeichnung": s.bezeichnung, "zweck": s.zweck}
            for s in formate()
        ]

    # -- Erzeugen ------------------------------------------------------
    def erzeugen(
        self,
        dokument: Dokument | str,
        format: str,
        name: str = "",
        *,
        unterordner: str = "",
        ueberschreiben: bool = False,
        angaben: dict | None = None,
    ) -> Artefakt:
        """Schreibt das Dokument als Datei und traegt sie ins Verzeichnis ein."""
        if isinstance(dokument, str):
            dokument = aus_markdown(dokument, titel=name or "")
        schreiber = hole(format)
        dokument.angaben = {
            "ersteller": f"{self.marke}{' - ' + self.profil if self.profil else ''}",
            **dokument.angaben, **(angaben or {}),
        }

        ziel_ordner = self.ordner
        if unterordner:
            teil = dateiname(unterordner, "ordner")
            ziel_ordner = ziel_ordner / teil
        ziel_ordner.mkdir(parents=True, exist_ok=True)

        grundname = dateiname(name or dokument.titel or "artefakt")
        ziel, version = self._freier_name(ziel_ordner, grundname, schreiber, ueberschreiben)

        try:
            inhalt = schreiber.funktion(dokument)
        except Exception as fehler:                     # defensiv: Formatfehler
            self._melden("artefakt_fehlgeschlagen", grundname, format, str(fehler))
            raise ArtefaktFehler(
                f"Die Datei konnte nicht erzeugt werden ({schreiber.bezeichnung}): {fehler}"
            ) from fehler

        # Erst vollstaendig schreiben, dann umbenennen: bricht der Vorgang ab,
        # entsteht keine halbe Datei, die wie ein fertiger Bericht aussieht.
        vorlaeufig = ziel.with_name(ziel.name + ".teil")
        try:
            vorlaeufig.write_bytes(inhalt)
            vorlaeufig.replace(ziel)
        except OSError as fehler:
            vorlaeufig.unlink(missing_ok=True)
            self._melden("artefakt_fehlgeschlagen", grundname, format, str(fehler))
            raise ArtefaktFehler(f"Die Datei konnte nicht gespeichert werden: {fehler}") from fehler

        artefakt = Artefakt(
            pfad=ziel, format=schreiber.kuerzel, name=ziel.name, version=version,
            groesse=len(inhalt), pruefsumme=hashlib.sha256(inhalt).hexdigest(),
            erzeugt=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            metadaten={"titel": dokument.titel, **dokument.angaben},
        )
        self._verzeichnen(artefakt)
        self._melden("artefakt_erzeugt", artefakt.name, artefakt.format, "")
        log.info("Artefakt erzeugt: %s (%d Bytes)", ziel, artefakt.groesse)
        return artefakt

    def _freier_name(self, ordner: Path, grundname: str, schreiber: Schreiber,
                     ueberschreiben: bool) -> tuple[Path, int]:
        ziel = ordner / f"{grundname}{schreiber.endung}"
        if ueberschreiben or not ziel.exists():
            return ziel, 1
        version = 2
        while True:
            ziel = ordner / f"{grundname}_v{version}{schreiber.endung}"
            if not ziel.exists():
                return ziel, version
            version += 1

    # -- Verzeichnis ---------------------------------------------------
    def _verzeichnis_datei(self) -> Path:
        return self.ordner / VERZEICHNIS

    def _verzeichnen(self, artefakt: Artefakt) -> None:
        datei = self._verzeichnis_datei()
        datei.parent.mkdir(parents=True, exist_ok=True)
        eintrag = artefakt.as_dict()
        eintrag["pfad"] = str(artefakt.pfad.relative_to(self.ordner))
        with datei.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(eintrag, ensure_ascii=False) + "\n")

    def liste(self, limit: int = 50) -> list[dict]:
        """Die zuletzt erzeugten Dateien - neueste zuerst."""
        datei = self._verzeichnis_datei()
        if not datei.is_file():
            return []
        eintraege = []
        for zeile in datei.read_text(encoding="utf-8").splitlines():
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                eintrag = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            eintrag["vorhanden"] = (self.ordner / eintrag.get("pfad", "")).is_file()
            eintraege.append(eintrag)
        return list(reversed(eintraege))[:limit]

    def _melden(self, aktion: str, name: str, format: str, fehler: str) -> None:
        if self.audit is None:
            return
        try:
            self.audit.record(aktion, "artefakt", name,
                              status="fehler" if fehler else "ok",
                              format=format, **({"grund": fehler} if fehler else {}))
        except Exception as ausnahme:                   # Protokoll darf nie blockieren
            log.debug("Artefakt nicht protokolliert: %s", ausnahme)
