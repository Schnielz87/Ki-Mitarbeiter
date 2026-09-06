"""Produktunterlagen, Telemetriefreiheit und Reifegrad (Masterprompt 63-77)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from pkc.product import (
    build_license_register, build_sbom, check_readiness, collect_components,
    open_questions,
)
from pkc.product.dossier import build_release_dossier

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------- Telemetrie (Abschnitt 69)
def test_keine_telemetrie_im_normalbetrieb(portable_root, monkeypatch):
    """Der Grundbetrieb baut keine ausgehende Verbindung auf.

    Dies belegt die Zusage aus KOMMERZIELLES_KONZEPT.md. Eine Behauptung im
    Dokument allein waere wertlos - hier wird jeder Netzzugriff abgefangen.
    """
    from test_controller import make_controller

    versuche: list[str] = []

    def aufzeichnen(request, *args, **kwargs):
        adresse = getattr(request, "full_url", str(request))
        versuche.append(adresse)
        raise AssertionError(f"Unerwarteter Netzzugriff: {adresse}")

    monkeypatch.setattr("urllib.request.urlopen", aufzeichnen)

    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        controller.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")
        controller.remember_manual("company.name", "Name", "Muster GmbH", "profile")
        controller.export_company_profile()
        controller.backup("telemetrietest")
        controller.status()
        controller.versions()
    finally:
        controller.shutdown()

    assert versuche == [], f"Es wurde nach aussen verbunden: {versuche}"


def test_kein_fernzugriff_im_code():
    """Abschnitt 68: kein dauerhaft versteckter Fernzugriff."""
    verdaechtig = re.compile(
        r"\b(socketserver|http\.server|ThreadingHTTPServer|socket\.bind|"
        r"listen\(|paramiko|telnetlib|pty\.spawn|reverse_shell)\b"
    )
    treffer: list[str] = []
    for pfad in (ROOT / "src").rglob("*.py"):
        for nummer, zeile in enumerate(pfad.read_text(encoding="utf-8").splitlines(), 1):
            if verdaechtig.search(zeile) and not zeile.strip().startswith("#"):
                treffer.append(f"{pfad.relative_to(ROOT)}:{nummer}: {zeile.strip()}")
    assert not treffer, "Moeglicher Fernzugriff im Programmcode:\n" + "\n".join(treffer)


#: Reine Nachschlagewerke: hier stehen Quellenangaben, die nie abgerufen
#: werden. Sie duerfen Adressen enthalten - dass dort nicht verbunden wird,
#: prueft ``test_nachschlagewerke_verbinden_nicht``.
_NUR_NACHSCHLAGEWERK = {"pkc/product/components.py"}


def test_ausgehende_adressen_sind_nur_die_erklaerten():
    """Adressen im ausfuehrenden Code muessen erklaerbar sein.

    Zweck: es soll keine Adresse geben, zu der die Anwendung unbemerkt
    verbinden koennte. Quellenangaben in Nachschlagewerken sind davon
    ausgenommen - dort wird nichts abgerufen.
    """
    muster = re.compile(r"https?://[\w.\-]+")
    gefunden: dict[str, str] = {}
    for pfad in (ROOT / "src").rglob("*.py"):
        relativ = pfad.relative_to(ROOT / "src").as_posix()
        if relativ in _NUR_NACHSCHLAGEWERK:
            continue
        for adresse in muster.findall(pfad.read_text(encoding="utf-8")):
            gefunden.setdefault(adresse, relativ)

    erlaubt_teile = (
        "127.0.0.1", "localhost",                                 # lokaler Modelldienst
        "gesetze-im-internet.de", "bundesfinanzministerium.de",   # Netzstatuspruefung
        "example",                                                # Beispiele
        # XML-Namensraeume der Office-Formate. Das sind Kennungen, keine
        # Abrufadressen: sie stehen in jeder DOCX-, XLSX- und PPTX-Datei und
        # werden nie aufgerufen. Der folgende Test sichert das ab.
        "schemas.openxmlformats.org", "purl.org", "www.w3.org", "schemas.",
    )
    unerklaert = {
        adresse: datei for adresse, datei in gefunden.items()
        if not any(teil in adresse for teil in erlaubt_teile)
    }
    assert not unerklaert, (
        "Nicht erklaerte fest hinterlegte Adressen im ausfuehrenden Code: "
        + ", ".join(f"{a} ({d})" for a, d in sorted(unerklaert.items()))
    )


def test_dateiformate_verbinden_nicht():
    """Die Formatschreiber duerfen keine Netzverbindung aufbauen.

    Sie enthalten Adressen - aber nur als XML-Namensraeume. Wuerde dort
    jemals ein Abruf hinzukommen, faellt dieser Test.
    """
    netz = re.compile(r"\b(urlopen|urlretrieve|requests\.|httpx\.|socket\.)")
    for datei in (ROOT / "src" / "pkc" / "artefakte").glob("*.py"):
        treffer = [z.strip() for z in datei.read_text(encoding="utf-8").splitlines()
                   if netz.search(z)]
        assert not treffer, f"{datei.name} enthaelt Netzzugriffe: {treffer}"


def test_nachschlagewerke_verbinden_nicht():
    """In den Nachschlagewerken darf kein Netzzugriff stehen."""
    netz = re.compile(r"\b(urlopen|urlretrieve|requests\.|httpx\.|socket\.)")
    for relativ in _NUR_NACHSCHLAGEWERK:
        text = (ROOT / "src" / relativ).read_text(encoding="utf-8")
        treffer = [z.strip() for z in text.splitlines() if netz.search(z)]
        assert not treffer, f"{relativ} enthaelt Netzzugriffe: {treffer}"


# ------------------------------------------- Lizenzregister und SBOM (63, 64)
def test_lizenzregister_wird_erzeugt(tmp_path):
    ziel = build_license_register(tmp_path / "LIZENZREGISTER.md")
    text = ziel.read_text(encoding="utf-8")
    assert "Kommerziell" in text and "Weitergabe" in text
    for pflicht in ("Python", "SQLite", "PyInstaller", "cryptography"):
        assert pflicht in text, f"{pflicht} fehlt im Lizenzregister"
    assert "ersetzt" in text and "keine Rechtsberatung" in text, \
        "der Vorbehalt muss im Dokument stehen"
    assert "Vor einem Vertrieb zu klaeren" in text


def test_sbom_ist_gueltiges_cyclonedx(tmp_path):
    ziel = build_sbom(tmp_path / "sbom.json", "1.2.3")
    daten = json.loads(ziel.read_text(encoding="utf-8"))
    assert daten["bomFormat"] == "CycloneDX"
    assert daten["metadata"]["component"]["version"] == "1.2.3"
    assert len(daten["components"]) >= 10
    for bestandteil in daten["components"]:
        assert bestandteil["name"] and bestandteil["licenses"]
        eigenschaften = {e["name"] for e in bestandteil["properties"]}
        assert {"kommerzielle_nutzung", "weitergabe", "geprueft_am"} <= eigenschaften


def test_offene_lizenzfragen_werden_benannt():
    """Die kritischen Punkte muessen sichtbar sein, nicht verschwiegen."""
    offen = " ".join(open_questions())
    assert "PyInstaller" in offen, "die Bootloader-Ausnahme ist zu klaeren"
    assert "Qwen" in offen or "Modell" in offen, "die Modellweitergabe ist zu klaeren"


def test_versionen_werden_wirklich_ermittelt():
    bestandteile = {c.name: c for c in collect_components()}
    assert bestandteile["Python"].version[0].isdigit()
    assert bestandteile["SQLite"].version[0].isdigit()


# ------------------------------------------------ Release-Dossier (Abschnitt 73)
def test_release_dossier_ist_vollstaendig(tmp_path):
    auslieferung = tmp_path / "PORTABLE_BUCHHALTER.exe"
    auslieferung.write_bytes(b"kein echtes Programm, nur fuer die Pruefsumme")

    ergebnis = build_release_dossier(
        ROOT, tmp_path / "RELEASE" / "1.0.0", "1.0.0",
        test_summary="166 Tests bestanden, 1 uebersprungen",
        known_issues=["Fenster per Doppelklick noch nicht abgenommen"],
        security_notes=["Programme sind nicht signiert"],
        files_to_checksum=[auslieferung],
    )
    ordner = Path(ergebnis["verzeichnis"])
    for pflicht in ("release_notes.md", "test_report.md", "known_issues.md",
                    "licenses.md", "sbom.json", "security_notes.md", "checksums.txt"):
        assert (ordner / pflicht).is_file(), f"{pflicht} fehlt im Dossier"

    pruefsummen = (ordner / "checksums.txt").read_text(encoding="utf-8")
    assert "PORTABLE_BUCHHALTER.exe" in pruefsummen
    assert len(pruefsummen.split()[0]) == 64, "SHA-256 erwartet"
    assert "Fenster per Doppelklick" in (ordner / "known_issues.md").read_text(encoding="utf-8")


# --------------------------------------------- Readiness-Gate (Abschnitte 77, 97)
def test_readiness_vergibt_commercial_ready_nicht_automatisch():
    bericht = check_readiness(ROOT)
    assert not bericht.commercial_ready, (
        "COMMERCIAL READY darf nicht automatisch vergeben werden - der "
        "Pilotbetrieb und die rechtliche Pruefung sind Voraussetzung."
    )
    manuelle = [i for i in bericht.items if not i.automatic]
    assert len(manuelle) >= 6
    schluessel = {i.key for i in bericht.items}
    for pflicht in ("pilot", "recht", "datenschutz", "sicherheitspruefung",
                    "lizenzpruefung", "lizenztests", "pruefschluessel"):
        assert pflicht in schluessel, f"Pruefpunkt {pflicht} fehlt"


def test_readiness_erkennt_vorhandene_unterlagen():
    bericht = check_readiness(ROOT)
    erfuellt = {i.key for i in bericht.items if i.fulfilled is True}
    for pflicht in ("lizenzpruefung", "lizenztests", "sicherheitskonzept",
                    "backup", "update", "testbericht", "kundentrennung",
                    "lizenzkonzept", "kommerziell"):
        assert pflicht in erfuellt, f"{pflicht} sollte als erfuellt erkannt werden"
    # Der fehlende Pruefschluessel muss als offen gelten
    offen = {i.key for i in bericht.items if i.fulfilled is False}
    assert "pruefschluessel" in offen


def test_readiness_text_nennt_den_status_klar():
    text = check_readiness(ROOT).as_text()
    assert "NOCH NICHT COMMERCIAL READY" in text
    assert "Pilotbetrieb" in text and "Rechtliche Pruefung" in text


def test_kein_privater_schluessel_im_repository():
    """Ein privater Signaturschluessel im Repository waere ein Totalschaden.

    Wer ihn haette, koennte beliebige Lizenzen ausstellen. Dieser Test ist
    das Sicherheitsnetz gegen ein Versehen.
    """
    import subprocess

    ergebnis = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    verdaechtig = [
        zeile for zeile in ergebnis.stdout.splitlines()
        if re.search(r"(privat|private|secret)\.pem$|\.key$|id_rsa", zeile)
    ]
    assert not verdaechtig, f"Moegliche Schluesseldateien im Repository: {verdaechtig}"

    # Und kein PEM-Block mit privatem Schluessel im eingecheckten Inhalt.
    # Die Suchmuster werden zur Laufzeit zusammengesetzt, damit diese Testdatei
    # sich nicht selbst meldet.
    marker = ("BEGIN " + "PRIVATE KEY", "BEGIN " + "OPENSSH " + "PRIVATE KEY",
              "BEGIN " + "RSA " + "PRIVATE KEY")
    treffer = []
    for datei in ergebnis.stdout.splitlines():
        pfad = ROOT / datei
        if not pfad.is_file() or pfad.suffix in (".png", ".zip", ".db"):
            continue
        try:
            inhalt = pfad.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(m in inhalt for m in marker):
            treffer.append(datei)
    assert not treffer, f"Privater Schluessel im Inhalt eingecheckter Dateien: {treffer}"


def test_keine_kundendaten_im_repository():
    """Kundenbereiche und Lizenzen duerfen nicht eingecheckt sein."""
    import subprocess

    ergebnis = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    verdaechtig = [
        zeile for zeile in ergebnis.stdout.splitlines()
        if zeile.startswith(("customers/", "license/", "lizenzen/"))
        or zeile.endswith(("company.db", "license.json", "license.sig"))
    ]
    assert not verdaechtig, f"Kundendaten oder Lizenzen im Repository: {verdaechtig}"
