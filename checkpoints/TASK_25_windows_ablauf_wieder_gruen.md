# Checkpoint 25 - Windows-Ablauf wieder gruen

* Zeitpunkt: 2026-09-05T15:01:43+00:00
* Status: **ABGESCHLOSSEN**
* Git-Commit: `fce4af59dcbc7f2df259c5918a9e50873e5a58d5`
* Naechster Task: Abnahme und Pilotbetrieb

## Fortsetzungspunkt

Status bleibt 'fertig zur Abnahme' - nicht MVP FERTIG, nicht COMMERCIAL READY

## Erledigte Arbeit

- Meldungsfenster-Haenger behoben (KIM_UNBEAUFSICHTIGT + Vorkehrung in conftest.py)
- Zeitgrenzen und cancel-in-progress im Bauablauf
- Plattformabhaengigen Test durch plattformunabhaengige Pruefung ersetzt, mit Gegenprobe
- Umgebungsschalter vollstaendig dokumentiert (ARCHITEKTUR.md 5a) und reserviert
- Wiedereinstiegspunkt WEITERARBEIT.md auf den belegten Stand neu geschrieben
- Checkpointmechanismus erstmals getestet; --test-result verlor stillschweigend Werte

## Dateien

- portable_buchhalter.py
- tests/conftest.py
- tests/test_start.py
- tests/test_kundentrennung.py
- tests/test_portability.py
- tests/test_checkpoints.py
- src/pkc/config.py
- tools/checkpoint.py
- .github/workflows/build-windows.yml
- ARCHITEKTUR.md
- TESTBERICHT.md
- docs/ABNAHME.md
- WEITERARBEIT.md

## Tests

- python -m pytest tests -q
- Windows-Ablauf 33973017177

**Testergebnis:** 219 bestanden, 1 uebersprungen | alle 13 Schritte bestanden, Artefakt 22.956.536 Bytes

## Offene Punkte

- Abnahme B bis G in docs/ABNAHME.md - Fenster per Doppelklick, echtes Sprachmodell, fachliche Qualitaet, zweiter Rechner, echte amtliche Quellen
- Kommerzielle Reife: rechtliche Pruefung StBerG, Pilotbetrieb, externe Sicherheitspruefung, Datenschutzkonzept, Herausgeberschluessel, Codesignatur, Modellweitergabe

## Pruefsummen (SHA-256)

| Datei | Pruefsumme |
|---|---|
| ANFORDERUNGSNACHWEIS.md | `61fdbe868a02c9ef492638aaca49580067004e8cd8e3fc4b1a11131f3bed35b2` |
| PROJEKTSTATUS.md | `2e74a431b933bdc361f7c695b80c1b60afca27949e4a939ac010671606010d9e` |
| TESTBERICHT.md | `7c00a79ba4078c8331a014c9c8bcad621c6585e5514fd8e7d740ff3a4873c166` |
