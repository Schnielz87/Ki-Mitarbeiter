# Projektstatus - Portabler KI-Buchhalter

> **Diese Datei ist die massgebliche Quelle des Projektstands, nicht der Chat.**
> Sie wird nach jedem abgeschlossenen Task aktualisiert (Masterprompt 44/45).

Stand: 07.09.2026 · Branch `claude/portable-ki-buchhalter-xr1qlj` ·
Version 0.4.0

> **UI/UX-Umbau umgesetzt** (freigegeben am 07.09.2026). Die Oberflaeche
> hat jetzt eine linke Navigation mit **zehn Bereichen**, ein
> Begruessungsbild mit dem PORTIVA-Classic-Logo und ein Quellenpanel mit
> getrennten Recherche-Details.
>
> Nachweise: `UI_UX_KONZEPT.md`, `UI_BUTTON_FUNKTIONSMATRIX.md`
> (62 Bedienelemente, 0 ohne Rueckruf), `UI_GAP_ANALYSE.md`,
> `BASELINE_VOR_UI_UMBAU.md`, `config/ui_action_registry.yaml`.
>
> **Alle zehn Bereiche sind gebaut.** Vorlagen seit Fassung 19,
> Aufgaben & Automationen seit Fassung 20 - siehe `FACHLOGIK_OFFEN.md`
> Abschnitte 4 und 5.
>
> **Wartezeit:** `ANTWORTZEIT_KONZEPT.md`. Hebel 1, 2 und 4 umgesetzt -
> der Prompt einer Begriffsfrage schrumpft um ein Drittel bis um die
> Haelfte, und eine wiederholte Frage kostet gar keine Wartezeit mehr.
> Hebel 3 (Prompt-Anfang wiederverwenden) ist gemessen und wirkt
> **nicht**: der zweite Durchgang ist genauso langsam wie der erste.
> Das sind 62 bis 64 Prozent der Wartezeit, die brachliegen. Die
> Gegenprobe zum Verdaechtigen (Beschleunigungsschalter) steht im
> Bauablauf.

---

## 1. Kurzfassung

Der portable KI-Mitarbeiter - Produktname **PORTIVA** - ist als
**lauffaehige Anwendung** umgesetzt: Offline-Kern, hybrider Betrieb mit
waehlbarer Betriebsart, persistentes Unternehmensgedaechtnis, lokale
Fachwissensbasis mit Quellenbelegen, Wissensupdate mit Ruecknahme,
Geheimnistresor, Freigabepflicht, Connector-Rahmen, Dateiausgabe in acht
Formaten, Plugin-System mit eigenem Vorgang je Plugin, mitgeliefertem
Modelldienst und gefuehrtem Weg zum Sprachmodell, grafische Oberflaeche und
Kommandozeile -
abgesichert durch **966 automatische Tests**, davon fuenfzehn mit einem
**echten Fenster** auf einem echten Bildschirm.

Seit dem 09.09.2026 rechnet die Anwendung selbst, statt es dem
Sprachmodell zu ueberlassen: Abschreibung, Rechnungsabgrenzung und die
Umsatzsteuer werden ausgerechnet und mit Rechenweg ausgewiesen, erfundene
Kontonummern und fachliche Widersprueche werden bemaengelt. Der Anlass
war ein gemeldeter Fehlschlag, bei dem aus 24.000 EUR 5.995.553,43 EUR
wurden. Siehe `FACHPRUEFUNG.md` - dort steht auch, was damit **nicht**
geloest ist.

**Noch nicht abgenommen** sind die Schritte, die zwingend Windows, ein
echtes Sprachmodell oder Zugriff auf die echten amtlichen Server
verlangen. Die grafische Oberflaeche gehoert seit dem 08.09.2026 nicht
mehr dazu: sie wird mit einem echten Fenster geprueft. Sie konnten in der Entwicklungsumgebung
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
| 31 | E5 Plugin- und Erweiterungssystem | TEILWEISE | 32 Tests; eigener Vorgang je Plugin. Katalog und Lizenzierung offen (`PLUGIN_KONZEPT.md`) |
| 32 | Sprachmodell laeuft | GETESTET | Modelldienst mitgeliefert, `modell einrichten`; 37 Tests. Mit echtem GGUF-Modell im Windows-Ablauf nachgewiesen |

## 4. Was tatsaechlich geprueft ist

**610 Tests bestanden, 1 uebersprungen** (`python -m pytest tests -q`).
Auf einem echten Windows-Rechner sind alle 23 Schritte des Bauablaufs
bestanden - zuletzt
https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/34037502726
(Stand `4321909`), Artefakt 56.844.357 Bytes. Einzelheiten in
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
| Tkinter-Oberflaeche | **Geloest.** Mit `xvfb` laesst sich hier ein echtes Fenster oeffnen. Es ist geoeffnet, fotografiert (`docs/Oberflaeche/`) und wird von `tests/test_echte_oberflaeche.py` automatisch geprueft - im Bauablauf unter Linux und unter Windows. Beim ersten Blick darauf war die Oberflaeche unbrauchbar, obwohl 745 Tests gruen waren; siehe `UI_REGRESSION_TEST_REPORT.md` Abschnitt 6a. Offen bleibt allein, wie Schriftglaettung und Farben auf einem echten Windows-Bildschirm wirken. | C |
| Lokales Sprachmodell | **Erledigt.** In dieser Entwicklungsumgebung ist Hugging Face gesperrt; auf dem Windows-Rechner des Bauablaufs nicht. Dort wird das Modell bezogen, der mitgelieferte llama.cpp-Dienst gestartet und eine Fachfrage tatsaechlich vom Modell beantwortet. Auf **Ihrem** Rechner bleibt der einmalige Bezug (`modell einrichten`). | C |
| Amtliche Quellen | `gesetze-im-internet.de`, `bundesfinanzministerium.de` und weitere waren durch die Netzrichtlinie gesperrt (403 des Proxys). Die Abrufkette ist gegen einen lokalen Server vollstaendig geprueft, **nicht gegen die echten Quellen**. Alle Registereintraege tragen `verified: false`. | G |
| Zweiter PC, echter Laufwerkswechsel | Der **Laufwerkswechsel ist auf echtem Windows geprueft** (`subst`, Zielpfad mit Leerzeichen) - das Unternehmenswissen war dort vorhanden. Ein physisch zweiter Rechner und ein echter USB-Datentraeger standen nicht zur Verfuegung. | F |
| Fachliche Qualitaet der Antworten | Haengt vom eingesetzten Sprachmodell ab. Geprueft ist, dass das **richtige Material** gefunden wird **und dass es das Modell erreicht** (ein Testdoppel zeichnet den Kontext auf). | D |
| Erzeugte Office-Dateien | Word-, Excel-, PowerPoint- und PDF-Dateien werden von den ueblichen Lesebibliotheken (python-docx, openpyxl, python-pptx, pypdf) wieder eingelesen. **Ob Microsoft Office sie anzeigt**, laesst sich nur auf einem Windows-Rechner feststellen. | K |
| Fachliche Guete der Modellantworten | Haengt vom gewaehlten Modell ab. Der Bauablauf weist nach, **dass** das Modell antwortet - nicht, wie gut. Das gehoert zur Abnahme. | D |
| Plugins fremder Herkunft | Jedes Plugin laeuft in einem eigenen Vorgang ohne Zugriff auf die Daten der Anwendung. Eine Beschraenkung durch das **Betriebssystem** gibt es nicht. | `PLUGIN_KONZEPT.md` 9.1 |

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
6. Plugin-Katalog und Plugin-Lizenzierung (E5.116, 119) sowie die
   Beschraenkung der Plugin-Vorgaenge durch das Betriebssystem - fuer
   Plugins fremder Herkunft zwingend, fuer mitgelieferte nicht

## 6. Naechste Schritte

1. **Abnahme durchfuehren** - `docs/ABNAHME.md`. Die Punkte A (Bau),
   C (Sprachmodell) und G (echte Quellen) sind durch den Windows-Ablauf
   belegt; das fertige Paket kann dort heruntergeladen werden. Zu pruefen
   bleiben B (Fenster oeffnet sich), D (fachliche Qualitaet der Antworten
   im Betrieb), F (zweiter Rechner) sowie K und L.
2. **Sechs tote Adressen ersetzen** - der Online-Lauf hat das Register
   geprueft: 9 von 32 Adressen erreichbar. Sechs antworten mit HTTP 404 und
   brauchen je eine neue Adresse (`quellen setzen`, ohne Programmaenderung).
   Zu `gesetze-im-internet.de` kam vom Baurechner gar keine Antwort - diese
   17 Adressen sind damit weder bestaetigt noch widerlegt und bleiben
   unveraendert. Einzelheiten in `WEITERARBEIT.md`, Abschnitt 4.
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
