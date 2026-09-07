# PORTIVA - Button-Funktionsmatrix

Erzeugt aus dem laufenden Fenster mit
`python tools/buttonmatrix_erzeugen.py` - nicht von Hand gepflegt.
Eine abgeschriebene Matrix stimmt schon beim naechsten Umbau
nicht mehr, und eine Matrix, die nicht stimmt, ist
gefaehrlicher als keine: sie behauptet Vollstaendigkeit.

**Was maschinell geprueft ist:** dass jedes sichtbare
Bedienelement einen Rueckruf hat. Ein toter Knopf kann so gar
nicht erst entstehen.

**Was nicht maschinell prueftbar ist:** ob der Rueckruf das
Richtige tut. Dafuer stehen die Tests - ihre Zahl je
Testdatei steht unten.

## Unterhaltung

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Senden | vorhanden |
| Schaltflaeche | Stoppen | vorhanden |
| Schaltflaeche | Datei anhaengen | vorhanden |
| anklickbar | Datei anhaengen (Ziehen ist auf diesem System nicht verfuegbar) | vorhanden |
| Schaltflaeche | Antwort speichern | vorhanden |
| Schaltflaeche | Neue Unterhaltung | vorhanden |
| Schaltflaeche | ausblenden | vorhanden |
| Schaltflaeche | Recherche-Details anzeigen | vorhanden |
| Schaltflaeche | Unterhaltung exportieren | vorhanden |

## Unternehmenswissen

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Suchen | vorhanden |
| Schaltflaeche | Alles anzeigen | vorhanden |
| anklickbar | Unternehmensprofil | vorhanden |
| anklickbar | 0 Eintraege | vorhanden |
| anklickbar | Buchhaltung | vorhanden |
| anklickbar | 0 Eintraege | vorhanden |
| anklickbar | Prozesse & Regeln | vorhanden |
| anklickbar | 0 Eintraege | vorhanden |
| anklickbar | Personen & Rollen | vorhanden |
| anklickbar | 0 Eintraege | vorhanden |
| anklickbar | Kunden & Lieferanten | vorhanden |
| anklickbar | 0 Eintraege | vorhanden |
| anklickbar | Vorlagen & Entscheidungen | vorhanden |
| anklickbar | 0 Eintraege | vorhanden |
| Schaltflaeche | Neu / Aendern | vorhanden |
| Schaltflaeche | Verlauf | vorhanden |
| Schaltflaeche | Archivieren | vorhanden |
| Schaltflaeche | Onboarding fortsetzen | vorhanden |
| Schaltflaeche | Profil exportieren | vorhanden |

## Belege & Dokumente

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Datei auswaehlen | vorhanden |
| Schaltflaeche | Oeffnen | vorhanden |
| Schaltflaeche | Erneut analysieren | vorhanden |
| Schaltflaeche | In Unterhaltung uebernehmen | vorhanden |
| Schaltflaeche | Aktualisieren | vorhanden |

## Arbeitsergebnisse

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Aktualisieren | vorhanden |
| Schaltflaeche | Oeffnen | vorhanden |
| Schaltflaeche | Exportieren | vorhanden |
| Schaltflaeche | Umbenennen | vorhanden |
| Schaltflaeche | Loeschen | vorhanden |

## Wissen & Quellen

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Wissen jetzt aktualisieren | vorhanden |
| Schaltflaeche | Trockenlauf (nichts schreiben) | vorhanden |
| Schaltflaeche | Letzten Lauf zuruecknehmen | vorhanden |
| Schaltflaeche | Sicherung erstellen | vorhanden |

## Vorlagen

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Zu den Arbeitsergebnissen | vorhanden |

## Aufgaben & Automationen

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Zu Wissen & Quellen | vorhanden |

## Plugins & Erweiterungen

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Aus Datei installieren | vorhanden |
| Schaltflaeche | Aktivieren | vorhanden |
| Schaltflaeche | Deaktivieren | vorhanden |
| Schaltflaeche | Berechtigungen | vorhanden |
| Schaltflaeche | Deinstallieren | vorhanden |
| Schaltflaeche | Aktualisieren | vorhanden |

## Verbundene Dienste

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Verbindung testen | vorhanden |
| Schaltflaeche | Trennen | vorhanden |
| Schaltflaeche | Aktualisieren | vorhanden |

## Einstellungen & Status

| Art | Beschriftung | Rueckruf |
|---|---|---|
| Schaltflaeche | Einstellungen speichern | vorhanden |
| Schaltflaeche | Anderes Modell einrichten | vorhanden |
| Schaltflaeche | Vorhandene Modelldatei uebernehmen | vorhanden |
| Schaltflaeche | Lage neu pruefen | vorhanden |
| Schaltflaeche | Modell ausprobieren | vorhanden |
| Schaltflaeche | Wartezeit messen | vorhanden |
| Schaltflaeche | Status aktualisieren | vorhanden |
| Schaltflaeche | Sicherung erstellen | vorhanden |
| Schaltflaeche | Sicherung wiederherstellen | vorhanden |

## Bilanz

- Bedienelemente insgesamt: **62**
- davon ohne Rueckruf: **0**

## Tests je Datei

| Testdatei | Tests |
|---|---|
| test_abnahme_kette.py | 3 |
| test_anleitung.py | 15 |
| test_ansichten_schritt4.py | 12 |
| test_antwortdarstellung.py | 19 |
| test_antwortqualitaet.py | 14 |
| test_artefakte.py | 20 |
| test_betriebsmodi.py | 14 |
| test_branding.py | 19 |
| test_checkpoints.py | 5 |
| test_cli.py | 15 |
| test_controller.py | 10 |
| test_fachliche_faelle.py | 4 |
| test_fragetyp.py | 14 |
| test_gui_logic.py | 31 |
| test_keine_toten_knoepfe.py | 4 |
| test_kundentrennung.py | 15 |
| test_lizenzierung.py | 18 |
| test_llm_providers.py | 18 |
| test_markdown.py | 14 |
| test_modell_einrichten.py | 23 |
| test_modell_im_fenster.py | 19 |
| test_modell_uebernehmen.py | 13 |
| test_modelldienst.py | 18 |
| test_modelltempo.py | 23 |
| test_netzpruefung.py | 11 |
| test_neue_ansichten.py | 23 |
| test_plugins.py | 32 |
| test_portability.py | 14 |
| test_produktreife.py | 15 |
| test_quellenpruefung.py | 13 |
| test_robots.py | 4 |
| test_schale.py | 9 |
| test_sicherheit_freigaben.py | 15 |
| test_softwareupdate.py | 11 |
| test_start.py | 7 |
| test_startbild.py | 8 |
| test_unterhaltung.py | 15 |
| test_updater_pipeline.py | 17 |
| test_wartezeit.py | 57 |
| test_wiederherstellen.py | 11 |
| test_wissenszeitplan.py | 22 |
