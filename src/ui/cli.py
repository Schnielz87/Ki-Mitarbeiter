"""Kommandozeilenoberflaeche.

Sie ist bewusst vollwertig: fuer automatische Tests, fuer Rechner ohne
grafische Oberflaeche und als Notweg, falls die GUI einmal nicht startet.
Sie nutzt exakt denselben Controller wie die grafische Oberflaeche.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.controller import AppController
from pkc.audit import ApprovalState
from pkc.config import Config
from pkc.paths import Paths, get_paths


def _controller(args) -> AppController:
    paths = Paths(Path(args.root).expanduser().resolve()) if args.root else get_paths()
    config = Config.load(paths)
    if args.offline:
        config.set("network.check_on_start", False)
    return AppController(paths, config, console_logging=not args.quiet)


def _print_report(report) -> None:
    print(report.as_text())


def cmd_check(args) -> int:
    controller = _controller(args)
    try:
        report = controller.bootstrap()
        if args.json:
            print(json.dumps(report.as_dict(), indent=2, ensure_ascii=False))
        else:
            _print_report(report)
        return 0 if report.usable else 2
    finally:
        controller.shutdown()


def cmd_ask(args) -> int:
    controller = _controller(args)
    try:
        report = controller.bootstrap()
        if not report.usable:
            print(report.as_text(), file=sys.stderr)
            return 2
        outcome = controller.ask(args.frage, as_of=args.stand)
        print(outcome.answer.text)
        if outcome.capture_candidates:
            print("\n--- Moegliche dauerhafte Unternehmensinformation ---")
            for candidate in outcome.capture_candidates:
                print(f"  {candidate.question()}")
                print(f"    Schluessel: {candidate.mem_key} · Sicherheit: {candidate.confidence}")
                if args.merken:
                    controller.remember(candidate)
                    print("    -> gespeichert")
        return 0
    finally:
        controller.shutdown()


def cmd_chat(args) -> int:
    controller = _controller(args)
    try:
        report = controller.bootstrap()
        print(report.as_text())
        if not report.usable:
            return 2
        print("\nEingabe 'ende' beendet. 'status' zeigt die Lage.\n")
        while True:
            try:
                question = input("Sie > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not question:
                continue
            if question.lower() in ("ende", "exit", "quit"):
                break
            if question.lower() == "status":
                print(json.dumps(controller.status(), indent=2, ensure_ascii=False))
                continue
            outcome = controller.ask(question)
            print(f"\nBuchhalter >\n{outcome.answer.text}\n")
            for candidate in outcome.capture_candidates:
                answer = input(f"  {candidate.question()} [j/N] ").strip().lower()
                if answer.startswith("j"):
                    controller.remember(candidate)
                    print("  -> dauerhaft gespeichert.")
        return 0
    finally:
        controller.shutdown()


def cmd_memory(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        if args.action == "list":
            entries = controller.memory.list(category=args.kategorie, status=args.status)
            if not entries:
                print("Kein Unternehmenswissen gespeichert.")
            for entry in entries:
                print(f"  {entry.mem_key:38s} v{entry.version} [{entry.category}] {entry.title}")
                print(f"      {entry.content}")
        elif args.action == "set":
            entry = controller.remember_manual(
                args.key, args.titel or args.key, args.wert, args.kategorie or "other"
            )
            print(f"gespeichert: {entry.mem_key} (Version {entry.version})")
        elif args.action == "get":
            entry = controller.memory.get(args.key)
            print(entry.content if entry else "nicht vorhanden")
        elif args.action == "history":
            for item in controller.memory.history(args.key):
                print(f"  v{item['version']} {item['change_type']:8s} {item['changed_at']} "
                      f"- {item['snapshot']['content'][:70]}")
        elif args.action == "delete":
            print("archiviert" if controller.forget(args.key, hard=args.endgueltig)
                  else "nicht gefunden")
        elif args.action == "search":
            for entry in controller.memory.search(args.key):
                print(f"  [{entry.score:.2f}] {entry.title}: {entry.content}")
        elif args.action == "export":
            print(f"geschrieben: {controller.export_company_profile()}")
        return 0
    finally:
        controller.shutdown()


def cmd_update(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        if args.zuruecknehmen:
            ok, message = controller.rollback_update(args.zuruecknehmen)
            print(message)
            return 0 if ok else 1

        def progress(title: str, index: int, total: int) -> None:
            print(f"  [{index}/{total}] {title[:60]}")

        report = controller.run_update(
            trigger="cli", source_ids=args.quelle or None, dry_run=args.trocken,
            progress=progress,
        )
        print(f"\nErgebnis: {report.status.upper()}")
        print(f"  geprueft {report.checked} · aktualisiert {report.updated} · "
              f"unveraendert {report.unchanged} · fehlgeschlagen {report.failed}")
        for message in report.messages:
            print(f"  - {message}")
        return 0 if report.status in ("success", "partial") else 1
    finally:
        controller.shutdown()


def cmd_status(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        print(json.dumps(controller.status(), indent=2, ensure_ascii=False))
        return 0
    finally:
        controller.shutdown()


def cmd_onboarding(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        questions = controller.onboarding_questions()
        done = sum(1 for q in questions if q["beantwortet"])
        print(f"Unternehmens-Onboarding: {done} von {len(questions)} beantwortet\n")
        for question in questions:
            if question["beantwortet"] and not args.alle:
                continue
            if args.interaktiv:
                try:
                    value = input(f"{question['titel']}: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if value:
                    controller.answer_onboarding(question["key"], value)
            else:
                mark = "x" if question["beantwortet"] else " "
                print(f"  [{mark}] {question['titel']:34s} {question['wert'][:44]}")
        return 0
    finally:
        controller.shutdown()


def cmd_backup(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        info = controller.backup(args.name)
        print(f"Sicherung: {info['verzeichnis']}")
        for name, checksum in info["pruefsummen"].items():
            print(f"  {name:24s} {checksum[:16]}...")
        return 0
    finally:
        controller.shutdown()


def cmd_document(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        if args.datei:
            result = controller.add_document(args.datei)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            for item in controller.documents():
                print(f"  {item['doc_uid']}  {item['title'][:52]:52s} {item['status']}")
        return 0
    finally:
        controller.shutdown()


def cmd_approvals(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        if args.freigeben:
            approval = controller.approvals.transition(
                args.freigeben, ApprovalState.FREIGEGEBEN, by=args.durch or "benutzer"
            )
            print(f"{approval.uid}: {approval.state.value}")
        else:
            for approval in controller.approvals.list():
                print(f"  {approval.uid}  {approval.state.value:12s} {approval.title}")
        return 0
    finally:
        controller.shutdown()


def _global_options(parser: argparse.ArgumentParser, suppress: bool = False) -> None:
    """Die drei allgemeinen Schalter.

    Sie werden am Hauptbefehl *und* an jedem Unterbefehl angeboten, damit
    sowohl ``... --quiet check`` als auch ``... check --quiet`` funktioniert.
    Ein Anwender soll nicht raten muessen, wo der Schalter hingehoert.
    """
    leer = argparse.SUPPRESS if suppress else None
    parser.add_argument("--root", default=leer,
                        help="Datenverzeichnis (Standard: automatisch erkannt)")
    parser.add_argument("--offline", action="store_true", default=leer,
                        help="Netzpruefung ueberspringen")
    parser.add_argument("--quiet", action="store_true", default=leer,
                        help="weniger Ausgaben")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portabler-buchhalter",
        description="Portabler KI-Buchhalter - Kommandozeile",
    )
    _global_options(parser)
    # Dieselben Schalter noch einmal fuer die Unterbefehle. SUPPRESS sorgt
    # dafuer, dass ein nicht angegebener Schalter den Wert vom Hauptbefehl
    # nicht ueberschreibt.
    gemeinsam = argparse.ArgumentParser(add_help=False)
    _global_options(gemeinsam, suppress=True)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=argparse.ArgumentParser)

    def neu(name: str, hilfe: str) -> argparse.ArgumentParser:
        return sub.add_parser(name, help=hilfe, parents=[gemeinsam])

    check = neu("check", "Systempruefung")
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=cmd_check)

    ask = neu("frage", "Eine Fachfrage stellen")
    ask.add_argument("frage")
    ask.add_argument("--stand", help="Rechtsstand (JJJJ-MM-TT) fuer zeitbezogene Recherche")
    ask.add_argument("--merken", action="store_true",
                     help="erkannte Unternehmensinformationen ohne Rueckfrage speichern")
    ask.set_defaults(func=cmd_ask)

    chat = neu("chat", "Interaktive Unterhaltung")
    chat.set_defaults(func=cmd_chat)

    memory = neu("wissen", "Unternehmensgedaechtnis verwalten")
    memory.add_argument("action",
                        choices=["list", "get", "set", "delete", "history", "search", "export"])
    memory.add_argument("key", nargs="?", default="")
    memory.add_argument("wert", nargs="?", default="")
    memory.add_argument("--titel", default="")
    memory.add_argument("--kategorie", default="")
    memory.add_argument("--status", default="active")
    memory.add_argument("--endgueltig", action="store_true")
    memory.set_defaults(func=cmd_memory)

    update = neu("update", "Wissensupdate")
    update.add_argument("--quelle", action="append", help="nur diese Quelle(n)")
    update.add_argument("--trocken", action="store_true", help="Trockenlauf ohne Schreiben")
    update.add_argument("--zuruecknehmen", help="Lauf-ID zuruecknehmen")
    update.set_defaults(func=cmd_update)

    status = neu("status", "Lagebericht als JSON")
    status.set_defaults(func=cmd_status)

    onboarding = neu("onboarding", "Unternehmensdaten erfassen")
    onboarding.add_argument("--interaktiv", action="store_true")
    onboarding.add_argument("--alle", action="store_true")
    onboarding.set_defaults(func=cmd_onboarding)

    backup = neu("sicherung", "Sicherung erstellen")
    backup.add_argument("--name", default="")
    backup.set_defaults(func=cmd_backup)

    document = neu("beleg", "Beleg hinzufuegen oder auflisten")
    document.add_argument("datei", nargs="?")
    document.set_defaults(func=cmd_document)

    approvals = neu("freigaben", "Freigaben anzeigen oder erteilen")
    approvals.add_argument("--freigeben", help="Kennung des Vorgangs")
    approvals.add_argument("--durch", help="Name der freigebenden Person")
    approvals.set_defaults(func=cmd_approvals)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
