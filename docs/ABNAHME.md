# Abnahme - Schritt fuer Schritt

Dieses Dokument fuehrt durch die Definition of Done aus Masterprompt 51 und
den Portabilitaetstest aus Abschnitt 49.

## Warum Sie diese Schritte selbst gehen muessen

Die Entwicklung fand in einem **Linux-Container ohne Windows, ohne Bildschirm
und mit gesperrtem Netzzugang zu amtlichen Quellen** statt. Was dort nicht
geprueft werden konnte, wird hier nicht als geprueft behauptet. Die folgende
Tabelle trennt das sauber:

| Punkt | In der Entwicklung | Bei Ihnen zu pruefen |
|---|---|---|
| Kernlogik, Gedaechtnis, Recherche, Update, Sicherheit | **automatisch getestet, 109 Tests** | - |
| Portabilitaet ueber Wurzelverzeichnisse und Pfade mit Leerzeichen | **automatisch getestet** | - |
| Windows-EXE gebaut | **ja** - auf einem echten Windows-Rechner im Ablauf der Fortlaufenden Integration | A nur noch bestaetigen |
| Grafische Oberflaeche in echtem Tkinter | nein - kein Tkinter, kein Bildschirm | **B** |
| Antwort eines echten Sprachmodells | nein - keine Modellquelle erreichbar | **C** |
| Abruf der echten amtlichen Quellen | nein - Netzrichtlinie sperrte die Hosts | **D** |
| Echter zweiter PC und echter Laufwerkswechsel | nur simuliert | **E** |

**Bereits auf echtem Windows bestanden** (Ablauf
https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/33970160321):
beide Programme gebaut, Systempruefung der EXE, Offline-Fachfrage mit
Quellenteil, Unternehmenswissen ueber einen Neustart hinweg, Laufwerkswechsel
ueber `subst` in einen Pfad mit Leerzeichen, alle 134 Tests. Das fertige
Paket liegt dort als Artefakt `Portable-Buchhalter-Windows` (22,8 MB).

Damit ist Punkt **A** faktisch erledigt - Sie koennen entweder selbst bauen
oder das Artefakt herunterladen und entpacken.

---

## Vorbereitung

Benoetigt: ein Windows-PC mit Python 3.11 oder neuer (nur zum **Bauen**;
der spaetere Anwender braucht kein Python) und ein externer Datentraeger mit
mindestens 16 GB frei.

---

## A. EXE bauen (oder herunterladen)

**Schneller Weg:** Im Ablauf oben auf „Artifacts" das Paket
`Portable-Buchhalter-Windows` herunterladen und entpacken. Dann weiter bei B.

**Selbst bauen:**

```
powershell -ExecutionPolicy Bypass -File build\build_windows.ps1
```

Das Skript prueft Python und Tkinter, installiert die Abhaengigkeiten, laesst
die Tests laufen, baut die EXE und stellt den fertigen portablen Ordner unter
`dist\Portable-Buchhalter\` her.

**Erfuellt, wenn:** `dist\Portable-Buchhalter\PORTABLE_BUCHHALTER.exe` **und**
`PORTABLE_BUCHHALTER_KONSOLE.exe` existieren und das Skript ohne Fehler endet.

Es sind zwei Programme mit demselben Code: das erste fuer den Doppelklick
(ohne Konsolenfenster), das zweite fuer die Eingabeaufforderung. Ein Programm
ohne Konsole hat unter Windows keine Ausgabe - deshalb die Trennung.

Danach den kompletten Ordnerinhalt auf den Datentraeger kopieren.

- [ ] A1 EXE existiert
- [ ] A2 Ordner auf den Datentraeger kopiert

---

## B. Start ohne Entwicklungsumgebung (DoD 1-4)

Am besten an einem PC **ohne** Python.

1. Datentraeger anschliessen
2. Projektordner oeffnen
3. `PORTABLE_BUCHHALTER.exe` doppelklicken

**Erwartung:** Es oeffnet sich das Fenster der Systempruefung mit den Zeilen
Datenverzeichnis, Unternehmensgedaechtnis, Fachwissen, Suchindex, Lokales
Modell, Quellenregister und Geheimnistresor, darunter Wissensstand,
Internet, Betriebsart. Der Knopf **BUCHHALTER STARTEN** ist anklickbar; es
oeffnet sich das Hauptfenster.

> Windows SmartScreen kann beim ersten Start warnen, weil die EXE nicht
> signiert ist. Ueber „Weitere Informationen" → „Trotzdem ausfuehren".

> **Wichtig fuer die Eingabeaufforderung:** Fuer Befehle immer
> `PORTABLE_BUCHHALTER_KONSOLE.exe` verwenden. Die Fensterfassung
> `PORTABLE_BUCHHALTER.exe` hat unter Windows keine Ausgabe, und die
> Eingabeaufforderung wartet nicht einmal auf sie - sie kehrt sofort zurueck.
> Das ist kein Fehler, sondern der Unterschied zwischen einem Fenster- und
> einem Konsolenprogramm (wie `pythonw.exe` und `python.exe`).

- [ ] B1 Doppelklick oeffnet die Systempruefung
- [ ] B2 Hauptfenster oeffnet sich
- [ ] B3 Registerkarten Unterhaltung, Unternehmenswissen, Belege, Wissen
      aktualisieren, Einstellungen sind vorhanden

---

## C. Sprachmodell (DoD 6)

Nach `docs\MODELL_EINRICHTEN.md` vorgehen, dann:

```
python tools\modell_einrichten.py pruefen
PORTABLE_BUCHHALTER_KONSOLE.exe check
```

**Erwartung:** Das Werkzeug gibt eine sinnvolle Antwort auf die Testfrage
aus. In der Systempruefung steht bei „Lokales Modell" **OK**.

- [ ] C1 Modell antwortet im Pruefwerkzeug
- [ ] C2 Systempruefung zeigt OK

---

## D. Offline-Fachfrage (DoD 5, 7, 8)

WLAN und Netzwerkkabel trennen. Anwendung starten.

**Erwartung:** Betriebsart **OFFLINE**, die Anwendung startet normal.

Fragen stellen, zum Beispiel:

1. „Welche Pflichtangaben muss eine Rechnung nach § 14 UStG enthalten?"
2. „Wie buche ich einen innergemeinschaftlichen Erwerb aus Frankreich?"
3. „Wann liegt Reverse Charge nach § 13b UStG vor?"

**Erwartung je Antwort:** eine fachliche Antwort im Schema (ERGEBNIS,
BEGRUENDUNG, ...), ein Abschnitt **QUELLEN** mit nachvollziehbaren
Fundstellen, ein Abschnitt **WISSENSSTAND**, ein Abschnitt
**FREIGABEBEDARF**. Rechts stehen die Quellen mit Auszug.

Die 22 fachlichen Testfaelle in
`src\profiles\buchhalter\testcases.json` eignen sich als Pruefliste. Dass die
Recherche zu jedem Fall das richtige Material findet, ist automatisch
geprueft; die **Qualitaet der Formulierung** haengt vom Modell ab und ist
hier zu beurteilen.

- [ ] D1 Anwendung startet ohne Internet
- [ ] D2 Fachfrage wird beantwortet
- [ ] D3 Quellen sind nachvollziehbar und passen zur Frage
- [ ] D4 Wissensstand wird genannt

---

## E. Unternehmensgedaechtnis (DoD 9, 10)

Im Chat eingeben:

> Wir verwenden grundsaetzlich SKR03.

**Erwartung:** Rueckfrage „Soll ich dauerhaft merken: ...?" → **Ja**.

Weiter:

> Merke dir: Rechnungen ab 5.000 EUR muessen durch den Geschaeftsfuehrer
> freigegeben werden.

Beide Angaben muessen unter **Unternehmenswissen** stehen.

- [ ] E1 Rueckfrage erscheint
- [ ] E2 Angaben stehen im Unternehmenswissen
- [ ] E3 `database\company.db` ist groesser geworden

---

## F. Datentraeger wechseln (DoD 11, 12, 13, 18)

1. Anwendung schliessen
2. Datentraeger sicher entfernen
3. An einen **anderen** Windows-PC anschliessen - moeglichst mit einem
   anderen Laufwerksbuchstaben
4. `PORTABLE_BUCHHALTER.exe` doppelklicken
5. Fragen: „Welchen Kontenrahmen verwendet dieses Unternehmen?"

**Erwartung:** Die Anwendung startet. Die Antwort nennt **SKR03**. Unter
Unternehmenswissen stehen beide Angaben. Die Statuszeile zeigt den neuen
Pfad.

- [ ] F1 Start am zweiten PC
- [ ] F2 SKR03 wird erkannt
- [ ] F3 Freigaberegel ist vorhanden
- [ ] F4 anderer Laufwerksbuchstabe stoert nicht

---

## G. Wissensupdate (DoD 14, 15, 16, 17)

Mit Internet: Registerkarte **Wissen aktualisieren** →
**Wissen jetzt aktualisieren**.

**Erwartung:** Ein Fortschrittsbalken laeuft, danach erscheint ein Bericht
mit den Zahlen geprueft/aktualisiert/unveraendert/fehlgeschlagen.

> Hier zeigt sich, ob die URLs im Quellenregister stimmen. Sie sind mit
> `verified: false` gekennzeichnet, weil sie in der Entwicklungsumgebung
> nicht erreichbar waren. Fehlschlaege stehen einzeln im Bericht unter
> `updates\<Lauf-ID>\bericht.md`. Eine geaenderte Adresse wird in
> `config\source_registry.json` korrigiert - ohne Programmaenderung.

Dann Internet trennen, Anwendung neu starten und eine Frage zu einem soeben
geladenen Inhalt stellen.

**Erwartung:** Betriebsart OFFLINE, die Antwort nutzt den neuen Inhalt und
nennt ihn als Quelle.

- [ ] G1 Update laeuft und liefert einen Bericht
- [ ] G2 Bericht liegt als Datei unter `updates\`
- [ ] G3 neues Wissen ist offline nutzbar
- [ ] G4 Wissensstand hat sich fortgeschrieben

---

## H. Verbindungswechsel im Betrieb

Bei laufender Anwendung das Netzwerk trennen.

**Erwartung:** Im Chat erscheint sinngemaess „Internetverbindung verloren.
Der portable Buchhalter arbeitet mit dem lokalen Wissensstand vom ... weiter."
Die Anwendung laeuft ohne Neustart weiter. Beim Wiederverbinden meldet sie
das ebenfalls.

- [ ] H1 Verbindungsverlust wird gemeldet, ohne die Anwendung zu stoeren
- [ ] H2 Wiederverbindung wird gemeldet

---

## I. Sicherung und Wiederherstellung (DoD 19)

```
PORTABLE_BUCHHALTER_KONSOLE.exe sicherung --name abnahme
```

Dann pruefen: Liegt `backups\<Zeitstempel>-abnahme\company.db`? Stimmen die
Pruefsummen in `MANIFEST.json`?

Wiederherstellung nach `BACKUP_WIEDERHERSTELLUNG.md` einmal ueben - am besten
mit einer Kopie, nicht mit dem Echtbestand.

- [ ] I1 Sicherung enthaelt die Dateien samt Pruefsummen
- [ ] I2 Wiederherstellung wurde einmal erfolgreich geuebt
- [ ] I3 `checkpoints\LETZTER_STAND.json` ist lesbar

---

## J. Kein Server (DoD 20)

Waehrend die Anwendung laeuft, im Task-Manager pruefen: Es laeuft nur
`PORTABLE_BUCHHALTER.exe` (und, sofern Weg B gewaehlt wurde,
`llama-server.exe` auf 127.0.0.1). Kein Datenbankdienst, kein Webserver, kein
Hintergrunddienst.

- [ ] J1 kein zusaetzlicher Dienst erforderlich

---

## Ergebnis

Erst wenn **alle** Haken gesetzt sind, gilt:

**PORTABLER BUCHHALTER MVP FERTIG**

Bitte das Ergebnis in `PROJEKTSTATUS.md` und `TESTBERICHT.md` eintragen -
mit Datum und den tatsaechlich beobachteten Ergebnissen, nicht mit den
erwarteten.
