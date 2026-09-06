#!/usr/bin/env python3
"""Packt einen Ordner zu einem Plugin-Paket (.kimplug) - und signiert es.

Aufruf:

    python tools/plugin_packen.py examples/plugin_html --ziel dist/html_export
    python tools/plugin_packen.py <ordner> --schluessel privat.pem [--passwort ...]

Ohne Schluessel entsteht ein **unsigniertes** Paket. Es laesst sich
installieren, gilt aber nicht als vertrauenswuerdig: die Anwendung sagt das
vor der Installation deutlich. Der private Schluessel des Herausgebers
gehoert niemals in die Kundenanwendung (Masterprompt 86).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pkc.plugins import Manifest, packen, signaturdaten  # noqa: E402
from pkc.plugins.paket import MANIFEST  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plugin-Paket erstellen")
    parser.add_argument("ordner", help="Ordner mit manifest.json und dem Code")
    parser.add_argument("--ziel", default="", help="Zieldatei (ohne Endung moeglich)")
    parser.add_argument("--schluessel", default="", help="privater Ed25519-Schluessel (PEM)")
    parser.add_argument("--passwort", default="", help="Passwort des Schluessels")
    args = parser.parse_args(argv)

    quelle = Path(args.ordner)
    daten = json.loads((quelle / MANIFEST).read_text(encoding="utf-8"))
    ziel = Path(args.ziel) if args.ziel else quelle.parent / str(daten.get("id", "plugin"))

    signatur = b""
    if args.schluessel:
        from pkc.licensing.issue import load_private_key

        # Die Pruefsummen stehen erst nach dem Sammeln fest - deshalb wird
        # zweimal gepackt: einmal, um das vollstaendige Manifest zu bekommen,
        # danach mit der Signatur darueber.
        vorlaeufig = packen(quelle, ziel.with_name(ziel.stem + "_ohne_signatur"), daten)
        import zipfile

        with zipfile.ZipFile(vorlaeufig) as archiv:
            manifest = Manifest.from_dict(json.loads(archiv.read(MANIFEST)))
        vorlaeufig.unlink()
        schluessel = load_private_key(Path(args.schluessel), args.passwort)
        signatur = schluessel.sign(signaturdaten(manifest))
        daten = manifest.as_dict()

    fertig = packen(quelle, ziel, daten, signatur)
    print(f"Paket erstellt: {fertig}")
    print("signiert" if signatur else
          "NICHT signiert - die Anwendung weist bei der Installation darauf hin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
