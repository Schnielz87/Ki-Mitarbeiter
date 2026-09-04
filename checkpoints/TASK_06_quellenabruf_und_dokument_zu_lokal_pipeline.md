# Checkpoint 06 - Quellenabruf und Dokument-zu-lokal-Pipeline

* Zeitpunkt: 2026-09-04T20:57:39+00:00
* Status: **ABGESCHLOSSEN**
* Git-Commit: `879b84c0ee242a35f6ce261b623b1e90e02508a0`
* Naechster Task: TASK 07

## Fortsetzungspunkt

Normalisierung, Metadaten und Versionierung

## Erledigte Arbeit

- HTTP-Client der Standardbibliothek mit ETag/Last-Modified, Wartezeit je Host und robots.txt
- Pipeline: Abruf, Originalablage, Extraktion, Normalisierung, Metadaten, Chunking, Index, Bericht
- Ruecknahme eines Laufs ueber eine Sicherung, die vor dem Lauf angelegt wird

## Dateien

- src/pkc/updater/http_client.py
- src/pkc/updater/pipeline.py

## Tests

- tests/test_updater_pipeline.py

**Testergebnis:** 8 Tests gruen gegen einen echten lokalen HTTP-Server

## Offene Punkte

- (keine)

## Hinweise

Gegen die echten amtlichen Server nicht geprueft - der Netzzugang der Entwicklungsumgebung war auf Paketregistries beschraenkt.
