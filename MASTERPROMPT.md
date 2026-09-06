# Masterprompt - Portabler KI-Mitarbeiter

**Verbindlicher Gesamtauftrag** · Referenzimplementierung: Portabler
KI-Buchhalter, Produktname **PORTIVA** · Fassung 3.0 zuzueglich der
Erweiterung um die Abschnitte 58 bis 97 (kommerzielle Produktperspektive und
Lizenzierung) und der nachgereichten Erweiterungen E1 bis E6 in Teil 4
(Marke, Betriebsmodi und Wissenssynchronisierung, Fachfragen ohne
Unternehmensdaten, Artefakterzeugung, Plugin-System, Antwortqualitaet).

---

## Hinweis zur Fassung dieses Dokuments

Der Auftrag wurde urspruenglich im Gespraech uebergeben. Damit der
Projektstand nach Masterprompt 45 **ohne den Chat** wiederherstellbar ist,
liegt er hier auf dem Datentraeger.

* **Abschnitte 58 bis 97** sind woertlich so wiedergegeben, wie sie uebergeben
  wurden.
* **Teil 4 (E1 bis E6)** enthaelt die spaeter nachgereichten Erweiterungen,
  ebenfalls wortgetreu.
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

---

# TEIL 4 - ERWEITERUNGEN DES AUFTRAGS

## Hinweis zu Teil 4

Die folgenden Abschnitte wurden **nach** der urspruenglichen Uebergabe
nachgereicht. Sie sind Bestandteil des verbindlichen Auftrags und hier
wortgetreu wiedergegeben; geaendert ist nur die Schreibweise der Umlaute
(ae, oe, ue, ss), wie sie in diesem Verzeichnis durchgehend verwendet wird,
sowie die Auszeichnung der Ueberschriften.

Die Erweiterungen tragen eine eigene Zaehlung. Damit sie sich nicht mit den
Abschnitten 1 bis 97 vermischt, sind sie hier als **E1** bis **E6** gefuehrt;
die Zahl hinter dem Punkt ist die Nummer aus der jeweiligen Ergaenzung. Bei
E5 ist zusaetzlich die Originalzaehlung 98 bis 123 vermerkt, weil der Auftrag
sie selbst so nummeriert hat.

E3 ist der einzige Abschnitt, der nicht als foermliche Ergaenzung uebergeben
wurde, sondern als Anforderung im Gespraech. Der uebergebene Wortlaut steht
dort als Zitat; darunter steht, was daraus fuer die Anwendung folgt.

Wo eine Erweiterung umgesetzt und geprueft ist, steht in
`ANFORDERUNGSNACHWEIS.md`.

---

## E1 - Marke und Erscheinungsbild PORTIVA

ERGAENZUNG ZUM PORTIVA-MASTERPROMPT
THEMA: VERBINDLICHE IMPLEMENTIERUNG DES FINALEN PORTIVA-LOGOS

WICHTIG:

Zusammen mit diesem Prompt erhaeltst Du das finale offizielle
PORTIVA-Logo als Bilddatei.

Dieses Bild ist das verbindliche Originalbranding der Software.

Verwende exakt dieses Logo.

Das Logo darf technisch:

- skaliert werden
- fuer unterschiedliche GUI-Groessen optimiert werden
- in PNG / ICO / SVG oder andere technisch erforderliche Formate
  ueberfuehrt werden, soweit dies sauber moeglich ist
- mit transparentem Hintergrund technisch aufbereitet werden
- als App-/Fenster-/Taskleistenicon abgeleitet werden

NICHT erlaubt:

- neues Logo entwerfen
- Logo neu interpretieren
- Farben eigenmaechtig veraendern
- Schriftzug PORTIVA veraendern
- Proportionen veraendern
- Symbole hinzufuegen oder entfernen
- ein aehnliches Ersatzlogo verwenden

Das beigefuegte Bild ist die visuelle Referenz.

### E1.1 MARKE

Verbindlicher Markenname:

PORTIVA

Verbindlicher Claim:

Portable KI-Mitarbeiter-Plattform

Der Mitarbeitername wird dynamisch aus dem aktiven Berufsprofil geladen.

Beispiele:

PORTIVA - Buchhalter
PORTIVA - Controller
PORTIVA - Rechtsabteilung
PORTIVA - Einkauf

PORTIVA ist fest.

Der Profilname ist dynamisch.

### E1.2 ORIGINALDATEI IM PROJEKT SPEICHERN

Speichere die beigefuegte Originaldatei unveraendert im Projekt.

Empfohlene Struktur:

assets/
    branding/
        original/
            portiva_logo_original.png
        portiva_logo_primary.png
        portiva_logo_light.png
        portiva_logo_dark.png
        portiva_icon.png
        portiva_icon.ico

Die Originaldatei darf nicht ueberschrieben werden.

Abgeleitete Varianten muessen nachvollziehbar daraus erzeugt werden.

### E1.3 PORTABLE PFADLOGIK

Keine absoluten Laufwerkspfade fuer Branding-Dateien verwenden.

Branding ausschliesslich ueber relative Pfade laden.

Beispiel:

assets/branding/portiva_logo_primary.png

Das Branding muss auch funktionieren, wenn die portable SSD spaeter
beispielsweise:

D:\

stattdessen als:

E:\

oder:

F:\

eingebunden wird.

### E1.4 STARTBILDSCHIRM / SPLASHSCREEN

Beim Start von PORTIVA muss ein professioneller Splashscreen erscheinen.

Mindestens anzeigen:

[PORTIVA-LOGO]

PORTIVA

Portable KI-Mitarbeiter-Plattform

Profil:
<dynamischer Profilname>

Beispiel:

Profil: Buchhalter

Optional darunter der tatsaechliche Initialisierungsstatus:

Lizenz
Lokales Modell
Wissensdatenbank
Unternehmensgedaechtnis
Plugins
Internetstatus
Betriebsmodus

Beispiel:

Lizenz: OK
Lokales Modell: OK
Wissensdatenbank: OK
Unternehmensgedaechtnis: OK
Plugins: OK
Betriebsmodus: HYBRID

WICHTIG:

Keine Statuswerte erfinden.

Nur tatsaechlich gepruefte Systemzustaende anzeigen.

### E1.5 HAUPTFENSTER

Nach dem Splashscreen muss das PORTIVA-Branding auch im Hauptfenster
sichtbar sein.

Fenstertitel:

PORTIVA - <Profilname>

Beispiel:

PORTIVA - Buchhalter

Der Profilname darf NICHT hart im Quellcode als "Buchhalter"
eingetragen sein.

Er muss aus dem aktiven Mitarbeiterprofil bzw. profession_manifest
geladen werden.

### E1.6 TITELLEISTE

Soweit durch die verwendete GUI-Technologie unterstuetzt:

Links in der Windows-Titelleiste:

[kleines PORTIVA-Icon]

daneben:

PORTIVA - Buchhalter

bzw. dynamisch:

PORTIVA - <aktiver Profilname>

### E1.7 FENSTERICON

Verwende das PORTIVA-Symbol als offizielles Fenstericon.

Das Icon muss auch bei kleinen Groessen klar erkennbar sein.

Erzeuge dafuer eine geeignete Icon-Variante aus dem Originallogo.

### E1.8 WINDOWS-TASKLEISTE

Das PORTIVA-Icon soll in der Windows-Taskleiste erscheinen.

Kein Standard-Python-, Framework- oder Platzhaltericon verwenden.

### E1.9 EXE-ICON

Soweit technisch moeglich muss das PORTIVA-Icon bereits in die finale
Windows-EXE eingebettet werden.

Bevorzugter finaler Produktname:

PORTIVA.exe

Wenn eine bestehende funktionierende EXE derzeit noch anders heisst,
darf die Umbenennung nur kontrolliert erfolgen.

Keine bestehenden Build-, Test- oder Checkpointpfade beschaedigen.

### E1.10 ICON-DATEI

Erzeuge eine Windows-kompatible:

portiva_icon.ico

mit geeigneten mehreren Aufloesungen.

Beispielsweise:

16x16
24x24
32x32
48x48
64x64
128x128
256x256

Soweit die eingesetzte Technik diese Groessen unterstuetzt.

### E1.11 GUI-BRANDING

Im Hauptfenster soll PORTIVA als feste Plattformmarke erkennbar sein.

Beispielsweise:

[kleines Logo] PORTIVA - Buchhalter

oder eine technisch und gestalterisch gleichwertige Loesung.

PORTIVA bleibt fest.

Nur der Profilname aendert sich.

### E1.12 PROFILWECHSEL

Wenn spaeter ein anderes Mitarbeiterprofil geladen wird:

PORTIVA - Buchhalter

wird beispielsweise zu:

PORTIVA - Controller

oder:

PORTIVA - Rechtsabteilung

Das PORTIVA-Logo und das Grundbranding bleiben unveraendert.

### E1.13 BRANDING-KONFIGURATION

Brand und Profil muessen technisch getrennt sein.

Beispiel:

brand:
    name: PORTIVA
    claim: Portable KI-Mitarbeiter-Plattform
    logo: assets/branding/portiva_logo_primary.png
    icon: assets/branding/portiva_icon.ico

profile:
    display_name: Buchhalter

Fenstertitel automatisch daraus erzeugen:

PORTIVA - Buchhalter

### E1.14 HELLER UND DUNKLER HINTERGRUND

Pruefe, ob das Originallogo auf dem tatsaechlich verwendeten GUI-Hintergrund
ausreichend lesbar ist.

Falls technisch erforderlich, duerfen aus dem Originallogo Varianten
fuer:

- hellen Hintergrund
- dunklen Hintergrund

abgeleitet werden.

Dabei darf die Markenidentitaet nicht veraendert werden.

### E1.15 KEINE ABHAENGIGKEIT VON INTERNET

Das PORTIVA-Branding muss vollstaendig offline funktionieren.

Logo, Splashscreen, Icon und Fenstertitel duerfen keinerlei
Internetverbindung benoetigen.

Alle erforderlichen Assets befinden sich lokal im PORTIVA-Projekt.

### E1.16 KEINE ABHAENGIGKEIT VOM HOST-PC

Branding darf nicht ausschliesslich aus:

- AppData
- Windows-Benutzerprofil
- Temp
- Browsercache

geladen werden.

Alle dauerhaft erforderlichen Branding-Dateien gehoeren zur portablen
PORTIVA-Installation.

### E1.17 FEHLERBEHANDLUNG

Falls ein Branding-Asset fehlt oder beschaedigt ist:

- Anwendung darf nicht unnoetig abstuerzen
- Fehler nachvollziehbar protokollieren
- sinnvollen Fallback verwenden
- keine neue Marke oder Fantasielogo erzeugen

### E1.18 TESTS

Nach Implementierung tatsaechlich testen:

TEST 1
PORTIVA starten.

Erwartung:
Splashscreen zeigt das beigefuegte Originallogo.

TEST 2
Logo auf Verzerrung pruefen.

Erwartung:
korrekte Proportionen.

TEST 3
Hauptfenster oeffnen.

Erwartung:

PORTIVA - <Profilname>

TEST 4
Windows-Fenstericon pruefen.

Erwartung:
PORTIVA-Icon.

TEST 5
Taskleistenicon pruefen.

Erwartung:
PORTIVA-Icon, soweit technisch unterstuetzt.

TEST 6
Finale EXE pruefen.

Erwartung:
PORTIVA-Icon eingebettet.

TEST 7
Profilname wechseln.

Erwartung:
nur Profilname aendert sich.

Beispiel:

PORTIVA - Buchhalter

zu:

PORTIVA - Controller

TEST 8
Internet deaktivieren und PORTIVA starten.

Erwartung:
vollstaendiges Branding funktioniert offline.

TEST 9
Laufwerksbuchstaben aendern.

Beispiel:

D:\ -> E:\

Erwartung:
Logo, Splashscreen und Icons funktionieren weiterhin.

### E1.19 DOKUMENTATION

Aktualisiere soweit vorhanden:

README.md
ARCHITEKTUR.md
PROJEKTSTATUS.md
CHANGELOG.md
BRANDING_KONZEPT.md

Dokumentiere:

- Pfad der Originaldatei
- erzeugte Brandingvarianten
- eingesetzte Icongroessen
- GUI-Einbindung
- Splashscreen
- Fenstertitel
- EXE-Icon
- ausgefuehrte Tests

### E1.20 CHECKPOINT

Nach erfolgreicher Implementierung:

1. Aenderungen speichern.
2. Tests ausfuehren.
3. Testergebnisse pruefen.
4. Git-Commit erstellen.
5. Projektstatus aktualisieren.
6. externen Checkpoint unter:

D:\Ki-Agent\checkpoints

erstellen.

7. tatsaechliche Speicherung verifizieren.

Erst danach diesen Bereich als abgeschlossen melden.

### E1.21 DEFINITION OF DONE

Die PORTIVA-Logo-Integration gilt erst als VERIFIZIERT, wenn:

- das beigefuegte Originallogo unveraendert im Projekt gespeichert ist
- abgeleitete Assets vorhanden sind
- Splashscreen das Logo verwendet
- Hauptfenster PORTIVA verwendet
- Fenstertitel dynamisch lautet:
  PORTIVA - <Profilname>
- Fenstericon umgesetzt ist
- Taskleistenicon umgesetzt ist, soweit technisch unterstuetzt
- finale EXE das PORTIVA-Icon enthaelt, soweit technisch moeglich
- Profilwechsel korrekt funktioniert
- Branding vollstaendig offline funktioniert
- Branding nach Laufwerksbuchstabenwechsel funktioniert
- keine absoluten Pfade verwendet werden
- alle vorgesehenen Tests tatsaechlich ausgefuehrt wurden
- Git-Commit und externer Checkpoint erstellt und verifiziert wurden

Erst dann Status:

VERIFIZIERT


---

## E2 - Betriebsmodi und automatische Wissenssynchronisierung

ERGAENZUNG ZUM MASTERPROMPT
THEMA: BETRIEBSMODI, MANUELLE UMSCHALTUNG UND AUTOMATISCHE WISSENSSYNCHRONISIERUNG

### E2.1 VERBINDLICHE BETRIEBSMODI

Die portable KI-Plattform muss drei klar getrennte Betriebsmodi besitzen:

1. HYBRID
2. OFFLINE
3. ONLINE

Diese Betriebsmodi muessen nicht nur technisch vorhanden sein, sondern
auch vom Benutzer in der grafischen Oberflaeche sichtbar und manuell
umschaltbar sein.

STANDARDMODUS:

HYBRID

### E2.2 HYBRIDMODUS

Im HYBRIDMODUS gilt:

- lokale KI bleibt immer die Grundfunktion
- lokales Fachwissen bleibt verfuegbar
- Unternehmensgedaechtnis bleibt lokal verfuegbar
- lokale Dokumente bleiben verfuegbar
- lokale Plugins bleiben verfuegbar
- Onlinequellen duerfen zusaetzlich verwendet werden
- Wissensupdates duerfen durchgefuehrt werden
- externe Plugins/Connectoren duerfen verwendet werden
- optionale Online-KI darf verwendet werden, sofern freigegeben

Wenn die Internetverbindung ausfaellt:

automatischer Fallback auf OFFLINE-Verhalten

ohne Verlust des lokalen Arbeitsstands.

Sobald Internet wieder vorhanden ist, darf die Anwendung wieder in
HYBRID-Funktionalitaet wechseln.

### E2.3 OFFLINEMODUS

Wenn der Benutzer OFFLINE manuell auswaehlt, gilt verbindlich:

- keine Webrecherche
- keine externen APIs
- keine Cloud-KI
- keine Online-Plugins
- keine automatischen Wissensupdates
- keine externen Connectoren
- kein versteckter Hintergrundzugriff auf das Internet

Erlaubt sind nur:

- lokales KI-Modell
- lokale Wissensdatenbank
- lokales Unternehmensgedaechtnis
- lokale Dokumente
- Offline-Plugins
- lokale Dateierzeugung
- lokale Historie
- lokale Arbeitsstaende

Der OFFLINEMODUS ist eine bewusste Benutzerentscheidung.

Er darf nicht automatisch durch die Anwendung aufgehoben werden.

### E2.4 ONLINEMODUS

Wenn der Benutzer ONLINE auswaehlt, gilt:

- Onlinefunktionen duerfen bevorzugt verwendet werden
- aktuelle Webquellen duerfen verwendet werden
- Online-KI darf verwendet werden, sofern freigegeben
- externe APIs und Connectoren duerfen verwendet werden
- Wissensupdates duerfen durchgefuehrt werden

Wichtig:

Auch im ONLINEMODUS bleiben lokale Daten, lokales Unternehmensgedaechtnis,
lokale Dokumente und lokale Wissensbestaende verfuegbar.

ONLINE bedeutet NICHT:

lokale Funktionen deaktivieren.

### E2.5 MANUELLE MODUSWAHL IN DER GUI

Die grafische Oberflaeche muss eine gut sichtbare Moduswahl besitzen.

Beispiel:

BETRIEBSMODUS

[ HYBRID v ]

Auswahl:

- HYBRID
- OFFLINE
- ONLINE

Alternativ technisch gleichwertige Schaltflaechen.

Der aktuell aktive Modus muss jederzeit sichtbar sein.

### E2.6 BESTAETIGUNG BEIM MODUSWECHSEL

Bei einem Wechsel in OFFLINE muss angezeigt werden:

"Offline-Modus aktiv.

Die Anwendung verwendet ausschliesslich lokale Modelle, Daten,
Dokumente, Plugins und Wissensbestaende.

Es werden keine externen Online-Dienste verwendet."

Bei Wechsel in ONLINE oder HYBRID soll angezeigt werden, dass wieder
Onlinezugriffe moeglich sind.

### E2.7 MODUSWECHSEL PROTOKOLLIEREN

Soweit sinnvoll im lokalen Audit protokollieren:

- vorheriger Modus
- neuer Modus
- Zeitpunkt
- Benutzer
- Grund, falls automatisch gewechselt
- Verbindungsstatus

Keine unnoetige Speicherung personenbezogener Inhalte.

### E2.8 INTERNETSTATUS GETRENNT VOM BETRIEBSMODUS

Wichtig:

BETRIEBSMODUS

und

INTERNETSTATUS

sind getrennte Zustaende.

Beispiel:

Betriebsmodus:
OFFLINE

Internet:
VERFUEGBAR

Trotz vorhandener Internetverbindung darf im manuell gewaehlten
OFFLINEMODUS kein Onlinezugriff erfolgen.

Weiteres Beispiel:

Betriebsmodus:
HYBRID

Internet:
NICHT VERFUEGBAR

Dann arbeitet die Anwendung automatisch lokal weiter.

### E2.9 PERSISTENZ DER MODUSWAHL

Die vom Benutzer gewaehlte Betriebsart soll gespeichert werden.

Beispiel:

Benutzer waehlt OFFLINE.

Programm wird beendet.

Programm wird erneut gestartet.

Erwartung:

OFFLINE bleibt aktiv, bis der Benutzer den Modus wieder aendert.

Der Benutzer darf nicht unbemerkt zurueck in einen Onlinebetrieb
versetzt werden.

### E2.10 AUTOMATISCHE WISSENSSYNCHRONISIERUNG

Die portable KI-Plattform benoetigt ein kontrolliertes System zur
regelmaessigen Aktualisierung der lokalen Wissensbestaende.

Ziel:

Die lokale Offline-Wissensbasis soll durch Online-Aktualisierungen
regelmaessig auf einem moeglichst aktuellen Stand gehalten werden.

Dies gilt nur, wenn:

- Betriebsmodus HYBRID oder ONLINE aktiv ist
- Internetverbindung vorhanden ist
- Anwendung oder freigegebener Updateprozess laeuft
- die betreffende Wissensquelle erreichbar ist

### E2.11 STANDARD-UPDATEINTERVALL

Standardmaessig soll das Fachwissen einmal pro Woche auf Aenderungen
geprueft werden.

STANDARD:

WOECHENTLICH

Die genaue technische Ausfuehrung darf beispielsweise sein:

alle 7 Tage

oder:

ein frei definierter Wochentag.

Die Anwendung soll zusaetzlich unterstuetzen:

- manuell
- taeglich
- woechentlich
- monatlich
- benutzerdefiniert
- deaktiviert

### E2.12 EINSTELLUNGEN FUER WISSENSUPDATES

In der GUI muss eine Einstellung vorgesehen werden.

Beispiel:

WISSEN AKTUALISIEREN

Automatisch:
[ EIN ]

Intervall:
[ Woechentlich v ]

Letzte Aktualisierung:
03.09.2026 18:42

Naechste Pruefung:
10.09.2026

[ JETZT AKTUALISIEREN ]

### E2.13 INKREMENTELLE SYNCHRONISIERUNG

Bei einer Wissensaktualisierung sollen nicht unnoetig saemtliche Quellen
immer vollstaendig neu heruntergeladen werden.

Soweit technisch moeglich, verwende:

- Aenderungsdatum
- Dokumentversion
- Dokument-ID
- ETag
- Last-Modified
- Hash / Pruefsumme
- Veroeffentlichungsdatum

Ablauf:

QUELLENREGISTER LADEN
|
AENDERUNGEN PRUEFEN
|
NUR NEUE / GEAENDERTE INHALTE ABRUFEN
|
ORIGINAL LOKAL SPEICHERN
|
NORMALISIEREN
|
METADATEN AKTUALISIEREN
|
INDEX AKTUALISIEREN
|
INTEGRITAET PRUEFEN
|
NEUEN WISSENSSTAND VEROEFFENTLICHEN

### E2.14 KEIN UNKONTROLLIERTES UEBERSCHREIBEN

Neue Wissensstaende duerfen vorhandene funktionierende Wissensbestaende
nicht unkontrolliert zerstoeren.

Updateprozess:

DOWNLOAD
|
STAGING
|
VALIDIERUNG
|
INDEX-TEST
|
AKTIVIERUNG

Bei Fehler:

ROLLBACK

auf den letzten funktionierenden Wissensstand.

### E2.15 VERSIONIERUNG DES WISSENSSTANDS

Jede erfolgreiche Aktualisierung muss nachvollziehbar sein.

Mindestens speichern:

- Wissensstand-ID
- Datum
- Uhrzeit
- aktualisierte Quellen
- neue Dokumente
- geaenderte Dokumente
- entfernte/veraltete Dokumente
- Fehler
- Pruefsummen
- vorherige Version

Beispiel:

Wissensstand:
2026-09-05

Vorher:
2026-08-29

### E2.16 MANUELLE AKTUALISIERUNG

Der Benutzer muss jederzeit in HYBRID oder ONLINE:

"WISSEN JETZT AKTUALISIEREN"

ausloesen koennen.

Die Anwendung soll anschliessend einen verstaendlichen Bericht anzeigen.

Beispiel:

Aktualisierung abgeschlossen.

12 Quellen geprueft.
3 Aenderungen gefunden.
2 neue Dokumente.
1 Dokument aktualisiert.
0 Fehler.

Neuer Wissensstand:
05.09.2026

### E2.17 VERHALTEN IM OFFLINEMODUS

Im manuell gewaehlten OFFLINEMODUS:

keine automatische Synchronisierung.

Auch dann nicht, wenn physisch eine Internetverbindung vorhanden ist.

Der Benutzer kann angezeigt bekommen:

"Automatische Aktualisierung pausiert - Offline-Modus aktiv."

Nach Rueckkehr in HYBRID oder ONLINE darf geprueft werden, ob ein
ausstehendes Update faellig ist.

### E2.18 AUSSTEHENDE UPDATES NACH OFFLINEPHASE

Beispiel:

letztes Update:
01.09.2026

Intervall:
woechentlich

Anwendung war bis 15.09.2026 offline.

Nach Wechsel in HYBRID:

Die Anwendung erkennt:

Update ueberfaellig.

Sie darf den Benutzer informieren:

"Der lokale Wissensstand wurde seit 14 Tagen nicht aktualisiert.

Jetzt aktualisieren?"

Optional kann bei entsprechender Benutzereinstellung automatisch
aktualisiert werden.

### E2.19 KEINE FALSCHE AKTUALITAETSBEHAUPTUNG

Die KI darf niemals behaupten:

"Mein Wissen ist aktuell."

wenn nicht nachgewiesen ist, wann die lokale Wissensbasis zuletzt
erfolgreich aktualisiert wurde.

Bei Fachantworten soll bei zeitkritischen Themen der lokale
Wissensstand beruecksichtigt werden.

Beispiel:

"Lokaler Wissensstand: 05.09.2026"

### E2.20 QUELLENSPEZIFISCHE UPDATEINTERVALLE

Die Architektur soll erlauben, dass spaeter verschiedene Quellen
unterschiedliche Pruefintervalle erhalten.

Beispiel:

Gesetze:
taeglich / woechentlich

Rechtsprechung:
woechentlich

interne Handbuecher:
monatlich

statische Grundlagen:
seltener

Das allgemeine Standardintervall bleibt:

WOECHENTLICH.

### E2.21 UPDATE-STATUS IN DER GUI

Die Anwendung soll sichtbar anzeigen:

Betriebsmodus:
HYBRID

Internet:
VERFUEGBAR

Wissensstand:
05.09.2026

Letzte Updatepruefung:
05.09.2026 18:42

Naechste Pruefung:
12.09.2026

Update-Status:
AKTUELL

oder beispielsweise:

UPDATE FAELLIG

UPDATE LAEUFT

UPDATE FEHLGESCHLAGEN

OFFLINE - UPDATE PAUSIERT

### E2.22 TESTFAELLE BETRIEBSMODI

Mindestens real testen:

TEST 1

HYBRID + Internet vorhanden.

Erwartung:
lokale und Onlinefunktionen verfuegbar.

TEST 2

HYBRID + Internet trennen.

Erwartung:
lokaler Betrieb laeuft weiter.

TEST 3

OFFLINE manuell waehlen, obwohl Internet vorhanden ist.

Erwartung:
kein Onlinezugriff.

TEST 4

Programm im OFFLINEMODUS schliessen und neu starten.

Erwartung:
OFFLINE bleibt aktiv.

TEST 5

ONLINE waehlen.

Erwartung:
Onlinefunktionen verfuegbar, lokale Funktionen weiterhin verfuegbar.

TEST 6

Offline -> Hybrid wechseln.

Erwartung:
Onlinefunktionen werden wieder verfuegbar.

### E2.23 TESTFAELLE WISSENSSYNCHRONISIERUNG

Mindestens real testen:

TEST 1

manuelles Wissensupdate.

TEST 2

automatisches woechentliches Update.

TEST 3

keine Aenderungen vorhanden.

TEST 4

neue Quelle / neues Dokument.

TEST 5

geaendertes Dokument.

TEST 6

Netzausfall waehrend Update.

TEST 7

fehlerhafte Quelldatei.

TEST 8

Rollback nach fehlgeschlagenem Update.

TEST 9

Offline-Modus verhindert Update.

TEST 10

ueberfaelliges Update nach laengerer Offlinephase wird erkannt.

TEST 11

neuer Wissensstand ist danach ohne Internet verwendbar.

### E2.24 VERBINDLICHE DEFINITION OF DONE

Diese Erweiterung gilt erst als vollstaendig umgesetzt, wenn:

- HYBRID manuell auswaehlbar ist
- OFFLINE manuell auswaehlbar ist
- ONLINE manuell auswaehlbar ist
- Moduswahl sichtbar ist
- Moduswahl persistent gespeichert wird
- OFFLINE tatsaechlich saemtliche Onlinezugriffe blockiert
- HYBRID bei Netzausfall lokal weiterarbeitet
- Wissensupdates manuell moeglich sind
- automatisches Standardintervall WOECHENTLICH vorhanden ist
- Intervall konfigurierbar ist
- Updates inkrementell arbeiten, soweit Quelle dies erlaubt
- Wissensstand versioniert wird
- Rollback funktioniert
- ueberfaellige Updates erkannt werden
- aktualisiertes Wissen anschliessend offline verfuegbar ist
- saemtliche genannten Tests tatsaechlich durchgefuehrt wurden

Erst dann darf dieser Funktionsbereich als:

VERIFIZIERT

bezeichnet werden.


---

## E3 - Fachfragen ohne Unternehmensdaten

Woertlich uebergeben:

> Wichtig fuer mich waere auch, das man die KI in deren Fachbereich (also in
> dem Fall Buchhalterisch) dennoch befragen kann auch ohne das man ihr die
> Unternehmensdaten uebermittelt hat. Geht das, wenn ja wie? Erweitere die
> Anleitung ebenfalls um das. und aendere den Masterpromt um diese aktion.

Daraus folgt verbindlich:

* Das Fachwissen des Mitarbeiters muss **ohne jede Angabe zum Unternehmen**
  nutzbar sein. Weder das Onboarding noch ein gefuelltes
  Unternehmensgedaechtnis duerfen Voraussetzung fuer eine Fachfrage sein.
* Wo eine Antwort ohne Unternehmensangaben fachlich nicht eindeutig sein
  kann, ist das zu sagen - mit Nennung der fehlenden Angabe und, soweit
  moeglich, der Antwort fuer die ueblichen Faelle. Es darf **nichts**
  ueber das Unternehmen angenommen werden.
* Die Anwendung darf in diesem Betrieb nichts ueber das Unternehmen
  speichern, was der Benutzer nicht ausdruecklich bestaetigt hat.
* Die Bedienungsanleitung muss diesen Betrieb erklaeren.

---

## E4 - Datei- und Artefakterzeugung (Artifact Engine)

Nachgereicht mit dem Hinweis "noch im masterprompt ergaenzen".

NEU: DATEI- UND ARTEFAKTERZEUGUNG
======================================================================

Die portable KI-Plattform muss nicht nur Dateien lesen und analysieren,
sondern auch eigenstaendig Dateien und Arbeitsergebnisse erzeugen koennen.

Dies muss offline funktionieren, soweit das jeweilige Dateiformat lokal
erzeugbar ist.

Mindestens unterstuetzte Ausgabeformate:

- XLSX
- CSV
- DOCX
- PPTX
- PDF
- TXT
- Markdown
- JSON

Weitere Formate muessen ueber Plugins bzw. File-Handler ergaenzbar sein.

### E4 - ARTIFACT ENGINE

Der Universal-Core soll eine allgemeine Artifact-/Dateiausgabe-Engine
besitzen.

Diese uebernimmt mindestens:

- Dateierzeugung
- Vorlagenverarbeitung
- Dateinamen
- Speicherort
- Versionierung
- Metadaten
- Ueberschreibschutz
- sichere Speicherung
- Export
- Fehlerbehandlung

### E4 - OFFLINE-DATEIERZEUGUNG

Die Erstellung ueblicher Office- und Dokumentdateien darf nicht zwingend
eine Internetverbindung voraussetzen.

Soweit technisch moeglich, darf auch keine installierte Microsoft-
Office-Version Voraussetzung sein.

Die Plattform soll geeignete lokale Bibliotheken bzw. Komponenten
verwenden koennen, um die Dateiformate direkt zu erzeugen.

### E4 - BERUFSSPEZIFISCHE AUSGABEN

Jedes Berufsprofil darf definieren, welche Ausgabeformate es benoetigt.

Beispiele:

BUCHHALTER:
- Excel-Auswertungen
- Buchungslisten
- PDF-Berichte
- Word-Dokumentationen

CONTROLLER:
- Excel-Dashboards
- KPI-Berichte
- PowerPoint-Managementpraesentationen
- PDF-Reports

RECHTSABTEILUNG:
- Word-Schreiben
- Vertragsentwuerfe
- PDF-Dokumente

PROJEKTMANAGER:
- Excel-Projektplaene
- Word-Berichte
- PowerPoint-Statuspraesentationen

### E4 - ONLINE-ERWEITERUNG

Bei vorhandener Verbindung duerfen Plugins zusaetzliche Funktionen
bereitstellen, z. B.:

- Datei in OneDrive speichern
- Datei in SharePoint speichern
- Datei in Google Drive speichern
- per E-Mail versenden
- in Cloudformat konvertieren
- gemeinsam freigeben

Die lokale Dateierzeugung bleibt davon unabhaengig.

### E4 - PLUGIN-ERWEITERBARKEIT

Neue Ausgabeformate sollen ueber Plugins ergaenzt werden koennen.

Beispiel:

FILE_HANDLER_PPTX
FILE_HANDLER_DWG
FILE_HANDLER_XML
FILE_HANDLER_CUSTOM

Der Core darf fuer ein neues Dateiformat nicht neu gebaut werden muessen.



Noch ergaenzen


---

## E5 - Allgemeines Plugin- und Erweiterungssystem

Nachgereicht mit dem Hinweis "noch ergaenzen". Der Auftrag nummeriert diese Abschnitte selbst mit 98 bis 123; die Nummer ist hier beibehalten.

### E5.98 ALLGEMEINES PLUGIN- UND ERWEITERUNGSSYSTEM

Die portable KI-Plattform muss ein allgemeines, modulares und innerhalb
der Anwendung installierbares Plugin-System besitzen.

Dieses Plugin-System darf NICHT auf E-Mail-Dienste, Cloudspeicher oder
ERP-Systeme beschraenkt sein.

Plugins sollen grundsaetzlich neue Faehigkeiten zur Plattform hinzufuegen
koennen, ohne dass der Portable-KI-Core dafuer neu programmiert oder
neu gebaut werden muss.

Moegliche Plugin-Kategorien:

- externe Dienste
- E-Mail
- Kalender
- Cloudspeicher
- ERP
- CRM
- DMS
- Datenbanken
- Dateiverarbeitung
- PDF-Verarbeitung
- OCR
- Tabellenverarbeitung
- Automationen
- Recherchewerkzeuge
- APIs
- lokale Tools
- Fachmodule
- zusaetzliche Wissensquellen
- zusaetzliche KI-Modelle
- Unternehmenssysteme
- Kommunikationsdienste
- weitere zukuenftige Erweiterungen

Grundprinzip:

PORTABLE-KI-CORE
|
PLUGIN-API
|
INSTALLIERBARE PLUGINS
|
NEUE FAEHIGKEITEN

### E5.99 INSTALLATION DIREKT IN DER ANWENDUNG

Die grafische Anwendung muss langfristig eine integrierte
Plugin-Verwaltung besitzen.

Beispiel:

EINSTELLUNGEN
-> PLUGINS / ERWEITERUNGEN

Dort sollen mindestens moeglich sein:

- verfuegbare Plugins anzeigen
- Plugin installieren
- Plugin aus lokaler Datei installieren
- Plugin aktivieren
- Plugin deaktivieren
- Plugin aktualisieren
- Plugin deinstallieren
- Berechtigungen anzeigen
- Berechtigungen aendern
- Plugin-Version anzeigen
- Kompatibilitaet anzeigen
- Hersteller anzeigen
- Sicherheitsstatus anzeigen

Ein normaler Anwender soll kein Terminal benoetigen.

### E5.100 PLUGIN-PAKETFORMAT

Plugins sollen als klar definierte installierbare Pakete vorliegen.

Beispielsweise:

*.pkiplugin

oder ein technisch geeignetes vergleichbares Paketformat.

Jedes Plugin-Paket muss mindestens enthalten:

- Plugin-Code
- Manifest
- Version
- Plugin-ID
- Hersteller
- Beschreibung
- benoetigte Core-Version
- benoetigte Berechtigungen
- benoetigte Abhaengigkeiten
- Online-/Offline-Status
- Signatur
- Pruefsumme

### E5.101 PLUGIN-MANIFEST

Jedes Plugin benoetigt ein maschinenlesbares Manifest.

Beispielsweise:

manifest.json

Mindestens enthalten:

- eindeutige Plugin-ID
- Name
- Version
- Hersteller
- Beschreibung
- Kategorie
- benoetigte Core-Version
- benoetigte Berechtigungen
- bereitgestellte Tools
- bereitgestellte Aktionen
- benoetigte Netzwerkverbindungen
- unterstuetzte Dateitypen
- Schreib-/Leserechte
- benoetigte APIs
- Lizenz
- Signaturinformationen

### E5.102 PLUGIN-API / SDK

Der Portable-KI-Core muss eine klar definierte Plugin-Schnittstelle
bereitstellen.

Plugins duerfen den Core nicht ueber beliebige interne Zugriffe veraendern.

Die Plugin-API soll definieren:

- welche Tools ein Plugin bereitstellen darf
- wie Eingaben uebergeben werden
- wie Ergebnisse zurueckgegeben werden
- wie Dateien uebergeben werden
- wie Berechtigungen geprueft werden
- wie Fehler behandelt werden
- wie Logging erfolgt
- wie Plugin-Status abgefragt wird

Langfristig soll daraus ein dokumentiertes Plugin-SDK entstehen koennen.

Ziel:

Neue Plugins entwickeln, ohne den Core zu veraendern.

### E5.103 TOOL-REGISTRIERUNG

Plugins sollen neue Tools beim KI-Mitarbeiter registrieren koennen.

Beispiel:

Plugin:
PDF Analyzer

stellt Tools bereit:

- PDF lesen
- Tabellen extrahieren
- Dokument klassifizieren


Plugin:
Microsoft 365

stellt Tools bereit:

- E-Mail suchen
- E-Mail lesen
- Entwurf erstellen
- Kalender lesen


Plugin:
SAP

stellt Tools bereit:

- Beleg suchen
- Buchungsdaten lesen
- Stammdaten lesen


Der KI-Core entscheidet anhand:

- Aufgabe
- Berechtigungen
- Plugin-Verfuegbarkeit
- Sicherheitsregeln

ob ein Tool verwendet werden darf.

### E5.104 PLUGIN-KATEGORIEN

Unterstuetze mindestens folgende logische Plugin-Kategorien:

CONNECTOR
Verbindung zu externen Systemen.

TOOL
Neue lokale oder externe Faehigkeit.

KNOWLEDGE
Neue Wissensquelle oder Fachwissenspaket.

MODEL
Zusaetzliches KI- oder Embedding-Modell.

FILE_HANDLER
Unterstuetzung weiterer Dateiformate.

AUTOMATION
Wiederkehrende oder ereignisgesteuerte Prozesse.

UI_EXTENSION
Zusaetzliche Benutzeroberflaechenfunktionen.

DOMAIN_MODULE
Fachliche Erweiterung eines Mitarbeiters.

### E5.105 OFFLINE- UND ONLINE-PLUGINS

Plugins muessen deklarieren, ob sie:

OFFLINE

ONLINE

oder:

HYBRID

funktionieren.

Beispiel:

PDF-Verarbeitungsplugin:
OFFLINE

Gmail-Plugin:
ONLINE

Lokales Excel-Analyseplugin:
OFFLINE

ERP-Connector:
ONLINE / Unternehmensnetzwerk

Ein nicht verfuegbares Online-Plugin darf die Grundanwendung nicht
beeintraechtigen.

### E5.106 PLUGIN-BERECHTIGUNGSSYSTEM

Plugins duerfen keine uneingeschraenkten Rechte erhalten.

Jedes Plugin muss nur die Berechtigungen anfordern duerfen, die es
wirklich benoetigt.

Beispiele:

FILES_READ

FILES_WRITE

COMPANY_MEMORY_READ

COMPANY_MEMORY_WRITE

EMAIL_READ

EMAIL_DRAFT

EMAIL_SEND

CALENDAR_READ

CALENDAR_WRITE

NETWORK_ACCESS

ERP_READ

ERP_WRITE

DATABASE_READ

DATABASE_WRITE

MODEL_ACCESS

CAMERA_ACCESS

MICROPHONE_ACCESS


Vor Installation oder erstmaliger Nutzung muss der Benutzer erkennen
koennen, welche Rechte ein Plugin verlangt.

### E5.107 LESE- UND SCHREIBRECHTE

Schreibende Aktionen sind besonders zu behandeln.

Standardmaessig:

READ ONLY

soweit sinnvoll.

Schreibende Funktionen wie:

- E-Mail senden
- ERP-Daten veraendern
- Dateien loeschen
- Datenbanken veraendern
- Unternehmensgedaechtnis veraendern
- Termine erstellen
- externe Aktionen ausloesen

benoetigen explizite Freigaben.

### E5.108 PLUGIN-ISOLATION / SANDBOXING

Plugins sind potenziell sicherheitskritischer Fremdcode.

Sie duerfen deshalb nicht uneingeschraenkt innerhalb des KI-Core laufen.

Pruefe geeignete Mechanismen fuer:

- Prozessisolation
- Sandbox
- eingeschraenkte Dateizugriffe
- eingeschraenkte Netzwerkzugriffe
- definierte API-Zugriffe
- Ressourcenlimits
- Timeout
- Fehlerisolation

Ein fehlerhaftes Plugin darf nach Moeglichkeit nicht den gesamten
KI-Mitarbeiter zum Absturz bringen.

### E5.109 KRYPTOGRAFISCHE PLUGIN-SIGNATUREN

Kommerziell eingesetzte Plugins sollen kryptografisch signiert sein.

Vor Installation pruefen:

- Signatur
- Hersteller
- Paketintegritaet
- Version
- Kompatibilitaet

Manipulierte Pakete duerfen nicht unbemerkt installiert werden.

### E5.110 PLUGIN-KOMPATIBILITAET

Vor Installation muss geprueft werden:

- Core-Version
- Betriebssystem
- benoetigte Runtime
- benoetigte Hardware
- Abhaengigkeiten
- Plugin-Version
- Konflikte

Inkompatible Plugins duerfen nicht einfach installiert werden.

### E5.111 PLUGIN-ABHAENGIGKEITEN

Plugins duerfen Abhaengigkeiten besitzen.

Diese muessen jedoch:

- versioniert
- nachvollziehbar
- lizenzrechtlich geprueft
- sicher
- reproduzierbar

verwaltet werden.

Abhaengigkeiten duerfen nicht unkontrolliert systemweit auf dem Ziel-PC
installiert werden.

Sie sollen soweit moeglich innerhalb der portablen Plattform verwaltet
werden.

### E5.112 PLUGIN-UPDATES

Plugins benoetigen ein eigenes Update-System.

Plugin-Updates muessen:

- versioniert
- signiert
- auf Integritaet geprueft
- kompatibel
- ruecksetzbar

sein.

Ein fehlerhaftes Plugin-Update darf die gesamte Plattform nicht
beschaedigen.

### E5.113 PLUGIN-DEINSTALLATION

Plugins muessen sauber deinstallierbar sein.

Dabei muessen unterschieden werden:

- Plugin-Code
- Plugin-Konfiguration
- Plugin-Cache
- Plugin-Zugangsdaten
- Plugin-Daten

Der Benutzer soll entscheiden koennen, ob Plugin-Daten bei
Deinstallation:

- behalten
- exportiert
- geloescht

werden.

### E5.114 VERBUNDENE DIENSTE ALS PLUGINS

Externe Dienste werden als spezielle Plugins umgesetzt.

Beispiele:

- Gmail
- Outlook / Microsoft 365
- Google Calendar
- Outlook Calendar
- Google Drive
- OneDrive
- SharePoint
- Teams
- Slack
- SAP
- Wilken
- DATEV
- CRM-Systeme
- DMS-Systeme

Fuer Google-Dienste vorzugsweise offizielle Google-APIs und OAuth.

Fuer Microsoft-365-Dienste vorzugsweise Microsoft Graph und geeignete
offizielle Authentifizierungsverfahren.

### E5.115 SICHERE AUTHENTIFIZIERUNG

Plugins duerfen Passwoerter, Tokens oder API-Schluessel nicht ungeschuetzt
speichern.

Bevorzugen:

- OAuth
- Windows Credential Manager
- verschluesselte Tokenablage
- sichere Secret-Stores

Zugangsdaten muessen vom normalen Unternehmensgedaechtnis getrennt sein.

### E5.116 PLUGIN-KATALOG / PLUGIN-STORE

Die Architektur soll langfristig einen eigenen freigegebenen
Plugin-Katalog ermoeglichen.

Beispiel:

PLUGIN-KATALOG

-> Gmail

-> Microsoft 365

-> SAP Connector

-> PDF Advanced

-> OCR

-> Excel Tools

-> DATEV

-> Branchenmodul X


Der Katalog darf spaeter lokal, online oder kombiniert bereitgestellt
werden.

Ein oeffentlicher Store ist fuer das MVP nicht zwingend erforderlich.

Die Architektur soll ihn jedoch ermoeglichen.

### E5.117 INSTALLATION AUS LOKALER DATEI

Da die Plattform offlinefaehig sein soll, muss ein Plugin auch aus einer
lokalen signierten Plugin-Datei installiert werden koennen.

Beispiel:

Plugin-Datei auf USB/SSD kopieren.

|

PLUGINS

|

AUS DATEI INSTALLIEREN

|

Signatur pruefen.

|

Berechtigungen anzeigen.

|

Installieren.

Dadurch koennen Plugins auch in abgeschotteten Unternehmensumgebungen
verteilt werden.

### E5.118 PLUGIN-AUDIT

Plugin-Aktionen sollen nachvollziehbar sein.

Soweit sinnvoll dokumentieren:

- Plugin
- Version
- Aktion
- Zeitpunkt
- Benutzer
- verwendete Berechtigung
- Freigabestatus
- Ergebnis
- Fehler

Keine unnoetige Speicherung sensibler Inhalte.

### E5.119 PLUGIN-LIZENZIERUNG

Plugins koennen spaeter Bestandteil unterschiedlicher Produkt- und
Lizenzmodelle sein.

Beispielsweise:

PORTABLER BUCHHALTER
Basislizenz

+

MICROSOFT-365-PLUGIN

+

SAP-PLUGIN

+

OCR-PRO-PLUGIN


Die Plugin-Architektur muss deshalb mit dem allgemeinen
Lizenzierungssystem der Plattform zusammenarbeiten koennen.

Ein Plugin darf beispielsweise nur aktiviert werden, wenn die
Produktlizenz dieses Modul erlaubt.

### E5.120 PLUGIN-KUNDENTRENNUNG

Plugin-Daten muessen strikt dem jeweiligen Unternehmen bzw. Kunden
zugeordnet sein.

Daten eines Kunden duerfen nicht in:

- andere Kundeninstanzen
- andere Unternehmensprofile
- allgemeines Fachwissen

uebertragen werden.

### E5.121 PLUGIN-TESTS

Vor Freigabe eines Plugins mindestens testen:

- Installation
- Signaturpruefung
- Aktivierung
- Deaktivierung
- Update
- Rollback
- Deinstallation
- Berechtigungen
- Offline-Verhalten
- Online-Verhalten
- Fehlerbehandlung
- Absturzisolation
- Kundentrennung
- Lizenzpruefung
- Token-Schutz
- Datenloeschung

### E5.122 COMMERCIAL-READY-GATE FUER PLUGINS

Ein Plugin darf fuer Kunden erst als:

COMMERCIAL READY

gelten, wenn mindestens geprueft wurden:

- Funktion
- Sicherheit
- Berechtigungen
- Datenschutz
- Lizenz
- Kompatibilitaet
- Update
- Deinstallation
- Fehlerisolation
- Audit
- Kundentrennung
- Authentifizierung
- Wiederherstellung

### E5.123 VERBINDLICHES PLUGIN-ENDZIEL

Die portable KI-Plattform soll langfristig wie eine erweiterbare
Anwendungsplattform funktionieren.

Der Anwender soll innerhalb der grafischen Oberflaeche zusaetzliche
Faehigkeiten installieren koennen, ohne den KI-Core neu bauen zu muessen.

Ziel:

PORTABLE_KI.exe

|

PLUGINS

|

PLUGIN INSTALLIEREN

|

BERECHTIGUNGEN PRUEFEN

|

PLUGIN AKTIVIEREN

|

KI BESITZT NEUE FAEHIGKEIT

Plugins koennen dabei sowohl:

- lokale Faehigkeiten
- externe Dienste
- Unternehmenssysteme
- Fachmodule
- zusaetzliche Modelle
- Automationen
- Datenquellen

bereitstellen.

Die Plugin-Architektur ist ein fester Bestandteil der langfristigen
Plattform und darf nicht auf E-Mail- oder ERP-Connectoren reduziert
werden.


---

## E6 - Qualitative KI-Antworten und Antwortdarstellung

ERGAENZUNG ZUM PORTIVA-MASTERPROMPT
THEMA: QUALITATIVE KI-ANTWORTEN, RAG-SYNTHESE UND CHATGPT-AEHNLICHE ANTWORTDARSTELLUNG

### E6.1 AUSGANGSPROBLEM

Die aktuelle PORTIVA-Implementierung liefert bei Fachfragen teilweise
lediglich rohe Retrieval-Treffer bzw. Fundstellen aus der lokalen
Wissensdatenbank.

Beispiel des aktuellen Verhaltens:

Benutzer stellt eine normale fachliche Frage.

PORTIVA zeigt:

- Hinweis auf fehlendes Sprachmodell
- mehrere rohe Quellen-Chunks
- teilweise abgeschnittene Textpassagen
- technische Wissensstandinformationen

Es entsteht jedoch keine eigentliche fachlich formulierte Antwort.

Dieses Verhalten erfuellt NICHT das gewuenschte Endprodukt.

PORTIVA soll sich fuer den Benutzer wie ein moderner KI-Assistent
verhalten.

Der Benutzer stellt eine Frage.

PORTIVA liefert eine verstaendliche, zusammenhaengende und fachlich
begruendete Antwort.

Quellen und technische Retrieval-Ergebnisse dienen der KI intern als
Grundlage und duerfen nicht die eigentliche Antwort ersetzen.

### E6.2 VERBINDLICHER ANTWORTWORKFLOW

Fuer normale Fachfragen muss der Ablauf grundsaetzlich sein:

BENUTZERFRAGE
|
FRAGE ANALYSIEREN
|
UNTERNEHMENSKONTEXT LADEN
|
LOKALE WISSENSSUCHE / RAG
|
RELEVANTE QUELLEN AUSWAEHLEN UND RANKEN
|
KONTEXT FUER DAS SPRACHMODELL AUFBEREITEN
|
LOKALES ODER FREIGEGEBENES ONLINE-MODELL AUFRUFEN
|
QUALITATIVE FACHANTWORT ERZEUGEN
|
ANTWORT AUFBEREITEN
|
QUELLEN SEPARAT DARSTELLEN
|
WISSENSSTAND / UNSICHERHEIT KENNZEICHNEN

Der Benutzer darf nicht hauptsaechlich die Rohdaten des Retrievalsystems
sehen.

### E6.3 DAS SPRACHMODELL MUSS DIE QUELLEN VERARBEITEN

Die durch RAG gefundenen Textstellen muessen als Kontext in den
Modellaufruf einfliessen.

Das Modell soll aus diesem Kontext:

- relevante Informationen extrahieren
- Zusammenhaenge herstellen
- Widersprueche erkennen
- Fachlogik anwenden
- Unternehmenskontext beruecksichtigen
- eine natuerliche Antwort formulieren
- Unsicherheiten benennen
- Quellenbezug erhalten

Die Quellen duerfen nicht einfach nur untereinander ausgegeben werden.

### E6.4 ANTWORTQUALITAET

Die normale Antwort soll qualitativ ungefaehr der Nutzung eines modernen
KI-Assistenten entsprechen.

Sie soll:

- natuerlich formuliert
- direkt
- verstaendlich
- fachlich strukturiert
- auf die konkrete Frage bezogen
- nicht unnoetig technisch
- nicht voller Rohdaten
- nicht voller interner Systeminformationen

sein.

Beispiel Benutzerfrage:

"Wenn ich Dir eine Frage zu einem buchhalterischen Ablauf sende, kannst
Du mir dabei helfen?"

Gewuenschte Antwort ungefaehr:

"Ja. Du kannst mir den buchhalterischen Sachverhalt einfach schildern.
Ich pruefe ihn anhand des lokal verfuegbaren Fachwissens und des fuer Dein
Unternehmen hinterlegten Kontexts.

Wenn fuer eine belastbare Beurteilung Informationen fehlen, frage ich
gezielt nach.

Bei fachlichen Themen kann ich Dir beispielsweise bei Kontierung,
Rechnungspruefung, Umsatzsteuer, Buchungsvorschlaegen oder
Plausibilitaetspruefungen helfen.

Bei zeitkritischen steuerlichen Fragen beruecksichtige ich den verfuegbaren
Wissensstand und zeige Dir die zugrunde liegenden Quellen an."

NICHT gewuenscht:

acht rohe Quellenausschnitte als Hauptantwort.

### E6.5 ANTWORT UND QUELLEN TRENNEN

Die GUI soll logisch zwischen:

ANTWORT

und:

QUELLEN

unterscheiden.

Hauptbereich:

fertig formulierte KI-Antwort.

Separater Quellenbereich:

- verwendete Quelle
- Titel
- relevante Fundstelle
- Datum
- gegebenenfalls Paragraph
- Quelle oeffnen / anzeigen

Die bereits vorhandene rechte Seitenleiste:

"Quellen der letzten Antwort"

kann dafuer verwendet und verbessert werden.

Die linke Hauptansicht darf nicht zusaetzlich saemtliche Quellen-Chunks
ungefiltert wiederholen.

### E6.6 ROHE RETRIEVAL-TREFFER NUR OPTIONAL

Rohe Retrieval-Treffer sind technische Detailinformationen.

Sie duerfen standardmaessig NICHT Bestandteil der normalen Benutzerantwort
sein.

Optional kann eine Funktion angeboten werden:

"Recherche-Details anzeigen"

oder:

"Gefundene Fundstellen anzeigen"

Erst dort duerfen:

- Chunks
- Scores
- Dokument-IDs
- technische Retrieval-Daten

angezeigt werden.

### E6.7 MARKDOWN / FORMATIERUNG

PORTIVA soll Antworten sauber darstellen.

Unterstuetze mindestens:

- Absaetze
- Ueberschriften
- Aufzaehlungen
- nummerierte Listen
- Fettdruck
- Tabellen, soweit sinnvoll
- hervorgehobene Hinweise
- Quellenverweise

Markdown-Zeichen wie:

**
#
-

duerfen nicht einfach roh im Benutzerfenster erscheinen, wenn die GUI
Markdown unterstuetzt.

Entweder:

Markdown korrekt rendern

oder:

in GUI-kompatible Formatierung umwandeln.

### E6.8 BERUFSSPEZIFISCHE ANTWORTSTRUKTUR

Das Mitarbeiterprofil darf die fachliche Antwortstruktur definieren.

Fuer:

PORTIVA - Buchhalter

soll bei komplexen Fachfragen soweit sinnvoll verwendet werden:

ERGEBNIS

BEGRUENDUNG

STEUERLICHE BEHANDLUNG

BUCHHALTERISCHE BEHANDLUNG

BUCHUNGSVORSCHLAG

BENOETIGTE UNTERLAGEN

OFFENE PUNKTE

RISIKEN

QUELLEN

WISSENSSTAND

FREIGABEBEDARF

Nicht jeder Abschnitt muss bei jeder einfachen Frage zwanghaft
angezeigt werden.

Bei einfachen Fragen darf PORTIVA auch einfach natuerlich antworten.

### E6.9 ADAPTIVE ANTWORTTIEFE

Unterscheide mindestens:

A. EINFACHE FRAGE

Kurze natuerliche Antwort.

B. FACHLICHE FRAGE

Strukturierte Fachantwort.

C. KOMPLEXER FALL

Ausfuehrliche Analyse mit Quellen, Risiken und offenen Punkten.

D. AKTIONSAUFTRAG

Ergebnis + auszufuehrende bzw. vorgeschlagene Aktion.

PORTIVA soll nicht jede Benutzerfrage mit derselben starren langen
Vorlage beantworten.

### E6.10 RUECKFRAGEN

Wenn entscheidende Informationen fehlen:

Nicht einfach beliebige Annahmen treffen.

Stattdessen gezielt nachfragen.

Beispiel:

"Fuer die genaue umsatzsteuerliche Beurteilung brauche ich noch zwei
Angaben:

1. In welchem Land sitzt der Lieferant?
2. Wann wurde die Leistung ausgefuehrt?"

### E6.11 KEINE QUELLENZWANGSANTWORT BEI SMALLTALK

Nicht jede Unterhaltung benoetigt RAG.

Beispiele:

"Hallo"

"Was kannst Du?"

"Kannst Du mir helfen?"

sollen normal durch das Sprachmodell beantwortet werden.

Keine unnoetige Fachwissenssuche und keine acht Quellen fuer einfache
Konversationsfragen.

Die Orchestrierung soll entscheiden:

CHAT / SMALLTALK

oder:

FACHFRAGE MIT RAG.

### E6.12 MODELLROUTING

PORTIVA besitzt entsprechend der allgemeinen Architektur:

LOCAL_MODEL

und optional:

ONLINE_MODEL.

Im OFFLINEMODUS:

ausschliesslich LOCAL_MODEL.

Im HYBRIDMODUS:

lokales Modell als Grundfunktion.

Optional darf ein freigegebenes Online-Modell verwendet werden.

Im ONLINEMODUS:

Online-Modell darf bevorzugt verwendet werden, sofern konfiguriert.

Die eigentliche Antwortlogik muss unabhaengig vom Provider funktionieren.

### E6.13 FEHLENDES LOKALES MODELL

Der aktuelle Zustand zeigt:

"kein Sprachmodell verfuegbar".

Dies ist fuer einen produktiven Offline-KI-Mitarbeiter kein akzeptabler
Endzustand.

Die PORTIVA-Definition of Done verlangt ein tatsaechlich eingerichtetes
lokales Modell.

Wenn kein lokales Modell vorhanden ist:

- klaren Fehlerstatus anzeigen
- Benutzer verstaendlich informieren
- Einrichtungs-/Modellstatus anzeigen
- NICHT so tun, als sei eine vollstaendige KI-Antwort entstanden

Wichtig:

Eine rohe Quellenliste ist kein Ersatz fuer ein fehlendes Sprachmodell.

### E6.14 MODELL-EINRICHTUNG

Pruefe den aktuellen Entwicklungsstand bezueglich des lokalen Modells.

Insbesondere:

- existiert ein echter GGUF- oder anderer unterstuetzter Modelldateipfad?
- funktioniert die lokale Inferenz?
- wird das Modell tatsaechlich geladen?
- wird es vom RAG-Orchestrator verwendet?
- existiert lediglich Code fuer ein Modell oder tatsaechlich ein Modell?
- funktioniert Inferenz offline?

Wenn das Modell fehlt:

diesen Punkt als echte offene Implementierungsanforderung behandeln.

Nicht lediglich Dokumentation:

"siehe MODELL_EINRICHTEN.md"

als endgueltige Produktloesung akzeptieren.

Fuer den normalen Endanwender soll die produktionsreife PORTIVA-Version
mit einem nutzbaren Modell bzw. einem gefuehrten technisch geeigneten
Modellbereitstellungsprozess ausgeliefert werden.

### E6.15 FALLBACK BEI MODELLAUSFALL

Falls ein Sprachmodell waehrend der Nutzung ausfaellt:

Keine erfundene Modellantwort.

Stattdessen beispielsweise:

"Die KI-Antwort konnte derzeit nicht erzeugt werden.

Die lokale Recherche hat relevante Quellen gefunden.

Du kannst die Fundstellen anzeigen oder den Modellstatus pruefen."

Optional:

[Fundstellen anzeigen]

[Modellstatus]

[Erneut versuchen]

Der technische Fallback darf nicht mit einer normalen Fachantwort
verwechselt werden.

### E6.16 QUELLEN IN DER FERTIGEN ANTWORT

Die synthetisierte Antwort soll Quellen referenzieren koennen.

Beispiel:

"Fuer den Vorsteuerabzug muss grundsaetzlich eine ordnungsgemaesse Rechnung
vorliegen. [1]"

Rechte Seitenleiste:

[1] UStG § ...
[2] UStAE ...
[3] BFH ...

So entsteht eine:

lesbare Antwort

+

nachvollziehbare Beleglage.

### E6.17 QUELLENQUALITAET

Die RAG-Synthese muss die im Profil definierte Quellenhierarchie
beruecksichtigen.

Fuer den Buchhalter insbesondere:

Primaerquellen vor Sekundaerquellen.

Wenn ausschliesslich Sekundaerquellen gefunden werden:

PORTIVA soll dies bei fachlich kritischen Fragen erkennen.

Beispiel:

"Fuer diese Aussage liegt mir derzeit nur eine Sekundaerquelle im lokalen
Wissensbestand vor. Fuer eine belastbare steuerliche Bewertung sollte die
Primaerquelle geprueft werden."

### E6.18 KEINE INTERNEN TECHNISCHEN TEXTE IN NORMALER ANTWORT

Folgende Inhalte gehoeren standardmaessig NICHT mitten in die normale
Fachantwort:

- Modellpfade
- GGUF-Dateipfade
- Retrievalscores
- interne Dokument-IDs
- Datenbankpfade
- Chunknummern
- Debuginformationen
- technische Fallbackmeldungen

Diese Informationen gehoeren in:

STATUS

LOG

DEBUG

oder:

RECHERCHE-DETAILS

### E6.19 CHATVERLAUF

PORTIVA muss vorherige Nachrichten innerhalb der aktuellen Unterhaltung
beruecksichtigen.

Beispiel:

Benutzer:
"Ich habe eine Rechnung aus Frankreich."

PORTIVA:
"Ist der Lieferant Unternehmer?"

Benutzer:
"Ja."

PORTIVA muss erkennen, dass:

"Ja"

auf die vorherige Rueckfrage bezogen ist.

Keine Behandlung jeder Nachricht als isolierte Suchanfrage.

### E6.20 UNTERNEHMENSGEDAECHTNIS IN ANTWORTEN

Das persistente Unternehmensgedaechtnis muss in die Antwortgenerierung
einfliessen.

Beispiel gespeichert:

"Wir verwenden SKR03."

Benutzer:

"Wie wuerdest Du das buchen?"

PORTIVA darf nicht erneut fragen, welcher Kontenrahmen verwendet wird,
wenn diese Information gueltig gespeichert ist.

### E6.21 STREAMING / AUSGABEVERHALTEN

Pruefe, ob die GUI technisch eine schrittweise Ausgabe der Modellantwort
unterstuetzen kann.

Bevorzugt:

Antwort erscheint waehrend der Generierung fortlaufend.

Aehnlich modernen KI-Chatoberflaechen.

Falls Streaming mit dem aktuell verwendeten Stack unverhaeltnismaessig
aufwendig ist:

vollstaendige Antwort nach Modellgenerierung anzeigen.

Streaming ist wuenschenswert, aber eine korrekte Antwort ist wichtiger.

### E6.22 ABBRUCH

Waehrend einer laengeren Antwort soll der Benutzer die Generierung soweit
technisch sinnvoll abbrechen koennen.

Beispiel:

[ Generierung stoppen ]

### E6.23 GUI-ANPASSUNG

Die Benutzeroberflaeche soll sich staerker wie eine echte
KI-Unterhaltung anfuehlen.

Bevorzugt:

BENUTZER
Nachricht

PORTIVA - Buchhalter
fertig formulierte Antwort

Darunter optional:

Quellen
Wissensstand

Die derzeitige Darstellung grosser unformatierter Textbloecke und
Rohfundstellen soll entsprechend verbessert werden.

### E6.24 KEINE CHATGPT-KOPIE ERFORDERLICH

PORTIVA soll nicht die visuelle Oberflaeche oder Markenidentitaet eines
anderen KI-Produkts kopieren.

Gemeint ist ausschliesslich die Qualitaetslogik:

Frage
-> verstehen
-> recherchieren
-> denken/verarbeiten
-> verstaendlich antworten.

Das PORTIVA-Branding und die eigene GUI bleiben erhalten.

### E6.25 TESTFAELLE

Nach Implementierung mindestens tatsaechlich testen:

TEST 1 - Smalltalk

Frage:

"Kannst Du mir bei meiner Buchhaltung helfen?"

Erwartung:

natuerliche Antwort.

Keine unnoetige RAG-Rohliste.

--------------------------------------------------

TEST 2 - einfache Fachfrage

Frage:

"Was ist Reverse Charge?"

Erwartung:

verstaendliche Erklaerung mit passenden Quellen.

Keine reine Fundstellenliste.

--------------------------------------------------

TEST 3 - komplexer Fall

realistischer buchhalterischer Sachverhalt.

Erwartung:

strukturierte Fachantwort.

--------------------------------------------------

TEST 4 - Rueckfrage

Sachverhalt mit fehlenden Informationen.

Erwartung:

gezielte Rueckfrage.

--------------------------------------------------

TEST 5 - Unternehmensmemory

Gespeichert:

SKR03.

Frage:

"Wie soll ich das buchen?"

Erwartung:

SKR03 wird beruecksichtigt.

--------------------------------------------------

TEST 6 - Offline

Internet deaktivieren.

Fachfrage.

Erwartung:

lokales Modell + lokales RAG erzeugen eine natuerliche Antwort.

--------------------------------------------------

TEST 7 - Quellen

Antwort muss Quelle referenzieren.

Rechte Quellenansicht zeigt entsprechende Dokumente.

--------------------------------------------------

TEST 8 - kein Modell

Modell absichtlich nicht verfuegbar.

Erwartung:

saubere Fehlermeldung.

Keine vorgetaeuschte KI-Antwort.

--------------------------------------------------

TEST 9 - Chatkontext

mehrteilige Unterhaltung.

Erwartung:

vorherige Nachrichten werden beruecksichtigt.

--------------------------------------------------

TEST 10 - Markdown/Formatierung

Antwort mit Ueberschrift, Liste und Fettdruck.

Erwartung:

sauber gerendert, keine stoerenden Markdown-Rohzeichen.

### E6.26 REGRESSIONSSCHUTZ

Die Verbesserung der Antwortgenerierung darf bestehende Funktionen nicht
beschaedigen.

Insbesondere erhalten:

- lokale Wissenssuche
- Quellenanzeige
- Unternehmensmemory
- Offlinebetrieb
- Hybridbetrieb
- Moduswahl
- Plugins
- Dokumentverarbeitung
- PORTIVA-Branding
- Gespraechsspeicherung

### E6.27 GAP-ANALYSE VOR AENDERUNG

Da PORTIVA bereits weitgehend programmiert ist:

NICHT neu von vorne bauen.

Pruefe zunaechst:

1. vorhandenen Modellprovider
2. aktuellen RAG-Orchestrator
3. Retrieval
4. Promptaufbau
5. Antwortpipeline
6. GUI-Ausgabe
7. Quellenpanel
8. Chatkontext
9. lokale Modellkonfiguration

Gib anschliessend aus:

BEREITS VORHANDEN

TEILWEISE VORHANDEN

FEHLT

ZU AENDERN

Erstelle danach einen gezielten Integrationsplan.

Bestehende funktionierende Komponenten erhalten.

### E6.28 VERBINDLICHE DEFINITION OF DONE

Dieser Bereich gilt erst als VERIFIZIERT, wenn:

- eine normale Benutzerfrage eine natuerliche KI-Antwort erzeugt
- Fachfragen mittels RAG verarbeitet und nicht nur Rohfundstellen
  ausgegeben werden
- die RAG-Treffer tatsaechlich in den Modellkontext eingehen
- Quellen separat angezeigt werden
- relevante Quellen in der Antwort referenziert werden koennen
- Smalltalk nicht unnoetig RAG erzwingt
- komplexe Fachfragen strukturiert beantwortet werden
- Rueckfragen funktionieren
- Chatkontext funktioniert
- Unternehmensmemory in Antworten beruecksichtigt wird
- Markdown/Formatierung sauber dargestellt wird
- technischer Debugtext nicht die normale Antwort dominiert
- lokales Modell tatsaechlich offline antwortet
- alle vorgesehenen Tests ausgefuehrt wurden
- bestehende PORTIVA-Funktionen weiterhin funktionieren

Erst dann darf der Status lauten:

QUALITATIVE ANTWORTGENERIERUNG VERIFIZIERT

ENDE DER ERGAENZUNG

