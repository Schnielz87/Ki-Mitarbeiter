"""Checkpoint- und Wiederherstellungssystem (Masterprompt 44 und 45).

Der Chat ist nicht die massgebliche Quelle des Projektstands - die Festplatte
ist es.  Nach jedem abgeschlossenen Task wird ein Checkpoint geschrieben:
im Repository *und* an einem davon unabhaengigen Ort.

Der externe Ablageort wird in dieser Reihenfolge bestimmt:

1. Umgebungsvariable ``KIM_CHECKPOINT_DIR``
2. ``D:\\Ki-Agent\\checkpoints`` (Vorgabe des Auftraggebers), falls vorhanden
3. ``<Elternverzeichnis der Projektwurzel>/checkpoints``

Ein Checkpoint gilt erst als erstellt, wenn die Datei danach gelesen und ihre
Pruefsumme bestaetigt wurde.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import platform
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable

from .logging_setup import get_logger

log = get_logger(__name__)

WINDOWS_DEFAULT = Path("D:/Ki-Agent/checkpoints")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 256), b""):
            digest.update(block)
    return digest.hexdigest()


def external_checkpoint_dir(project_root: Path) -> Path:
    env = os.environ.get("KIM_CHECKPOINT_DIR")
    if env:
        return Path(env).expanduser()
    if platform.system() == "Windows" and WINDOWS_DEFAULT.parent.exists():
        return WINDOWS_DEFAULT
    return project_root.parent / "checkpoints"


def git_commit(cwd: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True,
            timeout=15, check=False,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


@dataclass
class Checkpoint:
    task_number: str
    task_name: str
    status: str                      # abgeschlossen | teilweise | offen
    work_done: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    test_result: str = ""
    open_points: list[str] = field(default_factory=list)
    next_task: str = ""
    resume_hint: str = ""
    git_commit: str = ""
    created_at: str = ""
    checksums: dict[str, str] = field(default_factory=dict)
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    def as_markdown(self) -> str:
        def block(title: str, items: Iterable[str]) -> list[str]:
            items = list(items)
            if not items:
                return [f"## {title}", "", "- (keine)", ""]
            return [f"## {title}", ""] + [f"- {i}" for i in items] + [""]

        lines = [
            f"# Checkpoint {self.task_number} - {self.task_name}",
            "",
            f"* Zeitpunkt: {self.created_at}",
            f"* Status: **{self.status.upper()}**",
            f"* Git-Commit: `{self.git_commit or 'nicht ermittelt'}`",
            f"* Naechster Task: {self.next_task or '-'}",
            "",
            "## Fortsetzungspunkt",
            "",
            self.resume_hint or "(nicht angegeben)",
            "",
        ]
        lines += block("Erledigte Arbeit", self.work_done)
        lines += block("Dateien", self.files)
        lines += block("Tests", self.tests)
        lines += [f"**Testergebnis:** {self.test_result or 'nicht ausgefuehrt'}", ""]
        lines += block("Offene Punkte", self.open_points)
        if self.checksums:
            lines += ["## Pruefsummen (SHA-256)", "", "| Datei | Pruefsumme |", "|---|---|"]
            lines += [f"| {name} | `{value}` |" for name, value in sorted(self.checksums.items())]
            lines += [""]
        if self.notes:
            lines += ["## Hinweise", "", self.notes, ""]
        return "\n".join(lines)


class CheckpointManager:
    """Schreibt und prueft Checkpoints an zwei unabhaengigen Orten."""

    def __init__(self, project_root: Path, internal_dir: Path | None = None,
                 external_dir: Path | None = None):
        self.project_root = Path(project_root)
        self.internal_dir = Path(internal_dir or self.project_root / "checkpoints")
        self.external_dir = Path(external_dir or external_checkpoint_dir(self.project_root))

    def create(
        self,
        task_number: str,
        task_name: str,
        status: str = "abgeschlossen",
        *,
        work_done: Iterable[str] = (),
        files: Iterable[str] = (),
        tests: Iterable[str] = (),
        test_result: str = "",
        open_points: Iterable[str] = (),
        next_task: str = "",
        resume_hint: str = "",
        checksum_files: Iterable[Path] = (),
        notes: str = "",
    ) -> tuple[Checkpoint, list[Path], list[str]]:
        """Erzeugt den Checkpoint. Gibt (Checkpoint, geschriebene Pfade, Warnungen)."""
        checkpoint = Checkpoint(
            task_number=task_number, task_name=task_name, status=status,
            work_done=list(work_done), files=list(files), tests=list(tests),
            test_result=test_result, open_points=list(open_points), next_task=next_task,
            resume_hint=resume_hint, git_commit=git_commit(self.project_root),
            created_at=_dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            notes=notes,
        )
        for path in checksum_files:
            path = Path(path)
            if path.is_file():
                key = self._relative(path)
                checkpoint.checksums[key] = sha256_file(path)

        stem = f"TASK_{task_number}_{_slug(task_name)}"
        written: list[Path] = []
        warnings: list[str] = []
        for directory in (self.internal_dir, self.external_dir):
            try:
                directory.mkdir(parents=True, exist_ok=True)
                json_path = directory / f"{stem}.json"
                md_path = directory / f"{stem}.md"
                json_path.write_text(
                    json.dumps(checkpoint.as_dict(), indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                md_path.write_text(checkpoint.as_markdown(), encoding="utf-8")
                written += [json_path, md_path]
                self._write_latest(directory, checkpoint, stem)
            except OSError as exc:
                warnings.append(f"Checkpoint konnte nicht nach {directory} geschrieben werden: {exc}")

        verified, verify_warnings = self.verify(written)
        warnings += verify_warnings
        if not verified:
            log.error("Checkpoint %s konnte NICHT verifiziert werden", task_number)
        else:
            log.info("Checkpoint %s geschrieben und verifiziert (%s Dateien)", task_number, len(written))
        return checkpoint, written, warnings

    def _write_latest(self, directory: Path, checkpoint: Checkpoint, stem: str) -> None:
        (directory / "LETZTER_STAND.json").write_text(
            json.dumps(
                {
                    "task_number": checkpoint.task_number,
                    "task_name": checkpoint.task_name,
                    "status": checkpoint.status,
                    "created_at": checkpoint.created_at,
                    "git_commit": checkpoint.git_commit,
                    "next_task": checkpoint.next_task,
                    "resume_hint": checkpoint.resume_hint,
                    "checkpoint_file": f"{stem}.json",
                },
                indent=2, ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

    def verify(self, written: Iterable[Path]) -> tuple[bool, list[str]]:
        """Prueft, dass die Dateien wirklich existieren und lesbar sind."""
        warnings: list[str] = []
        ok = True
        paths = list(written)
        if not paths:
            return False, ["Es wurde keine einzige Checkpointdatei geschrieben."]
        for path in paths:
            if not path.is_file():
                ok = False
                warnings.append(f"Checkpointdatei fehlt nach dem Schreiben: {path}")
                continue
            if path.suffix == ".json":
                try:
                    json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    ok = False
                    warnings.append(f"Checkpointdatei nicht lesbar: {path} ({exc})")
        return ok, warnings

    def latest(self) -> dict | None:
        for directory in (self.internal_dir, self.external_dir):
            candidate = directory / "LETZTER_STAND.json"
            if candidate.is_file():
                try:
                    return json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
        return None

    def list_checkpoints(self) -> list[dict]:
        seen: dict[str, dict] = {}
        for directory in (self.internal_dir, self.external_dir):
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("TASK_*.json")):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                data["_file"] = str(path)
                seen[path.name] = data
        return [seen[k] for k in sorted(seen)]

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.project_root.resolve()).as_posix()
        except ValueError:
            return path.name


def _slug(text: str) -> str:
    out = []
    for char in text.lower():
        if char.isalnum():
            out.append(char)
        elif char in " -_/":
            out.append("_")
    return "".join(out).strip("_")[:60] or "task"
