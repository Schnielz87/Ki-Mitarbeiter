"""Softwareupdates getrennt vom Wissensupdate (Masterprompt 65).

Kernzusage: Ein fehlerhaftes Update darf eine funktionierende
Kundeninstallation nicht unkontrolliert zerstoeren.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from pkc.licensing.issue import generate_keypair
from pkc.updater.software import (
    MANIFEST_NAME, SoftwareUpdateError, SoftwareUpdater, build_package,
)


@pytest.fixture
def installation(tmp_path):
    """Eine bestehende Installation mit Programm- und Kundendaten."""
    wurzel = tmp_path / "installation"
    (wurzel / "src" / "pkc").mkdir(parents=True)
    (wurzel / "src" / "pkc" / "modul.py").write_text("# Fassung 1\n", encoding="utf-8")
    (wurzel / "start.py").write_text("print('alt')\n", encoding="utf-8")
    (wurzel / "database").mkdir()
    (wurzel / "database" / "company.db").write_bytes(b"Unternehmensgedaechtnis")
    return wurzel, SoftwareUpdater(wurzel, tmp_path / "sicherungen")


@pytest.fixture
def neue_fassung(tmp_path):
    """Quelle fuer ein Paket mit einer neueren Fassung."""
    quelle = tmp_path / "neu"
    (quelle / "src" / "pkc").mkdir(parents=True)
    (quelle / "src" / "pkc" / "modul.py").write_text("# Fassung 2\n", encoding="utf-8")
    (quelle / "start.py").write_text("print('neu')\n", encoding="utf-8")
    return quelle


def test_paket_wird_geprueft_bevor_etwas_passiert(installation, neue_fassung, tmp_path):
    wurzel, updater = installation
    paket = build_package(neue_fassung, ["src/pkc/modul.py", "start.py"],
                          tmp_path / "update.zip", "0.2.0", notes="Testfassung")
    info = updater.inspect(paket)
    assert info.version == "0.2.0" and info.file_count == 2
    assert not info.signed
    assert any("nicht signiert" in w for w in info.warnings)
    # inspect veraendert nichts
    assert (wurzel / "start.py").read_text(encoding="utf-8") == "print('alt')\n"


def test_update_wird_eingespielt_und_ist_ruecknehmbar(installation, neue_fassung, tmp_path):
    wurzel, updater = installation
    paket = build_package(neue_fassung, ["src/pkc/modul.py", "start.py"],
                          tmp_path / "update.zip", "0.2.0")

    ergebnis = updater.apply(paket)
    assert ergebnis["status"] == "eingespielt" and ergebnis["version"] == "0.2.0"
    assert (wurzel / "start.py").read_text(encoding="utf-8") == "print('neu')\n"
    # Kundendaten unberuehrt
    assert (wurzel / "database" / "company.db").read_bytes() == b"Unternehmensgedaechtnis"

    zurueck = updater.rollback(Path(ergebnis["sicherung"]))
    assert "start.py" in zurueck["wiederhergestellt"]
    assert (wurzel / "start.py").read_text(encoding="utf-8") == "print('alt')\n"


def test_trockenlauf_schreibt_nichts(installation, neue_fassung, tmp_path):
    wurzel, updater = installation
    paket = build_package(neue_fassung, ["start.py"], tmp_path / "u.zip", "0.2.0")
    ergebnis = updater.apply(paket, dry_run=True)
    assert ergebnis["status"] == "trockenlauf"
    assert (wurzel / "start.py").read_text(encoding="utf-8") == "print('alt')\n"


def test_beschaedigtes_paket_wird_abgewiesen(installation, neue_fassung, tmp_path):
    """Stimmt eine Pruefsumme nicht, wird gar nichts eingespielt."""
    wurzel, updater = installation
    paket = build_package(neue_fassung, ["start.py"], tmp_path / "u.zip", "0.2.0")

    # Inhalt nachtraeglich veraendern, Manifest unveraendert lassen
    manipuliert = tmp_path / "manipuliert.zip"
    with zipfile.ZipFile(paket) as alt, zipfile.ZipFile(manipuliert, "w") as neu:
        for eintrag in alt.namelist():
            daten = alt.read(eintrag)
            if eintrag == "start.py":
                daten = b"print('untergeschoben')\n"
            neu.writestr(eintrag, daten)

    with pytest.raises(SoftwareUpdateError) as fehler:
        updater.inspect(manipuliert)
    assert "Pruefsumme" in str(fehler.value)
    assert (wurzel / "start.py").read_text(encoding="utf-8") == "print('alt')\n"


def test_paket_darf_keine_kundendaten_anfassen(installation, tmp_path):
    """Ein Softwarepaket, das an die Datenbank will, wird abgewiesen."""
    wurzel, updater = installation
    boese = tmp_path / "boese"
    (boese / "database").mkdir(parents=True)
    (boese / "database" / "company.db").write_bytes(b"ueberschrieben")
    paket = build_package(boese, ["database/company.db"], tmp_path / "b.zip", "9.9.9")

    with pytest.raises(SoftwareUpdateError) as fehler:
        updater.inspect(paket)
    assert "geschuetzte Bereiche" in str(fehler.value)
    assert (wurzel / "database" / "company.db").read_bytes() == b"Unternehmensgedaechtnis"


def test_paket_mit_pfadausbruch_wird_abgewiesen(installation, tmp_path):
    wurzel, updater = installation
    paket = tmp_path / "ausbruch.zip"
    manifest = {"version": "1.0", "released": "", "notes": "",
                "files": {"../../ausserhalb.py": "0" * 64}}
    with zipfile.ZipFile(paket, "w") as archiv:
        archiv.writestr(MANIFEST_NAME, json.dumps(manifest))
        archiv.writestr("../../ausserhalb.py", "x")
    with pytest.raises(SoftwareUpdateError) as fehler:
        updater.inspect(paket)
    assert "ausserhalb" in str(fehler.value)


def test_paket_ohne_manifest_wird_abgewiesen(installation, tmp_path):
    _, updater = installation
    paket = tmp_path / "ohne.zip"
    with zipfile.ZipFile(paket, "w") as archiv:
        archiv.writestr("start.py", "print('x')")
    with pytest.raises(SoftwareUpdateError) as fehler:
        updater.inspect(paket)
    assert "fehlt" in str(fehler.value)


def test_signiertes_paket(installation, neue_fassung, tmp_path):
    """Mit Pruefschluessel wird die Herkunft belegt."""
    wurzel, _ = installation
    privat, oeffentlich = generate_keypair(tmp_path / "p.pem", tmp_path / "o.pem")
    paket = build_package(neue_fassung, ["start.py"], tmp_path / "signiert.zip",
                          "0.3.0", private_key_path=privat)

    updater = SoftwareUpdater(wurzel, tmp_path / "sicherungen",
                              public_key_pem=oeffentlich.read_bytes())
    info = updater.inspect(paket)
    assert info.signed and info.signature_ok is True
    assert not info.warnings


def test_fremd_signiertes_paket_wird_abgewiesen(installation, neue_fassung, tmp_path):
    wurzel, _ = installation
    fremd, _ = generate_keypair(tmp_path / "f.pem", tmp_path / "f.pub")
    _, echt_oeffentlich = generate_keypair(tmp_path / "e.pem", tmp_path / "e.pub")
    paket = build_package(neue_fassung, ["start.py"], tmp_path / "fremd.zip",
                          "0.3.0", private_key_path=fremd)

    updater = SoftwareUpdater(wurzel, tmp_path / "s",
                              public_key_pem=echt_oeffentlich.read_bytes())
    with pytest.raises(SoftwareUpdateError) as fehler:
        updater.inspect(paket)
    assert "Signatur" in str(fehler.value)


def test_fehlerhaftes_einspielen_setzt_automatisch_zurueck(
    installation, neue_fassung, tmp_path, monkeypatch
):
    """Der wichtigste Fall: ein Update, das mittendrin scheitert."""
    wurzel, updater = installation
    paket = build_package(neue_fassung, ["src/pkc/modul.py", "start.py"],
                          tmp_path / "u.zip", "0.2.0")

    from pkc.updater import software as modul

    echt = modul._sha256
    aufrufe = {"n": 0}

    def kaputt(pfad):
        aufrufe["n"] += 1
        if aufrufe["n"] > 1:          # die zweite Nachpruefung schlaegt fehl
            return "0" * 64
        return echt(pfad)

    monkeypatch.setattr(modul, "_sha256", kaputt)
    ergebnis = updater.apply(paket)

    assert ergebnis["status"] == "zurueckgesetzt"
    assert "Pruefsummen" in ergebnis["fehler"]
    # Die Installation ist auf dem alten Stand - nichts ist kaputt
    assert (wurzel / "start.py").read_text(encoding="utf-8") == "print('alt')\n"
    assert (wurzel / "src" / "pkc" / "modul.py").read_text(encoding="utf-8") == "# Fassung 1\n"
    assert (wurzel / "database" / "company.db").read_bytes() == b"Unternehmensgedaechtnis"


def test_verlauf_der_softwareupdates(installation, neue_fassung, tmp_path):
    wurzel, updater = installation
    for nummer, fassung in enumerate(("0.2.0", "0.3.0"), start=1):
        (neue_fassung / "start.py").write_text(f"print('{fassung}')\n", encoding="utf-8")
        paket = build_package(neue_fassung, ["start.py"],
                              tmp_path / f"u{nummer}.zip", fassung)
        updater.apply(paket)
    verlauf = updater.history()
    assert len(verlauf) == 2, (
        "Zwei Updates in derselben Sekunde duerfen sich die Sicherung nicht "
        "ueberschreiben - sonst geht der Ruecksetzpunkt verloren."
    )
    assert {e["neue_version"] for e in verlauf} == {"0.2.0", "0.3.0"}

    # Und die aeltere Sicherung fuehrt wirklich auf den Ursprungsstand zurueck
    aelteste = min(verlauf, key=lambda e: e["neue_version"])
    updater.rollback(Path(aelteste["sicherung"]))
    assert (wurzel / "start.py").read_text(encoding="utf-8") == "print('alt')\n"
