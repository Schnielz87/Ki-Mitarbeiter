"""Sicherheit, Freigaben, Protokoll und Connectoren (Masterprompt 21, 40, 41)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pkc.audit import ApprovalError, ApprovalState, ApprovalStore, AuditLog
from pkc.config import Config
from pkc.connectors import (
    ConnectorMode, NotConfigured, WriteRequiresApproval, build_registry,
)
from pkc.db import Database
from pkc.db.schema import COMPANY_MIGRATIONS
from pkc.security import SecretVault, VaultError, VaultLocked
from pkc.security.vault import crypto_available, suggest_passphrase


@pytest.fixture
def company(portable_root):
    db = Database(portable_root.company_db, COMPANY_MIGRATIONS)
    audit = AuditLog(db)
    return db, audit, ApprovalStore(db, audit)


# ----------------------------------------------------------------- Tresor
def test_vault_really_encrypts(portable_root):
    ok, detail = crypto_available()
    assert ok, detail
    vault = SecretVault(portable_root.secrets_file)
    vault.create("EinSicheresPasswort2026")
    vault.set("erp_password", "streng-geheim-4711")
    vault.set("online_llm_api_key", "sk-nicht-im-klartext")

    inhalt = portable_root.secrets_file.read_text(encoding="utf-8")
    assert "streng-geheim-4711" not in inhalt
    assert "sk-nicht-im-klartext" not in inhalt
    huelle = json.loads(inhalt)
    assert huelle["cipher"] == "AES-256-GCM" and huelle["kdf"]["name"] == "scrypt"


def test_vault_needs_correct_passphrase(portable_root):
    vault = SecretVault(portable_root.secrets_file)
    vault.create("RichtigesPasswort1")
    vault.set("schluessel", "wert")

    zweiter = SecretVault(portable_root.secrets_file)
    with pytest.raises(VaultError) as info:
        zweiter.unlock("FalschesPasswort9")
    assert "Falsches Passwort" in str(info.value)
    zweiter.unlock("RichtigesPasswort1")
    assert zweiter.get("schluessel") == "wert"


def test_locked_vault_reveals_nothing(portable_root):
    vault = SecretVault(portable_root.secrets_file)
    vault.create("EinSicheresPasswort2026")
    vault.set("token", "geheim")
    vault.lock()
    with pytest.raises(VaultLocked):
        vault.get("token")
    assert vault.get_quiet("token") is None, "der stille Zugriff darf nichts liefern"


def test_vault_rejects_weak_and_duplicate(portable_root):
    vault = SecretVault(portable_root.secrets_file)
    with pytest.raises(VaultError):
        vault.create("kurz")
    vault.create("LangGenugFuerDenTresor")
    with pytest.raises(VaultError):
        SecretVault(portable_root.secrets_file).create("NochEinPasswort123")


def test_passphrase_change_keeps_content(portable_root):
    vault = SecretVault(portable_root.secrets_file)
    vault.create("AltesPasswort2025")
    vault.set("a", "1")
    vault.change_passphrase("AltesPasswort2025", "NeuesPasswort2026")
    neu = SecretVault(portable_root.secrets_file)
    neu.unlock("NeuesPasswort2026")
    assert neu.get("a") == "1"
    assert len(suggest_passphrase()) > 15


# --------------------------------------------------------------- Freigaben
def test_no_execution_without_approval(company):
    _, _, approvals = company
    vorgang = approvals.create("booking", "Buchung ER 2026-4711",
                               {"soll": "3400", "haben": "1600", "betrag": 1190.0})
    assert vorgang.state is ApprovalState.ENTWURF and not vorgang.executable
    with pytest.raises(ApprovalError):
        approvals.require_executable(vorgang.uid)
    with pytest.raises(ApprovalError):
        approvals.transition(vorgang.uid, ApprovalState.AUSGEFUEHRT)


def test_approval_path_is_enforced_in_order(company):
    _, _, approvals = company
    vorgang = approvals.create("payment", "Zahlung an Meier GmbH")
    approvals.transition(vorgang.uid, ApprovalState.GEPRUEFT, by="buchhalterin")
    freigegeben = approvals.transition(vorgang.uid, ApprovalState.FREIGEGEBEN,
                                       by="geschaeftsfuehrer", note="geprueft")
    assert freigegeben.executable and freigegeben.decided_by == "geschaeftsfuehrer"
    ausgefuehrt = approvals.transition(vorgang.uid, ApprovalState.AUSGEFUEHRT)
    assert ausgefuehrt.state is ApprovalState.AUSGEFUEHRT
    with pytest.raises(ApprovalError):
        approvals.transition(vorgang.uid, ApprovalState.ENTWURF)


def test_audit_records_every_decision(company):
    db, audit, approvals = company
    vorgang = approvals.create("erp_write", "Stammdatenaenderung")
    approvals.transition(vorgang.uid, ApprovalState.GEPRUEFT, by="pruefer")
    approvals.transition(vorgang.uid, ApprovalState.ABGELEHNT, by="leitung",
                         note="Beleg fehlt")
    aktionen = [e["action"] for e in audit.entries()]
    assert aktionen.count("freigabe_status") == 2
    letzter = audit.entries()[0]
    assert letzter["detail"]["nach"] == "ABGELEHNT"
    assert letzter["actor"] == "leitung"


# ------------------------------------------------------------- Connectoren
def test_connectors_are_read_only_by_default(portable_root, company):
    _, audit, approvals = company
    config = Config.load(portable_root)
    registry = build_registry(config, approvals, audit)
    for info in registry.info():
        assert info.mode is ConnectorMode.READ_ONLY, f"{info.connector_id} darf nicht schreiben"


def test_write_is_blocked_without_mode_and_approval(portable_root, company):
    _, audit, approvals = company
    config = Config.load(portable_root)
    config.set("connectors.settings", {"generic_rest": {"base_url": "http://127.0.0.1:1"}})
    registry = build_registry(config, approvals, audit)
    rest = registry.get("generic_rest")

    with pytest.raises(WriteRequiresApproval) as info:
        rest.write({"body": {}}, "beliebig")
    assert "read_only" in str(info.value)

    rest.mode = ConnectorMode.READ_WRITE
    with pytest.raises(WriteRequiresApproval):
        rest.write({"body": {}}, "existiert-nicht")

    uid = rest.propose_write({"body": {"konto": "3400"}}, "Testbuchung")
    with pytest.raises(WriteRequiresApproval):
        rest.write({"body": {}}, uid)          # noch nicht freigegeben


def test_unconfigured_erp_connectors_are_honest(portable_root, company):
    _, audit, approvals = company
    registry = build_registry(Config.load(portable_root), approvals, audit)
    for connector_id in ("sap", "wilken", "datev"):
        connector = registry.get(connector_id)
        info = connector.info()
        assert not info.configured
        assert info.open_questions, "die offenen Fragen muessen benannt sein"
        with pytest.raises(NotConfigured) as fehler:
            connector.read("beliebige Abfrage")
        assert "nicht angebunden" in str(fehler.value)


def test_csv_connector_reads_real_file(portable_root, company):
    _, audit, approvals = company
    verzeichnis = portable_root.get("workspace")
    (verzeichnis / "stapel.csv").write_text(
        "Konto;Gegenkonto;Betrag;Steuerschluessel;Text\n"
        "3400;1600;1190,00;9;Wareneingang Meier GmbH\n"
        "6815;1200;238,00;9;Buerobedarf\n",
        encoding="utf-8",
    )
    config = Config.load(portable_root)
    config.set("connectors.settings", {"csv": {"directory": str(verzeichnis)}})
    registry = build_registry(config, approvals, audit)
    csv_connector = registry.get("csv")
    assert csv_connector.configured()[0]

    ergebnis = csv_connector.read("stapel.csv")
    assert ergebnis.count == 2
    assert ergebnis.rows[0]["Konto"] == "3400"
    assert "Steuerschluessel" in ergebnis.meta["spalten"]


@pytest.mark.parametrize("versuch", [
    "../geheim.csv",
    "../../geheim.csv",
    "unterordner/../../geheim.csv",
])
def test_file_connector_stays_in_its_directory(portable_root, company, versuch):
    """Ein Connector darf nur dort lesen, wofuer er eingerichtet wurde.

    Ohne diese Grenze koennte eine Angabe wie ``../geheim.csv`` beliebige
    Dateien des Rechners lesen - besonders heikel, sobald Abfragen nicht
    mehr von Hand, sondern automatisiert entstehen.
    """
    from pkc.connectors import ConnectorError

    _, audit, approvals = company
    verzeichnis = portable_root.get("workspace")
    verzeichnis.mkdir(parents=True, exist_ok=True)
    (verzeichnis / "erlaubt.csv").write_text("a;b\n1;2\n", encoding="utf-8")
    (portable_root.root / "geheim.csv").write_text(
        "Konto;Passwort\n1;streng-geheim\n", encoding="utf-8"
    )
    config = Config.load(portable_root)
    config.set("connectors.settings", {"csv": {"directory": str(verzeichnis)}})
    csv_connector = build_registry(config, approvals, audit).get("csv")

    assert csv_connector.read("erlaubt.csv").count == 1

    with pytest.raises(ConnectorError) as fehler:
        csv_connector.read(versuch)
    assert "innerhalb" in str(fehler.value)


def test_file_connector_rejects_absolute_paths(portable_root, company):
    from pkc.connectors import ConnectorError

    _, audit, approvals = company
    verzeichnis = portable_root.get("workspace")
    verzeichnis.mkdir(parents=True, exist_ok=True)
    ausserhalb = portable_root.root / "geheim.csv"
    ausserhalb.write_text("Konto;Passwort\n1;geheim\n", encoding="utf-8")
    config = Config.load(portable_root)
    config.set("connectors.settings", {"csv": {"directory": str(verzeichnis)}})
    csv_connector = build_registry(config, approvals, audit).get("csv")

    with pytest.raises(ConnectorError) as fehler:
        csv_connector.read(str(ausserhalb))
    assert "absoluter Pfad" in str(fehler.value)


def test_preview_does_not_write(portable_root, company):
    _, audit, approvals = company
    config = Config.load(portable_root)
    config.set("connectors.settings", {"generic_rest": {"base_url": "http://127.0.0.1:1"}})
    registry = build_registry(config, approvals, audit)
    vorschau = registry.get("generic_rest").preview_write({"body": {"betrag": 100}})
    assert vorschau.ok and "nichts geschrieben" in vorschau.message
