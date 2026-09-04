# Datenspeicherung - Konzept

Masterprompt Abschnitte 5, 19, 20, 37.

## Grundsatz

**Der Datentraeger ist der massgebliche Speicher, nicht der Gastrechner.**
Wird der Datentraeger abgezogen, bleibt auf dem PC nichts fachlich
Relevantes zurueck. Wird er an einem anderen PC angesteckt, ist alles da.

## Kein Server im Grundbetrieb

Diese Funktionen laufen ohne jeden Serverdienst:

Start · Sprachmodell · lokale Wissenssuche · Unternehmensgedaechtnis ·
Gespraechsverlaeufe · Arbeitsstaende · Dokumente · Einstellungen ·
Checkpoints · lokale Datenbank.

Gewaehlt wurde **SQLite** - eine eingebettete Datenbank, die aus einer
einzigen Datei besteht und ohne Dienst, Port oder Installation auskommt. Ein
spaeterer zentraler Server bleibt moeglich (Masterprompt 6), ersetzt den
Offline-Kern aber nie.

## Ablage auf dem Datentraeger

```
<Wurzel>/                        erkannt ueber die Markerdatei .portable_root
  PORTABLE_BUCHHALTER.exe        Programm
  src/profiles/                  Mitarbeiterprofil (Masterprompt, Fachmodule) - lesbar
  config/settings.json           Einstellungen (nur Abweichungen von den Vorgaben)
  config/source_registry.json    Quellenregister
  config/secrets.enc             verschluesselter Geheimnistresor
  models/                        lokales Sprachmodell (GGUF)
  database/company.db            UNTERNEHMENSGEDAECHTNIS, Gespraeche, Belege,
                                 Protokoll, Freigaben  <- die wichtigste Datei
  resources/index/knowledge.db   Fachwissen, Abschnitte, Vektoren
  resources/raw/                 Originaldokumente, unveraendert
  resources/normalized/          extrahierter Text
  resources/metadata/            Metadaten je Dokument
  company/                       lesbarer Export des Unternehmensprofils
  conversations/                 exportierte Gespraeche
  workspace/belege/              aufgenommene Belege
  updates/<Lauf-ID>/             Sicherung + Updatebericht (Ruecknahme)
  backups/<Zeitstempel>/         Sicherungen mit Pruefsummen
  logs/                          Protokolle
  checkpoints/                   Projektstaende
```

## Keine Ablage auf dem Gastrechner (Abschnitt 20)

Nicht verwendet werden: Windows AppData, Temp als dauerhafter Ort,
Browsercache, Registry, Windows-Benutzerprofil, versteckte Datenbanken auf
dem Host.

Zwei Stellen beruehren den Gastrechner ueberhaupt:

| Stelle | Warum unkritisch |
|---|---|
| Schreibtest beim Start | Legt eine Datei **im Wurzelverzeichnis** an und loescht sie sofort. |
| Temporaere Dateien beim Speichern | Werden **im Zielverzeichnis** angelegt und sofort umbenannt (atomares Schreiben). |

Bewusst wurde **onedir** statt **onefile** fuer die EXE gewaehlt: eine
onefile-EXE entpackt sich bei jedem Start in das Temp-Verzeichnis des
Gastrechners. Das widerspricht diesem Grundsatz.

## Portabilitaet der Pfade

Kein fester Laufwerksbuchstabe, kein fester Benutzerpfad. Die Wurzel wird zur
Laufzeit ermittelt:

1. Umgebungsvariable `KIM_ROOT` (Tests, Sonderfaelle)
2. bei gepackter EXE: das Verzeichnis der EXE
3. Aufwaertssuche nach der Markerdatei `.portable_root`
4. Aufwaertssuche nach dem Programmverzeichnis

Ein automatischer Test durchsucht den gesamten Quellcode nach festen
Laufwerkspfaden und schlaegt fehl, wenn einer auftaucht.

Getestet mit Pfaden, die Leerzeichen, Umlaute, Klammern und tiefe
Verschachtelung enthalten.

## Datenintegritaet

* **WAL-Modus**: ein Stromausfall oder abruptes Abziehen fuehrt nicht zu
  einer halb geschriebenen Datenbank.
* **Atomares Schreiben**: Konfiguration und Tresor werden erst vollstaendig
  in eine Nebendatei geschrieben und dann umbenannt.
* **Integritaetspruefung** beim Start und nach jedem Wissensupdate.
* **SHA-256** ueber jede Sicherungsdatei, im Manifest hinterlegt.
* **Fremdschluessel** aktiviert - keine verwaisten Abschnitte.

## Umgang mit einem defekten Bestand

| Fall | Verhalten |
|---|---|
| `knowledge.db` fehlt | wird beim naechsten Start neu aufgebaut, Fachmodule werden erneut aufgenommen |
| `knowledge.db` beschaedigt | Integritaetspruefung meldet es; Wiederherstellung aus `backups/` oder Neuaufbau |
| `company.db` fehlt | wird neu angelegt (leer) - deshalb ist die Sicherung dieser Datei wichtig |
| `company.db` beschaedigt | Wiederherstellung aus `backups/`, siehe `BACKUP_WIEDERHERSTELLUNG.md` |
| Datentraeger schreibgeschuetzt | Systempruefung meldet es als kritischen Fehler und startet nicht |

## Platzbedarf (Richtwerte)

| Bestandteil | Groesse |
|---|---|
| Programm samt Laufzeit | etwa 40-80 MB |
| Fachmodule und Index | wenige MB |
| Sprachmodell | 2-9 GB je nach Profil |
| Amtliche Quellen nach Updates | je nach Umfang einige hundert MB |
| Unternehmensgedaechtnis | typischerweise unter 50 MB |

Empfehlung: mindestens 16 GB freier Platz auf dem Datentraeger.
