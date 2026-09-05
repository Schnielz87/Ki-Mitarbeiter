#!/usr/bin/env python3
"""Erzeugt die Brandingvarianten aus dem Originallogo.

Das Original wird **nie** veraendert oder ueberschrieben. Alle Varianten
entstehen nachvollziehbar daraus - wird das Original ausgetauscht, genuegt
ein erneuter Lauf.

    python tools/branding_ableiten.py

Braucht Pillow:

    pip install pillow

Bewusst kein Bestandteil der Anwendung: die Ableitung passiert einmal beim
Einrichten oder im Bauablauf, nicht zur Laufzeit auf dem Kundenrechner.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from pkc.branding import ORIGINAL_DATEI, VARIANTEN  # noqa: E402

#: Kantenlaengen der Icondatei. Windows waehlt daraus die passende aus;
#: ohne die kleinen Groessen sieht das Taskleistensymbol matschig aus.
ICON_GROESSEN = [(g, g) for g in (16, 24, 32, 48, 64, 128, 256)]

#: Breite der Logovarianten in Bildpunkten.
LOGO_BREITE = 900


def _laden():
    try:
        from PIL import Image
    except ImportError:
        print("Pillow fehlt. Installieren mit:  pip install pillow", file=sys.stderr)
        raise SystemExit(2)
    return Image


def _quadratisch(bild, kante: int):
    """Legt das Bild mittig auf eine durchsichtige quadratische Flaeche.

    Ohne das wuerde ein breites Logo beim Erzeugen des Icons gestaucht -
    die Proportionen duerfen sich nicht aendern.
    """
    from PIL import Image

    kopie = bild.copy()
    kopie.thumbnail((kante, kante), Image.LANCZOS)
    flaeche = Image.new("RGBA", (kante, kante), (0, 0, 0, 0))
    flaeche.paste(kopie, ((kante - kopie.width) // 2, (kante - kopie.height) // 2), kopie)
    return flaeche


def _auf_grund(bild, farbe):
    """Legt das Bild auf einen einfarbigen Grund - fuer helle/dunkle Flaechen."""
    from PIL import Image

    flaeche = Image.new("RGBA", bild.size, farbe)
    flaeche.alpha_composite(bild)
    return flaeche


def main() -> int:
    Image = _laden()

    assets = REPO / "assets"
    original = assets / ORIGINAL_DATEI
    if not original.is_file():
        print(f"Originallogo fehlt: {original}", file=sys.stderr)
        print("Siehe assets/branding/original/HIER_ORIGINAL_ABLEGEN.md", file=sys.stderr)
        return 1

    quelle = Image.open(original).convert("RGBA")
    print(f"Original: {original.name}  {quelle.width}x{quelle.height}")

    geschrieben = []

    # Hauptlogo: nur skaliert, Seitenverhaeltnis unveraendert.
    haupt = quelle.copy()
    if haupt.width > LOGO_BREITE:
        hoehe = round(haupt.height * LOGO_BREITE / haupt.width)
        haupt = haupt.resize((LOGO_BREITE, hoehe), Image.LANCZOS)
    ziel = assets / VARIANTEN["primary"]
    ziel.parent.mkdir(parents=True, exist_ok=True)
    haupt.save(ziel)
    geschrieben.append(ziel)

    # Fuer helle und dunkle Oberflaechen: derselbe Bildinhalt, nur auf
    # passendem Grund. Farben und Formen bleiben unveraendert.
    _auf_grund(haupt, (255, 255, 255, 255)).save(assets / VARIANTEN["light"])
    geschrieben.append(assets / VARIANTEN["light"])
    _auf_grund(haupt, (23, 32, 46, 255)).save(assets / VARIANTEN["dark"])
    geschrieben.append(assets / VARIANTEN["dark"])

    # Symbol: quadratisch, ohne Verzerrung.
    symbol = _quadratisch(quelle, 256)
    symbol.save(assets / VARIANTEN["icon"])
    geschrieben.append(assets / VARIANTEN["icon"])

    ico = assets / VARIANTEN["ico"]
    symbol.save(ico, format="ICO", sizes=ICON_GROESSEN)
    geschrieben.append(ico)

    print()
    for pfad in geschrieben:
        print(f"  geschrieben: {pfad.relative_to(REPO)}  ({pfad.stat().st_size} Bytes)")
    print(f"\nDas Original blieb unveraendert: {original.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
