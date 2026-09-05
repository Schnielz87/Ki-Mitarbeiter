"""Checkpoints (Masterprompt 44, 45).

Die Regel ist verbindlich: Ein Checkpoint gilt erst, wenn die Datei
tatsaechlich geschrieben wurde - im Projekt **und** an einem davon
unabhaengigen Ort. "Checkpoint erstellt" als blosse Behauptung reicht nicht.

Bis hierher war ausgerechnet dieser Mechanismus ungetestet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pkc.checkpoint import CheckpointManager

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def store(tmp_path):
    return CheckpointManager(
        tmp_path / "projekt",
        internal_dir=tmp_path / "projekt" / "checkpoints",
        external_dir=tmp_path / "woanders" / "checkpoints",
    )


def test_checkpoint_landet_an_beiden_orten(store):
    """Ein Ort genuegt nicht - geht der Datentraeger verloren, ist alles weg."""
    checkpoint, geschrieben, warnungen = store.create(
        "42", "Beispieltask", work_done=["etwas getan"], tests=["pytest"],
        test_result="alles gruen",
    )

    assert not warnungen, warnungen
    for pfad in geschrieben:
        assert pfad.is_file(), f"behauptet geschrieben, liegt aber nicht vor: {pfad}"
        assert pfad.stat().st_size > 0

    innen = store.internal_dir / "TASK_42_beispieltask.json"
    aussen = store.external_dir / "TASK_42_beispieltask.json"
    assert innen.is_file() and aussen.is_file()
    assert json.loads(innen.read_text(encoding="utf-8")) == \
           json.loads(aussen.read_text(encoding="utf-8"))


def test_letzter_stand_zeigt_auf_den_neuesten(store):
    """Der Wiedereinstieg beginnt bei LETZTER_STAND.json."""
    store.create("1", "Erster", next_task="der zweite")
    store.create("2", "Zweiter", next_task="der dritte",
                 resume_hint="hier ansetzen")

    for verzeichnis in (store.internal_dir, store.external_dir):
        stand = json.loads((verzeichnis / "LETZTER_STAND.json").read_text(encoding="utf-8"))
        assert stand["task_number"] == "2"
        assert stand["next_task"] == "der dritte"
        assert stand["resume_hint"] == "hier ansetzen"
        assert (verzeichnis / stand["checkpoint_file"]).is_file(), \
            "die genannte Datei muss es wirklich geben"


def test_pruefsummen_werden_ueber_die_echte_datei_gebildet(store, tmp_path):
    quelle = tmp_path / "beleg.txt"
    quelle.write_text("Inhalt", encoding="utf-8")

    checkpoint, _, _ = store.create("3", "Mit Pruefsumme", checksum_files=[quelle])
    assert checkpoint.checksums, "die Pruefsumme fehlt"

    import hashlib
    erwartet = hashlib.sha256(b"Inhalt").hexdigest()
    assert erwartet in checkpoint.checksums.values()


def test_fehlender_zweiter_ort_wird_gemeldet_nicht_verschwiegen(tmp_path):
    """Schlaegt ein Ort fehl, muss das auffallen - nicht still durchgehen."""
    ziel = tmp_path / "belegt"
    ziel.write_text("keine Datei-Ablage, sondern eine Datei", encoding="utf-8")
    store = CheckpointManager(tmp_path / "projekt",
                            internal_dir=tmp_path / "projekt" / "checkpoints",
                            external_dir=ziel / "checkpoints")

    _, geschrieben, warnungen = store.create("4", "Halb geschrieben")

    assert warnungen, "der fehlgeschlagene Ort muss gemeldet werden"
    assert any("nicht nach" in w for w in warnungen)
    assert geschrieben, "der erreichbare Ort muss trotzdem geschrieben sein"


def test_werkzeug_verliert_kein_testergebnis(monkeypatch):
    """Zwei --test-result duerfen sich nicht gegenseitig ueberschreiben.

    Genau das ist passiert: der erste Wert ("214 bestanden") wurde
    stillschweigend verworfen, im Checkpoint stand nur noch der zweite.

    Geprueft wird die Argumentauswertung des Werkzeugs gegen ein Doppel -
    ohne Unterprozess, denn der wuerde in das echte Projektverzeichnis
    schreiben und dessen LETZTER_STAND.json ueberschreiben.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "checkpoint_werkzeug", ROOT / "tools" / "checkpoint.py")
    werkzeug = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(werkzeug)

    gesehen = {}

    class ManagerDoppel:
        def __init__(self, *args, **kwargs):
            pass

        def create(self, task_number, task_name, status="abgeschlossen", **kwargs):
            gesehen.update(kwargs)
            gesehen["task_number"] = task_number
            return object(), [], []

    monkeypatch.setattr(werkzeug, "CheckpointManager", ManagerDoppel)

    werkzeug.main(["create", "--task", "5", "--name", "Zwei Ergebnisse",
                   "--test", "pytest", "--test-result", "214 bestanden",
                   "--test", "Windows", "--test-result", "13 Schritte bestanden"])

    assert "214 bestanden" in gesehen["test_result"]
    assert "13 Schritte bestanden" in gesehen["test_result"]
    assert gesehen["tests"] == ["pytest", "Windows"]
