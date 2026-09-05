"""PORTIVA-Branding: Marke fest, Profil dynamisch, Pfade relativ.

Der Kern der Vorgabe: PORTIVA ist die Plattformmarke und aendert sich nie.
Der Mitarbeitername kommt aus dem aktiven Berufsprofil und darf nirgends
fest im Programmcode stehen. Alles muss offline und nach einem Wechsel des
Laufwerksbuchstabens unveraendert funktionieren.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from pkc.branding import (CLAIM, MARKE, ORIGINAL_DATEI, VARIANTEN, Brand,
                          load_brand, profilname)

ROOT = Path(__file__).resolve().parents[1]


class ProfilDoppel:
    def __init__(self, **felder):
        for name, wert in felder.items():
            setattr(self, name, wert)


# ---------------------------------------------------------------- Marke
def test_marke_ist_fest_und_heisst_portiva():
    assert MARKE == "PORTIVA"
    assert CLAIM == "Portable KI-Mitarbeiter-Plattform"


def test_titel_verbindet_marke_und_profil():
    brand = Brand()
    assert brand.titel("Buchhalter") == "PORTIVA - Buchhalter"
    assert brand.titel("Controller") == "PORTIVA - Controller"
    assert brand.titel("Rechtsabteilung") == "PORTIVA - Rechtsabteilung"


def test_titel_ohne_profil_ist_nur_die_marke():
    assert Brand().titel("") == "PORTIVA"
    assert Brand().titel("   ") == "PORTIVA"


def test_profilname_kommt_aus_dem_profil_nie_aus_dem_code():
    """Ein Profilwechsel muss ohne Programmaenderung wirken."""
    assert profilname(ProfilDoppel(short_name="Buchhalter")) == "Buchhalter"
    assert profilname(ProfilDoppel(short_name="Controller")) == "Controller"
    # Faellt auf die naechstbeste Angabe zurueck
    assert profilname(ProfilDoppel(name="Einkauf")) == "Einkauf"
    assert profilname(ProfilDoppel(profile_id="recht")) == "recht"
    assert profilname(ProfilDoppel()) == ""


def test_echtes_buchhalterprofil_ergibt_portiva_buchhalter():
    """Gegen das tatsaechlich ausgelieferte Profil, nicht gegen ein Doppel."""
    daten = json.loads(
        (ROOT / "src/profiles/buchhalter/profile.json").read_text(encoding="utf-8"))
    profil = ProfilDoppel(**daten)
    assert Brand().titel(profilname(profil)) == "PORTIVA - Buchhalter"


# ---------------------------------------------------------------- Pfade
def test_fehlende_dateien_werden_gemeldet_nicht_erfunden(tmp_path):
    """Ohne Logo kein Absturz - und kein Ersatzlogo."""
    brand = Brand(asset_root=tmp_path)
    assert brand.logo_pfad is None
    assert brand.icon_pfad is None
    assert set(brand.fehlende_dateien()) == set(VARIANTEN.values())
    # Der Titel funktioniert trotzdem
    assert brand.titel("Buchhalter") == "PORTIVA - Buchhalter"


def test_absolute_pfade_werden_abgewiesen(tmp_path):
    """Ein absoluter Pfad ueberlebt den Wechsel des Laufwerks nicht."""
    (tmp_path / "branding").mkdir()
    datei = tmp_path / "branding" / "x.png"
    datei.write_bytes(b"\x89PNG")
    brand = Brand(asset_root=tmp_path, logo=str(datei))
    assert brand.logo_pfad is None, "absolute Pfade duerfen nicht greifen"


def test_pfad_kann_nicht_aus_dem_assetbereich_ausbrechen(tmp_path):
    geheim = tmp_path.parent / "geheim.png"
    geheim.write_bytes(b"\x89PNG")
    brand = Brand(asset_root=tmp_path, logo="../geheim.png")
    assert brand.logo_pfad is None


def test_branding_ueberlebt_den_ortswechsel(tmp_path):
    """Derselbe Bestand an einem anderen Ort - gleiches Ergebnis.

    Das bildet den Wechsel des Laufwerksbuchstabens nach: die Anwendung
    findet ihre Assets ueber relative Pfade, nicht ueber D: oder E:.
    """
    erst = tmp_path / "Laufwerk D" / "assets"
    (erst / "branding").mkdir(parents=True)
    (erst / "branding" / "portiva_logo_primary.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    brand_d = Brand(asset_root=erst)
    assert brand_d.logo_pfad is not None

    zweit = tmp_path / "Laufwerk E mit Leerzeichen" / "assets"
    zweit.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(erst, zweit)

    brand_e = Brand(asset_root=zweit)
    assert brand_e.logo_pfad is not None
    assert brand_e.logo_pfad != brand_d.logo_pfad, "es ist wirklich ein anderer Ort"
    assert brand_e.titel("Buchhalter") == brand_d.titel("Buchhalter")


# ---------------------------------------------------------------- Laden
def test_brand_json_wird_gelesen(portable_root):
    ziel = portable_root.get("config") / "brand.json"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps({"brand": {
        "name": "PORTIVA", "claim": "Eigener Zusatz",
        "logo": "branding/eigen.png", "icon": "branding/eigen.ico"}}),
        encoding="utf-8")

    brand = load_brand(portable_root)
    assert brand.name == "PORTIVA"
    assert brand.claim == "Eigener Zusatz"
    assert brand.logo == "branding/eigen.png"


def test_kaputte_brand_json_bricht_nichts_ab(portable_root):
    ziel = portable_root.get("config") / "brand.json"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text("{kein json", encoding="utf-8")

    brand = load_brand(portable_root)
    assert brand.name == MARKE, "Vorgaben muessen greifen, statt abzustuerzen"


def test_ausgeliefertes_brand_json_ist_gueltig_und_relativ():
    daten = json.loads((ROOT / "config" / "brand.json").read_text(encoding="utf-8"))
    marke = daten["brand"]
    assert marke["name"] == "PORTIVA"
    assert marke["claim"] == CLAIM
    for schluessel in ("logo", "icon"):
        pfad = marke[schluessel]
        assert not Path(pfad).is_absolute(), f"{schluessel} muss relativ sein"
        assert ":" not in pfad, f"{schluessel} darf keinen Laufwerksbuchstaben enthalten"


def test_kein_laufwerksbuchstabe_im_brandingcode():
    """Masterprompt: keine absoluten Laufwerkspfade fuer Brandingdateien."""
    import re

    quelle = (ROOT / "src/pkc/branding.py").read_text(encoding="utf-8")
    assert not re.search(r"[A-Za-z]:\\\\", quelle)
    assert "C:/" not in quelle and "D:/" not in quelle


def test_original_wird_nie_ueberschrieben():
    """Das Ableitungswerkzeug schreibt Varianten, nie das Original."""
    werkzeug = (ROOT / "tools" / "branding_ableiten.py").read_text(encoding="utf-8")
    assert "original.save" not in werkzeug
    assert "quelle.save" not in werkzeug
    assert ORIGINAL_DATEI in werkzeug or "ORIGINAL_DATEI" in werkzeug
