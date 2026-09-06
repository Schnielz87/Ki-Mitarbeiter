# Anforderungsnachweis

Zu jedem Abschnitt des Masterprompts: wo er umgesetzt und wo er geprueft ist.

Stand siehe `PROJEKTSTATUS.md`. Statusbegriffe nach Masterprompt 52:
**VERIFIZIERT** (geprueft), **GETESTET** (automatischer Test lief),
**GEBAUT** (Artefakt existiert), **IMPLEMENTIERT** (Code vorhanden),
**KONZEPT** (beschrieben, noch nicht umgesetzt), **OFFEN**.

---

## Teil 1 - Grundauftrag

| § | Anforderung | Status | Umsetzung | Nachweis |
|---|---|---|---|---|
| 1 | Nutzbare portable Anwendung, kein Konzept | GEBAUT | gesamtes Projekt | Windows-Ablauf, EXE gebaut und ausgefuehrt |
| 2 | Wiederverwendbare Plattform | VERIFIZIERT | `src/pkc`, `src/profiles` | `docs/NEUER_MITARBEITER.md` |
| 3 | Kein fester Laufwerksbuchstabe | GETESTET | `pkc.paths` | `test_portability.py` (Code-Scan + Pfadtests) |
| 4 | Echte Portabilitaet | GETESTET | `pkc.paths` | `test_abnahme_kette.py`, `subst`-Test auf Windows |
| 5 | Kein Server noetig | GETESTET | SQLite eingebettet | `test_abnahme_kette.py::test_kein_server_noetig` |
| 6 | Optionaler Server spaeter | KONZEPT | - | `ARCHITEKTUR.md` |
| 7 | Ein hybrider Mitarbeiter | GETESTET | `pkc.netstate`, ein Controller | `test_gui_logic.py`, `test_abnahme_kette.py` |
| 8 | Offline-Betrieb vollstaendig | GETESTET | Offline-Kern | `test_abnahme_kette.py`, `test_controller.py` |
| 9 | Online-Betrieb | GETESTET | `pkc.updater` | `test_updater_pipeline.py` |
| 10 | Automatischer Wechsel | GETESTET | `pkc.netstate` | `test_gui_logic.py::test_network_loss_message...` |
| 11 | Online erworbenes Wissen offline | GETESTET | `pkc.updater.pipeline` | `test_abnahme_kette.py` (TEST 10-12) |
| 12 | Funktionsparitaet | GETESTET | - | `test_abnahme_kette.py` |
| 13 | Persistentes Unternehmensgedaechtnis | VERIFIZIERT | `pkc.memory` | Neustart- und Ortswechseltests |
| 14 | Trennung Fach-/Unternehmenswissen | GETESTET | zwei Datenbanken | `test_kundentrennung.py` |
| 15 | Automatische Erkennung | GETESTET | `pkc.memory.capture` | `test_controller.py`, `test_gui_logic.py` |
| 16 | Aendern und Loeschen | GETESTET | `pkc.memory.store` | Versionierung, Verlauf, Archiv |
| 17 | Metadaten | GETESTET | Schema `memory` | `test_controller.py` |
| 18 | Struktur des Gedaechtnisses | IMPLEMENTIERT | `database/company.db`, `company/` | `DATENSPEICHER_KONZEPT.md` |
| 19 | Keine PC-Abhaengigkeit | GETESTET | `pkc.paths` | Ortswechseltest, Windows-`subst` |
| 20 | Keine Host-Speicherung | VERIFIZIERT | onedir statt onefile | `DATENSPEICHER_KONZEPT.md` |
| 21 | Datenschutz, SSD-Verlust | GETESTET | `pkc.security` | `test_sicherheit_freigaben.py` |
| 22 | Rolle des Buchhalters | IMPLEMENTIERT | Fach-Masterprompt | `MITARBEITERPROFIL_BUCHHALTER.md` |
| 23 | Fachlicher Aufgabenumfang | GETESTET | 13 Fachmodule | `test_fachliche_faelle.py` |
| 24 | Standardlogik und Antwortschema | IMPLEMENTIERT | `prompts/system.md`, `pkc.rag` | Schema wird erzwungen |
| 25 | Zeitbezogener Rechtsstand | IMPLEMENTIERT | `gueltig_ab/bis`, `as_of` | `pkc.retrieval.search._valid_at` |
| 26 | Quellenhierarchie | GETESTET | Prioritaet 1-5 im Ranking | `test_updater_pipeline.py` |
| 27 | Quellenregister Q01-Q12 | GETESTET | `config/source_registry.json` | `test_updater_pipeline.py` |
| 28 | Keine blossen Links | GETESTET | Abrufkette mit Originalablage | `test_updater_pipeline.py` |
| 29 | Lokale Wissensdatenbank | GETESTET | `resources/`, `knowledge.db` | Systempruefung |
| 30 | RAG mit Quellenvorrang | GETESTET | `pkc.rag` | `test_fachliche_faelle.py` |
| 31 | Update-System | GETESTET | `pkc.updater` | 9 Tests inkl. Ruecknahme |
| 32 | Lokales Sprachmodell | GETESTET | `pkc.llm`, mitgelieferter llama.cpp-Dienst | `test_modelldienst.py`; echtes Modell im Windows-Ablauf |
| 33 | Optionales Online-Modell | GETESTET | `LlmManager` | `test_llm_providers.py` |
| 34 | Hardware-Erkennung | GETESTET | `pkc.hardware` | `tools/modell_einrichten.py` |
| 35 | Grafische Oberflaeche | IMPLEMENTIERT | `ui.tk_app` | Struktur getestet, **Fenster nie geoeffnet** |
| 36 | Echte Windows-Anwendung | GEBAUT | PyInstaller | Windows-Ablauf, beide Programme |
| 37 | Daten auf der SSD | GETESTET | `pkc.paths` | `test_abnahme_kette.py` |
| 38 | Erster Programmstart | GETESTET | `StartupReport` | Systempruefung der EXE auf Windows |
| 39 | Unternehmens-Onboarding | GETESTET | 21 Fragen | `test_controller.py` |
| 40 | Connector-/ERP-Architektur | GETESTET | `pkc.connectors` | `test_sicherheit_freigaben.py` |
| 41 | Human-in-the-Loop | GETESTET | Zustandsautomat | Ausfuehrung technisch gesperrt |
| 42 | Halluzinationsschutz | GETESTET | `pkc.rag.engine` | erfundene Fundstellen werden entfernt |
| 43 | Projektstruktur | VERIFIZIERT | Verzeichnisbaum | `ARCHITEKTUR.md` |
| 44 | Checkpoint-Regel | VERIFIZIERT | `pkc.checkpoint` | `checkpoints/` doppelt abgelegt |
| 45 | Wiederherstellbarkeit | GETESTET | `restore_info` | `test_abnahme_kette.py` |
| 46 | Qualitaetssicherung | GETESTET | 192 Tests | `TESTBERICHT.md` |
| 47 | Fachliche Testfaelle | GETESTET | 22 Sachverhalte | `test_fachliche_faelle.py` |
| 48 | Projektplan 18 Tasks | VERIFIZIERT | Checkpoints 01-18 | `checkpoints/` |
| 49 | Portabilitaetstest | GETESTET | 12 Schritte | `test_abnahme_kette.py`, Windows-Ablauf |
| 50 | Abschlussdateien | VERIFIZIERT | alle vorhanden | Wurzelverzeichnis |
| 51 | Definition of Done | TEILWEISE | 20 Punkte | `docs/ABNAHME.md` - B, C, D, F, G offen |
| 52 | Keine Scheinerfuellung | VERIFIZIERT | durchgaengig | `PROJEKTSTATUS.md` Abschnitt 5 |
| 53 | Blaupause | VERIFIZIERT | Core ohne Fachbegriffe | `docs/NEUER_MITARBEITER.md` |
| 54 | Langfristige Plattform | KONZEPT | Profilarchitektur | `KOMMERZIELLES_KONZEPT.md` |
| 55 | Arbeitsregeln | VERIFIZIERT | - | Commit-Historie |
| 56 | Erster Schritt | VERIFIZIERT | - | `ARCHITEKTUR.md` |
| 57 | Endziel | TEILWEISE | - | siehe § 51 |

## Teil 2 - Kommerzielle Produktperspektive

| § | Anforderung | Status | Umsetzung | Nachweis |
|---|---|---|---|---|
| 58 | Standardisierte Plattform statt Bastelloesung | VERIFIZIERT | Core / Profil / Kundenkonfiguration | `KOMMERZIELLES_KONZEPT.md` |
| 59 | Positionierung als Fachassistent | GETESTET | Freigabepflicht, Grenzen im Prompt | `test_sicherheit_freigaben.py` |
| 60 | Keine 100-Prozent-Annahme | GETESTET | 11 pruefbare Zusagen | `KOMMERZIELLES_KONZEPT.md` Abschnitt 3 |
| 61 | Kundentrennung | GETESTET | `customers/<kennung>/` | `test_kundentrennung.py` (10 Tests) |
| 62 | Datenexport und Loeschung | GETESTET | `kunde export/loeschen`, Belege, Gespraeche | `test_kundentrennung.py` |
| 63 | Lizenz- und Redistributionspruefung | GETESTET | `LIZENZREGISTER.md` | `test_produktreife.py` |
| 64 | SBOM | GETESTET | `sbom.json` (CycloneDX) | `test_produktreife.py` |
| 65 | Sichere Softwareupdates | GETESTET | `pkc.updater.software` | `test_softwareupdate.py` (11 Tests) |
| 66 | Produktversionierung | GETESTET | Befehl `version` | `test_lizenzierung.py` |
| 67 | Audit- und Fehlernachvollziehbarkeit | GETESTET | `pkc.audit`, Versionsangaben | `test_sicherheit_freigaben.py` |
| 68 | Kein versteckter Fernzugriff | GETESTET | keiner vorhanden | `test_produktreife.py::test_kein_fernzugriff_im_code` |
| 69 | Keine zwingende Telemetrie | GETESTET | keine vorhanden | `test_produktreife.py::test_keine_telemetrie...` |
| 70 | Security-by-Design | GETESTET | Tresor, Freigaben, Integritaet | `SICHERHEITSKONZEPT.md` |
| 71 | Rechtlicher Compliance-Check | **OFFEN** | - | nur extern leistbar, siehe `reife` |
| 72 | Fachliche Grenzen des Moduls | IMPLEMENTIERT | Grenzen im Profil, Freigabepflicht | rechtliche Abgrenzung offen |
| 73 | Release-Dossier | GETESTET | `build_release_dossier` | `test_produktreife.py` |
| 74 | Kunden-Onboarding als Produktfunktion | GETESTET | Befehl `einrichten`, 7 Schritte | `test_kundentrennung.py` |
| 75 | Backup-Strategie | GETESTET | `sicherung --ziel` | `test_kundentrennung.py` |
| 76 | Pilotbetrieb | **OFFEN** | Ablauf beschrieben | braucht einen realen Kunden |
| 77 | Commercial-Readiness-Gate | GETESTET | `reife` | `test_produktreife.py` |
| 78 | Geschaeftsmodell nicht verdrahtet | VERIFIZIERT | Lizenzfelder offen gehalten | `LIZENZKONZEPT.md` |
| 79 | Langfristige Produktvision | KONZEPT | Profilarchitektur | `docs/NEUER_MITARBEITER.md` |
| 80 | Reihenfolge bis zur Vermarktung | VERIFIZIERT | - | `KOMMERZIELLES_KONZEPT.md` |

## Teil 3 - Kopierschutz und Lizenzierung

| § | Anforderung | Status | Umsetzung | Nachweis |
|---|---|---|---|---|
| 84 | Kopierschutz im Grunddesign | GETESTET | `pkc.licensing` | `test_lizenzierung.py` |
| 85 | Portabilitaet bleibt erhalten | GETESTET | Bindung an Datentraeger, nicht PC | `test_portabilitaet_bleibt_erhalten` |
| 86 | Signierte Lizenz, Instanzbindung | GETESTET | Ed25519, kanonische Daten | `test_lizenzierung.py` |
| 87 | Offline-Lizenzpruefung | GETESTET | ohne Netz | `test_4_ohne_internet_gueltig` |
| 88 | Optionale Online-Aktivierung | KONZEPT | Ablauf vorbereitet | `LIZENZKONZEPT.md` |
| 89 | Mehrere Lizenzmodelle | IMPLEMENTIERT | Felder in der Lizenz | `LIZENZKONZEPT.md` |
| 90 | Schutz vor Vervielfaeltigung | GETESTET | Kopie ist nicht lizenziert | `test_2_kopie_auf_zweite_ssd...` |
| 91 | Keine reine Dateipruefung | GETESTET | Signatur statt Textdatei | `test_3_veraenderte_lizenzdatei...` |
| 92 | Schutz des Programmcodes | TEILWEISE | Pruefsummen, signierte Pakete | Code-Signing **offen** |
| 93 | Ausfall- und Ersatzprozess | GETESTET | neue Instanz, neue Lizenz | `test_6_ersatz_datentraeger...` |
| 94 | Lizenz und Daten trennen | GETESTET | Export ohne Lizenz | `test_7_datensicherung...` |
| 95 | Verhalten bei Lizenzverletzung | GETESTET | keine Daten beschaedigt | `test_5_fehlende_lizenz...` |
| 96 | Sieben Lizenztestfaelle | GETESTET | alle sieben | `test_lizenzierung.py` |
| 97 | Commercial-Ready-Anforderung | TEILWEISE | Gate vorhanden | Pruefschluessel und Recht offen |

## Teil 4 - Erweiterungen (E1 bis E6)

### E1 - Marke und Erscheinungsbild PORTIVA

| § | Anforderung | Status | Umsetzung | Nachweis |
|---|---|---|---|---|
| E1.1 | Marke fest, Profil dynamisch | GETESTET | `pkc.branding` | `test_branding.py` |
| E1.2 | Originaldatei im Projekt | VERIFIZIERT | `assets/branding/original/` | Datei liegt vor |
| E1.3 | Nur relative Pfade | GETESTET | `Brand.pfad()` weist absolute ab | `test_branding.py` |
| E1.4 | Startbildschirm mit Logo | IMPLEMENTIERT | `StartupWindow`, `_BrandKopf` | `test_gui_logic.py` (Struktur) |
| E1.5 | Hauptfenster mit Marke und Profil | GETESTET | `_BrandKopf` im Kopfbereich | `test_gui_logic.py` |
| E1.6 | Titelleiste `PORTIVA - <Profil>` | GETESTET | `MainWindow.__init__` | `test_fenstertitel_traegt_marke_und_profil` |
| E1.7 | Fenstericon | GETESTET | `_fenstericon` | `test_fenstersymbol_wird_gesetzt` |
| E1.8 | Windows-Taskleiste | IMPLEMENTIERT | `_taskleisten_kennung` (AppUserModelID) | nur unter Windows wirksam |
| E1.9 | EXE-Icon | GEBAUT | `build/portable_buchhalter.spec` | Windows-Ablauf |
| E1.10 | Icon-Datei mehrere Groessen | GETESTET | `tools/branding_ableiten.py` | `test_branding.py` |
| E1.11 | GUI-Branding durchgehend | GETESTET | Kopf, Titel, Symbol, Sprecher | `test_gui_logic.py` |
| E1.12 | Profilwechsel aendert nur den Zusatz | GETESTET | `profilname()` | `test_branding.py` |
| E1.13 | Branding-Konfiguration | GETESTET | `config/brand.json` | `test_branding.py` |
| E1.14 | Heller und dunkler Hintergrund | IMPLEMENTIERT | Varianten light/dark abgeleitet | Aussehen nur visuell pruefbar |
| E1.15 | Keine Abhaengigkeit von Internet | GETESTET | Dateien liegen bei | `test_branding.py` |
| E1.16 | Keine Abhaengigkeit vom Host-PC | GETESTET | relative Pfade, Paketfallback | `test_portability.py` |
| E1.17 | Fehlendes Logo bricht nicht ab | GETESTET | Rueckfall auf den Schriftzug | `test_branding.py` |
| E1.18 | Tests | GETESTET | 14 Tests | `test_branding.py`, CI-Schritt |
| E1.19 | Dokumentation | VERIFIZIERT | `BRANDING_KONZEPT.md` | im Verzeichnis |
| E1.20 | Checkpoint | VERIFIZIERT | `checkpoints/` | Datei geschrieben |
| E1.21 | Definition of Done | TEILWEISE | alles ausser Sichtpruefung | Aussehen gehoert zur Abnahme |

### E2 - Betriebsmodi und Wissenssynchronisierung

| § | Anforderung | Status | Umsetzung | Nachweis |
|---|---|---|---|---|
| E2.1 | HYBRID, OFFLINE, ONLINE | GETESTET | `pkc.netstate.Mode` | `test_betriebsmodi.py` |
| E2.2 | Hybridmodus | GETESTET | Standard, wechselt selbsttaetig | `test_betriebsmodi.py` |
| E2.3 | Offlinemodus | GETESTET | kein Netzzugriff, auch nicht probeweise | `test_3_offline_trotz_vorhandenem_internet` |
| E2.4 | Onlinemodus | GETESTET | `Betriebsart`, Modellrouting | `test_betriebsmodi.py` |
| E2.5 | Moduswahl in der Oberflaeche | GETESTET | Auswahlfeld im Kopfbereich | `test_gui_logic.py` |
| E2.6 | Bestaetigung beim Wechsel | GETESTET | Meldung mit Folgen | `test_gui_logic.py::test_moduswahl_in_der_oberflaeche` |
| E2.7 | Moduswechsel protokollieren | GETESTET | Audit-Eintrag | `test_betriebsmodi.py` |
| E2.8 | Internetstatus getrennt vom Modus | GETESTET | zwei Anzeigen, zwei Begriffe | `test_betriebsmodi.py` |
| E2.9 | Wahl bleibt ueber Neustart | GETESTET | `network.mode` in der Konfiguration | `test_betriebsmodi.py` |
| E2.10 | Automatische Synchronisierung | GETESTET | `pkc.updater.zeitplan` | `test_wissenszeitplan.py` |
| E2.11 | Standard woechentlich | GETESTET | `VORGABE = "weekly"` | `test_wissenszeitplan.py` |
| E2.12 | Einstellungen fuer Updates | GETESTET | Registerkarte Einstellungen | `test_gui_logic.py` |
| E2.13 | Inkrementelle Synchronisierung | GETESTET | ETag/If-None-Match | `test_updater_pipeline.py` |
| E2.14 | Kein unkontrolliertes Ueberschreiben | GETESTET | Staging, Pruefung, Aktivierung | `test_updater_pipeline.py` |
| E2.15 | Versionierung des Wissensstands | GETESTET | Lauf-ID, Ruecknahme | `test_updater_pipeline.py` |
| E2.16 | Manuelle Aktualisierung | GETESTET | Schaltflaeche und `update` | `test_gui_logic.py` |
| E2.17 | Verhalten im Offlinemodus | GETESTET | pausiert, kein Abruf | `test_wissenszeitplan.py` |
| E2.18 | Ausstehende Updates erkennen | GETESTET | `UpdateLage.UEBERFAELLIG` | `test_wissenszeitplan.py` |
| E2.19 | Keine falsche Aktualitaetsbehauptung | GETESTET | Wissensstand in jeder Antwort | `test_antwortqualitaet.py` |
| E2.20 | Quellenspezifische Intervalle | GETESTET | drei Ebenen: Quelle, Quellenart, Vorgabe | `test_wissenszeitplan.py` (7 Tests) |
| E2.21 | Update-Status in der Oberflaeche | GETESTET | Statusfeld mit Faelligkeit | `test_gui_logic.py` |
| E2.22 | Testfaelle Betriebsmodi | GETESTET | alle fuenf | `test_betriebsmodi.py` |
| E2.23 | Testfaelle Synchronisierung | GETESTET | TEST 6 bis 11 | `test_wissenszeitplan.py` |
| E2.24 | Definition of Done | ERFUELLT | alle Abschnitte umgesetzt | `test_betriebsmodi.py`, `test_wissenszeitplan.py` |

### E3 - Fachfragen ohne Unternehmensdaten

| § | Anforderung | Status | Umsetzung | Nachweis |
|---|---|---|---|---|
| E3 | Fachfrage ohne Onboarding moeglich | GETESTET | kein Zwang zum Onboarding | `test_fachfrage_ohne_unternehmensdaten_wird_beantwortet` |
| E3 | Fehlende Angabe wird benannt, nicht angenommen | GETESTET | Rueckfragen statt Annahmen | `test_ohne_unternehmensdaten_wird_nichts_erfunden` |
| E3 | Nichts wird ungefragt gespeichert | GETESTET | Rueckfrage vor jedem Merken | `test_eine_fachfrage_speichert_nichts_ungefragt`, `test_gui_logic.py` |
| E3 | In der Anleitung erklaert | VERIFIZIERT | eigenes Kapitel | `docs/BEDIENUNGSANLEITUNG.docx` |

### E4 - Datei- und Artefakterzeugung

| § | Anforderung | Status | Umsetzung | Nachweis |
|---|---|---|---|---|
| E4 | Acht Ausgabeformate | GETESTET | `pkc.artefakte.schreiber` | `test_artefakte.py` |
| E4 | Artifact Engine (Name, Ort, Fassung, Metadaten, Schutz) | GETESTET | `Artefaktwerk` | `test_artefakte.py` |
| E4 | Offline, ohne installiertes Office | GETESTET | nur Standardbibliothek | `test_artefakte.py`, `test_produktreife.py` |
| E4 | Berufsspezifische Ausgaben | IMPLEMENTIERT | jedes Profil waehlt seine Formate | Formatauswahl in Oberflaeche und CLI |
| E4 | Online-Erweiterung (OneDrive, Mail ...) | **OFFEN** | ueber Plugins vorgesehen | `PLUGIN_KONZEPT.md` |
| E4 | Neue Formate ueber Plugins | GETESTET | `registrieren()`, Beispielplugin HTML | `test_plugins.py` |

### E5 - Plugin- und Erweiterungssystem

| § | Anforderung | Status | Umsetzung | Nachweis |
|---|---|---|---|---|
| 98 | Allgemeines Plugin-System | GETESTET | `pkc.plugins` | `test_plugins.py` |
| 99 | Installation in der Anwendung | TEILWEISE | Kommandozeile vollstaendig | Oberflaeche: nur Anzeige |
| 100 | Paketformat `.kimplug` | GETESTET | ZIP mit Manifest und Pruefsummen | `test_plugins.py` |
| 101 | Manifest | GETESTET | `Manifest` mit Pruefung | `test_plugins.py` |
| 102 | Plugin-API/SDK | IMPLEMENTIERT | `Pluginkontext` | `PLUGIN_KONZEPT.md` |
| 103 | Tool-Registrierung | GETESTET | `werkzeug_anmelden` | `test_plugins.py` |
| 104 | Kategorien | GETESTET | sechs Kategorien | `test_plugins.py` |
| 105 | Offline- und Online-Plugins | GETESTET | Modus sperrt auch berechtigte Plugins | `test_netzzugriff_scheitert_im_offlinebetrieb` |
| 106 | Berechtigungssystem | GETESTET | zwoelf Rechte, einzeln erteilt | `test_plugins.py` |
| 107 | Lese- und Schreibrechte getrennt | GETESTET | Lesen erlaubt heisst nicht schreiben | `test_lesen_erlaubt_heisst_nicht_schreiben_erlaubt` |
| 108 | Isolation / Sandboxing | TEILWEISE | eigener Vorgang je Plugin, kein Objekt der Anwendung drueben | `test_plugin_laeuft_in_einem_eigenen_vorgang`; Beschraenkung durch das Betriebssystem offen |
| 109 | Kryptografische Signaturen | TEILWEISE | Pruefung gebaut und getestet | Herausgeberschluessel nicht hinterlegt |
| 110 | Kompatibilitaet | GETESTET | Fassung der Schnittstelle | `test_falsche_schnittstellenfassung...` |
| 111 | Abhaengigkeiten | TEILWEISE | Voraussetzung wird geprueft | keine Fassungsaufloesung |
| 112 | Plugin-Updates | TEILWEISE | erneute Installation ersetzt sauber | Abgleich braucht Katalog |
| 113 | Deinstallation | GETESTET | Daten bleiben erhalten | `test_entfernen_laesst_die_daten_stehen` |
| 114 | Verbundene Dienste als Plugins | KONZEPT | Kategorie CONNECTOR vorhanden | `ERP_CONNECTOR_KONZEPT.md` |
| 115 | Sichere Authentifizierung | IMPLEMENTIERT | Tresor (scrypt + AES-256-GCM) | `test_sicherheit_freigaben.py` |
| 116 | Plugin-Katalog | **OFFEN** | setzt Betreiber und Pruefstelle voraus | `PLUGIN_KONZEPT.md` 9.3 |
| 117 | Installation aus lokaler Datei | GETESTET | `plugin installieren <paket>` | `test_plugins.py` |
| 118 | Plugin-Audit | GETESTET | jeder Vorgang im Protokoll | `test_plugins.py` |
| 119 | Plugin-Lizenzierung | **OFFEN** | Geschaeftsentscheidung | Masterprompt 78 |
| 120 | Kundentrennung | GETESTET | Daten im Kundenbereich | `test_plugincode_liegt_im_programmordner...` |
| 121 | Plugin-Tests | GETESTET | 22 Tests | `test_plugins.py` |
| 122 | Commercial-Ready-Gate | **NICHT ERFUELLT** | Sandboxing und Katalog fehlen | `PLUGIN_KONZEPT.md` 10 |
| 123 | Endziel: neue Faehigkeit ohne neuen Bau | GETESTET | Beispielplugin HTML | `test_beispielplugin_ergaenzt_ein_ausgabeformat` |

### E6 - Qualitative KI-Antworten

| § | Anforderung | Status | Umsetzung | Nachweis |
|---|---|---|---|---|
| E6.1 | Keine rohen Trefferlisten als Antwort | GETESTET | `RetrievalOnlyProvider` neu gefasst | `test_antwortdarstellung.py` |
| E6.2 | Verbindlicher Antwortablauf | GETESTET | `RagEngine.answer` | `test_antwortqualitaet.py` |
| E6.3 | Treffer erreichen das Modell | GETESTET | Kontext wird mitgegeben | `test_antwortqualitaet.py` (Doppel zeichnet auf) |
| E6.4 | Antwortqualitaet | IMPLEMENTIERT | Fachprompt und Tiefenanweisung | ohne echtes Modell nicht messbar |
| E6.5 | Antwort und Quellen getrennt | GETESTET | `ui.antwort.teilen` | `test_antwortdarstellung.py` |
| E6.6 | Rohtreffer nur auf Abruf | GETESTET | Befehl `recherche` | `test_antwortdarstellung.py::test_recherche_befehl_zeigt_rohtreffer` |
| E6.7 | Markdown wird dargestellt | GETESTET | `ui.markdown` | `test_markdown.py` |
| E6.8 | Berufsspezifische Struktur | IMPLEMENTIERT | Profil gibt das Schema vor | `prompts/system.md` |
| E6.9 | Adaptive Antworttiefe | GETESTET | `pkc.rag.fragetyp` | `test_fragetyp.py` |
| E6.10 | Rueckfragen | GETESTET | Anweisung im Kontext | `test_antwortqualitaet.py` |
| E6.11 | Kein Quellenzwang bei Smalltalk | GETESTET | keine Recherche, kein Quellenteil | `test_antwortqualitaet.py` |
| E6.12 | Modellrouting nach Betriebsart | GETESTET | OFFLINE lokal, ONLINE bevorzugt online | `test_modellrouting_folgt_der_betriebsart` |
| E6.13 | Fehlendes Modell ist kein Endzustand | GETESTET | Modelldienst wird mitgeliefert und selbst gestartet; `modell einrichten` | `test_modelldienst.py`, `test_modell_einrichten.py`; mit echtem Modell im Windows-Ablauf |
| E6.14 | Modell-Einrichtung in der Anwendung | GETESTET | `modell einrichten` mit Katalog, Pruefsumme und Probe | `test_modell_einrichten.py` (17 Tests) |
| E6.15 | Fallback sieht nicht aus wie eine Antwort | GETESTET | kurzer, ehrlicher Status | `test_antwortdarstellung.py` |
| E6.16 | Quellen in der fertigen Antwort | GETESTET | Verweise `[n]`, Quellenteil | `test_antwortqualitaet.py` |
| E6.17 | Quellenqualitaet | GETESTET | Warnung bei nur Sekundaerquellen | `test_antwortqualitaet.py` |
| E6.18 | Keine technischen Texte in der Antwort | GETESTET | keine Modellpfade, keine Bewertungen | `test_antwortdarstellung.py` |
| E6.19 | Chatverlauf | GETESTET | Verlauf im Kontext | `test_antwortqualitaet.py` |
| E6.20 | Unternehmensgedaechtnis in Antworten | GETESTET | Gedaechtnis im Kontext | `test_antwortqualitaet.py` |
| E6.21 | Streaming | GETESTET | schrittweise Ausgabe, Rueckfall | `test_llm_providers.py`, `test_gui_logic.py` |
| E6.22 | Abbruch | GETESTET | "Generierung stoppen" | `test_gui_logic.py` |
| E6.23 | Gespraechsdarstellung | GETESTET | Sprecher, Anhang darunter | `test_gui_logic.py` |
| E6.24 | Keine ChatGPT-Kopie noetig | ERFUELLT | eigene, schlichte Darstellung | - |
| E6.25 | Zehn Testfaelle | GETESTET | alle zehn | `test_antwortqualitaet.py` |
| E6.26 | Regressionsschutz | GETESTET | Unterhaltungen, Quellen, Audit | `test_antwortqualitaet.py` |
| E6.27 | Gap-Analyse vor Aenderung | ERFUELLT | Bestand geprueft, nichts neu gebaut | `PROJEKTSTATUS.md` |
| E6.28 | Definition of Done | TEILWEISE | Modelldienst und Weg zum Modell stehen | die fachliche Guete eines echten Modells bleibt Sache der Abnahme |

---

## Die wichtigsten offenen Punkte

1. **Rechtliche Pruefung (§ 71, 72)** - insbesondere die Abgrenzung zur
   Steuerberatung nach StBerG. Nur extern leistbar und der wichtigste Punkt
   des gesamten Vorhabens vor einer Vermarktung.
2. **Pilotbetrieb (§ 76)** - braucht einen realen Kunden.
3. **Abnahme mit echtem Sprachmodell (§ 32, 51)** - `docs/ABNAHME.md` C und D.
4. **Fenster per Doppelklick (§ 35, 51)** - `docs/ABNAHME.md` B.
5. **Pruefschluessel des Herausgebers (§ 86)** - geschaeftliche Entscheidung.
6. **Code-Signing (§ 92)** - benoetigt ein Zertifikat.
7. **Weitergabe des Sprachmodells (§ 63)** - Empfehlung: vom Kunden beziehen
   lassen.
8. **Beschraenkung der Plugins durch das Betriebssystem (E5.108)** - die
   Trennung auf Vorgangsebene steht; ein eigenes Benutzerkonto oder ein
   Job-Objekt fehlt. Fuer Plugins fremder Herkunft erforderlich, siehe
   `PLUGIN_KONZEPT.md` 9.1.

---

## Anmerkung zur Zaehlung

Die Abschnitte **81 bis 83 gibt es nicht**. Die Vorgabe springt von 80
auf 84. In dieser Uebersicht fehlt an der Stelle also nichts.
