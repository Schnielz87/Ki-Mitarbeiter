# Checkpoint 17 - Sicherheit, Freigaben, Audit, Packaging, Windows-EXE und Launcher

* Zeitpunkt: 2026-09-05T13:57:44+00:00
* Status: **ABGESCHLOSSEN**
* Git-Commit: `32db7304884026a146cab62bde0e25c937fb4710`
* Naechster Task: TASK 18

## Fortsetzungspunkt

Abnahme mit echtem Sprachmodell und zweitem Rechner

## Erledigte Arbeit

- Geheimnistresor mit scrypt und AES-256-GCM, am Dateiinhalt nachgewiesen
- Freigabe-Zustandsautomat sperrt die Ausfuehrung technisch
- Zwei Programme gebaut: Fensterfassung fuer den Doppelklick, Konsolenfassung fuer die Kommandozeile
- Auf echtem Windows gebaut und ausgefuehrt: alle 13 Schritte des Ablaufs bestanden

## Dateien

- build/portable_buchhalter.spec
- build/build_windows.ps1
- .github/workflows/build-windows.yml

## Tests

- Windows-Ablauf 33970160321

**Testergebnis:** 13 von 13 Schritten bestanden; Artefakt Portable-Buchhalter-Windows, 22,8 MB

## Offene Punkte

- (keine)

## Pruefsummen (SHA-256)

| Datei | Pruefsumme |
|---|---|
| build/portable_buchhalter.spec | `6b1b3cb2f96fc68283f2c87cc0fecad4349a404557c9f183a97bcc43a2199a06` |

## Hinweise

Belegt durch https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/33970160321 - EXE existiert tatsaechlich und wurde ausgefuehrt. Nicht darin enthalten: Oeffnen des Fensters per Doppelklick, echtes Sprachmodell.
