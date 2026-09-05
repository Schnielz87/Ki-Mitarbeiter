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
| 32 | Lokales Sprachmodell | IMPLEMENTIERT | `pkc.llm` | **kein echtes Modell ausgefuehrt** |
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
