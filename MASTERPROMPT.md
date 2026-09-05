# Masterprompt - Portabler KI-Mitarbeiter

**Verbindlicher Gesamtauftrag** · Referenzimplementierung: Portabler
KI-Buchhalter · Fassung 3.0 zuzueglich der Erweiterung um die Abschnitte 58
bis 97 (kommerzielle Produktperspektive und Lizenzierung).

---

## Hinweis zur Fassung dieses Dokuments

Der Auftrag wurde urspruenglich im Gespraech uebergeben. Damit der
Projektstand nach Masterprompt 45 **ohne den Chat** wiederherstellbar ist,
liegt er hier auf dem Datentraeger.

* **Abschnitte 58 bis 97** sind woertlich so wiedergegeben, wie sie uebergeben
  wurden.
* **Abschnitte 1 bis 57** sind inhaltlich vollstaendig wiedergegeben; einzelne
  Formulierungen koennen vom Original abweichen. Bei Zweifeln gilt der
  Originalauftrag des Auftraggebers.

Welche Anforderung wo umgesetzt und wo geprueft ist, steht in
`ANFORDERUNGSNACHWEIS.md`.

---

# TEIL 1 - GRUNDAUFTRAG (Abschnitte 1 bis 57)

## 1. Gesamtauftrag

Vollstaendige Konzeption, Entwicklung, Umsetzung, Pruefung, Dokumentation und
Fertigstellung eines portablen KI-Mitarbeiters. Erste
Referenzimplementierung: **Portabler KI-Buchhalter**.

Ausdruecklich **nicht** gewollt: blosser Chatbot, blosser Masterprompt,
blosses Python-Projekt, Quellcodesammlung, Dokumentensammlung, technisches
Framework, Kommandozeilenanwendung, Wissensdatenbank ohne Oberflaeche,
Konzept, Prototyp ohne nutzbare Oberflaeche.

Das Endprodukt muss eine **tatsaechlich nutzbare portable KI-Anwendung** sein.
Der Auftraggeber ist kein Softwareentwickler; der Nutzer braucht im
Normalbetrieb keine Python-, Terminal- oder Git-Befehle, keinen Compiler,
keine Entwicklungsumgebung und keine manuelle Paketinstallation.

**Zielszenario:** Externe SSD an einen Windows-PC anschliessen, Projektordner
oeffnen, `PORTABLE_BUCHHALTER.exe` per Doppelklick starten, grafische
Oberflaeche oeffnet sich, sofort nutzbar. Ohne Internet mit lokalem Modell,
lokalem Fachwissen, lokalem Unternehmenswissen und lokalen Daten. Mit
Internet erweitert um aktuelle Quellen, Wissensupdates, APIs und spaeter
ERP-Schnittstellen. Es handelt sich um **ein** hybrides System.

## 2. Uebergeordnetes Produktziel

Der Buchhalter ist die erste Referenzimplementierung einer wiederverwendbaren
Plattform portabler KI-Mitarbeiter (Controller, Geschaeftsfuehrer-Assistent,
Rechtsabteilung, Einkauf, Verkauf, Personal, Immobilien, Projektmanagement,
weitere).

Zielarchitektur: PORTABLE-KI-CORE + MITARBEITERPROFIL + MASTERPROMPT +
FACHWISSEN + UNTERNEHMENSGEDAECHTNIS + LOKALE WISSENSDATENBANK + LOKALES
KI-MODELL + OPTIONALE ONLINE-FUNKTIONEN + OPTIONALE CONNECTOREN.

Ein neuer Mitarbeiter soll nicht neu programmiert werden muessen; der Core
wird wiederverwendet, ausgetauscht werden Rolle, Fachprompt, Wissensmodule,
Quellenregister, Fachregeln, Unternehmenskonfiguration, Rechte, Connectoren
und bei Bedarf Oberflaechenmodule.

## 3. Entwicklungspfade

Primaeres Entwicklungsverzeichnis `D:\Ki-Agent\Portable-Buchhalter`,
Sicherungsbereich `D:\Ki-Agent\checkpoints`. Die fertige Anwendung darf
**nicht** an einen festen Laufwerksbuchstaben gebunden sein; sie muss ihren
eigenen Startpfad erkennen (D:, E:, F: gleichwertig). Final bevorzugt relative
Pfade: `./models`, `./knowledge`, `./resources`, `./company`, `./database`,
`./data`, `./conversations`, `./workspace`, `./config`, `./logs`, `./runtime`,
`./connectors`, `./updates`, `./backups`.

## 4. Echte Portabilitaet

Die SSD muss an einem anderen geeigneten Windows-PC weiterverwendbar sein.
Der Ziel-PC stellt nur CPU, RAM, gegebenenfalls GPU, Betriebssystem und bei
Bedarf Netzwerk. Alle persistenten Daten bleiben auf der SSD: Anwendung,
Modell, Runtime, Fachwissen, Suchindex, Unternehmenswissen, Dokumente,
Gespraechsverlaeufe, Einstellungen, Arbeitsstaende, Updates, Logs,
Sicherungen.

## 5. Kein Server als Grundvoraussetzung

Ohne Server funktionieren muessen: Anwendung starten, Modell ausfuehren,
lokale Wissenssuche, Unternehmenswissen speichern, Gespraechsverlaeufe,
Arbeitsstaende, Dokumente, Einstellungen, Checkpoints, lokale Datenbank. Die
SSD ist der massgebliche Speicher. Eingebettete Datenbank (SQLite oder
gleichwertig) zulaessig; ein Datenbankserver darf nicht erforderlich sein.

## 6. Optionaler Server in spaeterer Ausbaustufe

Eine spaetere zentrale Synchronisation darf vorgesehen werden (gemeinsame
Daten, zentrale Backups, gemeinsame Wissensbasis, Benutzer- und
Rechteverwaltung, Synchronisation, Updateverteilung, Auditierung,
Teamarbeit). Sie ist **nicht** Bestandteil der Grundfunktion und darf den
Offlinebetrieb niemals ersetzen.

## 7. Ein einziger hybrider KI-Mitarbeiter

Offline- und Onlinebetrieb duerfen **nicht** zwei getrennte Programme sein.
Der Benutzer arbeitet immer mit derselben Anwendung, Oberflaeche, demselben
Profil, derselben Wissensdatenbank, demselben Unternehmensgedaechtnis,
derselben Historie, denselben Einstellungen und Dokumenten. Der Offline-Core
ist die Grundlage, Onlinefunktionen erweitern ihn.

## 8. Offline-Betrieb

Ohne Internet muss mindestens funktionieren: Start, grafische Oberflaeche,
lokales Sprachmodell, Fachwissensdatenbank, Unternehmensgedaechtnis,
Volltextsuche, semantische Suche, RAG, lokale Gesetze,
Verwaltungsanweisungen, Rechtsprechung, Fachunterlagen,
Unternehmensinformationen, Dokumentenanalyse, Berechnungen, Fachfragen,
Buchungsvorschlaege, Rechnungspruefung, Quellenanzeige, Gespraechshistorie,
Arbeitsstaende, Protokolle. Fehlendes Internet darf nicht zum Ausfall
fuehren. Der lokale Wissensstand ist anzuzeigen.

## 9. Online-Betrieb

Mit Internet bleibt dieselbe Anwendung aktiv; zusaetzlich duerfen freigegebene
Onlinefunktionen genutzt werden: aktuelle Rechtsquellen, neue Gesetze,
BMF-Schreiben, Rechtsprechung, Behoerdeninformationen, Wissensaktualisierung,
APIs, ERP-Systeme (SAP, Wilken, DATEV), optionale Online-KI. Die lokale
Wissensbasis bleibt Bestandteil.

## 10. Automatischer Offline-/Online-Wechsel

Beim Start pruefen; mit Verbindung HYBRIDMODUS, ohne OFFLINEMODUS. Faellt das
Netz waehrend einer Sitzung aus, soll ohne Neustart umgeschaltet werden, mit
Meldung wie: „Internetverbindung verloren. Der portable Buchhalter arbeitet
mit dem lokalen Wissensstand vom 03.09.2026 weiter." Bei Wiederkehr koennen
Onlinefunktionen wieder aktiviert werden.

## 11. Online erworbenes Wissen offline verfuegbar machen

Soweit technisch, rechtlich, lizenzrechtlich und fachlich moeglich:
Online-Quelle → Abruf → Original speichern → Inhalt extrahieren →
normalisieren → Metadaten erzeugen → indexieren → lokale Wissensdatenbank
aktualisieren → offline verfuegbar.

## 12. Funktionsparitaet

Groesstmoegliche Gleichheit zwischen Offline- und Onlinebetrieb. Offline
moeglich: Fachfragen, Buchungsvorschlaege, Rechnungspruefung,
Gesetzes- und Urteilsrecherche, Dokumentenanalyse, Berechnungen,
Unternehmenswissen, Historie, RAG, Quellenanzeige. Nur online: Live-ERP,
Onlinebanking, Webrecherche, externe APIs, Cloud-KI.

## 13. Persistentes Unternehmensgedaechtnis

Dauerhaftes lokales Gedaechtnis. Unternehmensbezogene Informationen duerfen
**nicht** nur im Chat, im Modellkontext, im RAM oder im Arbeitsspeicher
existieren, sondern muessen strukturiert auf der SSD liegen: Name,
Rechtsform, Branche, Standorte, Ansprechpartner, Mitarbeiter,
Zustaendigkeiten, Organigramm, Buchhaltungsregeln, Kontenrahmen,
Steuerschluessel, Kostenstellen, Prozesse, Arbeitsanweisungen,
Freigaberegeln, ERP-Konfiguration, Lieferanten, Kunden, wiederkehrende
Sachverhalte, Sonderfaelle, Entscheidungen, Vorlagen, Dokumente,
Benutzerpraeferenzen, Fachregeln, Besonderheiten, Arbeitsweisen.

## 14. Trennung von Fachwissen und Unternehmenswissen

Allgemeines Fachwissen und unternehmensspezifisches Wissen sind getrennt zu
speichern, bei einer Anfrage aber gemeinsam zu beruecksichtigen.

## 15. Automatische Speicherung relevanter Unternehmensinformationen

Teilt der Benutzer im Alltag dauerhaft relevante Informationen mit, soll das
erkannt werden. Zu unterscheiden sind temporaere Informationen („Pruefe diese
Rechnung.") und dauerhaft relevante („Unsere Rechnungen ab 5.000 EUR muessen
durch den Geschaeftsfuehrer freigegeben werden."). Bei Unsicherheit ist der
Benutzer zu fragen.

## 16. Aenderung und Loeschung von Unternehmenswissen

Gespeicherte Informationen muessen ansehbar, suchbar, ergaenzbar, aenderbar,
archivierbar und loeschbar sein. Alte Informationen duerfen nicht unsichtbar
ueberschrieben werden; bei wichtigen Aenderungen ist zu versionieren.

## 17. Metadaten des Unternehmensgedaechtnisses

Soweit sinnvoll: Inhalt, Kategorie, Erstellungsdatum, Aenderungsdatum,
Quelle, Ursprung, Gueltigkeitsstatus, Version, gueltig ab, gueltig bis,
Ueberpruefungsdatum.

## 18. Empfohlene Struktur des Unternehmensgedaechtnisses

`company/` mit profile, organization, people, accounting, processes, rules,
approvals, tax, customers, suppliers, cases, documents, templates, memory;
`database/company.db`; `conversations/`; `workspace/`. Eine technisch bessere
Struktur ist zulaessig.

## 19. Keine Abhaengigkeit vom urspruenglichen PC

Das Gedaechtnis liegt auf dem portablen Datentraeger. Information auf PC A
speichern, Anwendung beenden, SSD an PC B anschliessen, starten - die
Information muss wieder verfuegbar sein.

## 20. Keine unkontrollierte Host-Speicherung

Unternehmensinformationen duerfen nicht ausschliesslich in Windows AppData,
Temp, Browsercache, Registry, Windows-Benutzerprofil oder versteckten
Host-Datenbanken liegen. Temporaere Dateien duerfen verwendet werden und sind
anschliessend kontrolliert zu entfernen.

## 21. Datenschutz und Schutz bei SSD-Verlust

Zu pruefen: Verschluesselung, Datenbankverschluesselung, Zugriffsschutz,
Passwortschutz, Integritaet, Backup, Wiederherstellung, sichere
Geheimnisverwaltung. Passwoerter, API-Tokens und Schluessel duerfen niemals
unverschluesselt im Unternehmensgedaechtnis liegen.

## 22. Rolle des KI-Buchhalters

Hochqualifizierter digitaler Fachmitarbeiter zur Zuarbeit. Ersetzt **nicht**
Steuerberater, Wirtschaftspruefer, verantwortlichen Buchhalter,
Geschaeftsfuehrung oder rechtsverbindliche Freigaben.

## 23. Fachlicher Aufgabenumfang

Sachverhalte analysieren, Kontierungsvorschlaege, Buchungssaetze,
Rechnungspruefung, Rechnungspflichtangaben, Umsatzsteuer, Vorsteuer, Reverse
Charge, innergemeinschaftlicher Erwerb und Lieferung, Leistungsort,
Steuerbefreiungen, Kleinunternehmerregelung, E-Rechnung, Debitoren,
Kreditoren, offene Posten, Bank, Kasse, Anlagevermoegen, Abschreibungen,
Rechnungsabgrenzung, Rueckstellungen, Jahresabschlussvorbereitung, GoBD,
Aufbewahrung, Dokumentation, Plausibilitaetspruefungen, Differenzanalysen,
fehlende Unterlagen, Berechnungen, Handlungsoptionen, Quellenrecherche.

## 24. Standardlogik bei fachlichen Anfragen

A Sachverhalt feststellen · B fehlende Informationen erkennen · C Zeitraum
bestimmen · D Unternehmenskontext beruecksichtigen · E Normen identifizieren ·
F Verwaltungsauffassung pruefen · G Rechtsprechung beruecksichtigen ·
H subsumieren · I steuerliche Folgen · J buchhalterische Behandlung ·
K Buchungsvorschlag · L Unsicherheiten benennen · M Quellen nennen ·
N menschliche Pruefung kennzeichnen.

Ausgabe soweit sinnvoll: ERGEBNIS, BEGRUENDUNG, STEUERLICHE BEHANDLUNG,
BUCHHALTERISCHE BEHANDLUNG, BUCHUNGSVORSCHLAG, BENOETIGTE UNTERLAGEN, OFFENE
PUNKTE, RISIKEN, QUELLEN, WISSENSSTAND, FREIGABEBEDARF.

## 25. Zeitbezogener Rechtsstand

Historische Sachverhalte duerfen nicht automatisch nach heutigem Recht
beurteilt werden. Quellen benoetigen moeglichst Veroeffentlichungsdatum,
Abrufdatum, gueltig ab, gueltig bis, Aenderungsdatum, Version, Quelle.

## 26. Quellenhierarchie

1. Gesetze, Verordnungen, amtliche Rechtsquellen
2. Amtliche Verwaltungsanweisungen
3. Hoechstrichterliche Rechtsprechung
4. Behoerdeninformationen
5. Serioese Fachsekundaerquellen

Sekundaerquellen duerfen entgegenstehende Primaerquellen nicht ueberstimmen.

## 27. Quellenregister

Maschinenlesbares Register (`config/sources.yaml` oder
`config/source_registry.json`) mit mindestens Q01 Gesetze im Internet (HGB,
AO, UStG, UStDV, EStG, EStDV, KStG, GewStG, BGB, GmbHG, weitere), Q02 BMF
(BMF-Schreiben, UStAE, GoBD, E-Rechnung), Q03 ELSTER, Q04 BZSt, Q05 BFH,
Q06 BVerfG, Q07 EUR-Lex, Q08 CURIA/EuGH, Q09 Bundesgesetzblatt,
Q10 Unternehmensregister, Q11 IHK und serioese Fachquellen, Q12 weitere
offizielle kostenfreie Quellen. Weitere notwendige Primaerquellen sind
eigenstaendig zu pruefen.

## 28. Keine blossen Links als Offline-Wissen

Ein gespeicherter Link ist keine Wissensbasis. Pipeline: Quelle → Abruf →
Original → Extraktion → Normalisierung → Metadaten → Chunking → Index →
lokale Recherche. Bevorzugt XML, strukturierte HTML-Daten, PDFs, APIs, RSS,
Aenderungsfeeds, offizielle maschinenlesbare Formate. Lizenz- und
Nutzungsbedingungen beachten; keine kostenpflichtigen oder geschuetzten
Datenbanken unzulaessig kopieren.

## 29. Lokale Wissensdatenbank

`resources/` mit raw, normalized, metadata, index; `knowledge/` mit
accounting, tax, vat, gobd, invoicing, e_invoice, eu_vat, legislation,
case_law, closing, assets, receivables, payables, banking, templates,
procedures.

## 30. RAG / Recherche

Fuer Fachfragen moeglichst nicht ausschliesslich Modellwissen. Priorität:
lokale Primaerquelle, lokale Verwaltungsanweisung, lokale Rechtsprechung,
lokale Fachquelle, Modellwissen ergaenzend. Quellen muessen nachvollziehbar
sein.

## 31. Update-System

Kontrolliertes Wissensupdate: manuell („Wissen jetzt aktualisieren") sowie
konfigurierbar woechentlich, monatlich, benutzerdefiniert. Automatische
Updates nur, wenn die Anwendung laeuft, der Datentraeger verbunden und
Internet verfuegbar ist - keine Behauptung, die SSD aktualisiere sich
selbstaendig. Moeglichst inkrementell ueber Aenderungsdatum, Version, ETag,
Last-Modified, Dokument-ID, Pruefsumme. Ablauf: Internet pruefen,
Quellenregister laden, Aenderungen erkennen, laden, Original speichern,
normalisieren, Metadaten, Index, Integritaet, Updatebericht, Wissensstand,
Rollback.

## 32. Lokales Sprachmodell

Geeignetes lokal ausfuehrbares Modell: gute deutsche Sprachqualitaet, fuer
Fachaufgaben geeignet, Windows, offline nutzbar, quantisierbar, CPU
grundsaetzlich unterstuetzt, GPU optional, keine zwingende Cloudverbindung,
geeignete Lizenz. Zu dokumentieren: Modell, Lizenz, Dateigroesse, RAM, VRAM,
CPU, Performance, Qualitaetsniveau, Runtime. Das Modell muss austauschbar
sein.

## 33. Optionales Online-KI-Modell

Das lokale Modell ist die Grundvoraussetzung; Online-Modelle sind optional.
Faellt die Online-KI aus, wird das lokale Modell weiterverwendet.

## 34. Hardware-Erkennung

Beim ersten Start pruefen: Windows-Version, CPU, RAM, GPU, VRAM, freier
Speicherplatz, Modell, Wissensindex, Schreibrechte, zentrale Dateien.
Optionale Modellprofile LIGHT, STANDARD, HIGH QUALITY.

## 35. Grafische Benutzeroberflaeche

Fuer normale Bueroanwender. Mindestens: Titel, Status ONLINE/HYBRID/OFFLINE,
Wissensstand, Chatbereich, Eingabefeld, Absenden. Funktionen: Neue
Unterhaltung, Verlauf, Dokument hinzufuegen, Quellen anzeigen, Wissen
aktualisieren, Unternehmenswissen anzeigen, Einstellungen, Status,
Fehlermeldungen.

## 36. Echte portable Windows-Anwendung

Final bevorzugt `PORTABLE_BUCHHALTER.exe`. Eine BAT-Datei darf waehrend
Entwicklung und Tests genutzt werden, ist aber nicht das bevorzugte
Endprodukt. Moeglichst ohne Python-Installation, Git, VS Code, Compiler,
Terminal, Administratorrechte und klassische Installation. Notwendige
Runtime-Komponenten sind soweit moeglich mitzuliefern.

## 37. Daten auf der SSD

Standardmaessig auf der SSD: Anwendung, Runtime, Modell, Fachwissen, Index,
Unternehmenswissen, Dokumente, Unternehmensdatenbank, Gespraechsverlaeufe,
Arbeitsstaende, Konfiguration, Updates, Logs, Checkpoints, Sicherungen.

## 38. Erster Programmstart

Systempruefung mit Ausgabe von lokalem Modell, Fachwissen,
Unternehmensgedaechtnis, Wissensstand, Internet, Betriebsart und einem
Knopf `[BUCHHALTER STARTEN]`.

## 39. Unternehmens-Onboarding

Bei neuem Unternehmen strukturiert erfassen: Name, Rechtsform, Branche,
Umsatzsteuerstatus, Wirtschaftsjahr, Kontenrahmen, Buchhaltungssystem, ERP,
Zahlungsverkehr, Debitoren- und Kreditorenprozess, Rechnungsworkflow,
Freigaberegeln, Kostenstellen, Steuerschluessel, Besonderheiten,
Ansprechpartner, gewuenschte Aufgaben, verbotene Taetigkeiten. Dauerhaft auf
der SSD speichern.

## 40. ERP- und Systemconnectoren

Connector-Schicht `connectors/` mit sap, wilken, datev, generic_rest, csv,
excel, database. Vor einer Integration zu klaeren: Produkt, Version, API,
REST, SOAP, OData, RFC/BAPI, Dateiimport, Datenbank, Authentifizierung, VPN,
Berechtigungen. Standard READ ONLY. Schreibaktionen: Vorschlag → Vorschau →
menschliche Freigabe → Ausfuehrung → Protokoll.

## 41. Human-in-the-Loop

Status ENTWURF, GEPRUEFT, FREIGEGEBEN, AUSGEFUEHRT. Ohne Freigabe keine
Steuererklaerungen, Behoerdenmeldungen, Zahlungen, verbindlichen Buchungen
oder Stammdatenaenderungen.

## 42. Halluzinationsschutz

Niemals Gesetze, Paragraphen, Urteile, Aktenzeichen oder Quellen erfinden;
niemals Speicherung, Tests, Onlineabrufe, ERP-Ausfuehrungen oder Aktualitaet
behaupten, die nicht stattgefunden haben. Bei Unsicherheit: „Nicht
ausreichend sicher.", dann Unsicherheit erklaeren, fehlende Information
nennen, geeignete Quelle nennen, menschliche Pruefung empfehlen.

## 43. Projektstruktur

`PORTABLE_BUCHHALTER.exe`, `START_HIER.md`, `app/`, `src/`, `core/`, `ui/`,
`agents/`, `models/`, `knowledge/`, `company/`, `database/`,
`conversations/`, `workspace/`, `resources/{raw,normalized,metadata,index}`,
`connectors/`, `updater/`, `config/`, `data/`, `runtime/`, `logs/`,
`updates/`, `backups/`, `tests/`, `docs/`, `tools/`.

## 44. Checkpoint-Regel (verbindlich)

Nach **jedem** abgeschlossenen Task: Implementierung abschliessen, Tests
durchfuehren, Ergebnisse pruefen, Projektstatus aktualisieren, Git-Commit,
Checkpoint erstellen, Checkpoint zusaetzlich ausserhalb des Repositorys
speichern (`D:\Ki-Agent\checkpoints`), Zwischenstand aktualisieren,
tatsaechliche Speicherung pruefen, erst danach den naechsten Task beginnen.

Checkpoint mindestens: Tasknummer, Taskname, Datum/Zeit, Status, erledigte
Arbeit, Dateien, Tests, Testergebnis, offene Punkte, naechster Task,
Fortsetzungspunkt, Git-Commit, Pruefsummen. Eine Chatmeldung „Checkpoint
erstellt" genuegt nicht - die Datei muss geschrieben sein.

## 45. Wiederherstellbarkeit

Das Projekt muss unabhaengig vom Chat wiederherstellbar sein. Nach
Chatverlust, Kontextverlust, Limit-Stopp, Neustart oder Rechnerwechsel muss
lokal erkennbar sein: letzter abgeschlossener Task, Git-Stand, Projektstatus,
offene Arbeit, naechster Schritt, Wiederherstellungsquelle. Die Festplatte
ist der massgebliche Projektstand.

## 46. Qualitaetssicherung

Mindestens testen: Offline-Start, Hybridstart, Internetverlust,
Internetwiederkehr, fehlendes Modell, beschaedigtes Modell, fehlende
Wissensdatenbank, beschaedigter Index, Unternehmensgedaechtnis, Speichern
neuer Informationen, Laden auf zweitem PC, Suchfunktion, Quellenbelege,
Dokumentanalyse, Update, Update-Abbruch, Rollback, Wiederherstellung,
anderer Laufwerksbuchstabe, Pfade mit Leerzeichen, Schreibrechte, GUI, EXE,
Datenintegritaet, Verschluesselung, portable Nutzung.

## 47. Fachliche Testfaelle

Mindestens: normale Eingangsrechnung, fehlerhafte Rechnung,
innergemeinschaftlicher Erwerb, innergemeinschaftliche Lieferung, Reverse
Charge, Kleinunternehmer, Vorsteuer, E-Rechnung, Anlagegut, Abschreibung,
Skonto, Gutschrift, Forderungsausfall, Rechnungsabgrenzung, Rueckstellung,
Vertragsstrafe ohne Lieferung, nachtraegliche Lieferung, unterschiedliche
Leistungs- und Rechnungszeitpunkte.

## 48. Verbindlicher Projektplan

TASK 01 Projektziel, Anforderungen, Definition of Done · TASK 02
Systemarchitektur und Technologieentscheidungen · TASK 03 Portable
Ordnerstruktur, relative Pfade, Konfiguration · TASK 04 Mitarbeiterprofil und
Fach-Masterprompt · TASK 05 Fachmodule und Quellenregister · TASK 06
Quellenabruf und Dokument-zu-lokal-Pipeline · TASK 07 Normalisierung,
Metadaten, Versionierung · TASK 08 Lokale Wissensdatenbank und Suchindex ·
TASK 09 Embedding-/Retrieval-System · TASK 10 Lokales Sprachmodell und
Inferenz · TASK 11 RAG-Orchestrierung und Quellenbelege · TASK 12
Persistentes Unternehmensgedaechtnis · TASK 13 Offlinefaehige Oberflaeche ·
TASK 14 Hybridbetrieb, Internetstatus, Update-System · TASK 15
Unternehmens-Onboarding und Memory-Verwaltung · TASK 16 Connector-/
ERP-Architektur · TASK 17 Sicherheit, Freigaben, Audit, Packaging,
Windows-EXE, Launcher · TASK 18 Gesamtintegration, Praxistest, Offline-/
Online-Test, Portabilitaetstest, Unternehmensmemory-Test,
Wiederherstellungstest, Endabnahme, finaler Checkpoint.

Zusaetzliche Tasks sind zu ergaenzen. Keine Funktion darf weggelassen werden,
nur um formal Task 18 zu erreichen.

## 49. Portabilitaetstest

TEST 1 Internet vorhanden, EXE starten → Hybridmodus. TEST 2 Internet
deaktivieren, EXE starten → funktioniert. TEST 3 Offline Fachfrage → lokales
Modell und Fachwissen. TEST 4 Neue Unternehmensinformation speichern
(„Wir verwenden SKR03."). TEST 5 Programm beenden. TEST 6 SSD an anderem
Windows-PC. TEST 7 EXE starten. TEST 8 Frage „Welchen Kontenrahmen verwendet
dieses Unternehmen?" → SKR03 aus dem Gedaechtnis. TEST 9 Laufwerkswechsel
D: → E: → weiterhin funktionsfaehig. TEST 10 Wissensupdate online. TEST 11
Internet deaktivieren. TEST 12 Aktualisiertes Wissen offline verwenden.

## 50. Abschlussdateien

Mindestens: `PORTABLE_BUCHHALTER.exe`, `START_HIER.md`, `README.md`,
`ARCHITEKTUR.md`, `PROJEKTSTATUS.md`, `CHANGELOG.md`, `TESTBERICHT.md`,
`SICHERHEITSKONZEPT.md`, `UPDATE_KONZEPT.md`, `ERP_CONNECTOR_KONZEPT.md`,
Quellenregister, Mitarbeiterprofil Buchhalter, Unternehmensprofil-Vorlage,
`MEMORY_KONZEPT.md`, `DATENSPEICHER_KONZEPT.md`,
`BACKUP_WIEDERHERSTELLUNG.md` sowie alle notwendigen Runtime-Dateien,
Modelle, Wissensdateien, Unternehmensdaten, Datenbanken, Indexdateien,
Konfigurationen und Programmdateien.

## 51. Verschaerfte Definition of Done

Abgeschlossen erst, wenn der Auftraggeber: 1. SSD anschliessen, 2.
Projektordner oeffnen, 3. `PORTABLE_BUCHHALTER.exe` doppelklicken, 4. ohne
Entwicklungsumgebung die GUI oeffnen, 5. ohne Internet eine Fachfrage
stellen, 6. eine Antwort mit lokalem Modell erhalten, 7. lokale Fachquellen
verwenden, 8. Quellen nachvollziehen, 9. neue Unternehmensinformationen
eingeben, 10. diese dauerhaft auf der SSD speichern, 11. die Anwendung
schliessen, 12. die SSD an einem anderen PC verwenden, 13. das
Unternehmenswissen dort weiterhin vorfinden, 14. mit Internet dieselbe
Anwendung verwenden, 15. Fachwissen aktualisieren, 16. Internet wieder
abschalten, 17. das aktualisierte Wissen offline weiterverwenden, 18. die
Anwendung auf einem anderen Laufwerksbuchstaben nutzen, 19. das Projekt aus
Checkpoints wiederherstellen und 20. dies alles ohne Server tun kann.

Erst dann: **PORTABLER BUCHHALTER MVP FERTIG**.

## 52. Keine Scheinerfuellung

Strikt zu unterscheiden: GEPLANT, IMPLEMENTIERT, GEBAUT, GESPEICHERT,
GETESTET, VERIFIZIERT. Eine EXE ist nur gebaut, wenn sie existiert; nur
getestet, wenn sie gestartet wurde. Eine Datei ist nur gespeichert, wenn sie
geschrieben wurde. Offlinefaehigkeit ist nur verifiziert, wenn offline
getestet. Portabilitaet nur, wenn Laufwerkswechsel bzw. zweiter PC geprueft
wurde. Das Unternehmensgedaechtnis nur, wenn gespeicherte Informationen nach
Neustart erneut verfuegbar sind.

## 53. Blaupause fuer weitere Mitarbeiter

Wiederverwendbar: GUI, lokales Modellmanagement, RAG, Wissensdatenbank,
Unternehmensgedaechtnis, Datenhaltung, Update-Engine, Sicherheitslogik,
Freigabelogik, Logging, Connector-Framework, Packaging, EXE-Launcher,
Checkpoint-System. Fuer einen neuen Mitarbeiter moeglichst nur
Mitarbeiterprofil, Masterprompt, Fachwissen, Quellen, Berechtigungen,
Fachmodule und Connectoren austauschen.

## 54. Langfristige Plattform

Spaeter moeglich: `PORTABLE_UNTERNEHMENS_KI.exe` mit auswaehlbaren
Mitarbeitern (Buchhalter, Controller, Rechtsabteilung, Einkauf, Verkaeufer),
gemeinsamem Core und gemeinsamer Unternehmenswissensbasis. Diese Moeglichkeit
darf beruecksichtigt werden, die Fertigstellung des ersten MVP aber nicht
verzoegern.

## 55. Arbeitsregeln

Eigenstaendig und systematisch arbeiten. Nur bei Entscheidungen fragen, die
die Architektur wesentlich aendern, geschaeftlich zu entscheiden sind,
sicherheitsrelevant sind oder nicht serioes selbst entschieden werden
koennen. Normale technische Detailentscheidungen selbst treffen und
dokumentieren. Niemals erfolgreiche Arbeitsschritte erfinden; niemals
„gespeichert", „getestet" oder „verifiziert" behaupten, wenn es nicht
zutrifft.

## 56. Erster Schritt

Zunaechst den vollstaendigen Masterprompt lesen, dann Zielbild, Machbarkeit,
Architektur, lokale Datenhaltung, Unternehmensgedaechtnis, lokales Modell,
Fachwissensarchitektur, RAG, Hybridbetrieb, Update-System, EXE-/
Packaging-Strategie, Sicherheitskonzept, Wiederherstellung und Connector-
Architektur pruefen. Danach Projektinitialisierung mit Verstaendnis des
Endprodukts, Architektur, Technologieauswahl, Speicherkomponenten,
Datenbankstrategie, Memory-Strategie, Modellstrategie, Wissensstrategie,
Packaging-Strategie, Sicherheitsstrategie, technischen Blockern,
Taskplan, Definition of Done, Projektpfad und Checkpointpfad. Danach TASK 01.
Nach jedem Task: implementieren → testen → verifizieren → Git-Commit →
Checkpoint auf Festplatte → Checkpoint verifizieren → erst danach der
naechste Task.

## 57. Verbindliches Endziel

Ein hybrider, portabler KI-Buchhalter, der von einer externen SSD ueber eine
echte Windows-Anwendung per Doppelklick startet, mit lokalem Modell, lokalen
Fachwissensbestaenden, lokalen Quellen, lokaler Wissensdatenbank,
persistentem Unternehmensgedaechtnis, lokalen Gespraechsverlaeufen,
Arbeitsstaenden, Dokumenten und Checkpoints. Ohne Internet arbeitsfaehig, mit
Internet kontrolliert erweitert um aktuelle Quellen, Wissensupdates,
Online-Recherche, optionale Online-KI und spaetere ERP-Schnittstellen.
Unternehmensinformationen bleiben nach Neustart, Rechnerwechsel und im
Offlinebetrieb verfuegbar. Fuer die Grundfunktion wird kein Server benoetigt.
Funktioniert diese Nutzungskette nicht, ist das Projekt nicht abgeschlossen.

---

# TEIL 2 - KOMMERZIELLE PRODUKTPERSPEKTIVE (Abschnitte 58 bis 80)

*Diese Abschnitte sind woertlich so wiedergegeben, wie sie uebergeben wurden.*

## 58. Kommerzielle Produktperspektive

Die Referenzimplementierung PORTABLER BUCHHALTER wird zunaechst als
funktionsfaehige interne bzw. pilotfaehige Anwendung entwickelt.

Die technische Architektur muss jedoch beruecksichtigen, dass der
Portable-KI-Core spaeter als B2B-Produkt fuer andere Unternehmen eingesetzt
werden koennen soll. Ziel ist keine einmalige kundenspezifische
Bastelloesung.

Langfristiges Produktprinzip: PORTABLE-KI-CORE + FACHMITARBEITER-MODUL +
KUNDENKONFIGURATION + UNTERNEHMENSGEDAECHTNIS + WISSENSPAKETE + OPTIONALE
CONNECTOREN.

Die Kernplattform soll moeglichst standardisiert bleiben. Kundenspezifisch
sollen insbesondere sein: Unternehmensprofil, Unternehmenswissen, Benutzer
und Berechtigungen, Fachregeln, Prozesse, ERP-Konfiguration,
Connector-Konfiguration, Vorlagen, kundenspezifische Dokumente.

## 59. Produktpositionierung

Das System ist als KI-FACHASSISTENT bzw. DIGITALER KI-MITARBEITER ZUR
FACHLICHEN ZUARBEIT zu konzipieren.

Es darf nicht technisch oder kommunikativ davon ausgegangen werden, dass ein
KI-System fehlerfrei arbeitet oder einen gesetzlich bzw. fachlich
verantwortlichen Menschen vollstaendig ersetzt.

Insbesondere beim Buchhalter-Modul gilt: Die KI analysiert, recherchiert,
strukturiert, berechnet, prueft, erkennt Auffaelligkeiten, erstellt
Vorschlaege, erstellt Entscheidungsvorlagen, bereitet Vorgaenge vor.
Kritische Ergebnisse bleiben Human-in-the-Loop.

## 60. Keine 100-Prozent-Richtigkeit als Produktannahme

Das Produkt darf niemals unter der technischen Annahme entwickelt werden,
dass KI-Ausgaben zu 100 Prozent korrekt sind. Stattdessen muessen
ueberpruefbare Qualitaetsmerkmale geschaffen werden. Beispielsweise:
Anwendung startet zuverlaessig, Offlinebetrieb funktioniert, Datenhaltung
funktioniert, Quellen sind nachvollziehbar, Wissensstand ist sichtbar,
Unsicherheiten werden gekennzeichnet, kritische Aktionen benoetigen Freigabe,
Updates sind versioniert, Tests sind dokumentiert, Aenderungen sind
nachvollziehbar, Rueckkehr auf vorherigen funktionierenden Stand ist
moeglich.

Das Produktversprechen soll auf ueberpruefbaren Systemeigenschaften basieren
und nicht auf einer behaupteten Fehlerfreiheit der KI.

## 61. Kundentrennung

Die Architektur muss eine strikte Trennung verschiedener Unternehmen
ermoeglichen. Unternehmenswissen von Kunde A darf unter keinen Umstaenden in
Kunde B, andere Unternehmensprofile, andere portable Installationen oder
allgemeines Fachwissen gelangen.

Jede Kundeninstanz benoetigt eine eindeutig getrennte Datenhaltung,
beispielsweise `customers/customer_001/{company,database,documents,
conversations,config,backups}` oder eine technisch gleichwertige, sichere
Architektur.

Es muss technisch verhindert werden, dass kundenspezifische Daten
versehentlich in allgemeine Wissenspakete uebernommen werden.

## 62. Datenexport und Datenloeschung

Fuer einen spaeteren Unternehmenseinsatz muss der Kunde Kontrolle ueber seine
Daten besitzen. Es muss architektonisch moeglich sein: Unternehmensdaten zu
exportieren, Unternehmenswissen anzuzeigen, gespeicherte Informationen zu
korrigieren, einzelne Informationen zu loeschen, Gespraechsverlaeufe zu
loeschen, Dokumente zu loeschen, eine komplette Kundeninstanz kontrolliert zu
loeschen, Sicherungen zu verwalten.

Loeschungen muessen, soweit technisch erforderlich und sinnvoll,
nachvollziehbar durchgefuehrt werden.

## 63. Lizenz- und Redistributionspruefung

Vor Aufnahme einer Komponente in das Produkt muss geprueft werden, ob deren
Lizenz den vorgesehenen Einsatz erlaubt. Dies betrifft insbesondere: lokales
Sprachmodell, Embedding-Modell, Inferenz-Runtime, Python- bzw. andere
Softwarebibliotheken, GUI-Framework, Datenbanksoftware, Vektorindex,
Dokumentparser, mitgelieferte Fachunterlagen, heruntergeladene
Wissensbestaende, Icons, Fonts und andere Ressourcen.

Unterscheide ausdruecklich: NUTZUNG IM EIGENEN PROJEKT und WEITERVERTRIEB AN
KUNDEN. Eine Komponente darf nicht allein deshalb in ein spaeteres
kommerzielles Produkt aufgenommen werden, weil sie technisch kostenlos
heruntergeladen werden kann.

Erstelle langfristig ein LIZENZREGISTER mit mindestens: Komponente, Version,
Hersteller/Projekt, Lizenz, kommerzielle Nutzung erlaubt, Weitergabe erlaubt,
notwendige Hinweise, Quelle, Pruefdatum.

## 64. Software-Bestandsliste / SBOM

Fuer die spaetere Produktreife soll eine nachvollziehbare Liste aller
relevanten Softwarebestandteile existieren. Mindestens dokumentieren: Name,
Version, Herkunft, Lizenz, Einsatzbereich. Die Architektur soll die spaetere
Erstellung einer Software Bill of Materials (SBOM) unterstuetzen.

## 65. Sichere Software-Updates

Ein kommerziell eingesetzter KI-Mitarbeiter benoetigt kontrollierbare
Softwareupdates. Fachwissensupdates und Programmupdates sind getrennt zu
behandeln.

A. WISSENSUPDATE: Gesetze, Verwaltungsanweisungen, Rechtsprechung,
Fachinformationen. B. SOFTWAREUPDATE: Programmcode, GUI, Runtime,
Sicherheitskorrekturen, Connectoren.

Softwareupdates muessen versioniert, nachvollziehbar, auf Integritaet
pruefbar und ruecksetzbar sein. Ein fehlerhaftes Update darf eine
funktionierende Kundeninstallation nicht unkontrolliert zerstoeren.

## 66. Versionierung des Produkts

Die Anwendung benoetigt eine eindeutig erkennbare Produktversion, zusaetzlich
getrennt anzuzeigen: Softwareversion, Wissensstand, Fachmodul,
Unternehmensprofil, Modell (Name/Version). Dadurch muessen Fehler und
Kundeninstallationen spaeter reproduzierbar zugeordnet werden koennen.

## 67. Audit- und Fehlernachvollziehbarkeit

Das System muss spaetere Support- und Haftungsfragen technisch
nachvollziehbar machen. Soweit datenschutzrechtlich und technisch vertretbar
dokumentieren: verwendete Softwareversion, verwendetes Modell, verwendeter
Wissensstand, verwendete Quellen, relevante Einstellungen, ausgefuehrte
Freigaben, Fehlermeldungen. Keine unnoetige Protokollierung vertraulicher
Inhalte. Ziel: Ein spaeter gemeldeter Fehler muss moeglichst reproduzierbar
untersucht werden koennen.

## 68. Remote-Support

Der portable KI-Mitarbeiter muss ohne Fernzugriff funktionieren. Soll spaeter
Remote-Support angeboten werden, muss dieser ausdruecklich aktiviert werden,
vom Kunden kontrollierbar sein, zeitlich begrenzbar sein, nachvollziehbar
sein und wieder deaktivierbar sein. Kein dauerhaft versteckter Fernzugriff.

## 69. Telemetrie

Der Grundbetrieb darf keine zwingende Telemetrie an den Hersteller
benoetigen. Falls spaeter Telemetrie oder Fehlerberichte angeboten werden:
transparent, konfigurierbar, moeglichst datensparsam, sicher, rechtlich
geprueft. Unternehmensdokumente und Fachinhalte duerfen nicht unkontrolliert
als Telemetriedaten uebertragen werden.

## 70. Security-by-Design

Die Plattform soll bereits waehrend der Entwicklung auf einen spaeteren
professionellen Unternehmenseinsatz vorbereitet werden. Mindestens
beruecksichtigen: sichere Standardkonfiguration, minimale Berechtigungen,
verschluesselte sensible Daten, sichere Geheimnisverwaltung,
Integritaetspruefung, Update-Sicherheit, Dependency-Management, Backup und
Wiederherstellung, Schutz bei Verlust der SSD, sichere Connectoren,
Fehlerprotokollierung, Rechtekonzept.

Sicherheitsanforderungen duerfen nicht erst kurz vor einer kommerziellen
Veroeffentlichung nachtraeglich hinzugefuegt werden.

## 71. Rechtlicher Produkt-Compliance-Check

Vor einer kommerziellen Veroeffentlichung muss eine separate
Compliance-Pruefung stattfinden. Dabei sind insbesondere die fuer den
konkreten Produktstand einschlaegigen Anforderungen zu pruefen,
beispielsweise aus Datenschutzrecht, KI-Regulierung, Produkthaftungsrecht,
IT-/Cybersicherheitsrecht, Vertragsrecht, Urheber- und Lizenzrecht,
steuerberatungsrechtlichen Grenzen und gegebenenfalls branchenspezifischen
Vorschriften.

Die Software darf nicht selbst davon ausgehen, dass ein einfacher
Haftungsausschluss rechtliche Risiken beseitigt. Rechtliche Grenzen sollen,
soweit moeglich, zusaetzlich technisch abgesichert werden.

## 72. Fachliche Grenzen des Buchhalter-Moduls

Bei spaeterer kommerzieller Nutzung muss besonders sorgfaeltig zwischen
SOFTWAREUNTERSTUETZUNG / FACHLICHER ZUARBEIT und einer moeglicherweise
rechtlich besonders geregelten Dienstleistung unterschieden werden.

Das Buchhalter-Modul soll deshalb standardmaessig: Sachverhalte analysieren,
Informationen recherchieren, Auffaelligkeiten erkennen, Dokumente pruefen,
Berechnungen durchfuehren, Buchungsvorschlaege erzeugen,
Entscheidungsgrundlagen schaffen.

Kritische steuerliche oder rechtliche Ergebnisse muessen als
pruefungsbeduerftige Zuarbeit gekennzeichnet werden. Vor kommerzieller
Vermarktung ist die konkrete Abgrenzung rechtlich pruefen zu lassen.

## 73. Produkthaftung und Qualitaetssicherung

Die Architektur muss darauf ausgelegt sein, spaeter nachvollziehen zu
koennen: welche Version beim Kunden eingesetzt wurde, welche Tests diese
Version bestanden hatte, welcher Wissensstand verwendet wurde, welche
bekannten Einschraenkungen bestanden, welche Updates bereitgestellt wurden,
welche Fehler bekannt waren.

Zu jeder veroeffentlichungsfaehigen Version soll langfristig ein
Release-Dossier erzeugt werden koennen, beispielsweise `RELEASE/` mit
`release_notes.md`, `test_report.md`, `known_issues.md`, `licenses.md`,
`sbom.json`, `security_notes.md`, `checksums.txt`.

## 74. Kunden-Onboarding als Produktfunktion

Das Unternehmens-Onboarding soll langfristig reproduzierbar sein. Nicht jeder
Kunde darf durch individuelle manuelle Entwicklerarbeit komplett neu
eingerichtet werden muessen.

Ziel: PORTABLE-KI INSTALLIEREN → NEUES UNTERNEHMEN ANLEGEN → ONBOARDING →
UNTERNEHMENSPROFIL → FACHREGELN → BERECHTIGUNGEN → OPTIONALE CONNECTOREN →
BETRIEBSBEREIT. Das Onboarding soll soweit sinnvoll durch die Anwendung
gefuehrt werden.

## 75. Backup-Strategie fuer Kunden

Da Unternehmenswissen ausschliesslich bzw. primaer lokal gespeichert werden
kann, darf der Verlust oder Defekt einer SSD nicht automatisch zum
Totalverlust des Unternehmensgedaechtnisses fuehren. Es muss ein
Backup-Konzept vorgesehen werden. Moegliche Ziele: zweite verschluesselte
externe SSD, kundeneigenes NAS, kundeneigener Server, freigegebener
verschluesselter Unternehmensspeicher.

Backups muessen optional bleiben. Die portable KI darf weiterhin ohne
zentralen Server funktionieren.

## 76. Pilotbetrieb vor kommerzieller Freigabe

Nach Fertigstellung des technischen MVP darf die Plattform nicht automatisch
als marktreifes Serienprodukt betrachtet werden. Vor breiter Vermarktung ist
eine Pilotphase vorzusehen.

Empfohlener Ablauf: TECHNISCHES MVP → INTERNER TEST → PILOTKUNDE → REALER
BETRIEB → FEHLER UND AUFWAND ERFASSEN → VERBESSERUNG → STANDARDISIERUNG →
SICHERHEITS-/COMPLIANCE-PRUEFUNG → MARKTREIFE VERSION.

Waehrend des Pilotbetriebs insbesondere messen: Antwortqualitaet, Fehlerrate,
Geschwindigkeit, Hardwareprobleme, Updateprobleme, Benutzerfreundlichkeit,
Supportaufwand, Speicherbedarf, Connector-Probleme, falsche oder unsichere
Fachantworten, Wiederherstellbarkeit.

## 77. Commercial-Readiness-Gate

Der Status PORTABLER BUCHHALTER MVP FERTIG ist NICHT identisch mit MARKTREIF.
Fuer eine kommerzielle Freigabe ist ein zusaetzlicher Status einzufuehren:
COMMERCIAL READY.

Dieser darf erst vergeben werden, wenn mindestens: Pilotbetrieb
durchgefuehrt, bekannte kritische Fehler behoben, Produktversion eindeutig,
Lizenzpruefung abgeschlossen, Sicherheitspruefung abgeschlossen, Backup-/
Restore geprueft, Updateprozess geprueft, Datenschutzkonzept geprueft,
notwendige rechtliche Pruefung durchgefuehrt, Produktdokumentation vorhanden,
Supportprozess definiert und Release-Unterlagen erstellt wurden.

## 78. Geschaeftsmodell nicht fest in die Technik einbauen

Die Architektur darf unterschiedliche spaetere Geschaeftsmodelle
unterstuetzen, beispielsweise: einmalige Lizenz, jaehrliche Lizenz,
Wartungsvertrag, Wissensupdate-Service, Support, zusaetzliche Fachmodule,
ERP-Connectoren, kundenspezifische Anpassungen.

Die Kernanwendung darf jedoch nicht unnoetig von einem bestimmten Lizenz-
oder Abrechnungsmodell abhaengig gemacht werden.

## 79. Erweiterte langfristige Produktvision

Langfristig kann aus dem ersten PORTABLEN BUCHHALTER eine allgemeine portable
Unternehmens-KI entstehen, beispielsweise `PORTABLE_UNTERNEHMENS_KI.exe` mit
auswaehlbaren Fachmitarbeitern: Buchhalter, Controller, Rechtsabteilung,
Einkauf, Verkauf, Geschaeftsfuehrer-Assistent.

Dabei sollen nach Moeglichkeit gemeinsam genutzt werden: technischer Core,
Unternehmensgedaechtnis, Benutzerverwaltung, Sicherheitsarchitektur,
Updatesystem, Connector-Framework, Dokumentenspeicher. Fachmitarbeiter
muessen trotzdem klare fachliche Grenzen und Berechtigungen besitzen.

## 80. Kommerzielles Endziel

Die Plattform soll technisch so aufgebaut werden, dass aus der
funktionierenden Buchhalter-Blaupause spaeter ein professionell einsetzbares
B2B-Produkt entstehen kann.

Dabei gilt: Erst technische Zuverlaessigkeit. Dann Pilotbetrieb. Dann
Standardisierung. Dann Sicherheits-, Lizenz- und Compliance-Pruefung. Erst
danach Skalierung und breite kommerzielle Vermarktung.

---

# TEIL 3 - KOPIERSCHUTZ UND LIZENZIERUNG (Abschnitte 84 bis 97)

> Anmerkung zur Zaehlung: Die Nummern 81 bis 83 gibt es nicht. Die
> Vorgabe springt an dieser Stelle von 80 auf 84. Hier fehlt also
> nichts - der Hinweis steht nur, damit spaeter niemand nach einem
> verlorenen Abschnitt sucht.

## 84. Kopierschutz und Lizenzierung

Die kommerzielle Produktarchitektur muss verhindern, dass ein einmal
erworbener portabler KI-Mitarbeiter durch einfaches Kopieren der
Programmdateien oder des vollstaendigen Datentraegers beliebig
vervielfaeltigt und mehrfach produktiv eingesetzt werden kann.

Wichtig: Eine absolute technische Verhinderung des Kopierens von Dateien kann
nicht garantiert werden. Ziel ist deshalb: KOPIERTE INSTANZ + KEINE GUELTIGE
LIZENZ = NICHT PRODUKTIV NUTZBAR.

Die Lizenzarchitektur muss bereits beim technischen Grunddesign
beruecksichtigt werden und darf nicht erst nachtraeglich aufgesetzt werden.

## 85. Portabilitaet darf nicht zerstoert werden

Die Lizenz darf standardmaessig NICHT fest an einen einzelnen Windows-PC
gebunden werden. Der portable Mitarbeiter soll weiterhin auf verschiedenen
geeigneten und freigegebenen Windows-PCs genutzt werden koennen.

Beispiel: Kunde besitzt eine lizenzierte portable SSD. Diese SSD kann an PC A,
PC B oder PC C angeschlossen werden. Die Lizenz bleibt gueltig. Eine Kopie
des Programms auf eine zweite nicht lizenzierte SSD darf dagegen nicht
automatisch eine zweite funktionsfaehige Produktinstanz erzeugen.

## 86. Bevorzugte Lizenzarchitektur

Pruefe eine Architektur aus mindestens: eindeutiger Instanz-ID, eindeutiger
Kunden-ID, eindeutiger Lizenz-ID, kryptografisch signierter Lizenzdatei,
lokal pruefbarer digitaler Signatur, eindeutiger Bindung an die jeweilige
portable Produktinstanz, optionaler Bindung an geeignete Merkmale des
Datentraegers, manipulationsgeschuetzter Lizenzpruefung.

Beispiel: `license/license.json`, `license/license.sig`. Die Lizenzdatei
koennte enthalten: Lizenz-ID, Kunde, Produkt, Fachmodul, erlaubte Instanzen,
Lizenztyp, Aktivierungsdatum, gegebenenfalls Ablaufdatum, Wartungsstatus,
erlaubte Zusatzmodule, Instanz-ID, Produktversion, Signaturinformationen.

Die Lizenz muss kryptografisch signiert sein. Der private Signaturschluessel
darf niemals Bestandteil der Kundenanwendung sein. Die Anwendung darf
lediglich den oeffentlichen Pruefschluessel enthalten.

## 87. Offline-Lizenzpruefung

Da der portable KI-Mitarbeiter vollstaendig offline funktionieren soll, muss
auch die grundlegende Lizenzpruefung offline moeglich sein. Der Start darf
nicht zwingend einen Lizenzserver oder eine dauerhafte Internetverbindung
benoetigen.

Beim Start: 1. Lizenzdatei laden. 2. Signatur pruefen. 3. Instanzbindung
pruefen. 4. Produkt-/Modulberechtigung pruefen. 5. gegebenenfalls Laufzeit
pruefen. 6. erst danach Anwendung freigeben.

Ohne gueltige Lizenz darf die produktive Anwendung nicht normal starten.

## 88. Optionale Online-Aktivierung

Fuer spaetere kommerzielle Versionen darf zusaetzlich eine Online-Aktivierung
vorgesehen werden: ERSTE AKTIVIERUNG ONLINE → LIZENZ WIRD DER PORTABLEN
INSTANZ ZUGEORDNET → SIGNIERTE OFFLINE-LIZENZ WIRD ERZEUGT → ANSCHLIESSEND
OFFLINE NUTZBAR.

Eine permanente Internetverbindung darf fuer die Grundfunktion nicht
erforderlich sein. Optional koennen spaetere Lizenzmodelle eine gelegentliche
Validierung vorsehen, sofern dies transparent und vertraglich vorgesehen ist.

## 89. Lizenzmodelle

Die technische Architektur darf unterschiedliche Lizenzmodelle
unterstuetzen: pro portabler Instanz, pro KI-Mitarbeiter, pro Fachmodul, pro
Unternehmen, pro Standort, Mehrfachlizenz, Unternehmenslizenz, zeitlich
befristete Lizenz, unbefristete Lizenz mit separatem Wartungsvertrag.

Das konkrete Geschaeftsmodell wird spaeter festgelegt. Die technische Basis
darf nicht auf nur ein einziges Lizenzmodell beschraenkt sein.

## 90. Schutz vor einfacher Vervielfaeltigung

Folgendes Szenario muss technisch beruecksichtigt werden: Kunde kauft 1 x
PORTABLER BUCHHALTER und kopiert anschliessend den vollstaendigen Ordner oder
Datentraeger auf SSD 2, SSD 3, SSD 4, SSD 5.

Diese Kopien duerfen nicht automatisch vier weitere lizenzierte Mitarbeiter
erzeugen. Die Anwendung muss erkennen koennen, dass die kopierte Instanz
keine gueltige Lizenz fuer diese zusaetzliche Produktinstanz besitzt.

## 91. Keine reine Dateipruefung

Ein Kopierschutz darf nicht ausschliesslich auf einer leicht editierbaren
Konfigurationsdatei beruhen. Unsichere Beispiele: `licensed=true` oder
`customer=Niels` in einer ungeschuetzten Textdatei. Eine solche Loesung ist
nicht ausreichend.

Verwende kryptografisch pruefbare Lizenzdaten und geeignete
Manipulationsschutzmechanismen.

## 92. Schutz des Programmcodes

Pruefe zusaetzlich angemessene Massnahmen gegen triviale Manipulation der
Anwendung, je nach gewaehlter Technologie beispielsweise: Code-Signing,
Integritaetspruefung wichtiger Dateien, Hash-Pruefung, signierte Manifeste,
Obfuscation soweit sinnvoll, Schutz kritischer Lizenzlogik, Pruefung
manipulierten Programmstands.

Wichtig: Security by Obscurity allein ist nicht ausreichend.

## 93. Ausfall- und Ersatzprozess

Der Kopierschutz darf einen legitimen Kunden bei Hardwaredefekt nicht
dauerhaft aussperren. Es muss deshalb ein kontrollierter
Wiederherstellungsprozess vorgesehen werden - SSD defekt, SSD verloren,
Datentraeger muss ersetzt werden, Kunde benoetigt neue Hardware, Instanz muss
migriert werden.

Dafuer muss es einen nachvollziehbaren Prozess geben: ALTE INSTANZ
DEAKTIVIEREN → NEUE INSTANZ AUTORISIEREN → NEUE SIGNIERTE LIZENZ AUSSTELLEN →
UNTERNEHMENSDATEN AUS BACKUP WIEDERHERSTELLEN. Keine automatisierte
unbegrenzte Selbstvervielfaeltigung.

## 94. Lizenz und Daten trennen

Unternehmensdaten und Lizenzstatus sind logisch getrennt zu behandeln. Ein
Kunde muss seine eigenen Unternehmensdaten sichern und wiederherstellen
koennen, ohne dadurch automatisch zusaetzliche Produktlizenzen zu erzeugen.

BACKUP DER UNTERNEHMENSDATEN darf moeglich sein. KOPIE DER LIZENZIERTEN
PROGRAMMINSTANZ darf daraus jedoch keine neue lizenzierte Produktinstanz
erzeugen.

## 95. Lizenzverletzung

Bei ungueltiger oder manipulierter Lizenz: keine Daten loeschen,
Unternehmensdaten nicht beschaedigen, keine Daten verschluesseln oder
sperren, verstaendliche Meldung anzeigen - beispielsweise „Fuer diese
Produktinstanz wurde keine gueltige Lizenz gefunden."

Danach duerfen beispielsweise angeboten werden: Lizenzinformationen anzeigen,
Supportinformationen, Aktivierung, Datenexport. Die Anwendung darf niemals
Kundendaten als Sanktion beschaedigen.

## 96. Testfaelle fuer Lizenzierung

Vor COMMERCIAL READY mindestens testen:

* TEST 1 Original lizenzierte SSD → Anwendung startet.
* TEST 2 Programmordner auf zweite SSD kopieren → zweite Instanz wird nicht
  automatisch als gueltig lizenziert.
* TEST 3 Lizenzdatei veraendern → Signaturpruefung schlaegt fehl.
* TEST 4 Ohne Internet starten → gueltige Offline-Lizenz funktioniert.
* TEST 5 Lizenzdatei fehlt → verstaendliche Lizenzmeldung.
* TEST 6 Defekte SSD durch neue legitime Instanz ersetzen → kontrollierter
  Wiederherstellungs-/Lizenztransfer moeglich.
* TEST 7 Unternehmensdaten aus Backup wiederherstellen → Daten werden
  wiederhergestellt, ohne zusaetzliche Lizenz zu erzeugen.

## 97. Commercial-Ready-Anforderung Lizenzierung

Der Status COMMERCIAL READY darf nicht vergeben werden, solange:
Lizenzmodell nicht definiert, Lizenzpruefung nicht implementiert,
Offline-Lizenzpruefung nicht getestet, Kopiertest nicht durchgefuehrt,
Manipulationstest nicht durchgefuehrt, Ersatz-/Wiederherstellungsprozess
nicht definiert oder Lizenzbedingungen nicht dokumentiert sind.
