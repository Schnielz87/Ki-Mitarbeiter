"""Der Vorlagenspeicher: aufnehmen, finden, aendern, entfernen.

Vorlagen liegen unter ``workspace/vorlagen`` und damit im Kundenbereich.
Das ist keine Formsache: eine Vorlage enthaelt Briefkopf, Anrede und
Formulierungen eines bestimmten Unternehmens. Sie hat bei einem anderen
Kunden nichts zu suchen (Abschnitt 61).

Jede Vorlage besteht aus zwei Teilen:

* dem **Rumpf** - eine Textdatei ``<kennung>.md`` im Vorlagenordner,
* dem **Eintrag** im Verzeichnis ``verzeichnis.json`` daneben.

Der Rumpf liegt bewusst als eigene, lesbare Datei da und nicht in einer
Datenbank. Wer eine Vorlage ausserhalb von PORTIVA anpassen oder
weitergeben will, kann das - portabel heisst auch, dass die Daten ohne
das Programm noch etwas wert sind.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from ..artefakte.werk import dateiname
from ..logging_setup import get_logger
from .modell import Vorlage

log = get_logger(__name__)

VERZEICHNIS = "verzeichnis.json"

#: Endungen, aus denen ein Vorlagenrumpf gelesen werden kann.
LESBAR = (".md", ".markdown", ".txt")


class VorlagenFehler(RuntimeError):
    """Etwas an der Vorlage stimmt nicht - mit einem Satz fuer den Menschen."""


class Vorlagenspeicher:
    """Verwaltet die Vorlagen eines Kundenbereichs."""

    def __init__(self, paths, audit=None):
        self.paths = paths
        self.audit = audit

    # -- Ort -----------------------------------------------------------
    @property
    def ordner(self) -> Path:
        return self.paths.get("vorlagen")

    def _verzeichnis_datei(self) -> Path:
        return self.ordner / VERZEICHNIS

    def _rumpf_datei(self, kennung: str) -> Path:
        """Loest den Rumpfpfad sicher auf.

        Die Kennung kommt aus dem Verzeichnis und damit aus einer Datei,
        die jemand von Hand geaendert haben kann. Ein Eintrag
        ``../../config/settings.json`` darf nicht dazu fuehren, dass
        ausserhalb des Vorlagenordners gelesen oder geschrieben wird.
        """
        ordner = self.ordner.resolve()
        ziel = (ordner / f"{kennung}.md").resolve()
        if ziel.parent != ordner:
            raise VorlagenFehler(f"Ausserhalb des Vorlagenordners: {kennung}")
        return ziel

    # -- Verzeichnis ---------------------------------------------------
    def _lesen(self) -> list[dict]:
        datei = self._verzeichnis_datei()
        if not datei.is_file():
            return []
        try:
            inhalt = json.loads(datei.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as fehler:
            # Ein beschaedigtes Verzeichnis darf den Bereich nicht
            # unbenutzbar machen. Die Rumpfdateien liegen noch da.
            log.warning("Vorlagenverzeichnis nicht lesbar: %s", fehler)
            return []
        return inhalt if isinstance(inhalt, list) else []

    def _schreiben(self, eintraege: list[dict]) -> None:
        datei = self._verzeichnis_datei()
        datei.parent.mkdir(parents=True, exist_ok=True)
        # Erst vollstaendig schreiben, dann umbenennen - sonst bleibt bei
        # einem Abbruch ein halbes Verzeichnis zurueck.
        vorlaeufig = datei.with_suffix(".json.teil")
        vorlaeufig.write_text(
            json.dumps(eintraege, ensure_ascii=False, indent=2),
            encoding="utf-8")
        vorlaeufig.replace(datei)

    # -- Auskunft ------------------------------------------------------
    def liste(self, kategorie: str = "", suche: str = "") -> list[Vorlage]:
        """Alle Vorlagen, nach Kategorie und Name geordnet."""
        vorlagen = []
        for eintrag in self._lesen():
            vorlage = self._aus_eintrag(eintrag)
            if vorlage is None:
                continue
            if kategorie and vorlage.kategorie != kategorie:
                continue
            if suche and not _passt(vorlage, suche):
                continue
            vorlagen.append(vorlage)
        return sorted(vorlagen, key=lambda v: (v.kategorie.lower(),
                                               v.name.lower()))

    def kategorien(self) -> list[str]:
        return sorted({v.kategorie for v in self.liste()}, key=str.lower)

    def holen(self, kennung: str) -> Vorlage | None:
        for eintrag in self._lesen():
            if eintrag.get("kennung") == kennung:
                return self._aus_eintrag(eintrag)
        return None

    def _aus_eintrag(self, eintrag: dict) -> Vorlage | None:
        kennung = eintrag.get("kennung") or ""
        if not kennung:
            return None
        try:
            datei = self._rumpf_datei(kennung)
        except VorlagenFehler as fehler:
            log.warning("Vorlage uebersprungen: %s", fehler)
            return None
        rumpf = ""
        if datei.is_file():
            try:
                rumpf = datei.read_text(encoding="utf-8")
            except OSError as fehler:                   # pragma: no cover
                log.warning("Vorlagenrumpf nicht lesbar: %s", fehler)
        return Vorlage(
            kennung=kennung,
            name=eintrag.get("name") or kennung,
            rumpf=rumpf,
            kategorie=eintrag.get("kategorie") or "Allgemein",
            beschreibung=eintrag.get("beschreibung") or "",
            format=eintrag.get("format") or "docx",
            herkunft=eintrag.get("herkunft") or "eigen",
            angelegt=eintrag.get("angelegt") or "",
        )

    # -- Aufnehmen -----------------------------------------------------
    def aufnehmen(self, name: str, rumpf: str, *, kategorie: str = "Allgemein",
                  beschreibung: str = "", format: str = "docx",
                  herkunft: str = "eigen",
                  kennung: str = "") -> Vorlage:
        """Nimmt eine Vorlage auf. Vorhandene gleicher Kennung wird ersetzt."""
        if not (name or "").strip():
            raise VorlagenFehler("Eine Vorlage braucht einen Namen.")
        if not (rumpf or "").strip():
            raise VorlagenFehler(
                "Die Vorlage ist leer. Eine leere Vorlage waere eine "
                "leere Datei mit einem Namen.")

        kennung = kennung or self._freie_kennung(name)
        datei = self._rumpf_datei(kennung)
        datei.parent.mkdir(parents=True, exist_ok=True)
        datei.write_text(rumpf, encoding="utf-8")

        vorlage = Vorlage(
            kennung=kennung, name=name.strip(), rumpf=rumpf,
            kategorie=(kategorie or "Allgemein").strip(),
            beschreibung=(beschreibung or "").strip(),
            format=(format or "docx").strip().lower(),
            herkunft=herkunft,
            angelegt=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        eintraege = [e for e in self._lesen() if e.get("kennung") != kennung]
        eintraege.append(vorlage.as_dict())
        self._schreiben(eintraege)
        self._melden("vorlage.aufgenommen", vorlage)
        log.info("Vorlage aufgenommen: %s (%s)", vorlage.name, kennung)
        return vorlage

    def aus_datei(self, pfad, *, name: str = "", kategorie: str = "",
                  beschreibung: str = "", format: str = "") -> Vorlage:
        """Nimmt eine vorhandene Textdatei als Vorlage auf.

        Word-, Excel- und PowerPoint-Dateien gehen hier ausdruecklich
        **nicht**. Das ist keine Nachlaessigkeit: aus einer .docx den
        Text herauszuloesen ist moeglich, aber das Ergebnis waere die
        Formatierung los - und eine Vorlage, die ihr Aussehen verliert,
        ist als Vorlage wertlos. Lieber ein klarer Satz als ein
        enttaeuschendes Ergebnis.
        """
        pfad = Path(pfad)
        if not pfad.is_file():
            raise VorlagenFehler(f"Die Datei gibt es nicht: {pfad}")
        if pfad.suffix.lower() not in LESBAR:
            raise VorlagenFehler(
                f"Aus {pfad.suffix or 'dieser Datei'} kann keine Vorlage "
                "werden. Lesbar sind Textdateien: "
                + ", ".join(LESBAR) + ". Wer eine Word-Vorlage uebernehmen "
                "will, kopiert ihren Text in eine solche Datei und setzt "
                "die Platzhalter in doppelte geschweifte Klammern.")
        try:
            roh = pfad.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise VorlagenFehler(
                "Die Datei ist nicht in UTF-8 geschrieben und laesst sich "
                "nicht zuverlaessig lesen.") from None

        kopf, rumpf = kopfzeilen_lesen(roh)
        return self.aufnehmen(
            name=name or kopf.get("name") or pfad.stem,
            rumpf=rumpf,
            kategorie=kategorie or kopf.get("kategorie") or "Allgemein",
            beschreibung=beschreibung or kopf.get("beschreibung") or "",
            format=format or kopf.get("format") or "docx",
            herkunft="eigen",
        )

    def _freie_kennung(self, name: str) -> str:
        grund = dateiname(name, "vorlage").lower()
        vorhanden = {e.get("kennung") for e in self._lesen()}
        if grund not in vorhanden:
            return grund
        nummer = 2
        while f"{grund}_{nummer}" in vorhanden:
            nummer += 1
        return f"{grund}_{nummer}"

    # -- Entfernen -----------------------------------------------------
    def entfernen(self, kennung: str) -> bool:
        """Entfernt eine eigene Vorlage. Mitgelieferte bleiben.

        Eine mitgelieferte Vorlage zu loeschen waere folgenlos: sie kaeme
        beim naechsten Start wieder. Ein Knopf, dessen Wirkung nicht
        haelt, ist schlimmer als keiner.
        """
        vorlage = self.holen(kennung)
        if vorlage is None:
            return False
        if vorlage.herkunft == "mitgeliefert":
            raise VorlagenFehler(
                f"„{vorlage.name}“ ist eine mitgelieferte Vorlage. "
                "Sie laesst sich nicht entfernen - beim naechsten Start "
                "waere sie wieder da. Eine eigene Fassung anlegen und "
                "diese benutzen geht jederzeit.")
        self._rumpf_datei(kennung).unlink(missing_ok=True)
        self._schreiben([e for e in self._lesen()
                         if e.get("kennung") != kennung])
        self._melden("vorlage.entfernt", vorlage)
        return True

    # -- Protokoll -----------------------------------------------------
    def _melden(self, aktion: str, vorlage: Vorlage) -> None:
        if self.audit is None:
            return
        try:
            self.audit.record(aktion, "vorlage", vorlage.kennung,
                              status="ok", kategorie=vorlage.kategorie)
        except Exception as ausnahme:       # Protokoll darf nie blockieren
            log.debug("Vorlage nicht protokolliert: %s", ausnahme)


_KOPF = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def kopfzeilen_lesen(roh: str) -> tuple[dict, str]:
    """Trennt einen Kopfblock (``---`` ... ``---``) vom Rumpf ab.

    Bewusst keine vollstaendige YAML-Auswertung: gebraucht werden vier
    Zeilen der Form ``schluessel: wert``. Eine Bibliothek dafuer
    einzubinden hiesse, eine ganze Sprache zu unterstuetzen, von der
    niemand etwas hat.
    """
    treffer = _KOPF.match(roh or "")
    if not treffer:
        return {}, roh or ""
    kopf: dict[str, str] = {}
    for zeile in treffer.group(1).splitlines():
        if ":" not in zeile:
            continue
        schluessel, wert = zeile.split(":", 1)
        schluessel = schluessel.strip().lower()
        if schluessel:
            kopf[schluessel] = wert.strip()
    return kopf, (roh[treffer.end():] or "")


def _passt(vorlage: Vorlage, suche: str) -> bool:
    text = " ".join((vorlage.name, vorlage.kategorie, vorlage.beschreibung))
    return suche.strip().lower() in text.lower()
