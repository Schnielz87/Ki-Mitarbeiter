#!/usr/bin/env python3
"""Kommandozeilenwerkzeug zum Erstellen und Pruefen von Checkpoints.

Beispiel:
    python tools/checkpoint.py create --task 01 --name "Projektziel" \
        --status abgeschlossen --next "TASK 02" --test-result "12 Tests gruen"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pkc.checkpoint import CheckpointManager  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Checkpointverwaltung")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Checkpoint schreiben und verifizieren")
    create.add_argument("--task", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--status", default="abgeschlossen")
    create.add_argument("--work", action="append", default=[])
    create.add_argument("--file", action="append", default=[])
    create.add_argument("--test", action="append", default=[])
    create.add_argument("--test-result", default="")
    create.add_argument("--open", action="append", default=[])
    create.add_argument("--next", dest="next_task", default="")
    create.add_argument("--resume", default="")
    create.add_argument("--checksum", action="append", default=[])
    create.add_argument("--notes", default="")

    sub.add_parser("list", help="Vorhandene Checkpoints anzeigen")
    sub.add_parser("latest", help="Letzten Stand anzeigen")

    args = parser.parse_args(argv)
    manager = CheckpointManager(ROOT)

    if args.command == "create":
        checkpoint, written, warnings = manager.create(
            args.task, args.name, args.status,
            work_done=args.work, files=args.file, tests=args.test,
            test_result=args.test_result, open_points=args.open,
            next_task=args.next_task, resume_hint=args.resume,
            checksum_files=[ROOT / c for c in args.checksum], notes=args.notes,
        )
        for path in written:
            print(f"geschrieben: {path}")
        for warning in warnings:
            print(f"WARNUNG: {warning}", file=sys.stderr)
        return 1 if warnings and not written else 0

    if args.command == "list":
        for item in manager.list_checkpoints():
            print(f"{item['task_number']:>4}  {item['status']:<14} {item['task_name']}")
        return 0

    latest = manager.latest()
    print(json.dumps(latest, indent=2, ensure_ascii=False) if latest else "kein Checkpoint vorhanden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
