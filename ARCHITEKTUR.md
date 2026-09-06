# Architektur - Portabler KI-Mitarbeiter (Referenz: KI-Buchhalter)

Version 0.1 · Stand siehe `PROJEKTSTATUS.md`

---

## 1. Leitidee

Es gibt **eine** Anwendung, nicht zwei. Der Offline-Kern ist die Grundlage;
Online-Funktionen sind eine Erweiterung desselben Programms mit derselben
Oberflaeche, derselben Wissensbasis, demselben Unternehmensgedaechtnis und
derselben Gespraechshistorie.

```
                     PORTABLER KI-BUCHHALTER
                              |
              +---------------+---------------+
              |                               |
        OFFLINE-CORE                   ONLINE-ERWEITERUNG
   lokales Sprachmodell            Wissensupdate (Quellenregister)
   lokale Fachwissens-DB           aktuelle Rechtsquellen
   Unternehmensgedaechtnis         optionale Online-KI
   lokale Dokumente                ERP-/System-Connectoren
   hybride Recherche (RAG)
   Gespraechshistorie
   lokale Datenhaltung (SQLite)
```

Faellt das Netz weg, entfaellt nur die rechte Saeule. Der linke Teil laeuft
unveraendert weiter.

## 2. Schichten

| Schicht | Paket | Aufgabe |
|---|---|---|
| Portabilitaet | `pkc.paths` | Wurzelerkennung, relative Pfade, Schreibrechte |
| Konfiguration | `pkc.config` | Defaults + `config/settings.json` + `KIM_*`-Variablen |
| Datenhaltung | `pkc.db` | SQLite mit Migrationen, WAL, Sicherung, Integritaet |
| Fachwissen | `pkc.knowledge` | Extraktion, Normalisierung, Chunking, Dokumentenspeicher |
| Recherche | `pkc.retrieval` | BM25 (FTS5) + Vektoren, RRF-Fusion, Quellenhierarchie |
| Unternehmenswissen | `pkc.memory` | Versioniertes Gedaechtnis, Erkennung dauerhafter Fakten |
| Sprachmodell | `pkc.llm` | Anbieterabstraktion: lokal / lokaler Server / online / Stub |
| Antwortlogik | `pkc.rag` | Kontextaufbau, Antwortschema, Quellenzwang |
| Aktualisierung | `pkc.updater` | Quellenregister, inkrementeller Abruf, Bericht, Ruecknahme |
| Sicherheit | `pkc.security` | Geheimnistresor, Zugriffsschutz |
| Nachweis | `pkc.audit` | Protokoll, Freigabe-Zustandsautomat (Human-in-the-Loop) |
| Anbindung | `pkc.connectors` | ERP-/Dateischnittstellen, standardmaessig nur lesend |
| Anwendung | `app.controller` | Kopflose Steuerung - von GUI *und* Tests genutzt |
| Oberflaeche | `ui.tk_app`, `ui.cli` | Tkinter-GUI und Kommandozeile ueber demselben Controller |
| Profil | `profiles/buchhalter` | Rolle, Masterprompt, Fachmodule, Testfaelle |

**Wichtige Entwurfsentscheidung:** Die gesamte Fachlogik liegt im
`AppController` und ist kopflos testbar. Die Tkinter-Oberflaeche ist eine
duenne Ansicht darauf. Dadurch ist die Logik automatisiert pruefbar, auch wo
keine grafische Oberflaeche vorhanden ist.

## 3. Technologieentscheidungen

| Thema | Entscheidung | Begruendung |
|---|---|---|
| Sprache | Python 3.11+ | Grosse Standardbibliothek, gutes Windows-Packaging (PyInstaller) |
| Oberflaeche | Tkinter (Standardbibliothek) | Keine Zusatzabhaengigkeit, offline, klein, in PyInstaller stabil |
| Datenbank | SQLite (eingebettet) + FTS5 | Kein Server noetig (Masterprompt 5), Datei wandert mit der SSD |
| Volltextsuche | SQLite FTS5, BM25 | Teil der Datenbank, kein separater Suchdienst |
| Vektorsuche | Eigener Vektorspeicher in SQLite | Kein zusaetzlicher Dienst; Vektoren als BLOB |
| Einbettung | Hashing-Verfahren (Standard), GGUF optional | Funktioniert **immer**, auch ohne Modell |
| Sprachmodell | llama.cpp (GGUF), lokal | Offline, CPU-tauglich, quantisierbar, austauschbar |
| Modellanbindung | In-Process **oder** lokaler llama-server | Server-Variante vermeidet Kompilierung auf dem Zielrechner |
| HTTP | `urllib` der Standardbibliothek | Keine `requests`-Abhaengigkeit im EXE-Build |
| Konfiguration | JSON (YAML optional) | Kein PyYAML noetig |
| Verschluesselung | `cryptography` (AES-256-GCM) | Nur fuer den Geheimnistresor; ohne sie: klare Fehlermeldung |
| PDF | `pypdf` optional | Fehlt es, wird das ehrlich gemeldet statt leeren Text zu liefern |
| Packaging | PyInstaller (onedir) auf Windows | Erzeugt `PORTABLE_BUCHHALTER.exe` ohne Installation |

### Warum kein Server?

Alle Kernfunktionen - Start, Modell, Suche, Gedaechtnis, Historie,
Einstellungen, Checkpoints - laufen gegen lokale Dateien und eingebettete
Datenbanken. Ein zentraler Server ist ausschliesslich eine spaetere,
optionale Ausbaustufe (Abschnitt 6 des Masterprompts) und ersetzt nie den
Offline-Kern.

## 4. Datenfluss einer Fachfrage

```
Benutzerfrage
   |
   +-- Unternehmensgedaechtnis  (company.db, FTS5)      -> Unternehmenskontext
   +-- Fachwissensrecherche     (knowledge.db, BM25+Vektor)
   |        |
   |        +-- Quellenhierarchie: Gesetz > Erlass > Rechtsprechung > Behoerde > Sekundaer
   |        +-- Zeitbezug: gueltig_ab / gueltig_bis (Masterprompt 25)
   |
   +-- Belegtexte des Nutzers   (user_chunks, FTS5)
   |
   v
Kontextaufbau (pkc.rag) -> Systemprompt des Mitarbeiterprofils + Fundstellen
   |
   v
Sprachmodell (lokal; optional online)
   |
   v
Antwort im Fachschema + Quellenliste + Wissensstand + Freigabehinweis
   |
   +-- Speicherung: Nachricht, Quellenbelege, Protokoll
   +-- Pruefung auf dauerhaft relevante Unternehmensinformationen -> Rueckfrage
```

## 5. Verzeichnisse auf dem portablen Datentraeger

```
<Wurzel>/                        (erkannt ueber .portable_root)
  PORTABLE_BUCHHALTER.exe        erzeugt durch den Windows-Build
  START_HIER.md
  src/                           Programmcode (pkc, profiles, app, ui)
  config/                        settings.json, source_registry.json, secrets.enc
  models/                        lokales GGUF-Sprachmodell (nicht im Repository)
  runtime/                       mitgelieferte Laufzeitteile, Zustandsdatei
  knowledge/                     kuratierte Fachmodule (mitgeliefert)
  resources/raw|normalized|metadata|index
  company/                       exportiertes Unternehmensprofil (lesbar)
  database/company.db            Unternehmensgedaechtnis, Historie, Protokoll
  resources/index/knowledge.db   Fachwissen, Abschnitte, Vektoren
  conversations/                 exportierte Gespraeche
  workspace/                     Arbeitsdateien des Nutzers
  connectors/                    Connector-Konfigurationen
  updates/<Lauf-ID>/             Sicherung + Updatebericht (Ruecknahme moeglich)
  logs/  backups/  data/  checkpoints/  tests/  docs/  tools/  build/
```

Es gibt **keinen** fest verdrahteten Laufwerksbuchstaben. Die Wurzel wird zur
Laufzeit ermittelt (`pkc.paths.detect_root`), Pfade mit Leerzeichen
funktionieren, `D:` und `E:` sind gleichwertig.

## 5a. Schalter der Umgebung

Die Anwendung braucht im Normalbetrieb **keine** Umgebungsvariable - die
Wurzel wird selbst gefunden. Die folgenden Schalter gibt es fuer Sonderfaelle;
sie sind vollstaendig, damit niemand raten muss.

| Schalter | Wirkung |
|---|---|
| `KIM_ROOT` | Setzt die portable Wurzel ausdruecklich, statt sie zu ermitteln. Fuer Tests und ungewoehnliche Ablagen. |
| `KIM_CHECKPOINT_DIR` | Zweiter, vom Datentraeger unabhaengiger Ort fuer Checkpoints. Unter Windows sonst `D:\Ki-Agent\checkpoints`. |
| `KIM_CARRIER_ID` | Ueberschreibt die Kennung des Datentraegers, an die eine Lizenz gebunden ist. Nur fuer Tests des Lizenzverfahrens. |
| `KIM_LLM_PROVIDER` | Beispiel fuer den allgemeinen Mechanismus: `KIM_<PFAD_MIT_UNTERSTRICHEN>` ueberschreibt einen Eintrag aus `config/settings.json`, hier `llm.provider`. Ueberschrieben werden nur **bereits vorhandene** Eintraege; ein unbekannter Name legt nichts an. |
| `KIM_PASSPHRASE` | Passwort des Geheimnistresors, damit es nicht abgefragt werden muss. Nur fuer unbeaufsichtigte Ablaeufe - ein Passwort in einer Umgebungsvariablen ist fuer andere Prozesse desselben Kontos lesbar und gehoert nicht in den Normalbetrieb. |
| `KIM_PLUGIN` | Wird von der Anwendung **gesetzt**, nicht vom Benutzer: sie traegt darin die Kennung des Plugins ein, das in diesem Vorgang laeuft (Erweiterung E5.108). So ist in Protokollen und im Taskmanager erkennbar, wozu ein Vorgang gehoert. |
| `KIM_UNBEAUFSICHTIGT` | Betrieb ohne Aufsicht: ein Startfehler wird nur nach stderr und in `logs\startfehler.txt` gemeldet, **kein Meldungsfenster**. Notwendig ueberall dort, wo niemand auf "OK" klicken kann - automatische Tests, Bauablaeufe, Dienste. Ein modales Fenster wartet sonst endlos; genau daran blieben die Windows-Ablaeufe 11 bis 16 haengen. Beim Doppelklick bleibt das Fenster, dort ist es der einzige sichtbare Weg. Erkannt werden `1`, `ja`, `true`; `0`, `nein`, `false` und leer schalten ab. |

## 6. Trennung Fachwissen / Unternehmenswissen (Masterprompt 14)

Zwei getrennte Datenbanken, bewusst nicht eine:

* `resources/index/knowledge.db` - allgemeingueltiges Fachwissen. Wird durch
  Updates ersetzt und kann jederzeit neu aufgebaut werden.
* `database/company.db` - Unternehmenswissen, Gespraeche, Belege, Protokoll,
  Freigaben. **Nicht ersetzbar**, wird gesichert, wandert mit der SSD.

Ein Wissensupdate kann daher nie Unternehmenswissen beschaedigen. Eine
Ruecknahme eines Updates laesst das Unternehmensgedaechtnis unberuehrt.

## 7. Wiederverwendung fuer weitere KI-Mitarbeiter (Masterprompt 53)

Wiederverwendbar ist alles unter `src/pkc`, `src/app` und `src/ui`.
Ein neuer Mitarbeiter (Controller, Einkauf, Recht ...) benoetigt nur ein
neues Verzeichnis unter `src/profiles/<rolle>/` mit:

```
profile.json        Rolle, Faehigkeiten, Grenzen, Rechte, Antwortschema
prompts/system.md   Masterprompt der Rolle
knowledge/*.md      mitgeliefertes Fachwissen
sources.json        rollenspezifische Ergaenzungen zum Quellenregister
testcases.json      fachliche Testfaelle
```

Kein Kernmodul kennt buchhaltungsspezifische Begriffe; die Fachlichkeit
steckt im Profil und in den Daten.
