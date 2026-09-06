# Projektstatus - Portabler KI-Buchhalter

> **Diese Datei ist die massgebliche Quelle des Projektstands, nicht der Chat.**
> Sie wird nach jedem abgeschlossenen Task aktualisiert (Masterprompt 44/45).

Stand: 06.09.2026 · Branch `claude/portable-ki-buchhalter-xr1qlj` ·
Version 0.3.0

---

## 1. Kurzfassung

Der portable KI-Mitarbeiter - Produktname **PORTIVA** - ist als
**lauffaehige Anwendung** umgesetzt: Offline-Kern, hybrider Betrieb mit
waehlbarer Betriebsart, persistentes Unternehmensgedaechtnis, lokale
Fachwissensbasis mit Quellenbelegen, Wissensupdate mit Ruecknahme,
Geheimnistresor, Freigabepflicht, Connector-Rahmen, Dateiausgabe in acht
Formaten, Plugin-System, grafische Oberflaeche und Kommandozeile -
abgesichert durch **431 automatische Tests**.

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
| 17 | Sicherheit, Freigaben, Audit, Packaging, EXE | **GEBAUT** | 13 Sicherheitstests gruen; beide Programme auf echtem Windows gebaut und ausgefuehrt |
| 18 | Gesamtintegration, Praxistest, Endabnahme | TEILWEISE | Nutzungskette automatisch **und auf echtem Windows** durchlaufen; Endabnahme mit Modell offen |

### Erweiterung: kommerzielle Produktperspektive (Masterprompt 58 bis 97)

| Task | Inhalt | Status | Nachweis |
|---|---|---|---|
| 19 | Lizenzierung und Kopierschutz | GETESTET | 22 Tests, alle sieben Faelle aus § 96 |
| 20 | Kundentrennung und Datenkontrolle | GETESTET | 13 Tests; Daten zweier Kunden vermischen sich nachweislich nicht |
| 21 | Lizenzregister, SBOM, Release-Dossier | GETESTET | 12 Tests; Unterlagen aus der echten Installation erzeugt |
| 22 | Softwareupdates getrennt vom Wissensupdate | GETESTET | 11 Tests; fehlerhaftes Update setzt automatisch zurueck |
| 23 | Produktversionierung, gefuehrte Einrichtung, zweites Sicherungsziel | GETESTET | Befehle `version`, `einrichten`, `sicherung --ziel` |
| 24 | Commercial-Readiness-Gate | GETESTET | `reife`; COMMERCIAL READY wird nie automatisch vergeben |
| 25 | Windows-Ablauf wieder gruen | GETESTET | alle Schritte des Bauablaufs bestanden |

### Erweiterung: nachgereichte Anforderungen (Masterprompt Teil 4, E1 bis E6)

| Task | Inhalt | Status | Nachweis |
|---|---|---|---|
| 26 | E1 Marke und Erscheinungsbild PORTIVA | GETESTET | 14 Tests; Logo, Symbole, Titel, eigener Schritt im Windows-Ablauf |
| 27 | E2 Betriebsmodi und Wissenssynchronisierung | GETESTET | 14 Tests; Modus bleibt ueber Neustart, OFFLINE prueft das Netz nicht |
| 28 | E3 Fachfragen ohne Unternehmensdaten | GETESTET | 3 Tests; Antwort mit Fundstellen bei leerem Gedaechtnis |
| 29 | E6 Qualitative Antworten und Darstellung | GETESTET | 14 Tests der zehn Pruefaufgaben; Markdown, Abbruch, schrittweise Ausgabe |
| 30 | E4 Datei- und Artefakterzeugung | GETESTET | 20 Tests; acht Formate, von fremden Lesebibliotheken gegengeprueft |
| 31 | E5 Plugin- und Erweiterungssystem | TEILWEISE | 22 Tests; Isolation, Katalog und Lizenzierung offen (`PLUGIN_KONZEPT.md`) |

## 4. Was tatsaechlich geprueft ist

**431 Tests bestanden, 1 uebersprungen** (`python -m pytest tests -q`).
Auf einem echten Windows-Rechner sind alle 13 Schritte des Bauablaufs
bestanden - zuletzt
https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/33973618581
(Stand `914b588`), Artefakt 22.958.149 Bytes. Einzelheiten in
`TESTBERICHT.md`. Besonders hervorzuheben:

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
| Windows-EXE | **Erledigt.** In dieser Entwicklungsumgebung nicht baubar, aber auf einem echten Windows-Rechner gebaut und ausgefuehrt - siehe Abschnitt 1. Das Paket kann als Artefakt heruntergeladen werden, statt selbst zu bauen. | `docs/ABNAHME.md` A |
| Tkinter-Oberflaeche | Weder Tkinter noch Bildschirm in der Entwicklungsumgebung. Die Oberflaechenlogik ist gegen ein Tkinter-Doppel geprueft, und auf Windows ist Tkinter nachweislich vorhanden - **das Fenster selbst wurde aber nie geoeffnet**. | B |
| Lokales Sprachmodell | Modellquellen waren gesperrt. Die Anbindung ist gegen einen echten lokalen Modelldienst geprueft, **nicht mit einem echten GGUF-Modell**. | C |
| Amtliche Quellen | `gesetze-im-internet.de`, `bundesfinanzministerium.de` und weitere waren durch die Netzrichtlinie gesperrt (403 des Proxys). Die Abrufkette ist gegen einen lokalen Server vollstaendig geprueft, **nicht gegen die echten Quellen**. Alle Registereintraege tragen `verified: false`. | G |
| Zweiter PC, echter Laufwerkswechsel | Der **Laufwerkswechsel ist auf echtem Windows geprueft** (`subst`, Zielpfad mit Leerzeichen) - das Unternehmenswissen war dort vorhanden. Ein physisch zweiter Rechner und ein echter USB-Datentraeger standen nicht zur Verfuegung. | F |
| Fachliche Qualitaet der Antworten | Haengt vom eingesetzten Sprachmodell ab. Geprueft ist, dass das **richtige Material** gefunden wird **und dass es das Modell erreicht** (ein Testdoppel zeichnet den Kontext auf). | D |
| Erzeugte Office-Dateien | Word-, Excel-, PowerPoint- und PDF-Dateien werden von den ueblichen Lesebibliotheken (python-docx, openpyxl, python-pptx, pypdf) wieder eingelesen. **Ob Microsoft Office sie anzeigt**, laesst sich nur auf einem Windows-Rechner feststellen. | K |
| Plugin-Isolation | Ein Plugin laeuft im selben Prozess mit den Rechten der Anwendung. Die Rechtepruefung ist eine vermittelte Schnittstelle, **kein Sandkasten**. Fuer Plugins Dritter ist der Stand nicht freigabereif. | `PLUGIN_KONZEPT.md` 9.1 |
| Schrittweise Ausgabe mit echtem Modell | Gegen einen echten HTTP-Ereignisstrom und ein Doppel des lokalen Modells geprueft, **nicht mit einem echten GGUF-Modell**. | C |

## 5a. Stand der kommerziellen Anforderungen

`ANFORDERUNGSNACHWEIS.md` ordnet jedem der 97 Abschnitte zu, wo er umgesetzt
und wo er geprueft ist. Der Reifegrad laesst sich jederzeit abfragen:

```
PORTABLE_BUCHHALTER_KONSOLE.exe reife
```

**Der Status lautet NICHT COMMERCIAL READY** und wird niemals automatisch
vergeben. Die wichtigsten offenen Punkte:

1. Rechtliche Pruefung, insbesondere die Abgrenzung zur Steuerberatung nach
   StBerG (§ 71, 72) - nur extern leistbar
2. Pilotbetrieb bei einem realen Kunden (§ 76)
3. Externe Sicherheitspruefung und Datenschutzkonzept (§ 70, 71)
4. Pruefschluessel des Herausgebers und Code-Signing (§ 86, 92)
5. Klaerung der Weitergabe des Sprachmodells (§ 63)
6. Plugin-Isolation, Plugin-Katalog und Plugin-Lizenzierung (E5.108, 116,
   119) - fuer Plugins Dritter zwingend, fuer mitgelieferte Plugins nicht

## 6. Naechste Schritte

1. **Abnahme durchfuehren** - `docs/ABNAHME.md`. Punkt A ist bereits durch
   den Windows-Ablauf belegt; das fertige Paket kann dort heruntergeladen
   werden. Zu pruefen bleiben vor allem B (Fenster oeffnet sich),
   C (Sprachmodell), D (fachliche Qualitaet), F (zweiter Rechner) und
   G (echte Quellen).
2. **Quellenregister validieren** - der erste Online-Lauf zeigt, welche URLs
   noch stimmen; Korrekturen erfolgen in `config/source_registry.json` ohne
   Programmaenderung.
3. **Ergebnis eintragen** - die tatsaechlich beobachteten Ergebnisse in
   `TESTBERICHT.md` und hier vermerken.
4. **Erzeugte Dateien in Office oeffnen** - je eine XLSX-, DOCX-, PPTX- und
   PDF-Datei aus der Anwendung heraus erzeugen und in Word, Excel und
   PowerPoint oeffnen (Abnahmepunkt K).

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
