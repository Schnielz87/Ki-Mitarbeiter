#!/usr/bin/env python3
"""Hilft beim Einrichten des lokalen Sprachmodells.

Drei Aufgaben:

1. ``empfehlen``  - prueft die Hardware und schlaegt ein passendes Modell vor
2. ``laden``      - laedt eine GGUF-Datei nach ./models (mit Pruefsumme)
3. ``pruefen``    - prueft, ob ein vorhandenes Modell tatsaechlich antwortet

Das Werkzeug laedt **nichts** ohne ausdrueckliche Angabe einer Adresse: die
Bezugsquellen und Lizenzbedingungen soll der Betreiber bewusst waehlen.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pkc.hardware import PROFILES, detect, recommend_profile  # noqa: E402
from pkc.llm.base import ChatMessage  # noqa: E402
from pkc.llm.manager import RECOMMENDED_MODELS, discover_models  # noqa: E402
from pkc.llm.providers import LlamaCppProvider, OpenAICompatibleProvider  # noqa: E402
from pkc.paths import get_paths  # noqa: E402


def cmd_empfehlen(args) -> int:
    paths = get_paths()
    info = detect(paths.root)
    profile = recommend_profile(info)
    print("Erkannte Hardware")
    print(f"  Betriebssystem : {info.os_name} {info.machine}")
    print(f"  Prozessor      : {info.cpu_name or 'unbekannt'} ({info.cpu_cores or '?'} Kerne)")
    print(f"  Arbeitsspeicher: {info.ram_total_gb if info.ram_total_gb else 'unbekannt'} GB")
    print(f"  Grafikkarte    : {info.gpu_name or 'keine erkannt'}"
          + (f" ({info.vram_gb} GB)" if info.vram_gb else ""))
    print(f"  Freier Platz   : {info.free_disk_gb} GB auf {paths.root}")
    print()
    print(f"Empfohlenes Profil: {PROFILES[profile]['label']}")
    print(f"  {PROFILES[profile]['description']}")
    print()
    print("Modellvorschlaege (alle mit freier Lizenz):")
    for key, entry in RECOMMENDED_MODELS.items():
        mark = ">>" if key == profile else "  "
        print(f"{mark} {PROFILES[key]['label']:14s} {entry['name']}")
        print(f"     Lizenz {entry['licence']} · etwa {entry['size_gb']} GB · "
              f"mindestens {entry['min_ram_gb']} GB RAM")
        print(f"     {entry['note']}")
    print()
    print("Vorhandene Modelle in", paths.get("models"))
    models = discover_models(paths.get("models"))
    if not models:
        print("  (keines)")
    for model in models:
        print(f"  {model.name}  {model.size_gb} GB  Quantisierung {model.quantisation}")
    print()
    print("Naechster Schritt: die gewuenschte GGUF-Datei nach ./models legen -")
    print("entweder von Hand oder mit:")
    print("  python tools/modell_einrichten.py laden <URL> [--sha256 <pruefsumme>]")
    return 0


def cmd_laden(args) -> int:
    paths = get_paths()
    target_dir = paths.get("models")
    target_dir.mkdir(parents=True, exist_ok=True)
    name = args.name or args.url.split("/")[-1].split("?")[0]
    if not name.endswith(".gguf"):
        print("Warnung: die Datei endet nicht auf .gguf - wird sie erkannt?", file=sys.stderr)
    target = target_dir / name
    if target.exists() and not args.ueberschreiben:
        print(f"Es gibt bereits {target}. Mit --ueberschreiben erneut laden.")
        return 1

    free = shutil.disk_usage(target_dir).free / 1024**3
    print(f"Freier Speicher am Ziel: {free:.1f} GB")
    print(f"Lade {args.url}\n  nach {target}")

    temporary = target.with_suffix(".gguf.teil")
    digest = hashlib.sha256()
    started = time.monotonic()
    try:
        request = urllib.request.Request(args.url, headers={"User-Agent": "Portabler-KI-Mitarbeiter"})
        with urllib.request.urlopen(request, timeout=60) as response, \
                temporary.open("wb") as handle:
            total = int(response.headers.get("Content-Length", 0))
            done = 0
            while True:
                block = response.read(1024 * 512)
                if not block:
                    break
                handle.write(block)
                digest.update(block)
                done += len(block)
                if total:
                    percent = done * 100 / total
                    speed = done / max(time.monotonic() - started, 0.001) / 1024**2
                    print(f"\r  {percent:5.1f} %  {done/1024**3:5.2f} von "
                          f"{total/1024**3:5.2f} GB  {speed:5.1f} MB/s", end="", flush=True)
        print()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        temporary.unlink(missing_ok=True)
        print(f"\nDownload fehlgeschlagen: {exc}", file=sys.stderr)
        return 1

    checksum = digest.hexdigest()
    print(f"SHA-256: {checksum}")
    if args.sha256 and args.sha256.lower() != checksum:
        temporary.unlink(missing_ok=True)
        print("Die Pruefsumme stimmt NICHT. Die Datei wurde verworfen.", file=sys.stderr)
        return 2
    if args.sha256:
        print("Pruefsumme bestaetigt.")
    else:
        print("Hinweis: es wurde keine erwartete Pruefsumme angegeben - "
              "die Datei ist damit nicht gegen Manipulation geprueft.")
    temporary.replace(target)
    print(f"Fertig: {target} ({target.stat().st_size / 1024**3:.2f} GB)")
    print("Naechster Schritt: python tools/modell_einrichten.py pruefen")
    return 0


def cmd_pruefen(args) -> int:
    paths = get_paths()
    if args.server:
        provider = OpenAICompatibleProvider(args.server, model=args.modell or "local",
                                            name="local-server")
    else:
        models = discover_models(paths.get("models"))
        if not models:
            print(f"Kein GGUF-Modell in {paths.get('models')} gefunden.", file=sys.stderr)
            return 1
        chosen = max(models, key=lambda m: m.size_gb)
        print(f"Pruefe {chosen.name} ({chosen.size_gb} GB)")
        provider = LlamaCppProvider(chosen.path)

    ok, detail = provider.available()
    print(f"Bereit: {ok} - {detail}")
    if not ok:
        return 1

    print("\nStelle eine Testfrage ...")
    started = time.monotonic()
    try:
        response = provider.generate(
            [ChatMessage("system", "Antworte knapp auf Deutsch."),
             ChatMessage("user", "Nenne in einem Satz, wofuer § 14 UStG steht.")],
            max_tokens=120,
        )
    except Exception as exc:
        print(f"Das Modell hat NICHT geantwortet: {exc}", file=sys.stderr)
        return 2
    elapsed = time.monotonic() - started
    print(f"\nAntwort nach {elapsed:.1f} s:\n{response.text}\n")
    if response.completion_tokens:
        print(f"Geschwindigkeit: etwa {response.completion_tokens/elapsed:.1f} Token je Sekunde")
    print("Das Modell ist einsatzbereit.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lokales Sprachmodell einrichten")
    sub = parser.add_subparsers(dest="command", required=True)

    empfehlen = sub.add_parser("empfehlen", help="Hardware pruefen und Modell vorschlagen")
    empfehlen.set_defaults(func=cmd_empfehlen)

    laden = sub.add_parser("laden", help="GGUF-Datei nach ./models laden")
    laden.add_argument("url")
    laden.add_argument("--name", default="", help="Dateiname im Modellordner")
    laden.add_argument("--sha256", default="", help="erwartete Pruefsumme")
    laden.add_argument("--ueberschreiben", action="store_true")
    laden.set_defaults(func=cmd_laden)

    pruefen = sub.add_parser("pruefen", help="Antwortet das Modell tatsaechlich?")
    pruefen.add_argument("--server", default="", help="Adresse eines llama-server")
    pruefen.add_argument("--modell", default="")
    pruefen.set_defaults(func=cmd_pruefen)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
