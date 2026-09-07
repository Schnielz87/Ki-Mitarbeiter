# BASELINE VOR UI-UMBAU

Aufgenommen am **2026-09-07**, Commit `ee18e88`, Zweig
`claude/portable-ki-buchhalter-xr1qlj`.

Zweck (Masterprompt Abschnitt 3): festhalten, was **vor** dem Umbau
nachweislich funktioniert. Nach dem Umbau werden dieselben Prüfungen
wiederholt und gegenübergestellt. Eine neue Oberfläche gilt nicht als
Erfolg, wenn vorher funktionierende Kernfunktionen danach ausfallen.

---

## 1. Testlauf

    python -m pytest -q

**638 bestanden, 1 übersprungen, 0 Fehlschläge** (67 s).

Der übersprungene Test verlangt eine echte Netzverbindung zu Hugging Face;
die ist in dieser Entwicklungsumgebung gesperrt. Auf dem Windows-Baurechner
läuft er.

## 2. Abdeckung je Kernbereich

| Bereich | Testdateien | Zustand |
|---|---|---|
| Unterhaltung / Chat | `test_controller.py`, `test_antwortdarstellung.py` | grün |
| RAG / Antwortsynthese | `test_antwortqualitaet.py`, `test_fachliche_faelle.py`, `test_fragetyp.py` | grün |
| Quellen & Fundstellen | `test_antwortqualitaet.py`, `test_quellenpruefung.py` | grün |
| Unternehmensgedächtnis | `test_controller.py`, `test_kundentrennung.py` | grün |
| Dokumentpipeline | `test_controller.py` | grün |
| Artifact Engine | `test_artefakte.py`, `test_markdown.py` | grün |
| Plugins | `test_plugins.py` | grün |
| Betriebsmodi | `test_betriebsmodi.py`, `test_netzpruefung.py` | grün |
| Wissensupdate | `test_updater_pipeline.py`, `test_wissenszeitplan.py`, `test_robots.py` | grün |
| Lizenz | `test_lizenzierung.py` | grün |
| Sprachmodell / Wartezeit | `test_wartezeit.py`, `test_modelltempo.py`, `test_modelldienst.py`, `test_llm_providers.py` | grün |
| Modell einrichten (Fenster) | `test_modell_im_fenster.py`, `test_modell_uebernehmen.py`, `test_modell_einrichten.py` | grün |
| Bestehende Oberfläche | `test_gui_logic.py`, `test_modell_im_fenster.py` | grün |
| Portabilität | `test_portability.py`, `test_start.py` | grün |
| Branding | `test_branding.py` | grün |
| Sicherheit / Freigaben | `test_sicherheit_freigaben.py`, `test_checkpoints.py` | grün |
| Anleitung | `test_anleitung.py` | grün |

## 3. Auf dem Windows-Baurechner nachgewiesen

Lauf **34155058461** vom 2026-09-07, vollständig grün. Darin unter anderem:

- EXE gebaut und ausgeführt
- echtes GGUF-Modell bezogen, Modelldienst gestartet, Fachfrage vom Modell
  beantwortet
- Unternehmenswissen gespeichert und nach Neustart gelesen
- Portabilität: anderes Laufwerk, Pfad mit Leerzeichen
- Dateien erzeugt: XLSX, DOCX, PPTX, PDF, CSV
- Plugin installiert, aktiviert, neues Format angemeldet
- 32 amtliche Quellenadressen abgerufen (25 erreichbar, 7 mit HTTP 404 —
  bekannt und dokumentiert)

## 4. Gemessene Wartezeit (Ausgangswert)

Baurechner, Probemodell 0,5B, zwei geteilte Kerne, keine Grafikkarte:

| Stufe | bis zum ersten Wort |
|---|---|
| schnell | 29,8 / 36,5 / 34,5 s (drei Läufe) |
| ausgewogen | 39,0 / 51,4 / 53,7 s |

Auf dem Rechner des Anwenders (7B-Modell, 12 logische Kerne, keine
Grafikkarte), mit der Stoppuhr gemessen:

- **„Was ist Buchhaltung“ — 4 min 20 s bis zum ersten Wort,
  danach 2 min bis zum Ende der Antwort.**

Diese Zahl ist der Ausgangswert für `ANTWORTZEIT_KONZEPT.md`.

## 5. Was in dieser Umgebung nicht prüfbar ist

Unverändert gegenüber `TESTBERICHT.md`:

1. Die echte Tkinter-Oberfläche — das Fenster wurde nie geöffnet. Geprüft
   wird gegen ein Doppel (`tests/tk_double.py`).
2. Ein echtes Sprachmodell — Hugging Face ist hier gesperrt.
3. Windows-Skalierung 100 / 125 / 150 %.

Diese drei Punkte bleiben auch nach dem UI-Umbau offen und werden im
Abschlussbericht erneut als offen ausgewiesen.
