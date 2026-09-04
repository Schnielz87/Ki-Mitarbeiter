# Checkpoint 07 - Normalisierung, Metadaten und Versionierung

* Zeitpunkt: 2026-09-04T20:57:39+00:00
* Status: **ABGESCHLOSSEN**
* Git-Commit: `879b84c0ee242a35f6ce261b623b1e90e02508a0`
* Naechster Task: TASK 08

## Fortsetzungspunkt

Lokale Wissensdatenbank und Suchindex

## Erledigte Arbeit

- Extraktion aus HTML, XML (inkl. Normen-XML von Gesetze im Internet), ZIP, PDF und Text
- Zitierfaehiges Chunking: Paragraphen bleiben moeglichst ungeteilt
- Metadaten je Dokument als eigene JSON-Datei, Dokumentversion steigt bei geaendertem Inhalt

## Dateien

- src/pkc/knowledge/extract.py
- src/pkc/knowledge/chunker.py
- src/pkc/knowledge/store.py

## Tests

- tests/test_updater_pipeline.py

**Testergebnis:** 8 Tests gruen

## Offene Punkte

- (keine)
