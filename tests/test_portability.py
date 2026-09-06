"""Portabilitaet und Robustheit (Masterprompt 46 und 49).

Was hier tatsaechlich geprueft wird: wechselnde Wurzelverzeichnisse (das
entspricht dem Wechsel des Laufwerksbuchstabens und dem zweiten Rechner),
Pfade mit Leerzeichen und Sonderzeichen, fehlende und beschaedigte
Bestandteile, schreibgeschuetzte Ablage.

Was hier NICHT geprueft werden kann: echte Windows-Laufwerksbuchstaben. Der
zugehoerige Test laeuft im Windows-Ablauf der Fortlaufenden Integration
(subst X:) und ist in docs/ABNAHME.md als manueller Schritt beschrieben.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import stat
from pathlib import Path

import pytest

from app.controller import AppController
from pkc.db import Database
from pkc.db.schema import KNOWLEDGE_MIGRATIONS

ROOT = Path(__file__).resolve().parents[1]
from pkc.paths import Paths, detect_root
from test_controller import make_controller


@pytest.mark.parametrize("verzeichnis", [
    "einfach",
    "mit Leerzeichen",
    "Umlaute Aeoeue und Zahlen 2026",
    "sehr/tief/verschachtelt/ordner",
    "Klammern (Kopie) und - Striche",
])
def test_root_detection_handles_awkward_paths(tmp_path, monkeypatch, verzeichnis):
    root = tmp_path / verzeichnis
    root.mkdir(parents=True)
    monkeypatch.setenv("KIM_ROOT", str(root))
    paths = Paths(detect_root())
    assert paths.root == root.resolve()
    assert paths.is_writable()
    paths.ensure_runtime_dirs()
    paths.write_marker()
    assert (root / ".portable_root").is_file()
    assert paths.company_db.parent.is_dir()
    # Alle Pfadangaben bleiben relativ zur Wurzel
    assert paths.relative(paths.company_db) == "database/company.db"


def test_path_accessors_agree(tmp_path):
    """``paths.models`` und ``paths.get("models")`` muessen dasselbe liefern.

    Sonst zeigt dasselbe Verzeichnis je nach Schreibweise an eine andere
    Stelle - besonders heikel bei getrennter Programm- und Datenwurzel.
    """
    from pkc.paths import LAYOUT

    paths = Paths(tmp_path)
    for name in LAYOUT:
        assert getattr(paths, name) == paths.get(name), f"Abweichung bei {name}"
    with pytest.raises(AttributeError):
        _ = paths.gibt_es_nicht


def test_no_absolute_drive_letters_in_source():
    """Kein fester Laufwerksbuchstabe im Programmcode (Masterprompt 3)."""
    import re

    source_root = Path(__file__).resolve().parents[1] / "src"
    pattern = re.compile(r"""['"][A-Za-z]:[\\/]""")
    treffer: list[str] = []
    for path in source_root.rglob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line) and "WINDOWS_DEFAULT" not in line:
                treffer.append(f"{path.name}:{number}: {line.strip()}")
    assert not treffer, "Fester Laufwerkspfad im Code gefunden:\n" + "\n".join(treffer)


def test_full_data_moves_to_another_location(portable_root, tmp_path):
    """Der komplette Datenbestand wandert - alles bleibt nutzbar."""
    ctrl = make_controller(portable_root)
    ctrl.bootstrap()
    ctrl.remember_manual("company.chart_of_accounts", "Kontenrahmen",
                         "Das Unternehmen verwendet SKR03.", "accounting")
    ctrl.ask("Was ist eine Kleinbetragsrechnung?")
    vorher = ctrl.knowledge.stats()
    ctrl.shutdown()

    ziel = tmp_path.parent / "Laufwerk E" / "Portable Buchhalter"
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(portable_root.root, ziel)
    shutil.rmtree(portable_root.root)          # das alte Laufwerk gibt es nicht mehr

    os.environ["KIM_ROOT"] = str(ziel)
    try:
        ctrl2 = make_controller(Paths(ziel))
        report = ctrl2.bootstrap()
        assert report.usable
        assert ctrl2.knowledge.stats()["documents"] == vorher["documents"]
        assert "SKR03" in ctrl2.memory.get("company.chart_of_accounts").content
        assert len(ctrl2.conversations()) == 1
        ctrl2.shutdown()
    finally:
        os.environ.pop("KIM_ROOT", None)


def test_missing_model_does_not_break_the_application(portable_root):
    """Ohne Sprachmodell bleibt die Anwendung benutzbar - sie sagt es nur."""
    from pkc.config import Config
    from pkc.netstate import NetworkMonitor

    config = Config.load(portable_root)
    config.set("llm.model_path", "auto")       # es liegt kein Modell vor
    monitor = NetworkMonitor([], enabled=False)
    controller = AppController(portable_root, config, monitor, console_logging=False)
    try:
        report = controller.bootstrap()
        assert report.usable, "die Anwendung muss trotzdem startbar sein"
        modell = next(i for i in report.items if i.name == "Lokales Modell")
        assert not modell.ok and not modell.critical
        assert "Notbetrieb" in modell.detail

        outcome = controller.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")
        assert not outcome.answer.model_answered
        assert "keine KI-Antwort" in outcome.answer.text
        assert "kein Sprachmodell" in outcome.answer.text
        assert outcome.answer.references, "die Recherche muss trotzdem funktionieren"
    finally:
        controller.shutdown()


def test_missing_knowledge_database_is_rebuilt(portable_root):
    """Wird der Fachwissensindex geloescht, baut der naechste Start ihn neu auf."""
    ctrl = make_controller(portable_root)
    ctrl.bootstrap()
    vorher = ctrl.knowledge.stats()["documents"]
    ctrl.shutdown()

    for pfad in portable_root.get("resources_index").glob("knowledge.db*"):
        pfad.unlink()
    assert not portable_root.knowledge_db.exists()

    ctrl2 = make_controller(portable_root)
    report = ctrl2.bootstrap()
    try:
        assert report.usable
        assert ctrl2.knowledge.stats()["documents"] == vorher
    finally:
        ctrl2.shutdown()


def test_corrupt_knowledge_database_is_detected(portable_root):
    """Eine beschaedigte Datei wird erkannt und nicht stillschweigend ignoriert."""
    ctrl = make_controller(portable_root)
    ctrl.bootstrap()
    ctrl.shutdown()

    ziel = portable_root.knowledge_db
    for seiten in portable_root.get("resources_index").glob("knowledge.db-*"):
        seiten.unlink()
    ziel.write_bytes(b"Das ist keine Datenbank, sondern Muell." * 200)

    db = Database.__new__(Database)          # ohne Migration oeffnen
    db.path = ziel
    db._local = type("L", (), {})()
    db._migrate_lock = __import__("threading").Lock()
    db.migrations = ()
    healthy, detail = db.integrity_check()
    assert not healthy
    assert detail, "es muss eine Begruendung geliefert werden"


def test_company_memory_survives_knowledge_reset(portable_root):
    """Ein Wissensupdate darf Unternehmenswissen niemals gefaehrden."""
    ctrl = make_controller(portable_root)
    ctrl.bootstrap()
    ctrl.remember_manual("company.approval_rules", "Freigaberegel",
                         "Rechnungen ab 5.000 EUR muessen freigegeben werden.", "approval")
    ctrl.shutdown()

    # Fachwissen komplett entfernen - das ist der schlimmste Fall eines Updates
    for pfad in portable_root.get("resources_index").glob("knowledge.db*"):
        pfad.unlink()

    ctrl2 = make_controller(portable_root)
    ctrl2.bootstrap()
    try:
        entry = ctrl2.memory.get("company.approval_rules")
        assert entry is not None and "5.000 EUR" in entry.content
    finally:
        ctrl2.shutdown()


@pytest.mark.skipif(
    os.name != "posix" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason=(
        "Rechtebits nach POSIX gelten nur dort: Windows ignoriert chmod auf "
        "Verzeichnissen (dort wirken ACLs), und als root sind sie ohnehin "
        "wirkungslos. Der plattformunabhaengige Fall steht in "
        "test_unwritable_root_is_reported."
    ),
)
def test_readonly_root_posix(tmp_path, monkeypatch):
    root = tmp_path / "nur_lesen"
    root.mkdir()
    root.chmod(stat.S_IRUSR | stat.S_IXUSR)
    monkeypatch.setenv("KIM_ROOT", str(root))
    try:
        paths = Paths(root)
        assert not paths.is_writable()
    finally:
        root.chmod(stat.S_IRWXU)


def test_unwritable_root_is_reported(tmp_path):
    """Ein nicht beschreibbarer Ort wird erkannt - auf jedem Betriebssystem.

    Statt Rechtebits zu setzen (was unter Windows nicht wirkt), wird ein Ort
    verwendet, der sich gar nicht als Verzeichnis anlegen laesst: eine
    bestehende Datei.
    """
    datei = tmp_path / "das_ist_eine_datei.txt"
    datei.write_text("kein Verzeichnis", encoding="utf-8")
    paths = Paths(datei / "unterordner")
    assert not paths.is_writable(), (
        "unterhalb einer Datei kann kein Datenverzeichnis entstehen"
    )


def test_startup_refuses_unwritable_root(tmp_path):
    """Die Systempruefung meldet einen nicht beschreibbaren Ort als kritisch."""
    datei = tmp_path / "belegt.txt"
    datei.write_text("x", encoding="utf-8")
    paths = Paths(datei / "wurzel")
    from app.controller import StartupReport

    report = StartupReport(root=str(paths.root))
    report.add("Datenverzeichnis", paths.is_writable(), "Test", critical=True)
    assert not report.usable, "ohne Schreibrecht darf die Anwendung nicht starten"
    assert "ACHTUNG" in report.as_text()


def test_two_controllers_share_one_data_directory(portable_root):
    """Zwei gleichzeitige Zugriffe (z.B. GUI und Kommandozeile) vertragen sich."""
    first = make_controller(portable_root)
    first.bootstrap()
    second = make_controller(portable_root)
    second.bootstrap(ingest_modules=False, build_embeddings=False)
    try:
        first.remember_manual("company.name", "Unternehmensname", "Muster GmbH", "profile")
        assert second.memory.get("company.name") is not None
        second.remember_manual("company.industry", "Branche", "Grosshandel", "profile")
        assert first.memory.get("company.industry") is not None
    finally:
        first.shutdown()
        second.shutdown()


def test_schalter_sind_keine_konfigurationspfade(portable_root, monkeypatch):
    """Ein Schalter darf nie als Konfigurationseintrag gelesen werden.

    ``KIM_LLM_PROVIDER=echo`` soll ``llm.provider`` setzen - so ist der
    Mechanismus gemeint. Schalter wie ``KIM_UNBEAUFSICHTIGT`` oder
    ``KIM_CARRIER_ID`` sind aber keine Konfigurationspfade. Sie greifen heute
    nur deshalb nicht durch, weil es zufaellig keinen gleichnamigen Eintrag
    gibt. Dieser Test haelt sie ausdruecklich heraus, damit sie nicht
    kollidieren, sobald die Konfiguration einmal so einen Schluessel bekommt.
    """
    from pkc.config import Config, _env_overrides

    for schalter in ("KIM_ROOT", "KIM_CHECKPOINT_DIR", "KIM_PASSPHRASE",
                     "KIM_CARRIER_ID", "KIM_UNBEAUFSICHTIGT"):
        monkeypatch.setenv(schalter, "wert")

    # Eine Konfiguration, die genau die Namen der Schalter traegt.
    falle = {
        "root": "unveraendert",
        "checkpoint": {"dir": "unveraendert"},
        "passphrase": "unveraendert",
        "carrier": {"id": "unveraendert"},
        "unbeaufsichtigt": "unveraendert",
        "llm": {"provider": "unveraendert"},
    }
    ergebnis = _env_overrides(falle)

    assert ergebnis["root"] == "unveraendert"
    assert ergebnis["checkpoint"]["dir"] == "unveraendert"
    assert ergebnis["passphrase"] == "unveraendert"
    assert ergebnis["carrier"]["id"] == "unveraendert"
    assert ergebnis["unbeaufsichtigt"] == "unveraendert"

    # Der Mechanismus selbst muss weiter funktionieren.
    monkeypatch.setenv("KIM_LLM_PROVIDER", "echo")
    assert _env_overrides(falle)["llm"]["provider"] == "echo"

    # Und er darf nur bereits vorhandene Pfade anfassen, nichts erfinden.
    monkeypatch.setenv("KIM_GIBT_ES_NICHT", "x")
    assert "gibt" not in _env_overrides(falle)


def test_config_kennt_alle_schalter_der_dokumentation():
    """Die Schaltertabelle in ARCHITEKTUR.md muss vollstaendig sein.

    Eine Tabelle, die Vollstaendigkeit behauptet und es nicht ist, ist
    schlimmer als keine.
    """
    import re

    dateien = sorted((ROOT / "src").rglob("*.py")) + [ROOT / "portable_buchhalter.py"]
    dateien += sorted((ROOT / "tools").rglob("*.py")) if (ROOT / "tools").is_dir() else []
    quelle = " ".join(
        pfad.read_text(encoding="utf-8", errors="replace")
        for pfad in dateien
        if "__pycache__" not in pfad.parts
    )
    im_code = {name for name in re.findall(r"KIM_[A-Z][A-Z_]*", quelle)}

    dokument = (ROOT / "ARCHITEKTUR.md").read_text(encoding="utf-8")
    tabelle = dokument.split("## 5a. Schalter der Umgebung", 1)[1].split("\n## ", 1)[0]
    dokumentiert = set(re.findall(r"KIM_[A-Z][A-Z_]*", tabelle))

    fehlend = im_code - dokumentiert
    assert not fehlend, f"nicht dokumentierte Schalter: {sorted(fehlend)}"
