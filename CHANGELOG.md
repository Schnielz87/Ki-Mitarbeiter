# Aenderungsverlauf

Format angelehnt an „Keep a Changelog". Versionierung nach Bedeutung, nicht
nach Zeitplan.

## [0.4.0] - 2026-09-06

Das Sprachmodell laeuft.

### Sprachmodell (E6.13, E6.14)

* Der Modelldienst **liegt bei**: `llama-server` aus llama.cpp (MIT) unter
  `runtime/llama`. Nichts zu installieren, nichts zu uebersetzen. Fuer
  llama-cpp-python gibt es keine fertigen Pakete - der Kunde haette einen
  Compiler gebraucht
* Die Anwendung startet den Dienst selbst, und zwar erst bei der ersten
  Frage; er hoert nur auf 127.0.0.1, oeffnet kein Fenster und wird beim
  Beenden heruntergefahren
* `modell einrichten` fuehrt zum Modell: Hardware ansehen, Vorschlag,
  Bezugsquellen mit Groesse, Lizenz und Pruefstand, Bezug nach
  ausdruecklicher Bestaetigung, Pruefsumme, und zum Schluss eine echte
  Frage an das Modell. Erst dann heisst es "einsatzbereit"
* Modelle in Teildateien werden vollstaendig bezogen; ein halb geladenes
  Modell gilt nicht als einsatzbereit
* Der Katalog behauptet keine geprueften Quellen: der Pruefstand kommt aus
  dem Bauablauf, der jede Adresse tatsaechlich abruft. Jeder Eintrag nennt
  den Lauf, in dem das geschah - nachzulesen statt zu glauben
* Der ausgelieferte Katalog traegt jetzt gemessene Werte: erreichbare
  Adressen, echte Groessen (0,49 / 2,10 / 4,68 / 8,99 GB), die Teildateien
  der beiden grossen Modelle und die Pruefsumme des Probemodells. Ein Test
  laesst keinen ungepruefen Eintrag mehr durch
* Die Modelltabelle der Bedienungsanleitung wird aus diesem Katalog gebaut.
  Vorher standen dort Zahlen, die niemand gemessen hatte - und sie waren
  falsch
* Nachgewiesen auf einem Windows-Rechner mit einem echten GGUF-Modell:
  beziehen, starten, eine Fachfrage beantworten, kein verwaister Vorgang

### Der Weg zum Modell fuehrte aus dem Fenster in die Konsole

Aufgefallen im Betrieb. Ohne Modell stand im Fenster:

> Es konnte keine KI-Antwort erzeugt werden. Auf diesem Rechner ist kein
> Sprachmodell eingerichtet. Einrichten mit:
> `PORTABLE_BUCHHALTER_KONSOLE.exe modell empfehlen`

Sachlich richtig - das Modell liegt bewusst nicht im Paket und wird einmalig
geladen. Als Bedienung unbrauchbar: wer die Anwendung per Doppelklick
oeffnet, hat keine Konsole offen und liest das als "geht nicht", nicht als
"fehlt noch".

* Neue Registerkarte **Sprachmodell**: Lage, erkannte Hardware, Empfehlung,
  die hinterlegten Bezugsquellen mit Groesse, Lizenz und Pruefstand, eine
  Rueckfrage vor dem Laden, ein Fortschrittsbalken - und danach der
  Nachweis, dass das Modell wirklich antwortet
* Die Meldung nennt jetzt den Weg, der zur Bedienung passt. Im Fenster die
  Registerkarte, in der Konsole den Befehl. Das gilt auch fuer den
  Notbetrieb, der erst mitten in einer Anfrage entsteht
* Zwei Fehler in der neuen Registerkarte, die eigene Tests gefunden haben:
  der Ergebnistext wurde sofort von der Katalogliste ueberschrieben, und ein
  fehlgeschlagener Bezug zeigte einen vollen Fortschrittsbalken
* **Vorhandene Modelldatei uebernehmen** - fuer einen zweiten Datentraeger,
  ein Buero mit gesperrtem Download oder eine Leitung, ueber die 4,7 GB
  nicht zweimal gehen. Die Datei wird auf den Datentraeger kopiert, nicht
  verknuepft: ein Verweis waere kleiner, aber der Datentraeger liefe nicht
  mehr fuer sich allein. Braucht kein Internet, geht auch im Modus OFFLINE.
  Auch als `modell uebernehmen --datei ...`
* Kapitel 2 der Bedienungsanleitung erklaert die Registerkarte jetzt Feld
  fuer Feld und sagt ausdruecklich, dass **einmal** geladen wird. Vorher
  stand dort ein Kasten mit drei Klicks und darunter weiter Konsolentext.
  Ein Test vergleicht die genannten Schaltflaechen mit denen im Fenster

### Die eigene Messung war geschoent - korrigiert

Der zweite Durchgang stellte dieselbe Frage wie der erste. Der Modelldienst
hatte damit den **gesamten** Prompt gemerkt und antwortete in 0,1 Sekunden.
Diese Zahl erlebt im Betrieb niemand: dort ist jede Frage neu, und dann ist
nur der unveraenderliche Kopf gemerkt, nicht die Fundstellen.

Sie stand kurz davor, als Alltagszahl berichtet zu werden. Die Messung
stellt jetzt zwei verschiedene Fachfragen; ein Test faellt, sobald wieder
zweimal dieselbe gestellt wird.

### Die Messung misst jetzt, was ein Mensch erlebt

`modell messen` wartet vor dem ersten Durchgang ab, bis die Anwendung
bereit ist - Modell geladen, Kopf des Prompts vorgewaermt. So wartet auch
ein Mensch: er oeffnet das Fenster und tippt erst dann seine Frage. Eine
Messung, die sofort losfragt, misst das Laden mit und damit etwas, das im
Betrieb nicht vorkommt.

### Gemessen: 0,1 Sekunden bis zum ersten Wort

Auf einem echten Windows-Rechner, Probemodell, nur CPU, mit `modell messen`:

| Durchgang | bis zum ersten Wort |
|---|---|
| erster (mit Laden des Modells) | 38 bis 71 s |
| **jeder weitere** | **0,1 s** |

Der Unterschied ist der gemerkte Kopf des Prompts: der Modelldienst behaelt
den verarbeiteten Anfang und muss ihn nicht erneut durchrechnen. Danach
laeuft die Antwort sichtbar weiter - man liest mit, statt zu warten.

* **Der Kopf wird beim Start einmal vorab geschickt** (Vorwaermen). Damit
  gilt die 0,1 Sekunde auch fuer die erste Frage, nicht erst fuer die
  zweite. Es kostet nur die Zeit, in der der Benutzer ohnehin das Fenster
  oeffnet
* **Beenden waehrend des Vorladens laesst keinen Dienst mehr zurueck.** Der
  Vorladefaden prueft vor jedem Schritt, ob die Anwendung noch laeuft, und
  das Beenden wartet auf ihn. Sonst waere ein Modelldienst erst nach dem
  Schliessen fertig hochgekommen - und niemand haette ihn je abgeschaltet
* Das Paket enthaelt beide Fassungen des Modelldienstes: 44,6 MB fuer CPU,
  97,6 MB fuer Vulkan

### Der Prompt selbst - der groesste verbliebene Posten

Die Messung im Bauablauf hat gezeigt, wo die Zeit wirklich hingeht: die
Anwendung selbst braucht 0,17 Sekunden, die Modellprobe eine Sekunde - eine
Fachfrage aber 70 bis 105. Der Unterschied ist der Prompt.

* **Der Systemtext ist von rund 1030 auf gut 500 Token gekuerzt** - jede der
  acht unumstoesslichen Regeln bleibt, nur kuerzer gesagt. Er geht bei
  **jeder** Frage vollstaendig durch das Modell; ein Test schlaegt an, wenn
  eine Regel verschwindet oder der Text wieder waechst
* **Das Antwortschema geht nur noch an Fachfragen.** Bei einer Begruessung
  wurde es mitgeschickt und in derselben Nachricht wieder ausser Kraft
  gesetzt ("verwende kein Fachschema") - rund 330 Token, die das Modell
  verarbeiten musste, um sie zu verwerfen
* Damit sinkt der feste Teil des Prompts von 1257 auf 1062 Token bei
  Fachfragen und auf 690 bei kurzen Anfragen
* **Neu: `modell messen`.** Stellt dieselbe Fachfrage zweimal im selben
  Vorgang und weist beide Zeiten getrennt aus. Der zweite Durchgang ist der
  Alltag: Dienst laeuft, Kopf des Prompts ist bekannt
* Die Messung im Bauablauf mass vorher die Laufzeit des ganzen
  Programmaufrufs - jeder Aufruf startet den Modelldienst neu, das ergab
  unbrauchbare 70 bis 105 Sekunden. Jetzt misst sie mit `modell messen`

### Wartezeit: der zweite Angriff, diesmal an der Wurzel

"Eine Antwort dauert immer noch viel zu lange." Zu Recht - der erste Anlauf
hat nur das falsch gewaehlte Modell behoben. Also gemessen, woraus die
Wartezeit tatsaechlich besteht. Ergebnis am echten Aufbau: **2712 Token
Kontext** gingen bei jeder Frage ins Modell, und **1024 Token** waren als
Antwort erlaubt. Beides ist eine Einstellung, keine Naturkonstante - und
beides zusammen erklaert Minuten.

* **Antworttempo** als ein Regler statt vier: Antwortlaenge, Kontextgroesse,
  Zahl der Fundstellen und Verlaufstiefe abgestimmt in drei Stufen
  (schnell / ausgewogen / ausfuehrlich). Vorgabe ist "ausgewogen" - 600
  statt 1024 Ausgabetoken und 1600 statt 3200 Kontexttoken
* **Der Modelldienst wird beim Start vorgeladen.** Das Laden mehrerer
  Gigabyte stand bisher voll in der Wartezeit der ersten Frage. Jetzt
  laeuft es im Hintergrund, waehrend der Benutzer sich zurechtfindet
* **Die Grafikfassung liegt bei.** Das Paket enthaelt den Modelldienst
  zweimal: als CPU-Fassung und als Vulkan-Fassung, die die Grafikkarte
  nutzt (NVIDIA, AMD, Intel). Die Anwendung waehlt beim Start selbst und
  faellt still auf die CPU zurueck, wenn die Grafikfassung nicht hochkommt
* **Schnellere Schalter fuer den Dienst**: Flash Attention, ein halbierter
  Kontextspeicher und alle Kerne fuer die Kontextverarbeitung. Kennt eine
  Fassung von llama.cpp einen davon nicht, startet die Anwendung
  automatisch ohne sie - lieber langsamer als gar nicht
* **Zwei Zahlen statt einer**: die Anwendung misst jetzt getrennt die Zeit
  bis zum ersten Wort (das ist die erlebte Wartezeit) und die
  Schreibgeschwindigkeit danach
* Neuer Befehl `einstellungen setzen`, und der Bauablauf misst damit die
  Wartezeit je Tempostufe auf einem echten Rechner mit echtem Modell

Zwei weitere Fehler fand der Bauablauf, nicht der Test:

* **Vorladen und erste Frage liefen in einen Wettlauf.** Wer fragte,
  waehrend der Dienst noch startete, zog mit Port 0 los und bekam "kein
  Sprachmodell eingerichtet" - obwohl eines dalag. Behoben; zwei Tests
  bilden den Fall mit zwei Faeden nach
* **"-fa" verlangt in der vorliegenden llama.cpp-Fassung einen Wert.** Der
  blosse Schalter erzeugte eine Hilfeseite statt eines Dienstes. Der
  eingebaute Rueckfall hat genau das aufgefangen und die Ursache ins
  Protokoll geschrieben - jetzt wird "-fa on" zuerst versucht

Zwei Fehler, die dabei auffielen:

* **Das Antworttempo wirkte erst nach einem Neustart.** Kontextgroesse und
  Fundstellenzahl werden beim Aufbau der Recherche festgelegt; wer
  umstellte, bemerkte keine Aenderung und haette die Einstellung fuer
  wirkungslos gehalten. Gefunden, weil ein Test denselben Weg ging wie die
  Oberflaeche
* Die gemessene Geschwindigkeit konnte absurde Werte annehmen, wenn die
  eigene Wanduhr und die Zeitmessung des Anbieters auseinanderliefen

### Geschwindigkeit: 200 Sekunden je Antwort

Aus dem Betrieb gemeldet: 0,3 Token je Sekunde, rund 200 Sekunden fuer eine
Antwort. Ursache war nicht das Modell, sondern das Schweigen der Anwendung.
Auf einem Rechner, dem sie selbst STANDARD empfiehlt, liess sie das
HIGH-Modell einrichten - 8,99 GB Gewichte. Der Rechner lagert dann auf die
Festplatte aus, und jedes Token wartet darauf.

Die Anwendung hat dazu dreimal geschwiegen, alle drei behoben:

* Sie laedt kein Modell mehr wortlos, das nicht passt. Die Auswahlliste
  kennzeichnet jeden Eintrag mit "KNAPP" oder "ZU GROSS FUER DIESEN
  RECHNER", und die Rueckfrage vor dem Laden sagt es noch einmal, mit Zahl
  und Grund
* Die Auswahl zeigte "standard", waehrend das 14B-Modell lief - sie setzte
  sich bei jeder Aktualisierung auf die Empfehlung zurueck und widersprach
  damit der Zeile darueber. Jetzt zeigt sie, was installiert ist, und
  ueberschreibt eine getroffene Wahl nie
* "0.3 Token je Sekunde" stand ohne Einordnung da. Jetzt steht dabei, ob
  das normal ist, woran es liegt und was hilft

Die Einstufung ist an der gemeldeten Messung ausgerichtet, nicht an einer
Faustformel: was dort 0,3 Token je Sekunde ergab, heisst hier "zu gross".

* Neu in "Einstellungen und Status": Grafikschichten, Rechenkerne und
  Kontextgroesse. Sie wirken sofort - der Modelldienst wird beim Speichern
  neu aufgebaut, statt bis zum naechsten Programmstart wirkungslos zu sein
* Der mitgelieferte Modelldienst rechnet nur auf der CPU. Wer eine
  GPU-Fassung von llama.cpp nach runtime\llama legt, kann die Grafikkarte
  nutzen; die Anleitung beschreibt das Schritt fuer Schritt
* Neues Kapitel in der Bedienungsanleitung: "Wie schnell ist das? Und warum
  nicht so schnell wie ChatGPT?" - mit der ehrlichen Antwort, dass ein
  Buerorechner kein Rechenzentrum ist, und mit dem, was auf ihm hilft

### Quellenpruefung

* `quellen pruefen` fragte mit HEAD, der Wissensabgleich fragt mit GET.
  Damit mass der Befehl etwas anderes als den Betrieb und konnte eine
  laufende Quelle als kaputt melden. Beide fragen jetzt gleich
* Neu: `tools/quellen_pruefen.py`. Es prueft das Quellenregister mit dem
  HTTP-Zugriff der Anwendung selbst, nennt zu jedem Ausfall den Grund und
  traegt das Ergebnis auf Wunsch ins Register ein (`--uebernehmen`).
  `verified` gilt fuer eine Quelle nur, wenn **jedes** ihrer Dokumente
  erreichbar war
* Der Windows-Bauablauf benutzt dieses Werkzeug statt eines
  PowerShell-Schnipsels mit HEAD-Anfragen. Der erste Online-Lauf hatte so
  23 Ausfaelle ohne brauchbaren Grund gemeldet
* Der Pruefstand einer Quelle geht beim Speichern des Registers nicht mehr
  verloren
* **robots.txt konnte den Wissensabgleich endlos anhalten.**
  `RobotFileParser.read()` ruft `urlopen` ohne Zeitgrenze auf. Ein Server,
  der die Verbindung annimmt und dann schweigt, haette den Abgleich
  angehalten - ohne Fehler, ohne Meldung, noch vor dem ersten Dokument.
  Jetzt mit Zeitgrenze und Groessengrenze; vier neue Tests, davon einer
  gegen einen absichtlich schweigenden Server
* Das Register traegt den Befund des Laufs 34035777317: 9 von 32 Adressen
  erreichbar. Sechs antworten mit 404 (`art: adresse_tot`), zu
  gesetze-im-internet.de kam vom Baurechner gar keine Antwort
  (`art: nicht_erreicht`) - das ist keine Aussage ueber diese Adressen,
  und sie bleiben deshalb unveraendert

### Plugins (E5.108)

* Jedes Plugin laeuft in einem **eigenen Vorgang**, ohne Datenbank, ohne
  Tresor, ohne Objekte der Anwendung. Es kann nur fragen; entschieden wird
  im Hauptvorgang
* Angemeldete Faehigkeiten und Ausgabeformate werden als Stellvertreter
  gefuehrt
* Offen bleibt die Beschraenkung durch das Betriebssystem

### Wissenssynchronisierung (E2.20)

* Intervalle je Quellenart: Gesetze, Rechtsprechung und
  Verwaltungsanweisungen woechentlich, allgemeine Behoerdeninformationen
  und Fachmodule monatlich - aenderbar an der Quelle, je Art oder als
  Vorgabe, ohne Programmaenderung
* Nur die Automatik richtet sich danach; von Hand wird alles geprueft

### Berichtigt

* `modell empfehlen` stuerzte ab - ausgerechnet der Befehl, auf den die
  Anleitung fuer die Einrichtung verwies
* "Bereit: ja" stand da, obwohl kein Modell vorhanden war
* `kunde anlegen` und `kunde loeschen` brachen mit einem Fehler ab
* Vier Ausweichzweige der Oberflaeche haetten selbst einen Fehler ausgeloest
* Die Versionsauskunft nannte einen anderen Produktnamen als das Fenster

### Unterlagen

* Bedienungsanleitung: neues Kapitel 2 zum Sprachmodell, jetzt 19 Kapitel
* `docs/MODELL_EINRICHTEN.md` neu geschrieben
* Abnahme um die Punkte K und L erweitert
* Lizenzregister: llama.cpp wird mitgeliefert, MIT-Hinweis liegt bei

## [0.3.0] - 2026-09-06

Umsetzung der nachgereichten Erweiterungen E1 bis E6 (Masterprompt Teil 4).

### Antwortqualitaet (E6)

* Jede Nachricht wird zuerst eingestuft: Konversation, kurze Wissensfrage,
  Fachfrage oder geschilderter Einzelfall. Danach richtet sich, ob
  recherchiert wird und wie ausfuehrlich geantwortet wird - auf "Guten
  Morgen" folgt keine Trefferliste aus dem Umsatzsteuerrecht
* Die gefundenen Fundstellen erreichen nachweislich das Modell; ein
  Testdoppel zeichnet auf, was es tatsaechlich bekommen hat
* Antwort und Quellen sind getrennt. Rohe Treffer erscheinen nur noch auf
  ausdruecklichen Abruf (Befehl `recherche`)
* Markdown wird dargestellt statt roh angezeigt - in der Oberflaeche mit
  Stilen, in der Konsole ohne Auszeichnungszeichen
* Warnung, wenn zu einer Fachaussage nur Sekundaerquellen vorliegen
* Keine Modellpfade, Bewertungen oder internen Kennungen mehr in der Antwort
* Antwort erscheint waehrend der Erzeugung Stueck fuer Stueck; ein
  abgerissener Ereignisstrom gilt als Ausfall und nicht als fertige Antwort
* "Generierung stoppen" bricht ab, ohne einen halben Satz stehenzulassen
* Gespraechsdarstellung: BENUTZER und PORTIVA - <Profil> als Sprecher,
  Quellen und Wissensstand ruhiger darunter
* Modellrouting nach Betriebsart: OFFLINE ausschliesslich lokal, ONLINE darf
  ein freigegebenes Online-Modell bevorzugen

### Dateiausgabe (E4)

* Acht Formate: XLSX, CSV, DOCX, PPTX, PDF, TXT, Markdown, JSON - erzeugt
  mit der Standardbibliothek, ohne installiertes Office und ohne Internet
* Artefakt-Engine mit Dateiname, Ablage, Versionierung, Metadaten,
  Ueberschreibschutz und Fehlerbehandlung
* Erzeugte Dateien liegen im Kundenbereich (`workspace/artefakte`)
* Neue Formate koennen ueber Dateihandler ergaenzt werden

### Plugins (E5)

* Paketformat `.kimplug` mit Manifest, Pruefsummen aller Dateien und
  Ed25519-Signatur des Herausgebers
* Zwoelf einzeln zu erteilende Berechtigungen; ein Plugin erhaelt nur einen
  vermittelten Kontext, nicht die Anwendung
* Installieren erst nach Anzeige der Berechtigungen und Bestaetigung;
  Aktivieren ist ein zweiter Schritt
* Plugindaten liegen im Kundenbereich; ein fehlerhaftes Plugin schaltet sich
  ab, ohne den Start zu verhindern
* Beispielplugin `examples/plugin_html`
* **Nicht** enthalten: Trennung auf Prozessebene, Katalog,
  Plugin-Lizenzierung - siehe `PLUGIN_KONZEPT.md`

### Marke und Betrieb (E1, E2)

* PORTIVA als feste Marke, Profilname dynamisch: Logo, Fenstersymbol,
  Taskleiste, EXE-Symbol, Titelzeile
* Betriebsart HYBRID, OFFLINE, ONLINE frei waehlbar und dauerhaft;
  Betriebsart und Internetstatus sind streng getrennt
* Wissenssynchronisierung mit Zeitplan, Faelligkeitsanzeige und Ruecknahme

### Unterlagen

* Masterprompt um Teil 4 (E1 bis E6) ergaenzt - der Auftrag ist ohne den
  Chat vollstaendig
* Anforderungsnachweis um alle Abschnitte der Erweiterungen ergaenzt,
  einschliesslich der nicht erfuellten
* Bedienungsanleitung auf 18 Kapitel erweitert
* `PLUGIN_KONZEPT.md` neu

## [0.2.0] - 2026-09-05

Erweiterung um die kommerzielle Produktperspektive und die Lizenzierung
(Masterprompt 58 bis 97).

### Lizenzierung und Kopierschutz

* Ed25519-signierte Lizenz, offline pruefbar, gebunden an den **Datentraeger**
  statt an den PC - die SSD laeuft weiter an jedem Rechner, eine Kopie auf
  einen zweiten Datentraeger ist nicht lizenziert
* Privater Signaturschluessel niemals im Produkt; ohne Pruefschluessel meldet
  die Anwendung ehrlich "nicht pruefbar"
* Ohne Lizenz wird nur die produktive Nutzung gesperrt - Daten bleiben
  unveraendert, Export und Sicherung moeglich
* Ersatzprozess bei Defekt; Werkzeug zur Lizenzausstellung fuer den Hersteller

### Kundentrennung und Datenkontrolle

* Getrennte Datenbereiche unter `customers/<kennung>/`
* Vollstaendiger Datenexport, Loeschen einzelner Gespraeche und Belege,
  kontrolliertes Loeschen einer ganzen Kundeninstanz mit Sicherung

### Produktunterlagen

* Lizenzregister und SBOM aus der tatsaechlichen Installation
* Release-Dossier mit Testbericht, bekannten Einschraenkungen und Pruefsummen
* Commercial-Readiness-Gate - wird nie automatisch vergeben

### Betrieb beim Kunden

* Softwareupdates getrennt vom Wissensupdate, signierbar, ruecksetzbar; ein
  fehlerhaftes Update setzt automatisch zurueck
* Zweites Sicherungsziel ausserhalb des Datentraegers
* Gefuehrte Einrichtung in sieben Schritten
* Getrennte Versionsangaben fuer Software, Fachmodul, Wissen, Modell, Profil

### Belegt statt behauptet

* Kein Fernzugriff und keine Telemetrie - durch Tests nachgewiesen
* Vier Pfadausbrueche gefunden und geschlossen
* Der Auftrag selbst liegt jetzt auf dem Datentraeger (`MASTERPROMPT.md`),
  mit Anforderungsnachweis je Abschnitt

### Tests

219 bestanden, 1 uebersprungen.

## [0.1.0] - 2026-09-04

Erste vollstaendige Fassung des portablen KI-Mitarbeiters mit der
Referenzimplementierung **KI-Buchhalter**.

### Portabler Core (wiederverwendbar fuer weitere Mitarbeiter)

* **Pfade** - Wurzelerkennung ohne festen Laufwerksbuchstaben ueber
  Markerdatei, Umgebungsvariable und Programmverzeichnis; Trennung von
  Programm- und Datenwurzel; Schreibrechtspruefung; Pfade mit Leerzeichen und
  Umlauten
* **Konfiguration** - Vorgabewerte, `settings.json` und
  `KIM_*`-Umgebungsvariablen; gespeichert werden nur Abweichungen
* **Datenhaltung** - SQLite mit Migrationen, WAL, Sicherung im laufenden
  Betrieb, Integritaetspruefung; getrennte Datenbanken fuer Fachwissen und
  Unternehmenswissen
* **Unternehmensgedaechtnis** - versioniert, mit Historie, Archivierung,
  Wiederherstellung, Volltextsuche und Export; regelbasierte Erkennung
  dauerhaft relevanter Angaben aus deutschen Formulierungen; bei Unsicherheit
  wird gefragt
* **Fachwissen** - Extraktion aus HTML, XML (einschliesslich des Normen-XML
  von „Gesetze im Internet"), ZIP, PDF und Text; Normalisierung;
  zitierfaehiges Chunking; Dokumentenspeicher mit Metadaten und Versionen
* **Recherche** - hybride Suche aus BM25 und Vektoren mit Reciprocal Rank
  Fusion, Quellenhierarchie, Zeitbezug, deutscher Wortstamm-Erweiterung;
  modellfreie Hashing-Einbettung als immer verfuegbarer Rueckfall
* **Sprachmodell** - Anbieterabstraktion fuer lokales GGUF, lokalen oder
  entfernten OpenAI-kompatiblen Dienst und einen Testanbieter; ehrlicher
  Notbetrieb ohne Modell; Hardwareerkennung und Modellprofile
* **Antwortlogik** - Kontextaufbau mit getrenntem Unternehmens- und
  Fachwissen, Tokenbudget, erzwungenem Quellen-, Wissensstands- und
  Freigabeteil; erfundene Fundstellennummern werden erkannt und entfernt
* **Aktualisierung** - Quellenregister, inkrementeller Abruf ueber
  ETag, Last-Modified und SHA-256, Originalablage, Updatebericht,
  Ruecknahme, Zeitplan
* **Sicherheit** - Geheimnistresor mit scrypt und AES-256-GCM
* **Nachweis** - Protokoll und Freigabe-Zustandsautomat; ohne FREIGEGEBEN ist
  eine Ausfuehrung technisch gesperrt
* **Anbindung** - Connector-Rahmen mit Standard READ ONLY; CSV, Excel und
  generisches REST nutzbar; SAP, Wilken und DATEV melden ehrlich, dass sie
  nicht angebunden sind
* **Checkpoints** - Projektstaende im Repository und ausserhalb, mit
  Pruefsummen und anschliessender Verifikation

### Mitarbeiter: Buchhalter

* Fach-Masterprompt mit unumstoesslichen Regeln, Vorgehen A bis N und
  Antwortschema
* Profildefinition mit 12 Faehigkeiten, 7 Grenzen, Freigabepflichten und 21
  Onboarding-Schluesseln
* 13 mitgelieferte Fachmodule - damit ist der Mitarbeiter ab dem ersten Start
  ohne Internet fachlich arbeitsfaehig
* Quellenregister Q01 bis Q12 nach der Quellenhierarchie, mit Lizenzangaben;
  das Unternehmensregister ist bewusst deaktiviert
* 22 fachliche Testfaelle

### Anwendung und Oberflaeche

* Kopfloser `AppController` - GUI, Kommandozeile und Tests nutzen dieselbe
  Logik
* Tkinter-Oberflaeche: Systempruefung, Chat mit Quellenanzeige,
  Unternehmenswissen mit Verlauf, Belege, Wissensupdate mit Fortschritt und
  Ruecknahme, Einstellungen, Status
* Vollwertige Kommandozeile fuer Automatisierung und Fehlersuche
* Automatischer Wechsel zwischen OFFLINE und HYBRID ohne Neustart

### Packaging

* PyInstaller-Beschreibung (onedir, damit sich nichts in das Temp-Verzeichnis
  des Gastrechners entpackt)
* Windows-Build-Skript, das den fertigen portablen Ordner herstellt und die
  gebaute EXE einem Rauchtest unterzieht
* GitHub-Actions-Ablauf, der die EXE auf einem echten Windows-Rechner baut
  und prueft, einschliesslich Laufwerkswechsel ueber `subst`
* Werkzeug zur Modelleinrichtung mit Hardwarepruefung, Download mit
  Pruefsumme und echtem Antworttest

### Tests

109 bestanden, 1 uebersprungen. Einzelheiten in `TESTBERICHT.md`.

### Auf einem echten Windows-Rechner geprueft

Der Ablauf https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/33970160321 hat alle
13 Schritte bestanden: beide Programme gebaut, Systempruefung der EXE,
Offline-Fachfrage mit Quellenteil, Unternehmenswissen ueber einen Neustart
hinweg, Laufwerkswechsel ueber `subst` in einen Pfad mit Leerzeichen. Das
fertige Paket liegt dort als Artefakt bereit.

### Bekannte Grenzen dieser Fassung
* Das Fenster wurde nie geoeffnet. Auf Windows ist Tkinter nachweislich
  vorhanden und die Oberflaechenlogik ist gegen ein Doppel geprueft - der
  Doppelklick selbst steht aus.
* Es wurde kein echtes Sprachmodell ausgefuehrt - keine Modellquelle
  erreichbar.
* Die URLs des Quellenregisters wurden nicht live geprueft - die
  Netzrichtlinie sperrte die amtlichen Hosts. Alle Eintraege tragen
  `verified: false`.

`docs/ABNAHME.md` fuehrt durch die Pruefung dieser Punkte.

### Geplant

* Auswahl mehrerer Mitarbeiter beim Start (`PORTABLE_UNTERNEHMENS_KI.exe`)
* Optionale zentrale Synchronisation als Erweiterung, nie als Ersatz des
  Offline-Kerns
* DATEV-Format als erster echter ERP-Weg
* Mitgelieferte Laufzeit, damit auch der Startweg ohne EXE kein installiertes
  Python braucht
