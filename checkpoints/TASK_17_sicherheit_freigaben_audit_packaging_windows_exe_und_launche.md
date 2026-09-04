# Checkpoint 17 - Sicherheit, Freigaben, Audit, Packaging, Windows-EXE und Launcher

* Zeitpunkt: 2026-09-04T21:11:17+00:00
* Status: **TEILWEISE**
* Git-Commit: `b5ce89b69e31e768ecbd36d9786921dd7981bbca`
* Naechster Task: TASK 18

## Fortsetzungspunkt

Gesamtintegration und Abnahmevorbereitung

## Erledigte Arbeit

- Geheimnistresor mit scrypt und AES-256-GCM; die Verschluesselung ist am Dateiinhalt nachgewiesen
- Freigabe-Zustandsautomat sperrt die Ausfuehrung technisch, nicht nur dokumentarisch
- Protokoll ueber alle relevanten Vorgaenge
- PyInstaller-Beschreibung (onedir), Windows-Build-Skript, Startdateien, Anforderungsdateien
- GitHub-Actions-Ablauf baut die EXE auf echtem Windows und prueft sie einschliesslich Laufwerkswechsel

## Dateien

- src/pkc/security/vault.py
- src/pkc/audit/approvals.py
- build/portable_buchhalter.spec
- build/build_windows.ps1
- .github/workflows/build-windows.yml
- PORTABLE_BUCHHALTER.bat

## Tests

- tests/test_sicherheit_freigaben.py

**Testergebnis:** 13 Tests gruen

## Offene Punkte

- PORTABLE_BUCHHALTER.exe wurde NICHT gebaut - in dieser Umgebung gibt es kein Windows
- Die EXE ist nicht codesigniert; Windows SmartScreen wird beim ersten Start warnen

## Pruefsummen (SHA-256)

| Datei | Pruefsumme |
|---|---|
| .github/workflows/build-windows.yml | `8606918814d17cdc57a98c470f53d54c41d1af664d6f943404c9e90ccc9363ea` |
| build/portable_buchhalter.spec | `9dde51a1545355ac20d5137df85509e4d11363924452b7049bade3b4f3ea0ce9` |

## Hinweise

Status bewusst 'teilweise': Der Bauweg ist vollstaendig vorbereitet und auf einem Windows-Rechner ausfuehrbar, das Artefakt selbst existiert hier aber nicht. Eine EXE gilt erst als gebaut, wenn sie tatsaechlich existiert.
