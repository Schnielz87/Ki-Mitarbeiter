"""Das Quellenregister gegen die echten Adressen pruefen.

Warum ein eigenes Werkzeug und nicht ein paar Zeilen im Bauablauf?

Ein Abruf mit einem fremden Werkzeug beweist nur, dass *irgendein* Programm
die Adresse erreicht. Fuer die Anwendung zaehlt aber, ob **sie** sie erreicht:
mit ihrem Nutzerkennzeichen, ihrem Zertifikatsspeicher, ihrer Beachtung von
robots.txt und ihren Wiederholungen. Genau das macht dieses Werkzeug - es
benutzt denselben HTTP-Zugriff wie der Wissensabgleich.

Aufruf::

    python tools/quellen_pruefen.py [--register config/source_registry.json]
                                    [--ziel ergebnis.json] [--quelle Q01_...]

Der Rueckgabewert ist 0, wenn jede Adresse erreichbar war, sonst 1. Der
Bauablauf ruft das Werkzeug mit ``continue-on-error`` auf: eine amtliche
Seite, die gerade umgebaut wird, ist ein Befund - kein Baufehler.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

from pkc.updater.http_client import HttpClient      # noqa: E402


def pruefen(register: Path, nur: str = "", zeitgrenze: float = 45.0) -> list[dict]:
    daten = json.loads(register.read_text(encoding="utf-8"))
    # Der Abgleich laedt die Dokumente wirklich - deshalb dieselbe
    # Hoeflichkeit wie im Betrieb: Pause je Server, echte Kopfzeilen.
    client = HttpClient(timeout=zeitgrenze, min_delay=1.0)
    heute = date.today().isoformat()
    zeilen: list[dict] = []

    for quelle in daten.get("sources", []):
        kennung = str(quelle.get("source_id", ""))
        if nur and kennung != nur:
            continue
        for dokument in quelle.get("documents", []):
            adresse = str(dokument.get("url", ""))
            ergebnis = client.fetch(adresse)
            zeilen.append({
                "quelle": kennung,
                "dokument": str(dokument.get("doc_uid", "")),
                "url": adresse,
                "status": int(ergebnis.status or 0),
                "erreichbar": bool(ergebnis.ok),
                "groesse_bytes": ergebnis.size,
                "art": ergebnis.content_type,
                "fehler": ergebnis.error or "",
                "geprueft_am": heute,
            })
    return zeilen


def bericht(zeilen: list[dict]) -> str:
    breite = max((len(z["dokument"]) for z in zeilen), default=8)
    reihen = [f"{'Quelle':<24} {'Dokument':<{breite}} {'Status':>6}  Befund"]
    for zeile in zeilen:
        befund = "in Ordnung" if zeile["erreichbar"] else (zeile["fehler"] or "nicht erreichbar")
        reihen.append(f"{zeile['quelle']:<24} {zeile['dokument']:<{breite}} "
                      f"{zeile['status']:>6}  {befund[:90]}")
    erreichbar = sum(1 for z in zeilen if z["erreichbar"])
    reihen.append("")
    reihen.append(f"ERREICHBAR: {erreichbar} von {len(zeilen)}")
    if erreichbar < len(zeilen):
        reihen.append("Nicht erreichbar:")
        for zeile in zeilen:
            if not zeile["erreichbar"]:
                reihen.append(f"  {zeile['quelle']}/{zeile['dokument']}: {zeile['url']}")
                reihen.append(f"      {zeile['fehler'] or 'ohne Meldung'}")
    return "\n".join(reihen)


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    zerleger.add_argument("--register", default=str(WURZEL / "config" / "source_registry.json"))
    zerleger.add_argument("--ziel", default="", help="Ergebnis als JSON ablegen")
    zerleger.add_argument("--quelle", default="", help="nur diese Quelle pruefen")
    zerleger.add_argument("--zeitgrenze", type=float, default=45.0)
    argumente = zerleger.parse_args(argv)

    zeilen = pruefen(Path(argumente.register), argumente.quelle, argumente.zeitgrenze)
    print(bericht(zeilen))
    if argumente.ziel:
        Path(argumente.ziel).write_text(
            json.dumps(zeilen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if all(z["erreichbar"] for z in zeilen) else 1


if __name__ == "__main__":
    raise SystemExit(main())
