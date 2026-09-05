# Testbericht

Stand: 05.09.2026 · Branch `claude/portable-ki-buchhalter-xr1qlj`

## Zusammenfassung

**199 automatische Tests bestanden, 1 uebersprungen.** Ausfuehrungszeit rund
10 Sekunden. Reproduzierbar mit:

```
python -m pytest tests -q
```

| Testdatei | Ergebnis | Gegenstand |
|---|---|---|
| `test_updater_pipeline.py` | 13 bestanden | Wissensupdate gegen einen echten lokalen HTTP-Server |
| `test_controller.py` | 10 bestanden | Anwendungssteuerung von Ende zu Ende |
| `test_portability.py` | 15 bestanden, 1 uebersprungen | Portabilitaet und Robustheit |
| `test_gui_logic.py` | 10 bestanden | Oberflaechenlogik gegen ein Tkinter-Doppel |
| `test_llm_providers.py` | 8 bestanden | Sprachmodellanbindung gegen einen echten lokalen Modelldienst |
| `test_sicherheit_freigaben.py` | 17 bestanden | Tresor, Freigaben, Protokoll, Connectoren, Pfadgrenzen |
| `test_fachliche_faelle.py` | 48 bestanden | 22 fachliche Sachverhalte nach Masterprompt 47 |
| `test_abnahme_kette.py` | 3 bestanden | Die vollstaendige Nutzungskette aus Masterprompt 49 |
| `test_cli.py` | 12 bestanden | Kommandozeile: alle allgemeinen Schalter an allen Unterbefehlen |
| `test_start.py` | 3 bestanden | Startfehler bleiben nicht stumm |
| `test_lizenzierung.py` | 22 bestanden | Lizenzierung und Kopierschutz, alle sieben Faelle aus § 96 |
| `test_kundentrennung.py` | 13 bestanden | Kundentrennung, Datenexport, Loeschung, Sicherungsziel |
| `test_softwareupdate.py` | 11 bestanden | Softwareupdates getrennt vom Wissensupdate |
| `test_produktreife.py` | 14 bestanden | Telemetriefreiheit, Lizenzregister, SBOM, Reifegrad, Schluesselschutz |

Der uebersprungene Test prueft das Verhalten bei schreibgeschuetztem
Verzeichnis. Als `root` sind Dateirechte nicht wirksam einschraenkbar; der
Test laeuft unter einem gewoehnlichen Benutzerkonto mit.

---

## 1. Wissensupdate (8 Tests)

Gegen einen im Test gestarteten echten HTTP-Server mit ETag-Unterstuetzung.

| Test | Geprueft |
|---|---|
| Erstlauf | Abruf, Originalablage, Extraktion, Normalisierung, Metadatendatei, Chunking, Index, Bericht als Datei - jede Datei wird auf der Platte nachgewiesen |
| Inkrementalitaet | Zweiter Lauf liefert 304, es wird nichts neu geladen und nichts neu indexiert |
| Aenderung | Geaenderter Inhalt wird erkannt und neu indexiert, der neue Text ist auffindbar |
| Recherche | Die indexierte Norm wird zur passenden Frage gefunden, mit Prioritaet 1 |
| Offline | Ohne Netz endet der Lauf mit `no_network`, der Bestand bleibt unveraendert |
| Trockenlauf | Es wird nichts geschrieben - weder in die Datenbank noch auf die Platte |
| Ruecknahme | Der vorherige Stand ist exakt wiederhergestellt, der neue Inhalt ist verschwunden |
| Zeitplan | manuell, woechentlich, Faelligkeitsberechnung nach dem letzten Erfolg |

Ein Dokument der Testquellen ist absichtlich nicht erreichbar. Der Lauf endet
deshalb mit `partial` und weist den Fehlschlag einzeln aus - er behauptet
keinen vollen Erfolg.

## 2. Anwendungssteuerung (10 Tests)

| Test | Geprueft |
|---|---|
| Systempruefung | Alle Pruefpunkte, Datenbanken liegen nachweislich auf der Platte, Markerdatei geschrieben |
| Offline-Fachfrage | Lokale Fundstellen werden gefunden, Antwort enthaelt QUELLEN und WISSENSSTAND, Nachricht und Quellenbelege werden gespeichert |
| Halluzinationsschutz | Eine erfundene Fundstellennummer wird aus der Antwort entfernt, die gueltige bleibt, der Nutzer wird informiert |
| Unternehmensgedaechtnis | „Wir verwenden grundsaetzlich SKR03" wird erkannt, gespeichert und ist **nach einem Neustart** wieder da |
| Ortswechsel | Nach dem Kopieren an einen Pfad mit Leerzeichen sind Unternehmenswissen und Fachwissen unveraendert nutzbar; SKR03 landet im Modellkontext |
| Onboarding | Fortschritt wird korrekt gezaehlt |
| Belege | Aufnahme, Ablage auf der Platte, Volltextsuche, Erkennung eines bereits vorhandenen Belegs |
| Sicherung | Dateien und Pruefsummen stimmen mit dem Manifest ueberein |
| Status und Export | Lagebericht stimmt, Profil wird als JSON und lesbares Markdown exportiert |
| Gespraechsexport | Datei enthaelt Frage und Antwort |

## 3. Portabilitaet und Robustheit (12 Tests, 1 uebersprungen)

| Test | Geprueft |
|---|---|
| Schwierige Pfade | Leerzeichen, Umlaute, Klammern, tiefe Verschachtelung - Wurzelerkennung und relative Pfade funktionieren |
| Kein fester Laufwerksbuchstabe | Der gesamte Quellcode wird durchsucht; ein fester Pfad wie `C:\` laesst den Test fehlschlagen |
| Vollstaendiger Ortswechsel | Der Datenbestand wird kopiert, das Original geloescht - alles bleibt nutzbar (entspricht D: nach E: und dem zweiten PC) |
| Fehlendes Modell | Die Anwendung startet, meldet den Notbetrieb, recherchiert weiter und formuliert bewusst keine Fachantwort |
| Geloeschter Index | Wird beim naechsten Start neu aufgebaut, alle Dokumente sind wieder da |
| Beschaedigter Index | Wird von der Integritaetspruefung erkannt und begruendet |
| Trennung der Bestaende | Unternehmenswissen ueberlebt den vollstaendigen Verlust der Fachwissensdatenbank |
| Gleichzeitiger Zugriff | Zwei Instanzen auf demselben Datenbestand sehen die Aenderungen des jeweils anderen |
| Schreibschutz | wird erkannt (uebersprungen, weil als root nicht pruefbar) |

## 4. Oberflaechenlogik (10 Tests)

Gegen ein Tkinter-Doppel, das Widgets, Texte und Rueckrufe nachbildet.

| Test | Geprueft |
|---|---|
| Aufbau | Alle Registerkarten entstehen, Begruessung, Betriebsart und Wissensstand in der Kopfzeile |
| Frage absenden | Antwort erscheint im Chat, Quellenfeld wird gefuellt, beide Nachrichten werden gespeichert |
| Rueckfrage Ja | Es wird gefragt, bevor gespeichert wird; bei Ja steht die Angabe im Gedaechtnis |
| Rueckfrage Nein | Bei Nein wird **nichts** gespeichert |
| Unternehmenswissen | Tabelle, Archivieren, Verlauf bleibt erhalten |
| Belege | Datei auswaehlen, aufnehmen, in der Liste anzeigen |
| Update ohne Netz | Es wird gewarnt, der Lauf meldet `no_network`, lokales Wissen bleibt nutzbar |
| Verbindungsverlust | Die Meldung nennt ausdruecklich den lokalen Wissensstand |
| Einstellungen | Werden nachweislich in `settings.json` geschrieben |
| Startfenster | Systempruefung wird angezeigt und gibt den Start frei |

> **Grenze dieser Tests:** Sie pruefen die Logik hinter der Oberflaeche, nicht
> das echte Tk. Aussehen, Layout und Verhalten des tatsaechlichen
> Fensters sind damit **nicht** geprueft. Siehe `docs/ABNAHME.md`, Punkt B.

## 5. Sprachmodell (8 Tests)

| Test | Geprueft |
|---|---|
| Lokaler Modelldienst | Echte HTTP-Anfrage und -Antwort, Systemnachricht und Frage kommen korrekt an, Tokenzahlen werden uebernommen |
| Serverfehler | HTTP 500 wird zu einer verstaendlichen Meldung, kein Absturz |
| Unerwartete Antwort | Wird erkannt statt falsch ausgewertet |
| Nicht erreichbar | Wird gemeldet, nicht verschwiegen |
| Rueckfall | Faellt das Online-Modell aus, antwortet das lokale weiter - der Ausfall wird dokumentiert |
| Kein Modell | Die Antwort sagt ehrlich, dass nichts erzeugt wurde, und nennt den Grund |
| Fehlende Modelldatei | Wird gemeldet |
| Modellerkennung | GGUF-Dateien und ihre Quantisierung werden erkannt, andere Dateien ignoriert |

> **Grenze:** Es wurde **kein echtes GGUF-Modell** ausgefuehrt. In der
> Entwicklungsumgebung war keine Modellquelle erreichbar. Siehe
> `docs/ABNAHME.md`, Punkt C.

## 6. Sicherheit und Freigaben (13 Tests)

| Test | Geprueft |
|---|---|
| Tresor verschluesselt wirklich | Der Klartext ist in der Datei nachweislich nicht enthalten; AES-256-GCM und scrypt sind in der Huelle vermerkt |
| Falsches Passwort | Verstaendliche Meldung, kein Zugriff |
| Verschlossener Tresor | Gibt nichts heraus, auch nicht beim stillen Zugriff |
| Schwaches Passwort, doppelter Tresor | Werden abgelehnt |
| Passwortwechsel | Inhalt bleibt erhalten |
| Keine Ausfuehrung ohne Freigabe | Der Uebergang zu AUSGEFUEHRT scheitert im Zustand ENTWURF |
| Reihenfolge der Freigabe | ENTWURF, GEPRUEFT, FREIGEGEBEN, AUSGEFUEHRT; ein Rueckweg von AUSGEFUEHRT ist gesperrt |
| Protokoll | Jede Entscheidung mit Person, Zustandswechsel und Begruendung |
| Connectoren nur lesend | Alle Connectoren starten im Modus `read_only` |
| Schreibsperre | Ohne Modus und ohne gueltige Freigabe schlaegt jeder Schreibversuch fehl |
| Nicht angebundene ERP-Systeme | SAP, Wilken und DATEV melden das ehrlich und liefern keine Daten |
| CSV | Liest eine echte Datei mit Semikolon und deutschem Dezimalkomma |
| Vorschau | Schreibt nachweislich nichts |

## 7. Nutzungskette (3 Tests)

Der Test `test_vollstaendige_nutzungskette` durchlaeuft die Kette aus
Masterprompt 49 in einem Stueck:

offline starten · Fachfrage mit Quellen und Wissensstand ·
"Wir verwenden grundsaetzlich SKR03" wird erkannt und gespeichert ·
Freigaberegel ergaenzt · Programm beenden · **kompletter Datenbestand an
einen anderen Ort mit Leerzeichen im Pfad** · dort starten ·
Unternehmenswissen ist vorhanden und fliesst in den Modellkontext ·
Gespraechshistorie ist mitgewandert · online gehen · Wissensupdate mit
Originalablage und Bericht als Datei · offline gehen · **das neu geladene
Schreiben ist offline auffindbar** · erneut starten - alles noch da.

Ersetzt wurden dabei: das Sprachmodell durch einen Testanbieter, die
amtlichen Quellen durch einen echten lokalen HTTP-Server, der zweite
Rechner durch ein anderes Wurzelverzeichnis.

Zwei weitere Tests belegen, dass der Grundbetrieb **ohne jeden Serverdienst**
auskommt und dass der Stand allein von der Platte ablesbar ist.

## 8. Fachliche Testfaelle (48 Tests)

22 Sachverhalte aus `src/profiles/buchhalter/testcases.json`, darunter alle
in Masterprompt 47 geforderten: normale und fehlerhafte Eingangsrechnung,
innergemeinschaftlicher Erwerb und innergemeinschaftliche Lieferung, Reverse
Charge, Kleinunternehmer, Vorsteuer, E-Rechnung, Anlagegut, Abschreibung,
geringwertiges Wirtschaftsgut, Skonto, Gutschrift, Forderungsausfall,
Rechnungsabgrenzung, Rueckstellung, Vertragsstrafe ohne Lieferung, Anzahlung
mit nachtraeglicher Lieferung, abweichender Leistungs- und
Rechnungszeitpunkt, Leistungsort, Aufbewahrung und GoBD,
Jahresabschlussvorbereitung.

Je Fall wird geprueft:

1. Die lokale Recherche findet ueberhaupt Material.
2. Die erwarteten fachlichen Stichworte kommen darin vor.
3. Mindestens eine der erwarteten Normen kommt darin vor - toleranz gegenueber
   Schreibweisen wie `§ 6 Abs. 2 EStG` gegenueber `§ 6 EStG`.
4. Fuer sechs Faelle zusaetzlich: die Antwort enthaelt Quellen und
   Wissensstand.

> **Grenze:** Geprueft ist, dass das **richtige Material gefunden** wird.
> Ob die ausformulierte Antwort fachlich ueberzeugt, haengt vom eingesetzten
> Sprachmodell ab und gehoert zur manuellen Abnahme
> (`docs/ABNAHME.md`, Punkt D).

---

## Pruefung auf einem echten Windows-Rechner

Ablauf https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/33970160321 - **alle 13 Schritte bestanden**:

| Schritt | Ergebnis |
|---|---|
| Tkinter vorhanden | ja |
| Alle Tests auf Windows | bestanden |
| Portablen Ordner bauen | erzeugt |
| Beide Programme existieren wirklich | `PORTABLE_BUCHHALTER.exe` und `PORTABLE_BUCHHALTER_KONSOLE.exe` |
| Systempruefung der gebauten EXE | lief durch, Fachwissen aufgenommen |
| **Offline-Fachfrage gegen die gebaute EXE** | beantwortet, mit Quellenteil |
| **Unternehmenswissen speichern und nach Neustart lesen** | SKR03 war nach einem eigenen Programmlauf wieder da |
| **Laufwerkswechsel ueber `subst`, Pfad mit Leerzeichen** | Unternehmenswissen dort vorhanden, EXE startete |
| Paket bereitgestellt | Artefakt `Portable-Buchhalter-Windows`, 22,8 MB |

Damit sind **gebaut**, **gespeichert** und **verifiziert** fuer die
Windows-Anwendung keine Behauptungen mehr, sondern belegt.

Nicht Teil dieses Ablaufs: das tatsaechliche Oeffnen des Fensters per
Doppelklick, ein echtes Sprachmodell, die echten amtlichen Quellen und ein
physisch zweiter Rechner.

## Kommerzielle Anforderungen (Masterprompt 58 bis 97)

| Bereich | Ergebnis |
|---|---|
| **Kopierschutz** | Kopie des Programmordners auf einen zweiten Datentraeger ist **nicht lizenziert**; das Original bleibt gueltig |
| **Manipulationsschutz** | Jede Aenderung an der Lizenzdatei laesst die Ed25519-Signatur fehlschlagen - geprueft fuer Kunde, Instanzenzahl, Ablaufdatum, Module und Fingerabdruck |
| **Portabilitaet trotz Lizenz** | Dieselbe Datentraegerkennung an drei verschiedenen Orten: Lizenz bleibt gueltig |
| **Offline-Lizenzpruefung** | Ein Test faengt jeden Netzzugriff ab - die Pruefung fasst das Netz nicht an |
| **Keine Sanktion gegen Daten** | Ohne Lizenz bleiben Unternehmensdaten unveraendert; Export und Sicherung bleiben moeglich |
| **Ersatz bei Defekt** | Neuer Datentraeger, neue Instanz-ID, neue signierte Lizenz - getestet |
| **Kundentrennung** | Unternehmenswissen von Kunde A taucht weder bei Kunde B noch im gemeinsamen Fachwissen auf |
| **Telemetrie** | Ein vollstaendiger Arbeitsgang - Start, Fachfrage, Wissen speichern, Export, Sicherung - baut **keine** ausgehende Verbindung auf |
| **Fernzugriff** | Im Programmcode nicht vorhanden |
| **Softwareupdate** | Ein mittendrin scheiterndes Update setzt automatisch zurueck; die Installation bleibt unversehrt |
| **Kundendatenschutz beim Update** | Ein Paket, das an `database/` will, wird abgewiesen |
| **Commercial Ready** | Wird **nicht** automatisch vergeben - ein Test stellt das sicher |

## Waehrend der Tests gefundene und behobene Maengel

Diese Punkte fielen den Tests auf und wurden korrigiert - sie sind hier
aufgefuehrt, weil ein Testbericht ohne Fundstellen wenig wert ist.

| Fund | Ursache | Behebung |
|---|---|---|
| Mitarbeiterprofil wurde nicht gefunden, wenn der Datenbereich getrennt lag | Programm- und Datenwurzel waren gleichgesetzt | Getrennte `program_root`; Vorgabedateien werden in neue Datenbereiche uebernommen |
| Dokumenttitel waren nicht durchsuchbar | Nur Text, Ueberschrift und Fundstelle im Volltextindex | Abschnitte ohne eigene Fundstelle tragen den Dokumenttitel |
| Normen eines Fachmoduls waren nur in dessen kurzer Einleitung auffindbar | Die `Massgeblich`-Zeile bildete einen eigenen, kurzen Abschnitt | Die tragenden Normen werden jedem Abschnitt des Moduls mitgegeben |
| Gute Volltexttreffer wurden von schwachen Vektortreffern verdraengt | Vektorliste zu hoch gewichtet | Gewicht gesenkt; haeufige deutsche Woerter fliessen nicht mehr in die Einbettung ein |
| Der Quellenteil fehlte in manchen Antworten | Die Pruefung fand das Wort „Quellen" im Fliesstext und hielt es fuer eine Ueberschrift | Abschnittserkennung nur noch am Zeilenanfang |
| Zwei Sicherungen in derselben Sekunde ueberschrieben sich | Der Ordnername war nur sekundengenau | Es wird ein freier Name gesucht - betraf sowohl Softwareupdates als auch die Datensicherung, in beiden Faellen waere der Ruecksetzpunkt verloren gewesen |
| Das Beenden war weder mehrfach aufrufbar noch robust | Ein zweiter Aufruf oeffnete das Protokoll erneut, auch bei entferntem Datenbereich | Beenden ist jetzt idempotent und faengt Fehler ab |
| Datei-Connectoren konnten aus ihrem Verzeichnis ausbrechen | Der Dateiname wurde ungeprueft angehaengt | Zielpfad wird aufgeloest und muss unterhalb des konfigurierten Verzeichnisses liegen |
| Kennungen des Quellenregisters konnten aus dem Ablagebereich fuehren | `source_id` und `doc_uid` werden zu Dateinamen | Zeichensatz eingeschraenkt, Pfadangaben abgewiesen |
| Ein Fensterprogramm liefert unter Windows weder Ausgabe noch Rueckgabecode | Die EXE war mit `console=False` gepackt. PowerShell wartet auf ein solches Programm gar nicht erst: der Rueckgabecode blieb leer und die Ausgabe traf erst Sekunden spaeter ein - ein Wettlauf, der mal gut ging und mal nicht | Aus demselben Code entstehen zwei Programme: `PORTABLE_BUCHHALTER.exe` (Fenster, fuer den Doppelklick) und `PORTABLE_BUCHHALTER_KONSOLE.exe` (Konsole, fuer die Kommandozeile) |
| Datei-Connectoren konnten aus ihrem Verzeichnis ausbrechen | Der Dateiname wurde ungeprueft angehaengt, `../geheim.csv` und absolute Pfade funktionierten | Zielpfad wird aufgeloest und muss nachweislich unterhalb des konfigurierten Verzeichnisses liegen |
| Kennungen des Quellenregisters konnten aus dem Ablagebereich fuehren | `source_id` und `doc_uid` werden zu Dateinamen und wurden ungeprueft uebernommen | Erlaubt sind nur Buchstaben, Ziffern, Punkt, Bindestrich und Unterstrich |
| Allgemeine Schalter nur vor dem Unterbefehl erlaubt | `check --quiet` scheiterte mit "unrecognized arguments" - ein Bedienfehler, den jeder Anwender trifft | `--root`, `--offline` und `--quiet` werden an beiden Stellen angenommen |
| Binaerdaten wurden als Fachwissen aufbereitet | Ohne erkanntes Format landete alles beim HTML-Extraktor | Ab 20 Prozent unlesbarer Zeichen wird das Dokument abgewiesen |
| Attributzugriff und `get()` lieferten verschiedene Pfade | Nur `get()` beruecksichtigte die Programmwurzel | Beide Wege gehen denselben Weg; ein Test vergleicht alle Layout-Eintraege |
| Eine abgeschaltete Netzpruefung ueberschrieb eine ausdrueckliche Statusvorgabe | „nicht pruefen" wurde als „kein Netz" behandelt | Ein bereits gesetzter Status bleibt erhalten |
| „Lokales Modell: OK" trotz fehlendem Modell | Der Notbetrieb meldete sich als verfuegbar | Systempruefung meldet HINWEIS und beschreibt den Notbetrieb |
| HTML-Titel wurde falsch erkannt | `<title>` liegt in `<head>`, das uebersprungen wurde | Titel wird vor der Bereichspruefung ausgewertet |
| Deutsche Abkuerzungen zerteilten Saetze | „GmbH & Co. KG" wurde als Satzende gelesen | Abkuerzungsliste in der Satztrennung |
| Firmennamen wurden faelschlich als eigenes Unternehmen erkannt | Jede GmbH-Nennung loeste die Regel aus | Zusaetzliche Bedingung: der Satz muss sich erkennbar auf das eigene Unternehmen beziehen |

---

## Was **nicht** getestet ist

Ehrlich und vollstaendig:

1. ~~**Windows-EXE**~~ - **erledigt**: auf einem echten Windows-Rechner
   gebaut und ausgefuehrt, siehe Abschnitt oben.
2. **Echte Tkinter-Oberflaeche** - das Fenster wurde nie geoeffnet. Auf
   Windows ist Tkinter nachweislich vorhanden, die Oberflaechenlogik ist
   gegen ein Doppel geprueft - der Doppelklick selbst steht aus.
3. **Echtes Sprachmodell** - keine Modellquelle erreichbar.
4. **Echte amtliche Quellen** - die Netzrichtlinie sperrte
   `gesetze-im-internet.de`, `bundesfinanzministerium.de` und die uebrigen.
   Die URLs im Quellenregister tragen deshalb `verified: false`.
5. **Echter zweiter PC und echter Laufwerksbuchstabe** - nur ueber wechselnde
   Wurzelverzeichnisse simuliert (im Windows-Ablauf zusaetzlich ueber
   `subst`).
6. **Fachliche Richtigkeit der formulierten Antworten** - haengt vom Modell
   ab.
7. **Excel-Connector mit echter Datei** - `openpyxl` war nicht installiert;
   der Connector meldet das korrekt.
8. **PDF-Belege mit echtem Inhalt** - die Extraktion ist umgesetzt und der
   Fehlerfall geprueft, ein echtes PDF wurde nicht ausgewertet.

Fuer die Punkte 1 bis 6 fuehrt `docs/ABNAHME.md` Schritt fuer Schritt durch
die Pruefung.
