# Projektstatus - Portabler KI-Buchhalter

> **Diese Datei ist die massgebliche Quelle des Projektstands, nicht der Chat.**
> Sie wird nach jedem abgeschlossenen Task aktualisiert (Masterprompt 44/45).

Stand: 04.09.2026 · Branch `claude/portable-ki-buchhalter-xr1qlj` ·
Version 0.1.0

---

## 1. Kurzfassung

Der portable KI-Mitarbeiter ist als **lauffaehige Anwendung** umgesetzt:
Offline-Kern, hybrider Betrieb, persistentes Unternehmensgedaechtnis, lokale
Fachwissensbasis mit Quellenbelegen, Wissensupdate mit Ruecknahme,
Geheimnistresor, Freigabepflicht, Connector-Rahmen, grafische Oberflaeche und
Kommandozeile - abgesichert durch **112 automatische Tests**.

**Noch nicht abgenommen** sind die Schritte, die zwingend Windows, eine
echte grafische Oberflaeche, ein echtes Sprachmodell oder Zugriff auf die
echten amtlichen Server verlangen. Sie konnten in der Entwicklungsumgebung
nicht ausgefuehrt werden und werden hier auch nicht als erledigt behauptet.

Der Status lautet daher **noch nicht** „PORTABLER BUCHHALTER MVP FERTIG".
Er lautet: **fertig zur Abnahme**. Der Weg dorthin steht in
`docs/ABNAHME.md`.

## 2. Statusbegriffe (Masterprompt 52)

| Begriff | Bedeutung |
|---|---|
| GEPLANT | Entwurf vorhanden, kein Code |
| IMPLEMENTIERT | Code geschrieben |
| GESPEICHERT | Datei liegt nachweislich auf der Platte |
| GETESTET | Automatischer Test ist tatsaechlich gelaufen |
| VERIFIZIERT | Ergebnis wurde geprueft, nicht nur behauptet |
| GEBAUT | Artefakt (z.B. EXE) existiert tatsaechlich |

## 3. Taskuebersicht

| Task | Inhalt | Status | Nachweis |
|---|---|---|---|
| 01 | Projektziel, Anforderungen, Definition of Done | VERIFIZIERT | `PROJEKTSTATUS.md`, `docs/ABNAHME.md` |
| 02 | Systemarchitektur und Technologieentscheidungen | VERIFIZIERT | `ARCHITEKTUR.md` |
| 03 | Portable Ordnerstruktur, relative Pfade, Konfiguration | GETESTET | 12 Tests, u.a. kein fester Laufwerksbuchstabe im Code |
| 04 | Mitarbeiterprofil und Fach-Masterprompt | GETESTET | Profil laedt, Grenzen wirken im Prompt |
| 05 | Fachmodule und Quellenregister | GETESTET | 13 Module indexiert, 12 Quellen validiert |
| 06 | Quellenabruf und Dokument-zu-lokal-Pipeline | GETESTET | 8 Tests gegen echten HTTP-Server |
| 07 | Normalisierung, Metadaten, Versionierung | GETESTET | Original, Normalisat und Metadatendatei nachgewiesen |
| 08 | Lokale Wissensdatenbank und Suchindex | GETESTET | FTS5, Migration, Integritaetspruefung |
| 09 | Embedding- und Retrieval-System | GETESTET | 48 fachliche Recherchetests |
| 10 | Lokales Sprachmodell und Inferenz | TEILWEISE GETESTET | 8 Tests gegen echten Modelldienst; **ohne echtes GGUF-Modell** |
| 11 | RAG-Orchestrierung und Quellenbelege | GETESTET | Erfundene Fundstellen werden entfernt |
| 12 | Persistentes Unternehmensgedaechtnis | VERIFIZIERT | Speichern, Neustart, Ortswechsel - Wissen ist wieder da |
| 13 | Offlinefaehige grafische Benutzeroberflaeche | TEILWEISE GETESTET | 10 Strukturtests; **nicht in echtem Tkinter ausgefuehrt** |
| 14 | Hybridbetrieb, Internetstatus, Update-System | GETESTET | Offlinelauf, Ruecknahme, Zeitplan |
| 15 | Unternehmens-Onboarding und Memory-Verwaltung | GETESTET | 21 Fragen, Rueckfrage vor dem Speichern |
| 16 | Connector-/ERP-Architektur | GETESTET | Nur-Lese-Standard und Freigabesperre erzwungen |
| 17 | Sicherheit, Freigaben, Audit, Packaging, EXE | TEILWEISE | 13 Sicherheitstests gruen; **EXE nicht gebaut** |
| 18 | Gesamtintegration, Praxistest, Endabnahme | TEILWEISE | Nutzungskette automatisch durchlaufen; Endabnahme offen |

## 4. Was tatsaechlich geprueft ist

**112 Tests bestanden, 1 uebersprungen** (`python -m pytest tests -q`).
Einzelheiten in `TESTBERICHT.md`. Besonders hervorzuheben:

* Die **vollstaendige Nutzungskette** aus Masterprompt 49 laeuft in einem
  Test durch: offline starten, Fachfrage mit Quellen, Unternehmenswissen
  speichern, beenden, Datenbestand an einen anderen Ort mit Leerzeichen im
  Pfad, dort starten, Wissen ist da, online gehen, Wissensupdate,
  offline gehen, das neu geladene Wissen offline nutzen, erneut starten.
* **Kein Server noetig**: alle Daten liegen nachweislich in Dateien unterhalb
  der Wurzel.
* **Wiederherstellbarkeit ohne Chat**: Wurzel, Sicherungen, Wissensstand und
  letzter Checkpoint sind allein von der Platte ablesbar.

## 5. Was **nicht** geprueft ist (und warum)

Die Entwicklung fand in einem **Linux-Container ohne Windows, ohne Bildschirm
und mit stark eingeschraenktem Netzzugang** statt.

| Punkt | Lage | Abnahme |
|---|---|---|
| Windows-EXE | In dieser Umgebung **nicht baubar**. Build-Skript und Windows-Ablauf der Fortlaufenden Integration sind vorhanden und bauen sie auf einem echten Windows-Rechner. | `docs/ABNAHME.md` A |
| Tkinter-Oberflaeche | Weder Tkinter noch Bildschirm vorhanden. Die Oberflaechenlogik ist gegen ein Tkinter-Doppel geprueft, das echte Fenster **nicht**. | B |
| Lokales Sprachmodell | Modellquellen waren gesperrt. Die Anbindung ist gegen einen echten lokalen Modelldienst geprueft, **nicht mit einem echten GGUF-Modell**. | C |
| Amtliche Quellen | `gesetze-im-internet.de`, `bundesfinanzministerium.de` und weitere waren durch die Netzrichtlinie gesperrt (403 des Proxys). Die Abrufkette ist gegen einen lokalen Server vollstaendig geprueft, **nicht gegen die echten Quellen**. Alle Registereintraege tragen `verified: false`. | G |
| Zweiter PC, echter Laufwerkswechsel | Ueber wechselnde Wurzelverzeichnisse simuliert; im Windows-Ablauf zusaetzlich ueber `subst`. Ein echter zweiter Rechner stand nicht zur Verfuegung. | F |
| Fachliche Qualitaet der Antworten | Haengt vom eingesetzten Sprachmodell ab. Geprueft ist, dass das **richtige Material** gefunden wird. | D |

## 6. Naechste Schritte

1. **Abnahme durchfuehren** - `docs/ABNAHME.md`, Punkte A bis J.
2. **Quellenregister validieren** - der erste Online-Lauf zeigt, welche URLs
   noch stimmen; Korrekturen erfolgen in `config/source_registry.json` ohne
   Programmaenderung.
3. **Ergebnis eintragen** - die tatsaechlich beobachteten Ergebnisse in
   `TESTBERICHT.md` und hier vermerken.

Erst danach darf der Status lauten: **PORTABLER BUCHHALTER MVP FERTIG**.

## 7. Sinnvolle Ausbaustufen danach

* Auswahl mehrerer Mitarbeiter beim Start (Masterprompt 54)
* DATEV-Format als erster echter ERP-Weg - kommt ohne Zugaenge und VPN aus
* Mitgelieferte Python-Laufzeit, damit auch der Startweg ohne EXE kein
  installiertes Python braucht
* Optionale zentrale Synchronisation als Erweiterung, nie als Ersatz des
  Offline-Kerns (Masterprompt 6)

## 8. Wiederherstellung nach Chat- oder Kontextverlust

1. `git log --oneline -20` - letzter Commit
2. `checkpoints/LETZTER_STAND.json` - letzter Task und Fortsetzungspunkt
3. `checkpoints/TASK_*.md` - Einzelheiten je Task mit Pruefsummen
4. `python -m pytest tests -q` - ist der Stand gruen?
5. diese Datei - Gesamtlage

Der Chat wird dafuer nicht benoetigt. Checkpoints liegen doppelt: im
Repository und in einem davon unabhaengigen Verzeichnis
(`KIM_CHECKPOINT_DIR`, unter Windows standardmaessig
`D:\Ki-Agent\checkpoints`).
