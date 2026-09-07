# PORTIVA — GAP-Analyse und Integrationsplan UI/UX

Stand **2026-09-07**, Commit `ee18e88`.
Grundlage: verbindlicher UI/UX-Auftrag, Referenzbilder 00–10,
PORTIVA-Classic-Logo.

Dieses Dokument ist die Antwort auf Abschnitt 61 des Auftrags. Es wird
**nichts umgesetzt**, bevor die Freigabe vorliegt.

---

## 0. Kurzfassung

Der PORTIVA-Kern ist weitgehend fertig und trägt die neue Oberfläche. Was
fehlt, ist zu etwa vier Fünfteln **Oberfläche zu vorhandenen Diensten** und
zu etwa einem Fünftel **neue Fachlogik** (Vorlagen, Aufgaben).

- Von den zehn geforderten Hauptbereichen sind **fünf** in der heutigen
  Oberfläche vorhanden (teils unter anderem Namen), **fünf fehlen**.
- Von den fehlenden fünf haben **drei** einen vollständigen Dienst im
  Hintergrund und brauchen nur eine Ansicht (Arbeitsergebnisse, Plugins,
  Verbundene Dienste).
- **Zwei** brauchen zusätzlich neue Fachlogik (Vorlagen, Aufgaben).
- Die Antwortpipeline erfüllt die Abschnitte 12–17 und 21 des Auftrags
  bereits: es wird synthetisiert, nicht nur aufgelistet.

Das ist die gute Nachricht: es ist kein Neubau, sondern ein Umbau.

---

## 1. Was heute da ist

### 1.1 Oberfläche

`src/ui/tk_app.py`, 2008 Zeilen, ein `ttk.Notebook` mit **sechs**
Registerkarten:

| heute | Zielbereich |
|---|---|
| Unterhaltung | 1. Unterhaltung |
| Unternehmenswissen | 2. Unternehmenswissen |
| Belege | 3. Belege & Dokumente |
| Wissen aktualisieren | 5. Wissen & Quellen |
| Sprachmodell | geht auf in 10. Einstellungen & Status → KI & Modelle |
| Einstellungen und Status | 10. Einstellungen & Status |

Darüber eine Kopfzeile (Logo, Betriebsmodus, Internetstatus, Wissensstand),
darunter eine Statusleiste.

### 1.2 Kern und Dienste

| Baustein | Datei | Zustand |
|---|---|---|
| Controller (eine Fassade über allem) | `src/app/controller.py` | 89 öffentliche Methoden |
| RAG-Orchestrator | `src/pkc/rag/engine.py` | vollständig |
| Fragetyp-Einstufung | `src/pkc/rag/fragetyp.py` | vollständig |
| Kontextaufbau | `src/pkc/rag/context.py` | vollständig |
| Retrieval (BM25 + Einbettungen) | `src/pkc/retrieval/` | vollständig |
| Sprachmodell (lokal + online) | `src/pkc/llm/` | vollständig |
| Unternehmensgedächtnis | `src/pkc/memory/` | vollständig |
| Dokumentpipeline | `src/pkc/knowledge/` | vollständig |
| Artifact Engine | `src/pkc/artefakte/` | vollständig, 9 Formate |
| Plugin-System | `src/pkc/plugins/` | vollständig, ohne Oberfläche |
| Connectoren | `src/pkc/connectors/` | Registry + Info, ohne Oberfläche |
| Wissensupdate | `src/pkc/updater/` | vollständig |
| Lizenz | `src/pkc/licensing/` | vollständig |
| Branding | `src/pkc/branding.py` | vollständig, Dateien veraltet |
| Profil | `src/pkc/profile.py` | vollständig, Name kommt aus Profil |

**Wichtig für den Umbau:** die Oberfläche spricht bereits ausschließlich
über `Controller` mit dem Kern. Es gibt keine Geschäftslogik in
`tk_app.py`. Damit ist der von Abschnitt 2 geforderte Aufbau

    NEUE GUI → BESTEHENDER CORE → BESTEHENDE SERVICES

heute schon gegeben und bleibt erhalten.

---

## 2. GAP-Analyse je Hauptbereich

### 1. Unterhaltung — **MUSS ANGEPASST WERDEN**

| Anforderung | Zustand |
|---|---|
| Zentrale Unterhaltung | BEREITS VORHANDEN |
| Natürliche KI-Antwort statt roher Fundstellen | BEREITS VORHANDEN (`rag/engine.py`) |
| Smalltalk ohne RAG | BEREITS VORHANDEN (`fragetyp.py`) |
| Unternehmensgedächtnis fließt ein | BEREITS VORHANDEN |
| Rückfragen bei fehlenden Angaben | BEREITS VORHANDEN (Systemtext Regel 3) |
| Antwortformatierung (Absätze, Listen, Fett, Tabellen) | BEREITS VORHANDEN (`ui/markdown.py`) |
| Eingabe dauerhaft unten | TEILWEISE — heute unten, aber im Karteireiter |
| Datei anhängen | TEILWEISE — Knopf „Dokument hinzufuegen“, nicht an der Eingabe |
| Generierung stoppen | BEREITS VORHANDEN |
| Neue Unterhaltung / Verlauf | BEREITS VORHANDEN |
| **Einklappbares rechtes Quellenpanel** | TEILWEISE — Quellen stehen als Fließtext rechts, nicht als Karten, nicht einklappbar |
| **Quelle: Nummer, Titel, Art, Herausgeber, Datum, Fundstelle, Primär/Sekundär, Öffnen, Details** | TEILWEISE — Daten liegen vor, Darstellung unvollständig |
| **Recherche-Details (Chunks, Scores, IDs) getrennt** | FEHLT |
| **Drag & Drop** | FEHLT — Tkinter kann das nicht von sich aus |
| **Enter sendet, Shift+Enter Zeilenumbruch** | MUSS ANGEPASST WERDEN — heute Strg+Enter |
| **Strg+N neue Unterhaltung, Escape bricht ab** | FEHLT |

### 2. Unternehmenswissen — **MUSS ANGEPASST WERDEN**

| Anforderung | Zustand |
|---|---|
| Suche, Öffnen, Bearbeiten, Löschen, Neuer Eintrag | BEREITS VORHANDEN |
| Versionen, Status/Bestätigung | BEREITS VORHANDEN (`memory/store.py`) |
| **Kategorien als Kacheln mit Anzahl** | FEHLT — heute eine flache Liste |
| **Zuletzt geändert als eigener Block** | FEHLT |
| **Archivieren** | FEHLT — Store kennt nur aktiv/gelöscht |

### 3. Belege & Dokumente — **MUSS ANGEPASST WERDEN**

| Anforderung | Zustand |
|---|---|
| Datei auswählen, Import, Analyse | BEREITS VORHANDEN |
| Letzte Dokumente, Typ, Status | TEILWEISE — Liste vorhanden, ohne Status-Spalte |
| **Drag & Drop** | FEHLT |
| **Erneut analysieren** | FEHLT |
| **In Unterhaltung übernehmen** | FEHLT |
| **Dokumenten-Workflow als Tabelle** | FEHLT |

### 4. Arbeitsergebnisse — **FEHLT (Ansicht), Dienst vorhanden**

| Anforderung | Zustand |
|---|---|
| Dienst: erzeugen, auflisten, versionieren | BEREITS VORHANDEN (`artefakt_liste`, `datei_erzeugen`, `antwort_speichern`) |
| **Eigene Ansicht** | FEHLT — heute nur ein Knopf „Antwort speichern“ im Chat |
| Öffnen, Exportieren, Umbenennen, Versionen, Löschen | FEHLT (Öffnen/Exportieren teilweise über den Dateipfad) |

### 5. Wissen & Quellen — **MUSS ANGEPASST WERDEN**

| Anforderung | Zustand |
|---|---|
| Wissensstand, letzte/nächste Prüfung, Intervall | BEREITS VORHANDEN |
| Manuelles Update, Ergebnis, Rollback | BEREITS VORHANDEN |
| Quellenregister mit Status | BEREITS VORHANDEN (`updater/registry.py`) |
| **Kennzahlenkacheln oben** | FEHLT |
| **Update-Pipeline sichtbar: Prüfen → Staging → Validieren → Indexieren → Aktivieren** | FEHLT — die Schritte gibt es, sie werden nicht angezeigt |
| **Quelle deaktivieren** | FEHLT |

### 6. Vorlagen — **FEHLT vollständig**

Weder Ansicht noch Dienst. Die Artifact Engine kann Dateien **erzeugen**,
aber es gibt keine Vorlagenverwaltung: kein Speicher, keine Metadaten,
keine Vorschau, kein „Verwenden“.

### 7. Aufgaben — **FEHLT weitgehend**

Es gibt eine Fälligkeitsrechnung für das Wissensupdate
(`updater/zeitplan.py`) — das ist **kein** allgemeiner Aufgabenplaner. Es
fehlen: Aufgabenobjekt, Speicherung, Auslöser, Ausführung, Status,
Historie, Ansicht Heute/Geplant/Wiederkehrend.

### 8. Plugins — **FEHLT (Ansicht), Dienst vollständig**

`Pluginverwaltung` kann prüfen, installieren, aktivieren, deaktivieren,
entfernen, Rechte beschreiben. Nur über die Konsole erreichbar. Keine
Ansicht, kein Katalog.

### 9. Verbundene Dienste — **FEHLT (Ansicht), Dienst teilweise**

`ConnectorRegistry` liefert Info und konfigurierte Kennungen. Es fehlen:
Ansicht, Verbindung testen, Verwalten, Trennen. Die Zugangsdaten liegen
bereits verschlüsselt im Tresor (`security/vault.py`) — Abschnitt 29
(keine Klartext-Zugangsdaten) ist damit erfüllt.

### 10. Einstellungen & Status — **MUSS ANGEPASST WERDEN**

| Anforderung | Zustand |
|---|---|
| Alle Einstellwerte | BEREITS VORHANDEN |
| Systemstatus | TEILWEISE — als JSON-Block, nicht als Liste mit Ampeln |
| Betriebsmodus schnell erreichbar | BEREITS VORHANDEN (Kopfzeile) |
| Backup | BEREITS VORHANDEN |
| **Restore** | TEILWEISE — `restore_info` liest, stellt aber nicht wieder her |
| **Gliederung in acht Gruppen** | FEHLT — heute eine lange Spalte |
| **Lokales Modell auswählen mit Testinferenz** | BEREITS VORHANDEN (Registerkarte Sprachmodell) |

### Querschnitt

| Anforderung | Zustand |
|---|---|
| Linke einklappbare Navigation | FEHLT |
| Aktive Ansicht hervorgehoben | FEHLT |
| Navigation profilspezifisch konfigurierbar | FEHLT |
| **PORTIVA-Classic-Logo (drei verbundene Punkte)** | MUSS ANGEPASST WERDEN — die Datei im Repo zeigt ein älteres, unscharfes P; die Punkte sind nicht als drei verbundene Punkte erkennbar |
| Hauptlogo ohne Fachbereich | BEREITS VORHANDEN (`branding.py`, `MARKE`) |
| Fenstertitel `PORTIVA – <Profilname>` | BEREITS VORHANDEN (`Brand.titel`) |
| Fenster-/Taskleisten-/EXE-Icon | BEREITS VORHANDEN, Datei zu ersetzen |
| **Begrüßungsbild 3 Sekunden beim Start** | FEHLT |
| Keine toten Knöpfe | BEREITS VORHANDEN — heute hat jeder Knopf einen Handler |
| Action Contract Registry | FEHLT |
| Button-Funktionsmatrix | FEHLT |
| Windows-Skalierung 100/125/150 % | UNGEPRÜFT |

---

## 3. Zuordnung: geplante UI-Aktion → vorhandener Dienst

Das ist der Kern von Abschnitt 2 („keine doppelte Geschäftslogik“). Für
jede geplante Aktion steht hier der bereits vorhandene Dienst. Wo „NEU“
steht, gibt es ihn noch nicht.

### Unterhaltung

| Aktion | vorhandener Dienst |
|---|---|
| Nachricht senden | `Controller.ask()` |
| Generierung stoppen | `BackgroundTask.abbrechen()` |
| Neue Unterhaltung | `Controller.new_conversation()` |
| Verlauf öffnen | `Controller.open_conversation()`, `.conversations()`, `.messages()` |
| Unterhaltung exportieren | `Controller.export_conversation()` |
| Datei anhängen | `Controller.add_document()` |
| Quellen anzeigen | `AskOutcome.answer.references` (liegt schon vor) |
| Recherche-Details | `AskOutcome.answer.references` + `hits` — **Adapter NEU** |
| Antwort speichern | `Controller.antwort_speichern()` |

### Unternehmenswissen

| Aktion | vorhandener Dienst |
|---|---|
| Suchen | `MemoryStore.search()` |
| Öffnen / Bearbeiten | `Controller.remember()`, `MemoryStore.get()` |
| Löschen | `Controller.forget()` |
| Neuer Eintrag | `Controller.remember()` |
| Versionen | `MemoryStore.history()` |
| Kategorien mit Anzahl | `WELL_KNOWN_KEYS` + `MemoryStore.list()` — **Adapter NEU** |
| Archivieren | **NEU** (Statusfeld im Store) |

### Belege & Dokumente

| Aktion | vorhandener Dienst |
|---|---|
| Datei auswählen / Drag & Drop | `Controller.add_document()` |
| Liste | `Controller.documents()`, `.search_documents()` |
| Löschen | `Controller.delete_document()` |
| Analysieren | `knowledge/extract.py` über `add_document` |
| Erneut analysieren | **NEU** (dünner Adapter auf `extract`) |
| In Unterhaltung übernehmen | **NEU** (dünner Adapter: Dokumenttext in den Chatkontext) |

### Arbeitsergebnisse

| Aktion | vorhandener Dienst |
|---|---|
| Liste | `Controller.artefakt_liste()` |
| Formate | `Controller.artefakt_formate()` |
| Neu erzeugen | `Controller.datei_erzeugen()` |
| Öffnen | Pfad aus `artefakt_liste` — **Adapter NEU** (`os.startfile`) |
| Exportieren | **NEU** (Kopieren an einen gewählten Ort) |
| Umbenennen / Löschen | **NEU** (`Artefaktwerk`) |
| Versionen | BEREITS VORHANDEN (`_v2`-Logik im `Artefaktwerk`) |

### Wissen & Quellen

| Aktion | vorhandener Dienst |
|---|---|
| Jetzt aktualisieren | `Controller.update_now()` / `updater/pipeline.py` |
| Fälligkeit / Intervall | `Controller.update_due()`, `.update_faelligkeit()` |
| Verlauf | `Controller.update_runs()` |
| Rollback | `Controller.rollback_update()` |
| Quellenregister | `updater/registry.py` |
| Quelle öffnen | **NEU** (dünner Adapter) |
| Quelle deaktivieren | **NEU** (Feld im Register) |
| Pipeline-Schritte anzeigen | `pipeline.py` meldet die Schritte bereits — **nur Anzeige NEU** |

### Vorlagen

| Aktion | Dienst |
|---|---|
| Alles | **NEU** — neues Modul `pkc/vorlagen/`, aufbauend auf `artefakte/` |

### Aufgaben

| Aktion | Dienst |
|---|---|
| Alles | **NEU** — neues Modul `pkc/aufgaben/`; `updater/zeitplan.py` liefert die Fälligkeitsrechnung |

### Plugins

| Aktion | vorhandener Dienst |
|---|---|
| Liste / Stand | `Pluginverwaltung.liste()`, `.stand()` |
| Prüfen | `.pruefen()` |
| Installieren | `.installieren()` |
| Aktivieren / Deaktivieren | `.aktivieren()`, `.deaktivieren()` |
| Deinstallieren | `.entfernen()` |
| Rechte anzeigen | `.rechtebeschreibung()` |
| Katalog | **NEU** (Katalogdatei, analog `model_catalog.json`) |

### Verbundene Dienste

| Aktion | vorhandener Dienst |
|---|---|
| Liste / Status | `ConnectorRegistry.info()` |
| Verbinden | `SecretVault.set()` + `Connector` — **Adapter NEU** |
| Verbindung testen | **NEU** (`Connector.pruefen()` je Connector) |
| Trennen | `SecretVault.delete()` — **Adapter NEU** |

### Einstellungen & Status

| Aktion | vorhandener Dienst |
|---|---|
| Einstellung speichern | `Controller.save_settings()` |
| Betriebsmodus ändern | `Controller.set_mode()` |
| Systemstatus | `Controller.status()` |
| Modell einrichten / prüfen / messen | `Controller.modell_*` (vollständig) |
| Backup | `Controller.backup()` |
| Restore | `Controller.restore_info()` — **Wiederherstellung NEU** |
| Lizenz | `licensing/verify.py` |

**Bilanz** (ausgezählt aus `config/ui_action_registry.yaml`, 69 Aktionen
über alle zehn Ansichten):

| Zustand | Anzahl | Anteil |
|---|---|---|
| **Dienst vorhanden** — nur Oberfläche nötig | **42** | 61 % |
| **Adapter nötig** — Dienst da, dünne Anbindung fehlt | **12** | 17 % |
| **Neu** — Fachlogik existiert noch nicht | **15** | 22 % |

Von den 15 neuen entfallen **9 auf Vorlagen und Aufgaben** — die beiden
Bereiche, die es heute überhaupt nicht gibt. Die übrigen 6 sind einzelne
Ergänzungen an vorhandenen Diensten (archivieren, umbenennen, löschen,
Quelle deaktivieren, Plugin-Katalog, Restore).

Anders gesagt: **rund vier von fünf Aktionen laufen auf Code, der heute
schon da ist und getestet ist.**

---

## 4. Skizze der Action Contract Registry

Vorgesehen als `config/ui_action_registry.yaml`, geprüft durch einen Test,
der jede Kennung gegen den benannten Dienst auflöst. Ein Eintrag ohne
auflösbaren Dienst lässt den Test fallen — damit kann ein toter Knopf gar
nicht erst entstehen.

    - action_id: chat.senden
      screen: unterhaltung
      control: senden_button
      label: "Senden"
      backend_service: app.controller.Controller.ask
      required_capability: chat
      required_permission: null
      input: {frage: str, anhang: optional[path]}
      validation: "nicht leer, hoechstens 8000 Zeichen"
      success_result: "Antwort im Verlauf, Quellen im Panel"
      error_result: "verstaendliche Meldung, Frage bleibt erhalten"
      audit_required: false
      offline_supported: true
      online_required: false
      human_approval_required: false
      test_id: test_ui_aktionen.py::test_chat_senden

Die vollständige Registry entsteht mit der Umsetzung. Ein erster Entwurf
mit allen 58 Kennungen liegt als `config/ui_action_registry.yaml` bei.

---

## 5. Integrationsplan

Sieben Schritte. Jeder Schritt endet grün und ist für sich auslieferbar —
so bleibt der Umbau jederzeit abbrechbar, ohne einen kaputten Zwischenstand
zu hinterlassen.

### Schritt 0 — Branding und Begrüßungsbild *(klein, sofort sichtbar)*
- PORTIVA-Classic-Logo als `assets/branding/` einsetzen (primary, light,
  dark, icon 256, ico) — aus der gelieferten Datei erzeugt, nicht neu
  gezeichnet.
- Begrüßungsfenster: Logo, 3 Sekunden, randlos, mittig, danach Startseite.
  Abbruch per Klick oder Taste; überspringbar per `--kein-startbild`.
- Kein Eingriff in Fachlogik. **Risiko: sehr gering.**

### Schritt 1 — Rahmen: linke Navigation statt Karteireiter
- Neues Modul `src/ui/schale.py`: Fensterrahmen, linke Navigation,
  Kopfzeile, Inhaltsbereich.
- Die sechs vorhandenen Registerkarten wandern **unverändert** als
  Inhaltsflächen hinein. Kein Handler wird angefasst.
- Navigation aus einer Profilangabe (`profile.json` → `navigation`), damit
  Abschnitt 9 („profilspezifisch konfigurierbar“) erfüllt ist.
- **Risiko: mittel** — betrifft jeden Test, der `MainWindow` aufbaut.

### Schritt 2 — Unterhaltung neu
- Quellenpanel als einklappbare Karten mit Nummer, Titel, Art, Herausgeber,
  Datum, Primär/Sekundär, Öffnen, Details.
- Recherche-Details als eigener, standardmäßig geschlossener Bereich.
- Enter sendet, Shift+Enter Zeilenumbruch, Strg+N, Escape.
- Datei anhängen direkt an der Eingabe; Drag & Drop siehe Risiko R3.
- **Risiko: mittel.**

### Schritt 3 — die drei Ansichten ohne neue Fachlogik
Arbeitsergebnisse, Plugins, Verbundene Dienste. Reine Oberfläche auf
vorhandene Dienste plus die genannten dünnen Adapter.
- **Risiko: gering.**

### Schritt 4 — die drei vorhandenen Ansichten nachziehen
Unternehmenswissen (Kacheln, zuletzt geändert), Belege & Dokumente
(Workflow-Tabelle, erneut analysieren, in Unterhaltung übernehmen),
Wissen & Quellen (Kennzahlen, Pipeline-Anzeige, Quelle deaktivieren).
- **Risiko: gering bis mittel.**

### Schritt 5 — neue Fachlogik
`pkc/vorlagen/` und `pkc/aufgaben/` samt Ansichten. Das ist der einzige
Schritt, der wirklich neue Fachlogik erzeugt — und der einzige, der ohne
weitere Absprache über den reinen UI-Auftrag hinausginge.
- **Risiko: mittel** — hier entstehen neue Datenmodelle und ein Planer,
  der im Hintergrund läuft.

### Schritt 6 — Einstellungen & Status neu, Nachweise
Acht Gruppen, Systemstatus als Ampelliste. Danach Action Registry,
Button-Funktionsmatrix, End-to-End-Tests je Primäraktion, Fehlerpfade,
Regressionsvergleich gegen `BASELINE_VOR_UI_UMBAU.md`, Dokumentation.
- **Risiko: gering.**

---

## 6. Risiken für bestehende Funktionen

| # | Risiko | Auswirkung | Gegenmaßnahme |
|---|---|---|---|
| R1 | **`tk_app.py` ist eine einzige Datei mit 2008 Zeilen.** Ein Umbau des Rahmens berührt jede Ansicht. | Mittlere bis hohe Wahrscheinlichkeit von Folgefehlern | Aufteilen in `ui/ansichten/*.py` **vor** dem Umbau; jede Ansicht behält ihre Handler unverändert |
| R2 | **Die vorhandenen Oberflächentests prüfen gegen `tk_double.py`.** Der Rahmenumbau lässt sie fallen. | 30+ Tests | Das Doppel um die neuen Widgets erweitern, bevor der Rahmen umgebaut wird. Kein Test wird gelöscht oder abgeschwächt |
| R3 | **Drag & Drop kann Tkinter nicht von sich aus.** Es bräuchte `tkinterdnd2` — eine zusätzliche Abhängigkeit im portablen Paket. | Anforderung aus Abschnitt 33 | Zur Entscheidung vorzulegen: (a) Abhängigkeit aufnehmen, (b) auf Windows über die native Schnittstelle lösen, (c) dokumentiert weglassen und „Datei auswählen“ prominent anbieten. **Empfehlung: (b)** — keine neue Abhängigkeit, Windows ist die Zielplattform |
| R4 | **Vorlagen und Aufgaben sind neue Fachlogik**, nicht Oberfläche. | Umfang deutlich größer als der Rest | Als eigener Schritt 5, getrennt freizugeben |
| R5 | **Ein Aufgabenplaner läuft im Hintergrund** und kann Vorgänge starten, während der Benutzer arbeitet. | Berührt §68/§69 (kein verborgener Fernzugriff, keine Telemetrie) | Nur lokale Aufgaben, sichtbar, abschaltbar, protokolliert |
| R6 | **Das Begrüßungsbild verzögert den Start um 3 Sekunden.** | Der Modellvorlauf beginnt später | Vorladen des Modells **während** das Bild steht, nicht danach — dann kostet es nichts, sondern gewinnt Zeit |
| R7 | **Das Logo im Repo ist nicht das Classic-Logo.** | Verstoß gegen Abschnitt 4 | Aus der gelieferten Datei erzeugen; `test_branding.py` um eine Prüfung der Bildgröße und des Seitenverhältnisses erweitern |
| R8 | **Restore ist heute nicht umgesetzt** (nur `restore_info`). Eine Ansicht mit einem Knopf „Wiederherstellen“ wäre ein toter Knopf. | Verstoß gegen Abschnitt 34 | Entweder Restore ausprogrammieren oder den Knopf sichtbar als „noch nicht verfügbar“ kennzeichnen. **Empfehlung: ausprogrammieren** — die Sicherung existiert bereits |
| R9 | **Windows-Skalierung 125/150 %** ist nie geprüft worden. Ein festes Pixelraster bricht dort. | Unbedienbar auf vielen Bürorechnern | Durchgehend relative Maße; im Bauablauf mit drei Skalierungen prüfen |

---

## 7. Erwartete Änderungen je Datei

### Neu

| Datei | Zweck |
|---|---|
| `src/ui/schale.py` | Fensterrahmen, linke Navigation, Kopfzeile |
| `src/ui/startbild.py` | Begrüßungsbild, 3 Sekunden |
| `src/ui/ansichten/__init__.py` | Registrierung der Ansichten |
| `src/ui/ansichten/unterhaltung.py` | aus `tk_app.py` herausgelöst und erweitert |
| `src/ui/ansichten/unternehmenswissen.py` | herausgelöst, Kacheln ergänzt |
| `src/ui/ansichten/belege.py` | herausgelöst, Workflow ergänzt |
| `src/ui/ansichten/arbeitsergebnisse.py` | neu |
| `src/ui/ansichten/wissen_quellen.py` | herausgelöst, Kennzahlen und Pipeline ergänzt |
| `src/ui/ansichten/vorlagen.py` | neu |
| `src/ui/ansichten/aufgaben.py` | neu |
| `src/ui/ansichten/plugins.py` | neu |
| `src/ui/ansichten/dienste.py` | neu |
| `src/ui/ansichten/einstellungen.py` | herausgelöst, gegliedert |
| `src/ui/quellenpanel.py` | Quellenkarten und Recherche-Details |
| `src/pkc/vorlagen/` | neues Modul (Schritt 5) |
| `src/pkc/aufgaben/` | neues Modul (Schritt 5) |
| `config/ui_action_registry.yaml` | Action Contract Registry |
| `UI_UX_KONZEPT.md`, `UI_BUTTON_FUNKTIONSMATRIX.md`, `UI_REGRESSION_TEST_REPORT.md` | Nachweise |

### Geändert

| Datei | Änderung | Umfang |
|---|---|---|
| `src/ui/tk_app.py` | wird zum schlanken Einstieg; Ansichten wandern aus | groß, aber **verschiebend, nicht umschreibend** |
| `src/app/controller.py` | 11 dünne Adapter (öffnen, exportieren, umbenennen, erneut analysieren, übernehmen, Quelle öffnen/deaktivieren, Dienst verbinden/testen/trennen, Restore) | mittel, nur Ergänzungen |
| `src/pkc/memory/store.py` | Feld „archiviert“ | klein |
| `src/pkc/artefakte/werk.py` | umbenennen, löschen | klein |
| `src/pkc/updater/registry.py` | Feld „aktiv“ | klein |
| `src/pkc/branding.py` | Variante für das Begrüßungsbild | klein |
| `src/pkc/profile.py` | Navigationsangabe aus dem Profil | klein |
| `assets/branding/*` | Classic-Logo ersetzt die alten Dateien | Dateien |
| `tests/tk_double.py` | neue Widgets ergänzen | mittel |
| `tests/test_gui_logic.py`, `test_modell_im_fenster.py` | an den neuen Rahmen anpassen | mittel |
| `tools/anleitung_erzeugen.py` | Anleitung auf zehn Bereiche umstellen | groß |
| `.github/workflows/build-windows.yml` | Skalierungsprüfung 100/125/150 % | klein |

### Ausdrücklich **nicht** angefasst

`rag/`, `retrieval/`, `llm/`, `knowledge/`, `db/`, `licensing/`,
`security/`, `plugins/` (nur genutzt), `connectors/` (nur genutzt),
`updater/pipeline.py`. Dort ändert sich nichts — das ist die Zusage aus
Abschnitt 2 und 52.

---

## 8. Was ich zur Entscheidung vorlege

Vier Punkte, bei denen ich Ihre Entscheidung brauche, bevor es losgeht:

1. **Umfang.** Ihr Anschreiben sagt „Oberfläche anpassen, ohne andere
   Funktionalitäten zu ändern“. Der Auftrag verlangt zusätzlich Vorlagen
   und Aufgaben — beides ist neue Fachlogik, kein Layout. Sollen Schritte
   0–4 und 6 zuerst laufen (reiner Oberflächenumbau, kein Eingriff in die
   Fachlogik) und Schritt 5 danach als eigener Auftrag?
2. **Drag & Drop** (R3): native Windows-Lösung, zusätzliche Abhängigkeit,
   oder dokumentiert weglassen? Meine Empfehlung: native Windows-Lösung.
3. **Restore** (R8): ausprogrammieren oder sichtbar als „noch nicht
   verfügbar“ kennzeichnen? Meine Empfehlung: ausprogrammieren.
4. **Wartezeit.** Siehe `ANTWORTZEIT_KONZEPT.md`. Der erste Schritt dort
   ist klein, misst sich sauber und bringt nach den vorliegenden Zahlen
   etwa den Faktor drei. Soll er vor dem UI-Umbau laufen?

---

**STOPP.** Es wird nichts umgesetzt, bevor Sie freigeben.
