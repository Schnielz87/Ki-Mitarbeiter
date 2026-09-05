# Checkpoint 19 - Lizenzierung und Kopierschutz

* Zeitpunkt: 2026-09-05T14:29:44+00:00
* Status: **ABGESCHLOSSEN**
* Git-Commit: `4350f7b3032575173b3387c553ba7d45c777b686`
* Naechster Task: TASK 20

## Fortsetzungspunkt

Kundentrennung

## Erledigte Arbeit

- Ed25519-signierte Lizenz, offline pruefbar, gebunden an den Datentraeger statt an den PC
- Kopie auf zweiten Datentraeger ist nicht lizenziert, Original bleibt gueltig
- Ohne Lizenz wird nur die Nutzung gesperrt - keine Daten beschaedigt

## Dateien

- src/pkc/licensing/verify.py
- src/pkc/licensing/instance.py
- tools/lizenz_ausstellen.py
- LIZENZKONZEPT.md

## Tests

- tests/test_lizenzierung.py

**Testergebnis:** 22 Tests gruen, alle sieben Faelle aus Abschnitt 96

## Offene Punkte

- Pruefschluessel des Herausgebers noch nicht hinterlegt - geschaeftliche Entscheidung

## Pruefsummen (SHA-256)

| Datei | Pruefsumme |
|---|---|
| LIZENZKONZEPT.md | `04e85e577891af5b3a6a19dcd3b032f9f9f2cf8aa045d64405b984f0571df0ba` |
