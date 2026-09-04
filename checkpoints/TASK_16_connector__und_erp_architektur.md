# Checkpoint 16 - Connector- und ERP-Architektur

* Zeitpunkt: 2026-09-04T20:57:40+00:00
* Status: **ABGESCHLOSSEN**
* Git-Commit: `879b84c0ee242a35f6ce261b623b1e90e02508a0`
* Naechster Task: TASK 17

## Fortsetzungspunkt

Sicherheit, Freigaben, Audit, Packaging und EXE

## Erledigte Arbeit

- Connector-Schicht mit Standard READ ONLY; Schreiben ist ohne Freigabe technisch gesperrt
- CSV und Excel vollstaendig nutzbar, generischer REST-Connector einsatzbereit
- SAP, Wilken und DATEV melden ehrlich, dass sie nicht angebunden sind, samt offener Fragen

## Dateien

- src/pkc/connectors/base.py
- src/pkc/connectors/files.py
- src/pkc/connectors/rest.py
- src/pkc/connectors/erp_stubs.py

## Tests

- tests/test_sicherheit_freigaben.py

**Testergebnis:** wird in Task 17 ergaenzt

## Offene Punkte

- (keine)
