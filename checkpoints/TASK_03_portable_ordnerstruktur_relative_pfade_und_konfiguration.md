# Checkpoint 03 - Portable Ordnerstruktur, relative Pfade und Konfiguration

* Zeitpunkt: 2026-09-04T20:56:49+00:00
* Status: **ABGESCHLOSSEN**
* Git-Commit: `879b84c0ee242a35f6ce261b623b1e90e02508a0`
* Naechster Task: TASK 04

## Fortsetzungspunkt

Mitarbeiterprofil und Fach-Masterprompt erstellen

## Erledigte Arbeit

- pkc.paths: Wurzelerkennung ueber Markerdatei, Umgebungsvariable und Quellbaum
- Trennung von Programm- und Datenwurzel; Vorgabedateien werden in neue Datenbereiche uebernommen
- pkc.config: Defaults, settings.json, KIM_*-Variablen; gespeichert werden nur Abweichungen

## Dateien

- src/pkc/paths.py
- src/pkc/config.py
- src/pkc/logging_setup.py

## Tests

- tests/test_portability.py

**Testergebnis:** 13 Tests gruen, 1 uebersprungen (Schreibschutz als root nicht pruefbar)

## Offene Punkte

- (keine)

## Pruefsummen (SHA-256)

| Datei | Pruefsumme |
|---|---|
| src/pkc/config.py | `caf2fcb6e30fb7e56d420cda578544508cabb7460cf7f15e50fd1b43dcb940ac` |
| src/pkc/paths.py | `5eeb1d046ccc4d4f22db4669afd335e532dd5fe2b3bfe50374e06a38d682daac` |
