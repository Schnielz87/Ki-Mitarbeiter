# Sicherung und Wiederherstellung

## Was unbedingt gesichert werden muss

| Rang | Was | Wo | Warum |
|---|---|---|---|
| 1 | **Unternehmensgedaechtnis** | `database/company.db` | Nicht wiederbeschaffbar. Enthaelt Unternehmenswissen, Gespraeche, Belege, Protokoll, Freigaben. |
| 2 | Geheimnistresor | `config/secrets.enc` | Zugangsdaten; ohne Passwort ohnehin unlesbar. |
| 3 | Einstellungen | `config/settings.json` | Schnell wiederherstellbar, aber laestig. |
| 4 | Quellenregister | `config/source_registry.json` | Nur bei eigenen Ergaenzungen wichtig. |
| 5 | Fachwissen | `resources/index/knowledge.db` | Jederzeit neu aufbaubar - Sicherung spart nur Zeit. |
| 6 | Belege | `workspace/belege/` | Sofern die Originale nicht anderswo liegen. |

Kurz: **Ohne `company.db` ist die Arbeit weg. Alles andere ist Komfort.**

## Sicherung erstellen

In der Anwendung: Registerkarte **Wissen aktualisieren** →
**Sicherung erstellen**.

Auf der Kommandozeile:

```
PORTABLE_BUCHHALTER.exe sicherung --name monatsende
```

Ergebnis: `backups/<Zeitstempel>-<Name>/` mit `company.db`, `knowledge.db`,
den Konfigurationsdateien und einer `MANIFEST.json`, die zu jeder Datei eine
SHA-256-Pruefsumme enthaelt.

Die Datenbanken werden mit der Sicherungsfunktion von SQLite kopiert - das
ist auch waehrend des Betriebs konsistent. Ein einfaches Kopieren der Datei
waehrend die Anwendung laeuft ist es **nicht**.

## Empfohlener Rhythmus

| Wann | Was |
|---|---|
| Nach dem Onboarding | einmal sichern |
| Woechentlich | sichern |
| Vor einem groesseren Wissensupdate | sichern (die Ruecknahme deckt nur das Fachwissen ab) |
| Vor der Weitergabe des Datentraegers | sichern |

**Wichtig:** Eine Sicherung, die nur auf demselben Datentraeger liegt, hilft
bei dessen Verlust nicht. Mindestens eine Kopie gehoert auf einen anderen
Datentraeger oder in ein gesichertes Netzlaufwerk.

## Wiederherstellung

### Fall 1: Unternehmenswissen versehentlich geloescht

Kein Grund fuer eine Wiederherstellung - Loeschen ist Archivieren:

```
PORTABLE_BUCHHALTER.exe wissen list --status archived
PORTABLE_BUCHHALTER.exe wissen history <schluessel>
```

In der Oberflaeche steht der Verlauf unter **Unternehmenswissen → Verlauf**.

### Fall 2: Falscher Inhalt gespeichert

Der frühere Stand steht im Verlauf. Einfach den richtigen Inhalt erneut
speichern - er wird zur naechsten Version, der falsche bleibt nachvollziehbar
erhalten.

### Fall 3: `company.db` beschaedigt oder verloren

1. Anwendung schliessen.
2. Die beschaedigte Datei umbenennen, nicht loeschen:
   `database/company.db` → `database/company.db.defekt`
3. Aus der juengsten Sicherung zurueckkopieren:
   `backups/<Zeitstempel>/company.db` → `database/company.db`
4. Auch die Dateien `company.db-wal` und `company.db-shm` entfernen, falls
   vorhanden.
5. Anwendung starten, `check` ausfuehren - die Systempruefung meldet die
   Zahl der Eintraege.

### Fall 4: Fachwissen beschaedigt

Am einfachsten neu aufbauen: die Dateien `resources/index/knowledge.db*`
loeschen und die Anwendung starten. Die mitgelieferten Fachmodule werden
automatisch wieder aufgenommen; amtliche Quellen holt ein Wissensupdate
zurueck.

### Fall 5: Ein Wissensupdate hat etwas verschlechtert

```
PORTABLE_BUCHHALTER.exe update --zuruecknehmen <Lauf-ID>
```

Die Lauf-ID steht im Ordnernamen unter `updates/`. Das
Unternehmensgedaechtnis bleibt unberuehrt.

### Fall 6: Der ganze Datentraeger ist defekt

1. Neuen Datentraeger vorbereiten (verschluesseln, siehe
   `SICHERHEITSKONZEPT.md`).
2. Programmordner erneut aufspielen (aus dem Build oder einer Kopie).
3. Sprachmodell nach `models/` legen.
4. Aus der Sicherung zurueckkopieren: `company.db`, `settings.json`,
   `secrets.enc`, gegebenenfalls `knowledge.db`.
5. `check` ausfuehren.
6. Fehlt `knowledge.db`, ein Wissensupdate durchfuehren.

## Sicherung pruefen

Eine ungeprüfte Sicherung ist keine Sicherung.

```
PORTABLE_BUCHHALTER.exe --root "<Pfad zur Sicherung>" check
```

Oder die Pruefsummen gegen `MANIFEST.json` vergleichen (PowerShell):

```
Get-FileHash backups\<Zeitstempel>\company.db -Algorithm SHA256
```

## Projektstand wiederherstellen (Entwicklung)

Unabhaengig vom Chat, ausschliesslich anhand des Datentraegers:

1. `git log --oneline -20` - letzter Commit
2. `checkpoints/LETZTER_STAND.json` - letzter abgeschlossener Task und
   Fortsetzungspunkt
3. `checkpoints/TASK_*.md` - Einzelheiten je Task mit Pruefsummen
4. `PROJEKTSTATUS.md` - Gesamtlage
5. `python -m pytest tests -q` - ist der Stand gruen?

Checkpoints liegen doppelt: im Repository und in einem davon unabhaengigen
Verzeichnis (`KIM_CHECKPOINT_DIR`, unter Windows standardmaessig
`D:\Ki-Agent\checkpoints`).
