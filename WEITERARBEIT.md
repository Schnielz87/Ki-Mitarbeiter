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
| Tests | **558 gruen, 1 uebersprungen** (`python -m pytest tests -q`) |
| Windows | alle 23 Schritte bestanden, Ablauf https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/34037502726 |
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
* **C** - erledigt: der Bauablauf bezieht ein echtes Modell, startet den
  mitgelieferten Dienst und laesst eine Fachfrage beantworten. Auf einem
  Kundenrechner bleibt der einmalige Bezug (`modell einrichten`)
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

### 3. Plugin-System zu Ende bauen (nur fuer Plugins fremder Herkunft)

`PLUGIN_KONZEPT.md` Abschnitt 9 nennt die offenen Punkte. Die Trennung auf
Vorgangsebene steht seit dieser Fassung: jedes Plugin laeuft in einem
eigenen Vorgang ohne Zugriff auf Datenbank, Tresor und Objekte der
Anwendung. Offen bleibt die Beschraenkung durch das Betriebssystem - ein
eigenes Benutzerkonto oder ein Job-Objekt.

### 4. Quellenregister validieren

Der erste Online-Lauf hat stattgefunden, und er hat Luecken gezeigt. Der
Bauablauf prueft das Register seitdem mit

```
python tools/quellen_pruefen.py --ziel ergebnis.json
```

Das Werkzeug benutzt **den HTTP-Zugriff der Anwendung selbst** - dasselbe
Nutzerkennzeichen, denselben Zertifikatsspeicher, dieselbe Beachtung von
robots.txt. Ein Abruf mit einem fremden Werkzeug wuerde etwas anderes
messen als der Betrieb; der erste Lauf tat genau das (PowerShell, HEAD
statt GET) und lieferte deshalb Zahlen, die nichts ueber die Anwendung
aussagen.

Das Ergebnis steht seit dem Lauf
https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/34035777317 in
`config/source_registry.json` bei jeder Quelle unter `pruefung`, mit dem
Lauf als Beleg: **9 von 32 Adressen erreichbar**.

Zwei Faelle, die nicht verwechselt werden duerfen:

| Befund | Was es heisst | Betroffen |
|---|---|---|
| `art: adresse_tot` | HTTP 404 - die Adresse zeigt ins Leere und braucht eine neue | `ELSTER_START`, `BZST_USTID`, `BZST_ZM`, `BVERFG_ENTSCHEIDUNGEN`, `BGBL_START`, `DIHK_STEUERN` |
| `art: nicht_erreicht` | gar keine Antwort - die Adresse ist weder bestaetigt noch widerlegt, nur dieser Rechner kam nicht hin | alle 17 Gesetzestexte von `gesetze-im-internet.de` |

**Hier ansetzen:** die sechs toten Adressen brauchen je eine neue. Sie
lassen sich nicht aus dieser Umgebung ermitteln - dort ist der Zugang
gesperrt - sondern von einem Buerorechner aus:

```
PORTABLE_BUCHHALTER_KONSOLE.exe quellen pruefen
PORTABLE_BUCHHALTER_KONSOLE.exe quellen setzen --dokument BGBL_START --url <neue Adresse>
```

Die 17 Gesetzestexte sind ausdruecklich **nicht** auszubessern, solange
nichts gegen sie spricht: der Baurechner nimmt zu diesem Server gar keine
Verbindung auf (Zeitablauf beim Verbindungsaufbau, kein HTTP-Fehler). Das
ist eine Eigenschaft dieses Netzes, keine Aussage ueber die Adresse. Auf
einem Buerorechner zuerst `quellen pruefen` laufen lassen.

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
