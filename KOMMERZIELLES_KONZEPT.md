# Kommerzielle Produktperspektive

Masterprompt Abschnitte 58 bis 80.

## 1. Was hier gebaut wird

Kein einmalig zusammengeschraubtes Kundenprojekt, sondern eine Plattform:

```
PORTABLE-KI-CORE          standardisiert, fuer alle Kunden gleich
  + FACHMITARBEITER-MODUL austauschbar (Buchhalter, Controller, ...)
  + KUNDENKONFIGURATION   je Kunde
  + UNTERNEHMENSGEDAECHTNIS je Kunde
  + WISSENSPAKETE         gemeinsam, versioniert
  + OPTIONALE CONNECTOREN je Kunde
```

### Was standardisiert bleibt

Alles unter `src/pkc`, `src/app` und `src/ui`: Oberflaeche, Kommandozeile,
Modellverwaltung, Recherche, Wissensdatenbank, Unternehmensgedaechtnis,
Datenhaltung, Update-Engine, Sicherheit, Freigaben, Protokoll,
Connector-Rahmen, Packaging, Lizenzierung, Checkpoints.

Der Core kennt **keinen** buchhaltungsspezifischen Begriff. Ein neuer
Fachmitarbeiter entsteht durch ein Profilverzeichnis, nicht durch Aenderungen
am Core (siehe `docs/NEUER_MITARBEITER.md`).

### Was je Kunde unterschiedlich ist

Unternehmensprofil · Unternehmenswissen · Benutzer und Berechtigungen ·
Fachregeln · Prozesse · ERP-Konfiguration · Connector-Konfiguration ·
Vorlagen · kundenspezifische Dokumente

Technisch getrennt unter `customers/<kennung>/` - siehe Abschnitt 4.

## 2. Produktpositionierung (Abschnitt 59)

**KI-Fachassistent zur fachlichen Zuarbeit.** Nicht: ein Ersatz fuer einen
verantwortlichen Menschen.

Die KI analysiert, recherchiert, strukturiert, berechnet, prueft, erkennt
Auffaelligkeiten, erstellt Vorschlaege und Entscheidungsvorlagen und bereitet
Vorgaenge vor. Kritische Ergebnisse bleiben beim Menschen.

Das ist keine Marketingformulierung, sondern technisch durchgesetzt:

* Buchungen, Meldungen, Zahlungen und Stammdatenaenderungen brauchen den
  Zustand `FREIGEGEBEN`; ohne ihn schlaegt die Ausfuehrung fehl.
* Connectoren stehen standardmaessig auf `read_only`.
* Jede Antwort traegt Quellen, Wissensstand und Freigabehinweis.
* Der Fach-Masterprompt benennt die Grenzen der Rolle ausdruecklich.

## 3. Kein Versprechen der Fehlerfreiheit (Abschnitt 60)

Das Produktversprechen beruht **nicht** darauf, dass die KI immer richtig
liegt. Es beruht auf ueberpruefbaren Systemeigenschaften:

| Zusage | Wie sie ueberprueft wird |
|---|---|
| Die Anwendung startet zuverlaessig | Systempruefung beim Start, auf echtem Windows getestet |
| Der Offlinebetrieb funktioniert | Automatischer Test der gesamten Nutzungskette ohne Netz |
| Die Datenhaltung funktioniert | Neustart- und Ortswechseltests, Integritaetspruefung |
| Quellen sind nachvollziehbar | Jede Antwort fuehrt die verwendeten Fundstellen |
| Der Wissensstand ist sichtbar | In jeder Antwort und in der Systempruefung |
| Unsicherheiten werden gekennzeichnet | „Nicht ausreichend sicher"; erfundene Fundstellen werden entfernt |
| Kritische Aktionen brauchen Freigabe | Zustandsautomat, technisch erzwungen |
| Updates sind versioniert | Updatebericht je Lauf, Ruecknahme moeglich |
| Tests sind dokumentiert | TESTBERICHT.md, aus tatsaechlichen Laeufen |
| Aenderungen sind nachvollziehbar | Git-Historie, Checkpoints, Protokoll |
| Rueckkehr auf einen funktionierenden Stand | Sicherungen, Update-Ruecknahme, Checkpoints |

Diese Liste ist der Kern des Produktversprechens. Sie ist pruefbar - die
Behauptung "die KI liegt richtig" waere es nicht.

## 4. Kundentrennung (Abschnitt 61)

Ist eine Kundenkennung gesetzt, liegen alle unternehmensbezogenen Daten unter
`customers/<kennung>/`:

```
customers/
    kunde_001/
        company/  database/  conversations/  workspace/
        config/   logs/      backups/        data/
```

Das allgemeine Fachwissen bleibt bewusst gemeinsam - es ist fuer alle gleich
und enthaelt keine Unternehmensdaten. Automatische Tests belegen, dass
Unternehmenswissen von Kunde A weder bei Kunde B noch im gemeinsamen
Fachwissen auftaucht, und dass eine Kennung wie `../andererkunde` abgewiesen
wird.

## 5. Datenkontrolle des Kunden (Abschnitt 62)

| Anforderung | Umsetzung |
|---|---|
| Unternehmensdaten exportieren | `kunde export` - vollstaendig, ohne Lizenz und Fachwissen |
| Unternehmenswissen anzeigen | Oberflaeche und `wissen list` |
| Informationen korrigieren | `wissen set` mit Versionierung und Verlauf |
| Einzelne Informationen loeschen | `wissen delete` (archivieren) bzw. endgueltig |
| Gespraechsverlaeufe loeschen | `delete_conversation` |
| Dokumente loeschen | `beleg --loeschen` |
| Komplette Kundeninstanz loeschen | `kunde loeschen` mit Bestaetigung und Sicherung |
| Sicherungen verwalten | `sicherung`, `backups/` |

Loeschungen werden protokolliert; das Loeschen eines ganzen Kundenbereichs
verlangt die ausdrueckliche Wiederholung der Kennung und sichert vorher.

## 6. Lizenzen der Bestandteile (Abschnitte 63, 64)

`LIZENZREGISTER.md` und `sbom.json` werden aus der tatsaechlichen Installation
erzeugt (`tools/produktunterlagen.py`). Je Bestandteil ist festgehalten, ob
die **kommerzielle Nutzung** und ob die **Weitergabe an Kunden** zulaessig ist -
Masterprompt 63 verlangt genau diese Unterscheidung.

**Offene Punkte, die vor einem Vertrieb zu klaeren sind** (Stand heute):

1. **PyInstaller** - die Bootloader-Ausnahme erlaubt die Weitergabe der
   erzeugten Programme unter eigener Lizenz, **solange der Bootloader
   unveraendert bleibt**.
2. **Sprachmodelle** - Apache-2.0 erlaubt die kommerzielle Nutzung. Die
   Weitergabe einer konkreten quantisierten Modellfassung ist gesondert zu
   pruefen; Quantisierungen stammen oft von Dritten. **Empfehlung: das Modell
   vom Kunden beziehen lassen, statt es mitzuliefern.**
3. **Amtliche Wissensbestaende** - Gesetzestexte sind gemeinfrei, die
   Aufbereitung der Portale unterliegt eigenen Bedingungen.

## 7. Software- und Wissensupdates getrennt (Abschnitt 65)

| | Wissensupdate | Softwareupdate |
|---|---|---|
| Inhalt | Gesetze, Erlasse, Rechtsprechung | Programmcode, Oberflaeche, Runtime, Connectoren |
| Umgesetzt | **ja**, mit Bericht und Ruecknahme | Konzept steht, siehe UPDATE_KONZEPT.md |
| Versioniert | ja, je Lauf | ueber die Produktversion |
| Ruecksetzbar | ja, getestet | ueber Sicherung des Programmordners |

Ein fehlerhaftes Update darf eine funktionierende Installation nicht
zerstoeren. Fuer Wissensupdates ist das umgesetzt und getestet; fuer
Softwareupdates ist der Weg beschrieben und muss vor der kommerziellen
Freigabe implementiert und getestet werden.

## 8. Versionierung (Abschnitt 66)

Der Befehl `version` weist getrennt aus: Softwareversion, Produktstufe,
Fachmodul, Wissenspaket, Wissensstand, Version des Unternehmensprofils,
Modell und Anbieter, Instanz-ID und Lizenzzustand. Damit laesst sich eine
Kundeninstallation spaeter eindeutig zuordnen.

## 9. Nachvollziehbarkeit (Abschnitt 67)

Protokolliert werden Softwareversion, Modell, Wissensstand, verwendete
Quellen, relevante Einstellungen, Freigaben und Fehler - ohne unnoetige
Aufzeichnung vertraulicher Inhalte. Der Fragetext selbst wird nicht ins
Protokoll geschrieben, nur die Kennzahlen des Vorgangs.

## 10. Fernwartung und Telemetrie (Abschnitte 68, 69)

**Beides gibt es nicht.** Der Grundbetrieb sendet nichts an den Hersteller,
und es existiert kein Fernzugriff. Ein automatischer Test belegt, dass die
Anwendung ohne ausdrueckliche Handlung keine ausgehende Verbindung ausser der
Netzstatuspruefung und dem angeforderten Wissensupdate aufbaut.

Wird spaeter Fernwartung angeboten, muss sie ausdruecklich aktiviert werden,
zeitlich begrenzbar, nachvollziehbar und wieder abschaltbar sein.

## 11. Was vor der kommerziellen Freigabe fehlt (Abschnitte 71, 76, 77)

`python tools/produktunterlagen.py reife` prueft den Stand. **COMMERCIAL
READY wird niemals automatisch vergeben.** Offen sind insbesondere:

* Pilotbetrieb bei einem realen Kunden
* danach: Behebung der dabei gefundenen kritischen Fehler
* externe Sicherheitspruefung
* Datenschutzkonzept (Verarbeitungsverzeichnis, Auftragsverarbeitung)
* **rechtliche Pruefung, insbesondere die Abgrenzung zur Steuerberatung nach
  StBerG** - das ist der wichtigste offene Punkt des gesamten Vorhabens
* Supportprozess
* Klaerung der Modellweitergabe

## 12. Reihenfolge (Abschnitt 80)

```
technische Zuverlaessigkeit  ->  Pilotbetrieb  ->  Standardisierung
->  Sicherheits-, Lizenz- und Compliance-Pruefung  ->  Vermarktung
```

Der aktuelle Stand ist der erste Schritt: eine technisch belastbare,
getestete Anwendung. Alles Weitere folgt in dieser Reihenfolge - nicht
parallel und nicht vorgezogen.
