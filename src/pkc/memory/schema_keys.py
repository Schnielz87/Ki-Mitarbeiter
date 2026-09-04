"""Kategorien und wohlbekannte Schluessel des Unternehmensgedaechtnisses."""

from __future__ import annotations

CATEGORIES: dict[str, str] = {
    "profile": "Unternehmensstammdaten",
    "organization": "Organisation und Standorte",
    "people": "Personen und Zustaendigkeiten",
    "accounting": "Buchhaltung, Kontenrahmen, Steuerschluessel",
    "tax": "Steuerliche Besonderheiten",
    "process": "Interne Prozesse und Arbeitsanweisungen",
    "rule": "Verbindliche Unternehmensregeln",
    "approval": "Freigaberegeln",
    "customer": "Kunden",
    "supplier": "Lieferanten",
    "case": "Wiederkehrende Sachverhalte und Sonderfaelle",
    "document": "Relevante Dokumente",
    "template": "Vorlagen",
    "preference": "Benutzerpraeferenzen und Arbeitsweisen",
    "erp": "ERP-/Systemkonfiguration",
    "other": "Sonstiges",
}

#: Schluessel, die das Onboarding abfragt und die im Prompt Vorrang haben.
WELL_KNOWN_KEYS: dict[str, dict[str, str]] = {
    "company.name":            {"category": "profile", "title": "Unternehmensname"},
    "company.legal_form":      {"category": "profile", "title": "Rechtsform"},
    "company.industry":        {"category": "profile", "title": "Branche"},
    "company.vat_status":      {"category": "tax", "title": "Umsatzsteuerstatus"},
    "company.vat_id":          {"category": "tax", "title": "USt-IdNr."},
    "company.tax_number":      {"category": "tax", "title": "Steuernummer"},
    "company.fiscal_year":     {"category": "accounting", "title": "Wirtschaftsjahr"},
    "company.chart_of_accounts": {"category": "accounting", "title": "Kontenrahmen"},
    "company.accounting_system": {"category": "accounting", "title": "Buchhaltungssystem"},
    "company.erp":             {"category": "erp", "title": "ERP-System"},
    "company.payment_process": {"category": "process", "title": "Zahlungsverkehr"},
    "company.ar_process":      {"category": "process", "title": "Debitorenprozess"},
    "company.ap_process":      {"category": "process", "title": "Kreditorenprozess"},
    "company.invoice_workflow": {"category": "process", "title": "Rechnungsworkflow"},
    "company.approval_rules":  {"category": "approval", "title": "Freigaberegeln"},
    "company.cost_centers":    {"category": "accounting", "title": "Kostenstellen"},
    "company.tax_keys":        {"category": "accounting", "title": "Steuerschluessel"},
    "company.specials":        {"category": "case", "title": "Besonderheiten"},
    "company.contacts":        {"category": "people", "title": "Ansprechpartner"},
    "company.allowed_tasks":   {"category": "preference", "title": "Gewuenschte Aufgaben"},
    "company.forbidden_tasks": {"category": "preference", "title": "Untersagte Taetigkeiten"},
    "company.locations":       {"category": "organization", "title": "Standorte"},
}
