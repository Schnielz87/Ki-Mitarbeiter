# Projektstatus - Portabler KI-Buchhalter

> **Diese Datei ist die massgebliche Quelle des Projektstands, nicht der Chat.**
> Sie wird nach jedem abgeschlossenen Task aktualisiert (Masterprompt 44/45).

Letzte Aktualisierung: siehe Git-Historie · Branch: `claude/portable-ki-buchhalter-xr1qlj`

---

## 1. Statusbegriffe (Masterprompt 52)

| Begriff | Bedeutung |
|---|---|
| GEPLANT | Entwurf vorhanden, kein Code |
| IMPLEMENTIERT | Code geschrieben |
| GESPEICHERT | Datei liegt nachweislich auf der Platte |
| GETESTET | Automatischer Test ist tatsaechlich gelaufen |
| VERIFIZIERT | Ergebnis wurde geprueft, nicht nur behauptet |
| GEBAUT | Artefakt (z.B. EXE) existiert tatsaechlich |

Diese Begriffe werden unten strikt getrennt verwendet.

## 2. Taskuebersicht

| Task | Inhalt | Status |
|---|---|---|
| 01 | Projektziel, Anforderungen, Definition of Done | offen |
| 02 | Systemarchitektur und Technologieentscheidungen | offen |
| 03 | Portable Ordnerstruktur, relative Pfade, Konfiguration | offen |
| 04 | Mitarbeiterprofil und Fach-Masterprompt | offen |
| 05 | Fachmodule und Quellenregister | offen |
| 06 | Quellenabruf und Dokument-zu-lokal-Pipeline | offen |
| 07 | Normalisierung, Metadaten, Versionierung | offen |
| 08 | Lokale Wissensdatenbank und Suchindex | offen |
| 09 | Embedding-/Retrieval-System | offen |
| 10 | Lokales Sprachmodell und Inferenz | offen |
| 11 | RAG-Orchestrierung und Quellenbelege | offen |
| 12 | Persistentes Unternehmensgedaechtnis | offen |
| 13 | Offlinefaehige grafische Benutzeroberflaeche | offen |
| 14 | Hybridbetrieb, Internetstatus, Update-System | offen |
| 15 | Unternehmens-Onboarding und Memory-Verwaltung | offen |
| 16 | Connector-/ERP-Architektur | offen |
| 17 | Sicherheit, Freigaben, Audit, Packaging, EXE | offen |
| 18 | Gesamtintegration, Tests, Endabnahme | offen |

## 3. Umgebungsbedingte Einschraenkungen (wichtig, bitte lesen)

Die Entwicklung fand in einem **Linux-Container ohne Windows, ohne
Bildschirm und mit stark eingeschraenktem Netzzugang** statt. Daraus folgt,
was hier *nicht* verifiziert werden konnte. Das wird offen benannt statt
behauptet:

| Punkt | Lage |
|---|---|
| Windows-EXE | Kann in dieser Umgebung **nicht gebaut** werden. Build-Skript und CI-Workflow fuer Windows sind vorhanden; die EXE entsteht dort. |
| Tkinter-Oberflaeche | Im Container ist **kein Tkinter und kein Bildschirm** vorhanden. Die Oberflaeche wurde daher nicht ausgefuehrt. Die gesamte Logik dahinter ist kopflos getestet. |
| Lokales Sprachmodell | Modell-Downloadquellen sind im Container **gesperrt**; kein GGUF-Modell vorhanden. Die Inferenzschicht ist implementiert und gegen einen echten lokalen HTTP-Modellserver getestet, aber **nicht mit einem echten GGUF-Modell**. |
| Amtliche Quellen | `gesetze-im-internet.de`, `bundesfinanzministerium.de` usw. sind im Container **durch die Netzrichtlinie gesperrt** (403 des Proxys). Die Abrufkette ist gegen einen lokalen HTTP-Server vollstaendig getestet, aber **nicht gegen die echten Quellen**. Die URLs im Quellenregister sind daher `verified: false`. |
| Zweiter PC / Laufwerkswechsel | Wird durch Tests mit wechselnden Wurzelverzeichnissen und Leerzeichen im Pfad simuliert. Ein echter zweiter Windows-PC stand nicht zur Verfuegung. |

Was daraus folgt: Die Abnahmeschritte, die zwingend Windows, ein Modell oder
echte Internetquellen brauchen, muss der Auftraggeber auf seinem Rechner
durchfuehren. `docs/ABNAHME.md` fuehrt Schritt fuer Schritt hindurch.

## 4. Naechster Schritt

Siehe `checkpoints/LETZTER_STAND.json`.

## 5. Wiederherstellung nach Chat-/Kontextverlust

1. `git log --oneline -20` - letzter Commit.
2. `checkpoints/LETZTER_STAND.json` - letzter abgeschlossener Task und
   Fortsetzungspunkt.
3. `checkpoints/TASK_*.md` - Detail je Task inklusive Pruefsummen.
4. `python -m pytest tests -q` - pruefen, ob der Stand gruen ist.
5. Diese Datei - Gesamtlage.

Der Chat wird dafuer nicht benoetigt.
