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

from pkc.branding import ORIGINAL_DATEI, ORIGINAL_ICON, VARIANTEN  # noqa: E402

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


def _beschnitt(bild):
    """Entfernt durchsichtige Raender rundherum.

    Das Original kann ungleichmaessigen Leerraum haben - beim gelieferten
    Symbol etwa 22 Bildpunkte links und 125 rechts. Ohne Beschnitt saehe das
    Icon sichtbar verrutscht aus. Das Zeichen selbst wird dabei nicht
    veraendert: gleiche Farben, gleiche Formen, gleiches Seitenverhaeltnis -
    es faellt nur der leere Rand weg.
    """
    kasten = bild.getchannel("A").getbbox() if bild.mode == "RGBA" else bild.getbbox()
    return bild.crop(kasten) if kasten else bild


def _quadratisch(bild, kante: int, rand: float = 0.06):
    """Legt das Bild mittig auf eine durchsichtige quadratische Flaeche.

    Ohne das wuerde ein breites Logo beim Erzeugen des Icons gestaucht -
    die Proportionen duerfen sich nicht aendern. Ein kleiner gleichmaessiger
    Rand bleibt stehen, damit das Zeichen in der Taskleiste nicht am
    Kachelrand klebt.
    """
    from PIL import Image

    kopie = _beschnitt(bild.copy())
    innen = max(1, int(kante * (1 - 2 * rand)))
    kopie.thumbnail((innen, innen), Image.LANCZOS)
    flaeche = Image.new("RGBA", (kante, kante), (0, 0, 0, 0))
    flaeche.paste(kopie, ((kante - kopie.width) // 2, (kante - kopie.height) // 2), kopie)
    return flaeche


def _erste_vorhandene(ordner, namen):
    """Nimmt die erste vorhandene Datei aus einer Liste moeglicher Namen.

    Der Auftraggeber soll seine Datei nicht umbenennen muessen, nur weil das
    Werkzeug einen bestimmten Namen erwartet.
    """
    for name in namen:
        pfad = ordner / name
        if pfad.is_file():
            return pfad
    # Sonst: irgendein PNG im Ordner, das nicht die Anleitung ist.
    for pfad in sorted(ordner.glob("*.png")):
        return pfad
    return None


def _auf_grund(bild, farbe):
    """Legt das Bild auf einen einfarbigen Grund - fuer helle/dunkle Flaechen."""
    from PIL import Image

    flaeche = Image.new("RGBA", bild.size, farbe)
    flaeche.alpha_composite(bild)
    return flaeche


def main() -> int:
    Image = _laden()

    assets = REPO / "assets"
    ordner = assets / "branding" / "original"
    ordner.mkdir(parents=True, exist_ok=True)

    # Breites Logo mit Schriftzug und quadratisches Symbol getrennt suchen.
    # Mehrere Namen sind erlaubt, damit niemand umbenennen muss.
    breit = _erste_vorhandene(ordner, [
        Path(ORIGINAL_DATEI).name,
        "portiva_logo.png", "portiva_logo_breit.png", "portiva_wortmarke.png",
    ])
    symbol_datei = _erste_vorhandene(ordner, [
        Path(ORIGINAL_ICON).name,
        "portiva_app_icon_512.png", "portiva_app_icon.png",
        "portiva_symbol.png", "portiva_icon.png",
    ])

    # Ist nur eine Datei da, entscheidet die Form: quadratisch = Symbol.
    if breit is not None and symbol_datei is not None and breit == symbol_datei:
        bild = Image.open(breit)
        if abs(bild.width / max(1, bild.height) - 1.0) < 0.15:
            breit = None                 # es ist ein Symbol, kein breites Logo
        else:
            symbol_datei = None

    if breit is None and symbol_datei is None:
        print(f"Kein Originallogo in {ordner}", file=sys.stderr)
        print("Siehe assets/branding/original/HIER_ORIGINAL_ABLEGEN.md", file=sys.stderr)
        return 1

    if breit is not None:
        original = breit
        quelle = Image.open(original).convert("RGBA")
        print(f"Hauptlogo   : {original.name}  {quelle.width}x{quelle.height}")
    else:
        original = symbol_datei
        quelle = Image.open(original).convert("RGBA")
        print(f"Hauptlogo   : {original.name}  {quelle.width}x{quelle.height}  "
              f"(Symbol - ein breites Logo mit Schriftzug liegt nicht vor)")

    geschrieben = []

    # Hauptlogo: nur skaliert, Seitenverhaeltnis unveraendert.
    haupt = _beschnitt(quelle.copy())
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

    # Symbol: quadratisch, ohne Verzerrung. Liegt ein eigenes Quadratsymbol
    # vor, wird es bevorzugt - aus einem breiten Logo abgeleitet wuerde der
    # Schriftzug bei 16 Pixeln unleserlich.
    if symbol_datei is not None:
        print(f"Symbolquelle: {symbol_datei.name} (eigenes Quadratsymbol)")
        symbol = _quadratisch(Image.open(symbol_datei).convert("RGBA"), 256)
    else:
        print("Symbolquelle: aus dem Hauptlogo abgeleitet "
              "(kein eigenes Quadratsymbol hinterlegt)")
        symbol = _quadratisch(quelle, 256)
    symbol.save(assets / VARIANTEN["icon"])
    geschrieben.append(assets / VARIANTEN["icon"])

    ico = assets / VARIANTEN["ico"]
    symbol.save(ico, format="ICO", sizes=ICON_GROESSEN)
    geschrieben.append(ico)

    print()
    for pfad in geschrieben:
        print(f"  geschrieben: {pfad.relative_to(REPO)}  ({pfad.stat().st_size} Bytes)")
    print(f"\nDie Originale blieben unveraendert.")
    if breit is None:
        print("\nHinweis: Ein breites Logo mit dem Schriftzug PORTIVA liegt nicht")
        print("vor. Als Hauptlogo dient deshalb das Symbol; der Schriftzug wird")
        print("in der Oberflaeche daneben als Text gesetzt. Wird das breite Logo")
        print("nachgereicht, genuegt ein erneuter Lauf dieses Werkzeugs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
