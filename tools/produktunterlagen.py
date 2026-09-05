#!/usr/bin/env python3
"""Erzeugt die Produktunterlagen (Masterprompt 63, 64, 73, 77).

    python tools/produktunterlagen.py lizenzregister
    python tools/produktunterlagen.py sbom
    python tools/produktunterlagen.py release --version 0.1.0
    python tools/produktunterlagen.py reife [--mit-tests]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pkc.product import (  # noqa: E402
    build_license_register, build_release_dossier, build_sbom, check_readiness,
    collect_components, open_questions,
)


def cmd_lizenzregister(args) -> int:
    ziel = build_license_register(Path(args.ziel or ROOT / "LIZENZREGISTER.md"))
    print(f"geschrieben: {ziel}")
    offen = open_questions()
    print(f"Bestandteile: {len(collect_components())} · offene Lizenzfragen: {len(offen)}")
    for punkt in offen:
        print(f"  - {punkt[:100]}")
    return 0


def cmd_sbom(args) -> int:
    ziel = build_sbom(Path(args.ziel or ROOT / "sbom.json"), args.version)
    daten = json.loads(ziel.read_text(encoding="utf-8"))
    print(f"geschrieben: {ziel} ({len(daten['components'])} Bestandteile)")
    return 0


def cmd_release(args) -> int:
    ziel = Path(args.ziel or ROOT / "RELEASE" / args.version)
    dateien = [Path(p) for p in (args.datei or [])]
    ergebnis = build_release_dossier(
        ROOT, ziel, args.version,
        test_summary=args.testergebnis,
        known_issues=args.problem or [],
        security_notes=args.sicherheitshinweis or [],
        files_to_checksum=dateien,
    )
    print(f"Release-Dossier: {ergebnis['verzeichnis']}")
    for datei in ergebnis["dateien"]:
        print(f"  {datei}")
    print(f"Pruefsummen ueber {ergebnis['pruefsummen']} Auslieferungsdatei(en)")
    return 0


def cmd_reife(args) -> int:
    bericht = check_readiness(ROOT, run_tests=args.mit_tests)
    if args.json:
        print(json.dumps(bericht.as_dict(), indent=2, ensure_ascii=False))
    else:
        print(bericht.as_text())
    return 0 if bericht.commercial_ready else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Produktunterlagen erzeugen")
    sub = parser.add_subparsers(dest="befehl", required=True)

    lizenz = sub.add_parser("lizenzregister", help="Lizenzregister schreiben")
    lizenz.add_argument("--ziel", default="")
    lizenz.set_defaults(func=cmd_lizenzregister)

    sbom = sub.add_parser("sbom", help="Software-Bestandsliste schreiben")
    sbom.add_argument("--ziel", default="")
    sbom.add_argument("--version", default="0.1.0")
    sbom.set_defaults(func=cmd_sbom)

    release = sub.add_parser("release", help="Release-Dossier erzeugen")
    release.add_argument("--version", required=True)
    release.add_argument("--ziel", default="")
    release.add_argument("--testergebnis", default="")
    release.add_argument("--problem", action="append")
    release.add_argument("--sicherheitshinweis", action="append")
    release.add_argument("--datei", action="append", help="Auslieferungsdatei fuer Pruefsummen")
    release.set_defaults(func=cmd_release)

    reife = sub.add_parser("reife", help="Commercial-Readiness pruefen")
    reife.add_argument("--mit-tests", dest="mit_tests", action="store_true")
    reife.add_argument("--json", action="store_true")
    reife.set_defaults(func=cmd_reife)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
