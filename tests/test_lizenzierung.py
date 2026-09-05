"""Lizenzierung und Kopierschutz (Masterprompt 84 bis 97).

Die sieben Testfaelle aus Abschnitt 96 sind hier vollstaendig abgebildet,
ergaenzt um die Zusagen aus Abschnitt 95 (eine ungueltige Lizenz darf keine
Daten beschaedigen) und Abschnitt 85 (Portabilitaet bleibt erhalten).

Der Datentraeger wird ueber ``KIM_CARRIER_ID`` nachgestellt: in der
Testumgebung gibt es keine zweite echte SSD, wohl aber genau den Vorgang,
auf den es ankommt - dieselben Dateien auf einer **anderen**
Datentraegerkennung.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from pkc.licensing import LicenseChecker
from pkc.licensing.instance import carrier_identity, instance_id_for
from pkc.licensing.issue import generate_keypair, issue_license
from pkc.licensing.model import LicenseState


@pytest.fixture
def herausgeber(tmp_path_factory):
    """Ein Schluesselpaar des Herstellers - einmal fuer alle Testfaelle."""
    verzeichnis = tmp_path_factory.mktemp("herausgeber")
    privat, oeffentlich = generate_keypair(
        verzeichnis / "privat.pem", verzeichnis / "oeffentlich.pem"
    )
    return privat, oeffentlich.read_bytes()


@pytest.fixture
def lizenzierte_ssd(tmp_path, herausgeber, monkeypatch):
    """Eine Instanz mit gueltiger, auf ihren Datentraeger ausgestellter Lizenz."""
    privat, oeffentlich = herausgeber
    wurzel = tmp_path / "SSD-1"
    wurzel.mkdir()
    monkeypatch.setenv("KIM_CARRIER_ID", "AAAA-1111-ORIGINAL")

    pruefer = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich)
    anfrage = pruefer.activation_request("Muster Handels GmbH")
    _, _, ablage = issue_license(
        privat, customer="Muster Handels GmbH",
        instance_id=anfrage["instanz_id"],
        carrier_fingerprint=anfrage["datentraeger_fingerabdruck"],
        modules=["buchhalter"], issuer="Hersteller",
        target_dir=tmp_path / "ausgestellt",
    )
    pruefer.install(ablage / "license.json", ablage / "license.sig")
    return wurzel, oeffentlich, privat


# --------------------------------------------------------------- TEST 1
def test_1_originale_lizenzierte_ssd_startet(lizenzierte_ssd):
    """Original lizenzierte SSD -> Anwendung startet."""
    wurzel, oeffentlich, _ = lizenzierte_ssd
    status = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich).check()
    assert status.state is LicenseState.GUELTIG, status.message
    assert status.productive_allowed
    assert status.license is not None
    assert status.license.customer == "Muster Handels GmbH"


# --------------------------------------------------------------- TEST 2
def test_2_kopie_auf_zweite_ssd_ist_nicht_lizenziert(lizenzierte_ssd, tmp_path, monkeypatch):
    """Programmordner auf zweite SSD kopieren -> nicht automatisch gueltig."""
    wurzel, oeffentlich, _ = lizenzierte_ssd
    zweite = tmp_path / "SSD-2"
    shutil.copytree(wurzel, zweite)

    # Derselbe Inhalt, aber ein anderer Datentraeger.
    monkeypatch.setenv("KIM_CARRIER_ID", "BBBB-2222-KOPIE")
    status = LicenseChecker(zweite, required=True, public_key_pem=oeffentlich).check()

    assert status.state is LicenseState.FALSCHE_INSTANZ
    assert not status.productive_allowed
    assert "anderen Datentraeger" in status.message
    assert any("Lizenzuebertragung" in h for h in status.hints)
    # Die Lizenzdatei selbst ist echt - nur eben nicht fuer diese Instanz.
    assert status.license is not None and status.license.customer == "Muster Handels GmbH"


def test_2b_original_bleibt_nach_dem_kopieren_gueltig(lizenzierte_ssd, tmp_path, monkeypatch):
    """Die Kopie darf das Original nicht entwerten."""
    wurzel, oeffentlich, _ = lizenzierte_ssd
    shutil.copytree(wurzel, tmp_path / "SSD-2")
    monkeypatch.setenv("KIM_CARRIER_ID", "AAAA-1111-ORIGINAL")
    status = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich).check()
    assert status.state is LicenseState.GUELTIG


# --------------------------------------------------------------- TEST 3
@pytest.mark.parametrize("feld,wert", [
    ("customer", "Fremdfirma GmbH"),
    ("allowed_instances", 99),
    ("expiry_date", "2099-12-31"),
    ("modules", ["buchhalter", "controller", "recht"]),
    ("carrier_fingerprint", "0" * 64),
])
def test_3_veraenderte_lizenzdatei_faellt_auf(lizenzierte_ssd, feld, wert):
    """Lizenzdatei veraendern -> Signaturpruefung schlaegt fehl."""
    wurzel, oeffentlich, _ = lizenzierte_ssd
    pfad = wurzel / "license" / "license.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    daten[feld] = wert
    pfad.write_text(json.dumps(daten, indent=2), encoding="utf-8")

    status = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich).check()
    assert status.state is LicenseState.UNGUELTIG_SIGNATUR
    assert not status.productive_allowed
    assert "veraendert" in status.message


def test_3b_fremde_signatur_faellt_auf(lizenzierte_ssd, tmp_path):
    """Eine mit einem anderen Schluessel signierte Lizenz wird abgewiesen."""
    wurzel, oeffentlich, _ = lizenzierte_ssd
    fremd_privat, _ = generate_keypair(tmp_path / "f.pem", tmp_path / "f.pub")
    pruefer = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich)
    anfrage = pruefer.activation_request("Selbst ausgestellt")
    _, _, ablage = issue_license(
        fremd_privat, customer="Selbst ausgestellt",
        instance_id=anfrage["instanz_id"],
        carrier_fingerprint=anfrage["datentraeger_fingerabdruck"],
        target_dir=tmp_path / "gefaelscht",
    )
    pruefer.install(ablage / "license.json", ablage / "license.sig")
    assert pruefer.check().state is LicenseState.UNGUELTIG_SIGNATUR


# --------------------------------------------------------------- TEST 4
def test_4_ohne_internet_gueltig(lizenzierte_ssd, monkeypatch):
    """Ohne Internet starten -> gueltige Offline-Lizenz funktioniert."""
    wurzel, oeffentlich, _ = lizenzierte_ssd

    def kein_netz(*args, **kwargs):
        raise AssertionError("Die Lizenzpruefung darf das Netz nicht benutzen.")

    monkeypatch.setattr("urllib.request.urlopen", kein_netz)
    status = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich).check()
    assert status.state is LicenseState.GUELTIG


# --------------------------------------------------------------- TEST 5
def test_5_fehlende_lizenz_meldet_verstaendlich(tmp_path, herausgeber, monkeypatch):
    """Lizenzdatei fehlt -> verstaendliche Meldung, keine Sanktion."""
    _, oeffentlich = herausgeber
    monkeypatch.setenv("KIM_CARRIER_ID", "CCCC-3333")
    wurzel = tmp_path / "ohne-lizenz"
    (wurzel / "database").mkdir(parents=True)
    daten = wurzel / "database" / "company.db"
    daten.write_bytes(b"Unternehmensdaten")

    status = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich).check()

    assert status.state is LicenseState.FEHLT
    assert not status.productive_allowed
    assert "keine Lizenzdatei" in status.message
    assert any("exportieren" in h for h in status.hints)
    assert any("keine Daten geloescht" in h for h in status.hints)
    # Abschnitt 95: die Daten bleiben unangetastet
    assert daten.read_bytes() == b"Unternehmensdaten"


def test_5b_beschaedigte_lizenzdatei(lizenzierte_ssd):
    wurzel, oeffentlich, _ = lizenzierte_ssd
    (wurzel / "license" / "license.json").write_text("{kein json", encoding="utf-8")
    status = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich).check()
    assert status.state is LicenseState.BESCHAEDIGT
    assert "nicht lesbar" in status.message


def test_5c_fehlende_signaturdatei(lizenzierte_ssd):
    wurzel, oeffentlich, _ = lizenzierte_ssd
    (wurzel / "license" / "license.sig").unlink()
    status = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich).check()
    assert status.state is LicenseState.UNGUELTIG_SIGNATUR
    assert "fehlt die Signatur" in status.message


# --------------------------------------------------------------- TEST 6
def test_6_ersatz_datentraeger_kann_neu_lizenziert_werden(
    lizenzierte_ssd, tmp_path, monkeypatch
):
    """Defekte SSD ersetzen -> kontrollierter Lizenztransfer moeglich."""
    wurzel, oeffentlich, privat = lizenzierte_ssd

    # Die Unternehmensdaten liegen im Backup und werden auf den Ersatz gespielt.
    ersatz = tmp_path / "SSD-Ersatz"
    shutil.copytree(wurzel, ersatz)
    monkeypatch.setenv("KIM_CARRIER_ID", "DDDD-4444-ERSATZ")

    pruefer = LicenseChecker(ersatz, required=True, public_key_pem=oeffentlich)
    assert pruefer.check().state is LicenseState.FALSCHE_INSTANZ, "erst ungueltig"

    # Der Hersteller stellt fuer den Ersatz eine neue Lizenz aus.
    anfrage = pruefer.activation_request("Muster Handels GmbH")
    _, _, ablage = issue_license(
        privat, customer="Muster Handels GmbH",
        instance_id=anfrage["instanz_id"],
        carrier_fingerprint=anfrage["datentraeger_fingerabdruck"],
        modules=["buchhalter"], notes="Ersatz fuer defekten Datentraeger",
        target_dir=tmp_path / "ersatzlizenz",
    )
    status = pruefer.install(ablage / "license.json", ablage / "license.sig")
    assert status.state is LicenseState.GUELTIG
    assert status.license.notes == "Ersatz fuer defekten Datentraeger"


# --------------------------------------------------------------- TEST 7
def test_7_datensicherung_erzeugt_keine_zusaetzliche_lizenz(
    lizenzierte_ssd, tmp_path, monkeypatch
):
    """Unternehmensdaten wiederherstellen -> keine zusaetzliche Lizenz."""
    wurzel, oeffentlich, _ = lizenzierte_ssd
    (wurzel / "database").mkdir(exist_ok=True)
    (wurzel / "database" / "company.db").write_bytes(b"Unternehmensgedaechtnis")

    # Nur die Daten werden gesichert und auf einen anderen Datentraeger gespielt.
    sicherung = tmp_path / "sicherung"
    sicherung.mkdir()
    shutil.copy(wurzel / "database" / "company.db", sicherung / "company.db")

    zweite = tmp_path / "SSD-neu"
    (zweite / "database").mkdir(parents=True)
    shutil.copy(sicherung / "company.db", zweite / "database" / "company.db")
    monkeypatch.setenv("KIM_CARRIER_ID", "EEEE-5555")

    status = LicenseChecker(zweite, required=True, public_key_pem=oeffentlich).check()
    assert status.state is LicenseState.FEHLT, "Daten allein erzeugen keine Lizenz"
    # Die Daten sind aber da - Wiederherstellung bleibt moeglich (Abschnitt 94)
    assert (zweite / "database" / "company.db").read_bytes() == b"Unternehmensgedaechtnis"


# ------------------------------------------------- Portabilitaet (Abschnitt 85)
def test_portabilitaet_bleibt_erhalten(lizenzierte_ssd, tmp_path, monkeypatch):
    """Derselbe Datentraeger an mehreren Rechnern - die Lizenz bleibt gueltig.

    Der Rechnerwechsel wird dadurch nachgestellt, dass der Einhaengepunkt
    wechselt, die Datentraegerkennung aber dieselbe bleibt - genau so verhaelt
    sich eine SSD an einem anderen PC.
    """
    wurzel, oeffentlich, _ = lizenzierte_ssd
    for pc in ("PC-A", "PC-B", "PC-C"):
        ziel = tmp_path / pc / "Portable Buchhalter"
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(wurzel, ziel)
        monkeypatch.setenv("KIM_CARRIER_ID", "AAAA-1111-ORIGINAL")   # gleiche SSD
        status = LicenseChecker(ziel, required=True, public_key_pem=oeffentlich).check()
        assert status.state is LicenseState.GUELTIG, f"{pc}: {status.message}"


def test_keine_lizenz_noetig_in_der_pilotfassung(tmp_path, monkeypatch):
    """Ohne Lizenzpflicht laeuft die Vorabfassung normal - und sagt das auch."""
    monkeypatch.setenv("KIM_CARRIER_ID", "FFFF-6666")
    status = LicenseChecker(tmp_path, required=False).check()
    assert status.state is LicenseState.NICHT_ERFORDERLICH
    assert status.productive_allowed
    assert "ohne Lizenzpruefung" in status.message


def test_ohne_pruefschluessel_wird_nichts_vorgetaeuscht(lizenzierte_ssd):
    """Fehlt der Pruefschluessel, gilt die Lizenz weder als gueltig noch ungueltig."""
    wurzel, _, _ = lizenzierte_ssd
    status = LicenseChecker(wurzel, required=True, public_key_pem=b"").check()
    assert status.state is LicenseState.NICHT_PRUEFBAR
    assert not status.valid
    assert "kein Pruefschluessel" in status.message


def test_abgelaufene_lizenz(tmp_path, herausgeber, monkeypatch):
    privat, oeffentlich = herausgeber
    monkeypatch.setenv("KIM_CARRIER_ID", "GGGG-7777")
    wurzel = tmp_path / "abgelaufen"
    wurzel.mkdir()
    pruefer = LicenseChecker(wurzel, required=True, public_key_pem=oeffentlich)
    anfrage = pruefer.activation_request("Alt GmbH")
    _, _, ablage = issue_license(
        privat, customer="Alt GmbH", instance_id=anfrage["instanz_id"],
        carrier_fingerprint=anfrage["datentraeger_fingerabdruck"],
        expiry_date="2020-01-01", target_dir=tmp_path / "alt",
    )
    status = pruefer.install(ablage / "license.json", ablage / "license.sig")
    assert status.state is LicenseState.ABGELAUFEN
    assert "2020-01-01" in status.message


def test_modul_nicht_lizenziert(tmp_path, herausgeber, monkeypatch):
    privat, oeffentlich = herausgeber
    monkeypatch.setenv("KIM_CARRIER_ID", "HHHH-8888")
    wurzel = tmp_path / "falschesmodul"
    wurzel.mkdir()
    pruefer = LicenseChecker(wurzel, module="controller", required=True,
                             public_key_pem=oeffentlich)
    anfrage = pruefer.activation_request("Muster GmbH")
    _, _, ablage = issue_license(
        privat, customer="Muster GmbH", instance_id=anfrage["instanz_id"],
        carrier_fingerprint=anfrage["datentraeger_fingerabdruck"],
        modules=["buchhalter"], target_dir=tmp_path / "nurbuch",
    )
    status = pruefer.install(ablage / "license.json", ablage / "license.sig")
    assert status.state is LicenseState.MODUL_NICHT_LIZENZIERT
    assert "controller" in status.message


# ------------------------------------------------- Wirkung in der Anwendung
def test_ohne_lizenz_ist_die_produktive_nutzung_gesperrt(portable_root, monkeypatch):
    """Ohne gueltige Lizenz keine Fachfrage - aber auch kein Datenverlust."""
    from app.controller import LicenseRequired
    from test_controller import make_controller

    monkeypatch.setenv("KIM_CARRIER_ID", "IIII-9999")
    controller = make_controller(portable_root)
    controller.config.set("license.required", True)
    controller.license.required = True
    controller.license_status = controller.license.check()
    bericht = controller.bootstrap()
    try:
        # Die Systempruefung meldet die fehlende Lizenz als kritisch
        lizenzpunkt = next(i for i in bericht.items if i.name == "Lizenz")
        assert not lizenzpunkt.ok and lizenzpunkt.critical
        assert not bericht.usable

        # Eine Fachfrage wird verstaendlich abgewiesen
        with pytest.raises(LicenseRequired) as fehler:
            controller.ask("Welche Pflichtangaben braucht eine Rechnung?")
        text = str(fehler.value)
        assert "keine Lizenzdatei" in text
        assert "exportieren" in text and "Sicherung" in text

        # Abschnitt 95: nichts wurde geloescht oder gesperrt
        assert portable_root.company_db.is_file()
        assert controller.knowledge.stats()["documents"] > 0

        # Der Ausweg bleibt offen: Daten ansehen, exportieren, sichern
        controller.remember_manual("company.name", "Name", "Muster GmbH", "profile")
        assert controller.memory.get("company.name") is not None
        ziel = controller.export_company_profile()
        assert ziel.is_file()
        assert controller.backup("ohne-lizenz")["dateien"]
    finally:
        controller.shutdown()


def test_versionsangaben_sind_getrennt(portable_root):
    """Masterprompt 66: Software, Fachmodul, Wissensstand und Modell getrennt."""
    from test_controller import make_controller

    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        felder = controller.versions()
        for pflicht in ("softwareversion", "fachmodul", "wissenspaket",
                        "wissensstand", "unternehmensprofil", "modell",
                        "instanz_id", "lizenz", "produktstufe"):
            assert pflicht in felder, f"{pflicht} fehlt in den Versionsangaben"
        assert felder["produktstufe"] == "pilot", "diese Fassung ist keine Serienfassung"
        text = controller.versions_text()
        assert "Softwareversion" in text and "Wissensstand" in text
    finally:
        controller.shutdown()
