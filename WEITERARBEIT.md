# Hier weitermachen

Diese Datei ist der Wiedereinstiegspunkt (Masterprompt 45). Der Chat wird
zum Fortsetzen **nicht** benoetigt - alles Notwendige steht auf dem
Datentraeger.

## Stand

| | |
|---|---|
| Branch | `claude/portable-ki-buchhalter-xr1qlj` |
| Letzter Commit | siehe `git log -1` |
| Gepusht | ja |
| Tests | **425 gruen, 1 uebersprungen** (`python -m pytest tests -q`) |
| Windows | alle 13 Schritte bestanden, Ablauf https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/33973618581 |
| Tasks 01 bis 18 | abgeschlossen (Masterprompt 48) |
| Tasks 19 bis 25 | abgeschlossen (Erweiterung, Masterprompt 58 bis 97) |
| Tasks 26 bis 31 | E1 bis E6 (Masterprompt Teil 4); E5 teilweise |
| Status | **fertig zur Abnahme** - nicht "MVP FERTIG", nicht "COMMERCIAL READY" |

Der Auftrag selbst liegt als `MASTERPROMPT.md` daneben, der Abgleich Punkt
fuer Punkt in `ANFORDERUNGSNACHWEIS.md`.

## Was fertig ist

Die Anwendung laeuft: Offline-Kern, hybrider Betrieb, persistentes
Unternehmensgedaechtnis, lokale Fachwissensbasis mit Quellenbelegen,
Wissensupdate mit Ruecknahme, Geheimnistresor, Freigabepflicht,
Connector-Rahmen, Oberflaeche und Kommandozeile. Dazu die kommerzielle
Erweiterung: Lizenzierung und Kopierschutz, Kundentrennung, Lizenzregister
und SBOM, ruecksetzbare Softwareupdates, Produktversionierung,
Commercial-Readiness-Gate.

Dazu die nachgereichten Erweiterungen (Masterprompt Teil 4): Marke
PORTIVA, waehlbare Betriebsart mit Wissenssynchronisierung, Fachfragen ohne
Unternehmensdaten, qualitative Antworten mit Einstufung der Frage und
schrittweiser Ausgabe, Dateiausgabe in acht Formaten und ein Plugin-System.

Auf einem echten Windows-Rechner sind beide Programme gebaut und
ausgefuehrt worden - Systempruefung, Offline-Fachfrage mit Quellenteil,
Unternehmenswissen ueber einen Neustart hinweg und nach Wechsel des
Laufwerksbuchstabens in einen Pfad mit Leerzeichen. Das fertige Paket liegt
als Artefakt am oben genannten Ablauf.

## Genau hier ansetzen

### 1. Abnahme durchfuehren (wichtigster Punkt)

`docs/ABNAHME.md`, Punkte **B bis G**. Punkt A ist belegt - das fertige
Paket kann heruntergeladen statt selbst gebaut werden. Offen sind die
Punkte, die diese Entwicklungsumgebung nicht leisten konnte:

* **B** - Fenster oeffnet sich per Doppelklick (hier kein Bildschirm)
* **C** - echtes Sprachmodell (keine Modellquelle erreichbar), Anleitung in
  `docs/MODELL_EINRICHTEN.md`
* **D** - fachliche Qualitaet der Antworten im echten Betrieb
* **F** - physisch zweiter Rechner
* **G** - echte amtliche Quellen (die Netzrichtlinie sperrte die Hosts)
* **K** - erzeugte Word-, Excel-, PowerPoint- und PDF-Dateien in Office
  oeffnen (hier ist kein Office vorhanden)
* **L** - Plugin installieren und aktivieren

Die beobachteten Ergebnisse gehoeren danach in `TESTBERICHT.md` und
`PROJEKTSTATUS.md`. **Erst dann** darf der Status "PORTABLER BUCHHALTER MVP
FERTIG" lauten.

### 2. Kommerzielle Reife

`PORTABLE_BUCHHALTER_KONSOLE.exe reife` zeigt den Stand. COMMERCIAL READY
wird nie automatisch vergeben; ein Test stellt das sicher. In dieser
Reihenfolge:

1. rechtliche Pruefung - Abgrenzung zur Steuerberatung (StBerG)
2. Pilotbetrieb bei einem realen Kunden
3. externe Sicherheitspruefung
4. Datenschutzkonzept
5. oeffentlicher Pruefschluessel des Herausgebers, dann Code-Signing
6. Freigabe zur Weitergabe des Sprachmodells

### 3. Plugin-System zu Ende bauen (nur fuer Plugins Dritter noetig)

`PLUGIN_KONZEPT.md` Abschnitt 9 nennt die offenen Punkte. Der wichtigste:
ein Plugin laeuft heute im selben Prozess. Fuer fremde Plugins braucht es
einen eigenen Prozess mit eingeschraenkten Rechten und eine Uebergabe ueber
eine Leitung statt ueber Objekte. Fuer mitgelieferte Plugins ist der Stand
tragfaehig.

### 4. Quellenregister validieren

Der erste Online-Lauf zeigt, welche URLs noch stimmen. Korrekturen erfolgen
in `config/source_registry.json` **ohne** Programmaenderung.

## Wo der Stand nachzulesen ist

1. `PROJEKTSTATUS.md` - Gesamtlage, Taskuebersicht, was geprueft ist und was nicht
2. `TESTBERICHT.md` - jeder Test mit Ergebnis, dazu alle gefundenen Maengel
3. `ANFORDERUNGSNACHWEIS.md` - alle 97 Abschnitte des Auftrags und die
   Erweiterungen E1 bis E6 mit Nachweis
4. `checkpoints/LETZTER_STAND.json` - letzter Task und Fortsetzungspunkt
5. `docs/ABNAHME.md` - die Abnahme Schritt fuer Schritt
6. `python -m pytest tests -q` - ist der Stand gruen?

## Hinweise zur Entwicklungsumgebung

* Linux **ohne Tkinter und ohne Bildschirm** - die Oberflaeche laesst sich
  dort nicht ausfuehren, nur ueber das Doppel in `tests/tk_double.py`
  pruefen.
* Der Netzzugang ist auf Paketregistries beschraenkt; amtliche Hosts
  antworten mit 403 des Proxys. Netzcode wird gegen lokale Testserver
  geprueft.
* Testabhaengigkeiten:
  `pip install --break-system-packages pytest cryptography pypdf cffi`
* Zum Gegenpruefen der erzeugten Office-Dateien zusaetzlich
  `pip install openpyxl python-docx python-pptx` - die Anwendung
  selbst braucht diese Pakete nicht.
* Checkpoints ausserhalb des Repositorys: `KIM_CHECKPOINT_DIR` setzen (in
  einem fluechtigen Container; unter Windows ist `D:\Ki-Agent\checkpoints`
  die Vorgabe).
* Alle Umgebungsschalter stehen vollstaendig in `ARCHITEKTUR.md`,
  Abschnitt 5a.
* **Automatische Laeufe brauchen `KIM_UNBEAUFSICHTIGT=1`**, sonst kann ein
  Startfehler ein modales Meldungsfenster oeffnen, auf dessen "OK" niemand
  klickt. `tests/conftest.py` setzt den Schalter fuer den Testlauf selbst.
