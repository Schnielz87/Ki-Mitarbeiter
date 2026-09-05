#!/usr/bin/env python3
"""Lizenzverwaltung fuer den Hersteller (Masterprompt 86 bis 93).

Dieses Werkzeug gehoert **nicht** auf den Datentraeger des Kunden: es
verwendet den privaten Signaturschluessel.

Ablauf:

    1. Einmalig:  python tools/lizenz_ausstellen.py schluessel --verzeichnis geheim/
    2. Der oeffentliche Schluessel wird in die Anwendung eingebaut
       (pkc/licensing/verify.py, PUBLIC_KEY_PEM).
    3. Der Kunde schickt seine Aktivierungsanfrage
       (PORTABLE_BUCHHALTER_KONSOLE.exe lizenz anfrage).
    4. python tools/lizenz_ausstellen.py ausstellen --instanz ... --fingerabdruck ...
    5. Der Kunde nimmt license.json und license.sig auf
       (PORTABLE_BUCHHALTER_KONSOLE.exe lizenz aufnehmen ...).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pkc.licensing.issue import generate_keypair, issue_license  # noqa: E402
from pkc.licensing.model import LicenseError  # noqa: E402


def cmd_schluessel(args) -> int:
    verzeichnis = Path(args.verzeichnis)
    privat = verzeichnis / "herausgeber_privat.pem"
    oeffentlich = verzeichnis / "herausgeber_oeffentlich.pem"
    if privat.exists() and not args.ueberschreiben:
        print(f"Es gibt bereits einen Schluessel: {privat}", file=sys.stderr)
        return 1
    generate_keypair(privat, oeffentlich, args.passwort)
    print(f"Privater Schluessel : {privat}")
    print(f"Oeffentlicher Schluessel: {oeffentlich}")
    print()
    print("WICHTIG:")
    print("  - Den privaten Schluessel sicher verwahren und niemals ausliefern.")
    print("  - Ohne ihn koennen keine Lizenzen mehr ausgestellt werden.")
    print("  - Den oeffentlichen Schluessel in src/pkc/licensing/verify.py")
    print("    als PUBLIC_KEY_PEM eintragen:")
    print()
    print("PUBLIC_KEY_PEM = b\"\"\"\\")
    print(oeffentlich.read_text(encoding="ascii").rstrip())
    print("\"\"\"")
    return 0


def cmd_ausstellen(args) -> int:
    anfrage = {}
    if args.anfrage:
        anfrage = json.loads(Path(args.anfrage).read_text(encoding="utf-8"))
    instanz = args.instanz or anfrage.get("instanz_id", "")
    fingerabdruck = args.fingerabdruck or anfrage.get("datentraeger_fingerabdruck", "")
    kunde = args.kunde or anfrage.get("kunde", "")
    if not instanz or not fingerabdruck or not kunde:
        print("Es fehlen Angaben: Kunde, Instanz-ID und Fingerabdruck sind noetig.",
              file=sys.stderr)
        return 2

    try:
        lizenz, signatur, ablage = issue_license(
            Path(args.schluessel), customer=kunde, customer_id=args.kundennummer,
            instance_id=instanz, carrier_fingerprint=fingerabdruck,
            modules=args.modul or ["buchhalter"], license_type=args.typ,
            allowed_instances=args.instanzen, expiry_date=args.gueltig_bis,
            maintenance_until=args.wartung_bis, issuer=args.herausgeber,
            notes=args.hinweis, passphrase=args.passwort,
            target_dir=Path(args.ziel), product_version=args.produktversion,
        )
    except LicenseError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Lizenz ausgestellt: {lizenz.license_id}")
    for schluessel, wert in lizenz.summary().items():
        print(f"  {schluessel:16s}: {wert}")
    print()
    print(f"Abgelegt in: {ablage}")
    print("Diese beiden Dateien an den Kunden uebergeben:")
    print("  license.json")
    print("  license.sig")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lizenzen ausstellen (Hersteller)")
    sub = parser.add_subparsers(dest="befehl", required=True)

    schluessel = sub.add_parser("schluessel", help="Schluesselpaar erzeugen")
    schluessel.add_argument("--verzeichnis", default="geheim")
    schluessel.add_argument("--passwort", default="")
    schluessel.add_argument("--ueberschreiben", action="store_true")
    schluessel.set_defaults(func=cmd_schluessel)

    ausstellen = sub.add_parser("ausstellen", help="Lizenz ausstellen und signieren")
    ausstellen.add_argument("--schluessel", default="geheim/herausgeber_privat.pem")
    ausstellen.add_argument("--passwort", default="")
    ausstellen.add_argument("--anfrage", help="JSON-Datei der Aktivierungsanfrage")
    ausstellen.add_argument("--kunde", default="")
    ausstellen.add_argument("--kundennummer", default="")
    ausstellen.add_argument("--instanz", default="")
    ausstellen.add_argument("--fingerabdruck", default="")
    ausstellen.add_argument("--modul", action="append")
    ausstellen.add_argument("--typ", default="instanz")
    ausstellen.add_argument("--instanzen", type=int, default=1)
    ausstellen.add_argument("--gueltig-bis", dest="gueltig_bis", default=None)
    ausstellen.add_argument("--wartung-bis", dest="wartung_bis", default=None)
    ausstellen.add_argument("--herausgeber", default="")
    ausstellen.add_argument("--hinweis", default="")
    ausstellen.add_argument("--produktversion", default="0.1.0")
    ausstellen.add_argument("--ziel", default="lizenzen")
    ausstellen.set_defaults(func=cmd_ausstellen)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
