# Checkpoint 18 - Gesamtintegration, Praxistest und Abnahmevorbereitung

* Zeitpunkt: 2026-09-05T13:57:44+00:00
* Status: **TEILWEISE**
* Git-Commit: `32db7304884026a146cab62bde0e25c937fb4710`
* Naechster Task: Abnahme durch den Auftraggeber: docs/ABNAHME.md B, C, D, F, G

## Fortsetzungspunkt

Paket herunterladen oder bauen, Fenster per Doppelklick oeffnen, Sprachmodell einrichten, Fachfragen beurteilen, zweiten Rechner und echte Quellen pruefen

## Erledigte Arbeit

- Nutzungskette aus Masterprompt 49 laeuft automatisch und auf echtem Windows durch
- Vier echte Fehler aus dem Windows-Ablauf behoben (Fensterprogramm ohne Ausgabe, Schalterposition, zwei Pfadausbrueche)
- Projektstatus, Testbericht, Abnahme und Changelog auf den belegten Stand gebracht

## Dateien

- tests/test_abnahme_kette.py
- docs/ABNAHME.md
- PROJEKTSTATUS.md

## Tests

- python -m pytest tests -q; Windows-Ablauf 33970160321

**Testergebnis:** 134 Tests bestanden, 1 uebersprungen; 13 von 13 Windows-Schritten bestanden

## Offene Punkte

- B: Fenster per Doppelklick oeffnen
- C: echtes Sprachmodell
- D: fachliche Qualitaet der Antworten
- F: zweiter Windows-Rechner
- G: Quellenregister gegen die echten amtlichen Server

## Pruefsummen (SHA-256)

| Datei | Pruefsumme |
|---|---|
| PROJEKTSTATUS.md | `f955bef178d4b14a855a3c3e53cce3e0417b6d4e060436b528a38cfd158df699` |
| TESTBERICHT.md | `28e04cf7ab18dbe4d35715416b0dc2236b0e744be5789a12f12905a58c0238b5` |

## Hinweise

Status weiterhin 'fertig zur Abnahme', nicht 'MVP FERTIG'. Der EXE-Bau ist belegt, die verbleibenden Punkte brauchen Hardware und ein Modell.
