# Checkpoint 25 - Windows-Ablauf wieder gruen

* Zeitpunkt: 2026-09-05T14:53:29+00:00
* Status: **ABGESCHLOSSEN**
* Git-Commit: `b9253b766bc2a8f0cda8ad7aa2ecdfb54a13c06b`
* Naechster Task: Abnahme und Pilotbetrieb

## Fortsetzungspunkt

Status bleibt 'fertig zur Abnahme' - nicht MVP FERTIG, nicht COMMERCIAL READY

## Erledigte Arbeit

- Meldungsfenster-Haenger behoben (KIM_UNBEAUFSICHTIGT + Vorkehrung in conftest.py)
- Zeitgrenzen und cancel-in-progress im Bauablauf
- Plattformabhaengigen Test durch plattformunabhaengige Pruefung ersetzt, mit Gegenprobe
- Umgebungsschalter vollstaendig dokumentiert (ARCHITEKTUR.md 5a) und reserviert

## Dateien

- portable_buchhalter.py
- tests/conftest.py
- tests/test_start.py
- tests/test_kundentrennung.py
- tests/test_portability.py
- src/pkc/config.py
- .github/workflows/build-windows.yml
- ARCHITEKTUR.md
- TESTBERICHT.md
- docs/ABNAHME.md

## Tests

- python -m pytest tests -q
- Windows-Ablauf 33973017177

**Testergebnis:** alle 13 Schritte bestanden, Artefakt 22.956.536 Bytes

## Offene Punkte

- Abnahme B bis G in docs/ABNAHME.md - Fenster per Doppelklick, echtes Sprachmodell, fachliche Qualitaet, zweiter Rechner, echte amtliche Quellen
- Kommerzielle Reife: rechtliche Pruefung StBerG, Pilotbetrieb, externe Sicherheitspruefung, Datenschutzkonzept, Herausgeberschluessel, Codesignatur, Modellweitergabe
