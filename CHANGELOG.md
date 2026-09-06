# Aenderungsverlauf

Format angelehnt an „Keep a Changelog". Versionierung nach Bedeutung, nicht
nach Zeitplan.

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
