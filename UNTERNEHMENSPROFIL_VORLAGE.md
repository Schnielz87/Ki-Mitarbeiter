# Unternehmensprofil - Vorlage

Diese Angaben erfasst der Buchhalter beim Onboarding. Sie werden dauerhaft in
`database/company.db` gespeichert und wandern mit dem Datentraeger.

Ausfuellen entweder in der Anwendung (**Unternehmenswissen → Onboarding
fortsetzen**), auf der Kommandozeile
(`PORTABLE_BUCHHALTER.exe onboarding --interaktiv`) oder beilaeufig im Chat -
der Buchhalter fragt dann nach, ob er sich die Angabe merken soll.

Alle Felder duerfen leer bleiben und spaeter ergaenzt werden.

## Stammdaten

| Feld | Schluessel | Ihre Angabe |
|---|---|---|
| Unternehmensname | `company.name` | |
| Rechtsform | `company.legal_form` | |
| Branche | `company.industry` | |
| Standorte | `company.locations` | |

## Steuer

| Feld | Schluessel | Ihre Angabe |
|---|---|---|
| Umsatzsteuerstatus (regelbesteuert / Kleinunternehmer) | `company.vat_status` | |
| USt-IdNr. | `company.vat_id` | |
| Steuernummer | `company.tax_number` | |

## Buchhaltung

| Feld | Schluessel | Ihre Angabe |
|---|---|---|
| Wirtschaftsjahr | `company.fiscal_year` | |
| Kontenrahmen (SKR03 / SKR04 / eigener) | `company.chart_of_accounts` | |
| Buchhaltungssystem | `company.accounting_system` | |
| ERP-System | `company.erp` | |
| Kostenstellen | `company.cost_centers` | |
| Steuerschluessel | `company.tax_keys` | |

## Prozesse

| Feld | Schluessel | Ihre Angabe |
|---|---|---|
| Zahlungsverkehr | `company.payment_process` | |
| Debitorenprozess | `company.ar_process` | |
| Kreditorenprozess | `company.ap_process` | |
| Rechnungsworkflow | `company.invoice_workflow` | |
| Freigaberegeln | `company.approval_rules` | |

## Organisation und Zusammenarbeit

| Feld | Schluessel | Ihre Angabe |
|---|---|---|
| Ansprechpartner | `company.contacts` | |
| Besonderheiten | `company.specials` | |
| Gewuenschte Aufgaben | `company.allowed_tasks` | |
| Untersagte Taetigkeiten | `company.forbidden_tasks` | |

## Hinweise zum Ausfuellen

**Freigaberegeln** moeglichst konkret, mit Betrag und Zustaendigkeit:
„Rechnungen ab 5.000 EUR muessen durch den Geschaeftsfuehrer freigegeben
werden."

**Untersagte Taetigkeiten** ernst nehmen. Der Buchhalter haelt sich daran,
zum Beispiel: „Keine Aussagen zu Lohnsteuer - dafuer ist ausschliesslich der
Steuerberater zustaendig."

**Keine Zugangsdaten hier eintragen.** Passwoerter, Tokens und
API-Schluessel gehoeren in den verschluesselten Tresor
(`SICHERHEITSKONZEPT.md`), nicht ins Unternehmensprofil.

**Spaeter ergaenzen** ist der Normalfall. Sagen Sie im Gespraech einfach:
„Wir buchen Bewirtungskosten immer auf 4650" - der Buchhalter fragt nach, ob
er sich das dauerhaft merken soll.

## Export

Der aktuelle Stand wird jederzeit lesbar exportiert:

```
PORTABLE_BUCHHALTER.exe wissen export
```

Ergebnis: `company/unternehmensprofil.md` (lesbar) und
`company/unternehmensprofil.json` (maschinenlesbar).
