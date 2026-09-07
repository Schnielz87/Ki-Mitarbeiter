# TASK 30 — UI/UX-Umbau umgesetzt

**Datum:** 2026-09-07
**Zustand:** UMGESETZT, LOKAL GRUEN — Windows-Bauablauf zum Zeitpunkt des
Checkpoints noch nicht bestaetigt.

## Aktueller Task
Verbindlicher UI/UX-Auftrag nach Freigabe. Entscheidungen des
Auftraggebers: (1) reiner Oberflaechenumbau zuerst, Vorlagen und Aufgaben
als eigener Auftrag; (2) Drag & Drop nach meiner Wahl; (3) Restore
ausprogrammieren; (4) Wartezeit-Hebel 1 und 2 zuerst.

## Letzter vollstaendig abgeschlossener Task
TASK 29 — GAP-Analyse und Integrationsplan.

## Git
Zweig `claude/portable-ki-buchhalter-xr1qlj`.
Ausgangs-Commit `ee18e88`, Stand dieses Checkpoints `b01a17e`.

## Erledigte Teilaufgaben
1. **Wartezeit, Hebel 1 und 2.** Neue Einstufung `BEGRIFF` mit
   Recherchetiefe 0,3; Fachschema nur noch fuer den verwickelten Fall.
   Prompt einer Begriffsfrage: ein Drittel bis die Haelfte kleiner.
2. **Schritt 0.** PORTIVA-Classic-Logo als Original, alle Varianten neu
   abgeleitet; die dunkle Variante faerbt den Schriftzug hell.
   Begruessungsbild `ui/startbild.py`, drei Sekunden, wegklickbar,
   abschaltbar mit `--kein-startbild`.
3. **Schritt 1.** `ui/schale.py` — linke Navigation statt Karteireiter,
   profilspezifisch konfigurierbar.
4. **Schritt 2.** Unterhaltung: Quellenpanel mit Karten
   (`ui/quellenpanel.py`), Recherche-Details getrennt und geschlossen,
   Eingabe sendet, Strg+N, Escape, Drag & Drop (`ui/dateiablage.py`).
5. **Schritt 3.** Arbeitsergebnisse, Plugins, Verbundene Dienste — drei
   neue Ansichten auf vorhandenen Diensten; elf duenne Adapter im
   Controller; `Artefaktwerk` kann umbenennen und loeschen.
6. **Schritt 4.** Unternehmenswissen mit Kategoriekacheln, Belege mit
   Ergebnisspalte und drei neuen Aktionen, Wissen & Quellen mit
   Kennzahlen und sichtbarer Update-Pipeline.
7. **Schritt 6.** Zehn Bereiche in der Reihenfolge des Zielentwurfs;
   Sprachmodell als Gruppe unter Einstellungen; Systemstatus als
   Ampelliste; Vorlagen und Aufgaben mit ehrlichem Leerezustand.
8. **Restore** ausprogrammiert (Risiko R8), mit vier Vorkehrungen.
9. **Anleitung** auf zehn Bereiche umgestellt, mit Waechtertest.
10. **Nachweise:** `UI_UX_KONZEPT.md`, `UI_BUTTON_FUNKTIONSMATRIX.md`
    (erzeugt, nicht abgeschrieben), `tests/test_keine_toten_knoepfe.py`.

## Offene Teilaufgaben
- Vorlagen und Aufgaben (eigener Auftrag, nicht freigegeben).
- Wartezeit-Hebel 3 (Prompt-Anfang wiederverwenden) und 4
  (Antwortspeicher).
- Plugin-Katalog.
- `UI_REGRESSION_TEST_REPORT.md` (nach dem gruenen Bauablauf).

## Letzte erfolgreiche Tests
`python -m pytest -q` → **745 bestanden, 1 uebersprungen** (2026-09-07).
Baseline vor dem Umbau: 638. Kein Test wurde geloescht oder abgeschwaecht.

## Nicht ausgefuehrte Tests
Echte Tkinter-Oberflaeche, echtes Drag & Drop, Windows-Skalierung
100/125/150 %. Unveraendert offen.

## Bekannte Fehler
- Prompt-Anfang wird nicht wiederverwendet (Ursache nicht ermittelt).
- Sieben Adressen im Quellenregister antworten mit HTTP 404.

## Exakter Fortsetzungspunkt
Windows-Bauablauf zum Commit `b01a17e` abwarten. Bei Gruen:
`UI_REGRESSION_TEST_REPORT.md` schreiben und dem Auftraggeber ZIP und
Anleitung uebergeben.

## Was dabei schiefging und behoben wurde
Fuenf eigene Fehler, alle von Gegenproben oder vom Bauablauf gefunden:
1. Begriffsfragen zunaechst ganz ohne Recherche — ein bestehender Test
   stoppte das: "Was ist Reverse Charge?" gehoert mit §13b belegt.
2. Die Warnung "nur Sekundaerquellen" haengte an der Frageart statt an den
   Fundstellen und waere durch die neue Einstufung ausgefallen.
3. Ein Verweis auf `self.fenster`, das kurz zuvor auf None gesetzt wurde —
   das Begruessungsbild waere beim Klick in einem Fehler geendet.
4. Der Messtest verglich zwei verschiedene Fragen; das Ergebnis hing an
   der Umgebung. Zweimal im Bauablauf gefallen.
5. Das Testdoppel unterschied Knoepfe nicht von Rahmen — der Test auf tote
   Knoepfe fand ausgerechnet die nicht, um die es geht.

## Hinweis zum externen Checkpoint
`D:\Ki-Agent\checkpoints` existiert in dieser Umgebung (Linux-Container)
nicht und wurde **nicht** angelegt. Der Checkpoint liegt im Repository
unter `checkpoints/`.
