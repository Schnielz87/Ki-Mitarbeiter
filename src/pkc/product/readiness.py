"""Commercial-Readiness-Gate (Masterprompt 77 und 97).

``MVP FERTIG`` ist ausdruecklich **nicht** ``MARKTREIF``. Dieses Modul prueft,
was sich technisch pruefen laesst, und benennt den Rest als das, was er ist:
offene geschaeftliche, rechtliche und organisatorische Punkte.

Der Status ``COMMERCIAL READY`` wird hier niemals automatisch vergeben. Er
verlangt Entscheidungen und Pruefungen ausserhalb der Software.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .components import open_questions


@dataclass
class ReadinessItem:
    key: str
    requirement: str
    section: str
    automatic: bool
    fulfilled: bool | None      # None = nicht automatisch pruefbar
    detail: str

    @property
    def symbol(self) -> str:
        if self.fulfilled is True:
            return "erfuellt"
        if self.fulfilled is False:
            return "OFFEN"
        return "manuell"


@dataclass
class ReadinessReport:
    items: list[ReadinessItem] = field(default_factory=list)

    @property
    def open_items(self) -> list[ReadinessItem]:
        return [i for i in self.items if i.fulfilled is not True]

    @property
    def commercial_ready(self) -> bool:
        """Nur wahr, wenn **jeder** Punkt erfuellt ist - auch die manuellen."""
        return all(i.fulfilled is True for i in self.items)

    def as_dict(self) -> dict:
        return {
            "commercial_ready": self.commercial_ready,
            "offene_punkte": len(self.open_items),
            "punkte": [
                {"schluessel": i.key, "anforderung": i.requirement,
                 "abschnitt": i.section, "automatisch": i.automatic,
                 "erfuellt": i.fulfilled, "detail": i.detail}
                for i in self.items
            ],
        }

    def as_text(self) -> str:
        zeilen = ["COMMERCIAL-READINESS-PRUEFUNG", ""]
        breite = max((len(i.requirement) for i in self.items), default=20)
        for eintrag in self.items:
            zeilen.append(
                f"  [{eintrag.symbol:8s}] {eintrag.requirement.ljust(breite)} "
                f"({eintrag.section})"
            )
            zeilen.append(f"              {eintrag.detail}")
        zeilen += ["", f"Offene Punkte: {len(self.open_items)} von {len(self.items)}", ""]
        zeilen.append(
            "STATUS: COMMERCIAL READY" if self.commercial_ready else
            "STATUS: NOCH NICHT COMMERCIAL READY - die offenen Punkte oben sind "
            "zuerst abzuarbeiten."
        )
        return "\n".join(zeilen)


def _tests_laufen(project_root: Path) -> tuple[bool, str]:
    try:
        ergebnis = subprocess.run(
            ["python3", "-m", "pytest", "tests", "-q", "--tb=no"],
            cwd=project_root, capture_output=True, text=True, timeout=600, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Tests nicht ausfuehrbar: {exc}"
    letzte = [z for z in ergebnis.stdout.strip().splitlines() if z.strip()]
    zusammenfassung = letzte[-1] if letzte else "keine Ausgabe"
    return ergebnis.returncode == 0, zusammenfassung


def check_readiness(project_root: Path, run_tests: bool = False) -> ReadinessReport:
    """Prueft die technisch pruefbaren Voraussetzungen."""
    wurzel = Path(project_root)
    bericht = ReadinessReport()

    def pruefe(key, requirement, section, fulfilled, detail, automatic=True):
        bericht.items.append(ReadinessItem(key, requirement, section, automatic,
                                           fulfilled, detail))

    # -- automatisch pruefbar ------------------------------------------
    lizenzmodul = wurzel / "src" / "pkc" / "licensing" / "verify.py"
    pruefe("lizenzpruefung", "Lizenzpruefung implementiert", "97",
           lizenzmodul.is_file(),
           "pkc.licensing vorhanden" if lizenzmodul.is_file() else "fehlt")

    lizenztests = wurzel / "tests" / "test_lizenzierung.py"
    pruefe("lizenztests", "Kopier- und Manipulationstest vorhanden", "96/97",
           lizenztests.is_file(),
           "tests/test_lizenzierung.py deckt die sieben Testfaelle ab"
           if lizenztests.is_file() else "fehlt")

    from ..licensing.verify import PUBLIC_KEY_PEM
    pruefe("pruefschluessel", "Pruefschluessel des Herausgebers eingebaut", "86",
           bool(PUBLIC_KEY_PEM),
           "hinterlegt" if PUBLIC_KEY_PEM else
           "noch nicht hinterlegt - geschaeftliche Entscheidung, gehoert zur "
           "kommerziellen Fassung")

    for schluessel, anforderung, datei, abschnitt in [
        ("lizenzregister", "Lizenzpruefung der Bestandteile", "LIZENZREGISTER.md", "63"),
        ("sbom", "Software-Bestandsliste (SBOM)", "sbom.json", "64"),
        ("sicherheitskonzept", "Sicherheitskonzept dokumentiert", "SICHERHEITSKONZEPT.md", "70"),
        ("backup", "Backup und Wiederherstellung beschrieben", "BACKUP_WIEDERHERSTELLUNG.md", "75"),
        ("update", "Updateprozess beschrieben", "UPDATE_KONZEPT.md", "65"),
        ("testbericht", "Testbericht vorhanden", "TESTBERICHT.md", "73"),
        ("lizenzkonzept", "Lizenzbedingungen dokumentiert", "LIZENZKONZEPT.md", "97"),
        ("kommerziell", "Kommerzielles Konzept dokumentiert", "KOMMERZIELLES_KONZEPT.md", "58"),
    ]:
        pfad = wurzel / datei
        pruefe(schluessel, anforderung, abschnitt, pfad.is_file(),
               f"{datei} vorhanden" if pfad.is_file() else f"{datei} fehlt")

    kundentrennung = wurzel / "tests" / "test_kundentrennung.py"
    pruefe("kundentrennung", "Kundentrennung geprueft", "61", kundentrennung.is_file(),
           "tests/test_kundentrennung.py vorhanden" if kundentrennung.is_file() else "fehlt")

    offen = open_questions()
    pruefe("lizenzfragen", "Keine offenen Lizenzfragen der Bestandteile", "63",
           not offen,
           "keine offenen Punkte" if not offen else
           f"{len(offen)} Punkte offen (siehe LIZENZREGISTER.md)")

    if run_tests:
        gruen, zusammenfassung = _tests_laufen(wurzel)
        pruefe("tests", "Alle automatischen Tests bestanden", "73", gruen, zusammenfassung)

    # -- nur manuell feststellbar --------------------------------------
    for schluessel, anforderung, abschnitt, hinweis in [
        ("pilot", "Pilotbetrieb durchgefuehrt", "76",
         "Ein realer Pilotkunde muss die Anwendung im Alltag eingesetzt haben."),
        ("kritische_fehler", "Bekannte kritische Fehler behoben", "77",
         "Setzt den Pilotbetrieb voraus - vorher sind die Fehler unbekannt."),
        ("sicherheitspruefung", "Sicherheitspruefung abgeschlossen", "70/77",
         "Externe Pruefung; das Sicherheitskonzept allein genuegt nicht."),
        ("datenschutz", "Datenschutzkonzept geprueft", "71/77",
         "Verarbeitungsverzeichnis, Rechtsgrundlagen, Auftragsverarbeitung."),
        ("recht", "Rechtliche Pruefung durchgefuehrt", "71/72",
         "Insbesondere die Abgrenzung zur Steuerberatung nach StBerG."),
        ("support", "Supportprozess definiert", "77",
         "Erreichbarkeit, Reaktionszeiten, Fehlermeldeweg, Fernwartung."),
        ("modelllizenz", "Weitergabe des Sprachmodells geklaert", "63",
         "Empfehlung: das Modell vom Kunden beziehen lassen."),
    ]:
        pruefe(schluessel, anforderung, abschnitt, None, hinweis, automatic=False)

    return bericht
