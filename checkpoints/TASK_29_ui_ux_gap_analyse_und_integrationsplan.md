# TASK 29 — GAP-Analyse und Integrationsplan UI/UX

**Datum:** 2026-09-07
**Zustand:** ANALYSE ABGESCHLOSSEN — WARTET AUF FREIGABE
**Es wurde nichts an der Oberfläche geändert.**

## Aktueller Task
Verbindlicher UI/UX-Auftrag, Abschnitt 61: Projektstand prüfen, Baseline
aufnehmen, GAP-Analyse, Dienstzuordnung, Action-Registry skizzieren,
Integrationsplan, Risiken, erwartete Änderungen je Datei. Danach STOPP.

## Letzter vollständig abgeschlossener Task
TASK 28 — Sprachmodell belegt, Quellenregister geprüft.
Danach: Wartezeitarbeiten (Tempostufe „automatisch", Zeitaufteilung,
Prompt-Wiederverwendung gemessen) bis Commit `ee18e88`.

## Git
Zweig `claude/portable-ki-buchhalter-xr1qlj`, Ausgangs-Commit `ee18e88`.

## Erledigte Teilaufgaben
1. Übergabepaket entpackt, elf Referenzbilder und das Classic-Logo gesichtet.
2. Baseline aufgenommen: **638 Tests grün, 1 übersprungen**
   → `BASELINE_VOR_UI_UMBAU.md`.
3. Realer Projektstand erfasst: 82 Python-Module, 19 446 Zeilen; Oberfläche
   ist ein Notebook mit sechs Registerkarten; Controller mit 89 öffentlichen
   Methoden als einzige Fassade zum Kern.
4. GAP-Analyse über alle zehn Zielbereiche → `UI_GAP_ANALYSE.md`.
5. Dienstzuordnung für jede geplante UI-Aktion.
6. Action Contract Registry entworfen: **69 Aktionen**, davon 42 mit
   vorhandenem Dienst, 12 mit nötigem Adapter, 15 neu
   → `config/ui_action_registry.yaml`.
7. Integrationsplan in sieben abbrechbaren Schritten.
8. Neun Risiken benannt, mit Gegenmaßnahme.
9. Erwartete Änderungen je Datei aufgelistet.
10. Wartezeit: Ursache gemessen und Lösungsvorschlag erarbeitet
    → `ANTWORTZEIT_KONZEPT.md`.

## Offene Teilaufgaben
Alles ab Schritt 0 des Integrationsplans. **Gesperrt bis zur Freigabe.**

## Letzte erfolgreiche Tests
`python -m pytest -q` → 638 bestanden, 1 übersprungen (2026-09-07).
Windows-Baurechner Lauf 34155058461 vollständig grün.

## Nicht ausgeführte Tests
Echte Tkinter-Oberfläche, echtes Sprachmodell in dieser Umgebung,
Windows-Skalierung 100/125/150 %. Unverändert offen.

## Geänderte Dateien
Nur neue Dokumente — kein Programmcode angefasst:
- `BASELINE_VOR_UI_UMBAU.md` (neu)
- `UI_GAP_ANALYSE.md` (neu)
- `ANTWORTZEIT_KONZEPT.md` (neu)
- `config/ui_action_registry.yaml` (neu)
- `PROJEKTSTATUS.md` (ergänzt)
- `checkpoints/TASK_29_*` (neu)

## Bekannte Fehler
Keine neuen. Bestehend und dokumentiert:
- Prompt-Anfang wird nicht wiederverwendet (Ursache nicht ermittelt),
  siehe `TESTBERICHT.md`.
- Sieben Adressen im Quellenregister antworten mit HTTP 404.

## Exakter Fortsetzungspunkt
`UI_GAP_ANALYSE.md`, Abschnitt 8 — vier Entscheidungen liegen dem
Auftraggeber vor: Umfang (mit oder ohne Vorlagen/Aufgaben), Drag & Drop,
Restore, Reihenfolge gegenüber der Wartezeitarbeit.

## Nächster Schritt
Freigabe abwarten. Danach Schritt 0 des Integrationsplans: Classic-Logo
einsetzen und Begrüßungsbild (3 Sekunden) — der kleinste Schritt mit dem
geringsten Risiko.

## Hinweis zum externen Checkpoint
Abschnitt 55 nennt `D:\Ki-Agent\checkpoints`. Dieser Pfad existiert in der
Entwicklungsumgebung (Linux-Container) nicht und wurde **nicht** angelegt.
Der Checkpoint liegt stattdessen im Repository unter `checkpoints/`, wo
auch die 28 vorherigen liegen — damit ist er versioniert und auf jedem
Rechner auffindbar.
