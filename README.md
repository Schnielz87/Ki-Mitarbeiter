# Portabler KI-Mitarbeiter · Referenzimplementierung: KI-Buchhalter

Ein hybrider, portabler KI-Fachmitarbeiter, der vollstaendig von einem
externen Datentraeger laeuft: **offline arbeitsfaehig**, mit lokalem
Fachwissen, lokalem Sprachmodell und einem **dauerhaften
Unternehmensgedaechtnis** - und mit Internet um aktuelle Quellen,
Wissensupdates und spaetere ERP-Anbindungen erweiterbar.

Fuer den taeglichen Gebrauch: **[START_HIER.md](START_HIER.md)**.

---

## Grundsatzentscheidungen

| Frage | Antwort |
|---|---|
| Braucht es einen Server? | Nein. Alle Kernfunktionen laufen gegen lokale Dateien und eine eingebettete Datenbank. |
| Braucht es Internet? | Nein. Ohne Netz laeuft der komplette Offline-Kern; Online-Funktionen sind eine Erweiterung derselben Anwendung. |
| Zwei Programme fuer offline und online? | Nein. **Eine** Anwendung, eine Oberflaeche, ein Gedaechtnis, eine Historie. |
| Fester Laufwerksbuchstabe? | Nein. Die Anwendung erkennt ihren eigenen Startpfad; D:, E:, F: sind gleichwertig, Leerzeichen im Pfad ebenfalls. |
| Wo liegen die Daten? | Auf dem Datentraeger. Nicht in AppData, nicht in der Registry, nicht im Browsercache. |
| Wer entscheidet? | Der Mensch. Buchungen, Meldungen und Zahlungen sind Vorschlaege und brauchen eine Freigabe. |

## Aufbau

```
Oberflaeche (Tkinter)      Kommandozeile
            \                  /
             +-> AppController <-+        kopflos, vollstaendig testbar
                      |
   +---------+--------+--------+---------+----------+
   |         |        |        |         |          |
Profil   Gedaechtnis  RAG   Recherche  Modell   Aktualisierung
                       |       |         |          |
                  company.db  knowledge.db      Quellenregister
```

Ausfuehrlich: **[ARCHITEKTUR.md](ARCHITEKTUR.md)**

## Bedienung ueber die Kommandozeile

Die Kommandozeile kann alles, was die Oberflaeche kann - nuetzlich fuer
Automatisierung und zur Fehlersuche.

Dafuer gibt es ein **zweites Programm**: `PORTABLE_BUCHHALTER_KONSOLE.exe`.
Beide enthalten denselben Code. Der Unterschied liegt allein in der Ausgabe:

| Programm | Wofuer |
|---|---|
| `PORTABLE_BUCHHALTER.exe` | Doppelklick. Oeffnet nur das Fenster, ohne schwarzes Konsolenfenster daneben. |
| `PORTABLE_BUCHHALTER_KONSOLE.exe` | Eingabeaufforderung und PowerShell. Ein Programm ohne Konsole hat unter Windows keine Ausgabe - `check` bliebe dort stumm. |

```
PORTABLE_BUCHHALTER_KONSOLE.exe check                      Systempruefung
PORTABLE_BUCHHALTER_KONSOLE.exe frage "..."                eine Fachfrage
PORTABLE_BUCHHALTER_KONSOLE.exe chat                       Unterhaltung
PORTABLE_BUCHHALTER_KONSOLE.exe wissen list                Unternehmenswissen anzeigen
PORTABLE_BUCHHALTER_KONSOLE.exe wissen set <schluessel> "<wert>"
PORTABLE_BUCHHALTER_KONSOLE.exe wissen history <schluessel>   Aenderungsverlauf
PORTABLE_BUCHHALTER_KONSOLE.exe onboarding --interaktiv    Unternehmensdaten erfassen
PORTABLE_BUCHHALTER_KONSOLE.exe update                     Wissen aktualisieren
PORTABLE_BUCHHALTER_KONSOLE.exe update --trocken           Trockenlauf ohne Schreiben
PORTABLE_BUCHHALTER_KONSOLE.exe update --zuruecknehmen <ID>
PORTABLE_BUCHHALTER_KONSOLE.exe beleg <datei>              Beleg aufnehmen
PORTABLE_BUCHHALTER_KONSOLE.exe freigaben                  offene Freigaben
PORTABLE_BUCHHALTER_KONSOLE.exe sicherung                  Sicherung erstellen
PORTABLE_BUCHHALTER_KONSOLE.exe status                     Lagebericht als JSON
```

Ohne gebaute EXE: `python portable_buchhalter.py <befehl>`.

## Entwicklung

```
python -m pytest tests -q                 Tests
python portable_buchhalter.py check       Systempruefung
python tools/modell_einrichten.py empfehlen
powershell -File build\build_windows.ps1  Windows-Build (nur auf Windows)
```

Pflichtabhaengigkeiten: **keine**. Die Anwendung laeuft mit der
Standardbibliothek von Python 3.11 oder neuer. Die Pakete in
`requirements.txt` erweitern sie; fehlt eines, sagt die Anwendung das und
arbeitet ohne die betreffende Funktion weiter.

## Ehrlichkeit ueber den Stand

`PROJEKTSTATUS.md` unterscheidet strikt zwischen geplant, implementiert,
gespeichert, getestet, verifiziert und gebaut - und benennt, was in der
Entwicklungsumgebung **nicht** geprueft werden konnte (Windows-EXE, echte
Tkinter-Oberflaeche, echtes Sprachmodell, echte amtliche Quellen).
`docs/ABNAHME.md` fuehrt durch genau diese Punkte.

## Weiterer KI-Mitarbeiter

Der technische Core enthaelt keinen buchhaltungsspezifischen Begriff. Ein
neuer Mitarbeiter (Controller, Einkauf, Recht ...) entsteht durch ein neues
Profilverzeichnis: **[docs/NEUER_MITARBEITER.md](docs/NEUER_MITARBEITER.md)**

## Lizenz und Verantwortung

Die fachlichen Ausgaben sind Zuarbeit ohne Gewaehr. Die Verantwortung und
jede rechtsverbindliche Freigabe verbleiben beim Menschen. Es werden nur frei
zugaengliche amtliche Quellen lokal gespeichert; entgeltpflichtige oder
zugangsbeschraenkte Datenbanken werden nicht kopiert.
