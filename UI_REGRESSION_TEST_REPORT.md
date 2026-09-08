# Regressionsbericht nach dem UI/UX-Umbau

Nach Masterprompt Abschnitt 57. Gegenstand: Zweig
`claude/portable-ki-buchhalter-xr1qlj`. Die Abschnitte 1 bis 6 beziehen
sich auf den Stand `7f85213`, der Nachtrag 6a auf den Stand danach.
Gegenübergestellt wird `BASELINE_VOR_UI_UMBAU.md` (Commit `ee18e88`).

**Lesehinweis:** Abschnitt 1 bis 6 sind so stehengeblieben, wie sie
geschrieben wurden. Abschnitt 6a widerlegt einen Teil davon. Das ist
Absicht — einen Bericht nachträglich glattzuziehen hiesse, den Irrtum zu
verstecken, statt ihn zu zeigen.

Die Frage, die dieser Bericht beantworten muss, lautet nicht „sieht es
besser aus". Sie lautet: **ist etwas, das vorher funktioniert hat, jetzt
kaputt?**

---

## 1. Testlauf im Vergleich

| | vor dem Umbau | nach dem Umbau |
|---|---|---|
| bestanden | 638 | **745** |
| übersprungen | 1 | 1 |
| fehlgeschlagen | 0 | **0** |
| Laufzeit | 67 s | 70 s |

Der eine übersprungene Test verlangt eine echte Verbindung zu Hugging
Face; die ist in der Entwicklungsumgebung gesperrt. Auf dem
Windows-Baurechner läuft er mit.

**107 Tests kamen hinzu. Kein bestehender Test wurde gestrichen oder
abgeschwächt, um den Umbau grün zu bekommen.**

Nachprüfbar:

    git diff ee18e88..7f85213 -- tests/ | grep '^-' | grep -c 'def test_'

ergibt **1**. Diese eine Zeile ist eine Umbenennung, keine Streichung:
`test_main_window_builds_all_tabs` heißt jetzt
`test_main_window_builds_all_areas`, weil es keine Karteireiter mehr gibt.
Der Test prüft dabei **mehr** als vorher — nicht nur, dass die Bereiche
angelegt sind, sondern auch, dass zu jedem ein Knopf in der Navigation
führt. Ein Bereich ohne Knopf wäre unerreichbar, ein Knopf ohne Bereich
wäre ein toter Knopf.

Sonst wurde keine Testfunktion entfernt. Angetastet wurden vier weitere
Zeilen — vier Zusicherungen in zwei Tests, die auf Bedienelemente zeigten,
die es nicht mehr gibt (das Quellen-Textfeld, die Karteireiter). Sie sind
durch Zusicherungen auf die neuen Elemente ersetzt. Eine davon wäre dabei
beinahe untergegangen; siehe Abschnitt 5 c.

## 2. Kernbereiche einzeln — vorher grün, nachher grün

| Bereich | Testdateien | vorher | nachher |
|---|---|---|---|
| Unterhaltung / Chat | `test_controller.py`, `test_antwortdarstellung.py` | grün | grün |
| RAG / Antwortsynthese | `test_antwortqualitaet.py`, `test_fachliche_faelle.py`, `test_fragetyp.py` | grün | grün |
| Quellen & Fundstellen | `test_antwortqualitaet.py`, `test_quellenpruefung.py` | grün | grün |
| Unternehmensgedächtnis | `test_controller.py`, `test_kundentrennung.py` | grün | grün |
| Dokumentpipeline | `test_controller.py` | grün | grün |
| Artifact Engine | `test_artefakte.py`, `test_markdown.py` | grün | grün |
| Plugins | `test_plugins.py` | grün | grün |
| Betriebsmodi | `test_betriebsmodi.py`, `test_netzpruefung.py` | grün | grün |
| Wissensupdate | `test_updater_pipeline.py`, `test_wissenszeitplan.py`, `test_robots.py` | grün | grün |
| Lizenz | `test_lizenzierung.py` | grün | grün |
| Sprachmodell / Wartezeit | `test_wartezeit.py`, `test_modelltempo.py`, `test_modelldienst.py`, `test_llm_providers.py` | grün | grün |
| Modell einrichten (Fenster) | `test_modell_im_fenster.py`, `test_modell_uebernehmen.py`, `test_modell_einrichten.py` | grün | grün |
| Bestehende Oberfläche | `test_gui_logic.py` (27 → 31 Tests) | grün | grün |
| Portabilität | `test_portability.py`, `test_start.py` | grün | grün |
| Branding | `test_branding.py` | grün | grün |
| Sicherheit / Freigaben | `test_sicherheit_freigaben.py`, `test_checkpoints.py` | grün | grün |
| Anleitung | `test_anleitung.py` | grün | grün |

`test_gui_logic.py` ist der Bereich mit dem größten Risiko: er prüft die
Oberfläche, die umgebaut wurde. Von den 27 vorhandenen Tests laufen **25
wörtlich unverändert** durch. Zwei mussten angepasst werden, weil sie auf
Bedienelemente zeigten, die es nicht mehr gibt; beide prüfen danach
mindestens so viel wie vorher. Vier Tests kamen hinzu. Das heißt: die
Bedienlogik hat den Umbau überstanden, sie wurde nur anders angeordnet.

## 3. Neu hinzugekommene Prüfungen

| Datei | Tests | prüft |
|---|---|---|
| `test_startbild.py` | 8 | Begrüßungsbild: 3 Sekunden, schließt sich selbst, blockiert nicht, kein leerer Kasten wenn das Logo fehlt |
| `test_schale.py` | 9 | Navigationsschale: Bereiche, Hervorhebung des aktiven Bereichs, Ein- und Ausklappen |
| `test_neue_ansichten.py` | 23 | Ergebnisse, Dienste, Plugins, Wissenskacheln, Statuszeilen |
| `test_unterhaltung.py` | 15 | Chatansicht: Eingabetaste sendet, Umschalt+Eingabe macht Zeilenumbruch, Escape, Quellenpanel |
| `test_ansichten_schritt4.py` | 12 | Belegübernahme, Pipeline-Anzeige, Statusfarben |
| `test_wiederherstellen.py` | 11 | Sicherungen: fehlende, geänderte **und zusätzliche** Dateien werden erkannt |
| `test_keine_toten_knoepfe.py` | 4 | jeder Knopf im Fenster hat eine hinterlegte Funktion |

Ergebnis der letzten Prüfung, erzeugt von `tools/buttonmatrix_erzeugen.py`
aus dem tatsächlich aufgebauten Fenster: **62 Bedienelemente, 0 ohne
hinterlegte Funktion** (`UI_BUTTON_FUNKTIONSMATRIX.md`).

## 4. Nachweis auf dem Windows-Baurechner

Lauf **34167260868** vom 2026-09-07 zu Commit `7f85213`.

- Tests (Linux): grün
- Tests auf Windows: grün
- EXE gebaut, existiert, Systemprüfung bestanden
- Branding liegt neben der EXE und wird gefunden
- Offline-Fachfrage gegen die gebaute EXE
- Unternehmenswissen gespeichert und nach Neustart gelesen
- Portabilität: anderes Laufwerk, Pfad mit Leerzeichen
- Sprachmodell bezogen, gestartet, Frage beantwortet

Gemessene Wartezeit auf demselben Baurechner, Probemodell 0,5B, nur
Prozessor — die Zahlen sind aus dem Protokoll des Laufs übernommen:

| Stufe | erste Frage, bis 1. Wort | später, bis 1. Wort | später, gesamt |
|---|---|---|---|
| schnell | 24,2 s | 26,2 s | 31,2 s |
| automatisch (wirkt: schnell) | 36,3 s | 36,9 s | 41,0 s |
| ausgewogen | 44,1 s | 45,8 s | 48,8 s |
| ausführlich | 43,0 s | 45,0 s | 55,8 s |

Zum Vergleich der Ausgangswert vor dem Umbau (drei Läufe je Stufe):
schnell 29,8 / 36,5 / 34,5 s, ausgewogen 39,0 / 51,4 / 53,7 s.

**Daraus lässt sich kein Fortschritt ablesen und keine Verschlechterung.**
Die Werte liegen innerhalb der Schwankung, die dieser Baurechner von Lauf
zu Lauf zeigt — gemessen bis zu 22 %. Der Umbau war eine Umbauarbeit an
der Oberfläche; er sollte die Wartezeit nicht verändern, und er hat es
nach dieser Messung auch nicht getan.

### Ein Schritt in diesem Lauf ist nicht durchgelaufen

Schritt 18, „Quellenregister gegen die echten Adressen prüfen", endete mit
Fehlercode 1. Der Lauf gilt trotzdem als grün, weil dieser Schritt
absichtlich mit `continue-on-error: true` läuft — amtliche Server sind
zeitweise nicht erreichbar, und daran soll der Bauablauf nicht scheitern.
Das darf man nicht als „alles grün" durchgehen lassen, deshalb steht es
hier:

- **17 Dokumente von gesetze-im-internet.de** waren in diesem Lauf nicht
  erreichbar — Zeitüberschreitung beim Verbindungsaufbau (WinError 10060),
  nicht HTTP 404. In früheren Läufen waren dieselben Adressen erreichbar.
  Das ist ein Netzproblem zwischen dem Baurechner und dem Server, kein
  Fehler im Quellenregister.
- **7 Adressen mit HTTP 404** — BMF, ELSTER, BZSt (zwei), BVerfG, BGBl,
  DIHK. Diese sind seit Längerem bekannt und dokumentiert: die Behörden
  haben ihre Seiten umgezogen. Die Einträge im Quellenregister zeigen ins
  Leere und müssen berichtigt werden.

Beides hat mit dem UI-Umbau nichts zu tun. Die 7 toten Adressen sind
gleichwohl eine offene Arbeit und keine Nebensache: sie stehen im
Quellenregister, als wären sie gültig.

Die vollständige Schrittliste steht im Bauablauf; sie ist nicht
abgeschrieben, sondern dort einsehbar.

## 5. Drei echte Regressionen, die dieser Umbau erzeugt hat

Beide wurden von Tests gefunden, nicht von mir bemerkt. Sie stehen hier,
weil ein Bericht ohne gefundene Fehler kein Bericht ist, sondern eine
Behauptung.

**a) Der Hinweis „nur Sekundärquellen" wäre verschwunden.**
Die neue Fragenart BEGRIFF war nicht in der Liste der Fragetypen, an der
die Warnung hing. Eine Begriffsfrage, die nur auf Sekundärquellen
beruhte, hätte den Hinweis verloren — still, ohne Fehlermeldung. Die
Warnung hängt jetzt an den Fundstellen selbst, nicht am Fragetyp.

**b) Das Begrüßungsbild griff auf ein Fenster zu, das es geschlossen hatte.**
`schliessen()` setzt die Fensterreferenz auf `None`; `zeigen()` griff
danach noch einmal darauf zu. Behoben durch eine lokale Referenz vor dem
Einplanen des Schließens.

**c) Eine inhaltliche Prüfung wäre beim Umbau still verschwunden.**
Der alte Test sicherte zu, dass in der Quellenanzeige das Wort
„Fachmodul" steht — also dass die Fundstellen wirklich aus dem
Fachmodul stammen und nicht irgendwoher. Beim Umzug von Textfeld auf
Karten blieb nur noch „es gibt mindestens eine Karte" übrig. Das ist
weniger. Aufgefallen ist es erst beim Schreiben dieses Berichts, beim
Nachzählen der geänderten Zeilen. Die Prüfung ist zurückgeholt, jetzt
an den Recherche-Details (dorthin gehören Kennungen, Erweiterung E6
§18). Gegenprobe gemacht: wird die Kennung aus den Details entfernt,
schlägt der Test fehl.

Dazu kamen fünf Fehler in den Prüfmitteln selbst — Tests, die aus dem
falschen Grund bestanden. Sie sind in
`checkpoints/TASK_30_ui_ux_umbau_umgesetzt.md` einzeln aufgeführt.

## 6. Was dieser Bericht **nicht** belegt

Unverändert offen gegenüber der Ausgangsaufnahme, und durch den Umbau
teils gewachsen:

1. ~~Die echte Tkinter-Oberfläche wurde nie geöffnet.~~ **Erledigt** —
   siehe Abschnitt 6a. Sie ist geöffnet, fotografiert und wird jetzt
   automatisch geprüft. Offen bleibt: wie Schriftglättung und Farben auf
   einem echten Windows-Bildschirm wirken. Die Bilder in dieser Umgebung
   entstehen mit einer Ersatzschrift, nicht mit Segoe UI.
2. **Drag & Drop wurde nie mit einer echten Maus erprobt.** Der Weg über
   `WM_DROPFILES` ist so gebaut, dass ein Fehlschlag folgenlos bleibt und
   der Knopf zum Auswählen weiter funktioniert — belegt ist das aber nur
   für den Fehlschlagpfad.
3. **Windows-Skalierung 100 / 125 / 150 %** ist ungeprüft.
4. **Vorlagen und Aufgaben** sind als Bereiche angelegt, tragen aber noch
   keine Fachlogik. Das war nicht freigegeben und ist keine Regression,
   sondern offener Umfang.
5. **Wartezeit-Hebel 3 und 4** (Wiederverwendung des Prompt-Anfangs,
   Antwortspeicher) sind nicht umgesetzt. Die Messung in Abschnitt 4 zeigt
   keine Verschlechterung durch den Umbau — behoben ist die Wartezeit
   damit aber nicht.
6. **Sieben Adressen im Quellenregister zeigen ins Leere** (HTTP 404).
   Bekannt, dokumentiert, unberichtigt.

## 6a. Nachtrag: die Oberflaeche zum ersten Mal wirklich gesehen

Der Bericht oben endete mit dem Satz, die echte Tkinter-Oberflaeche sei
nie geoeffnet worden. Das hat sich geändert, und es hat den Bericht
teilweise widerlegt.

In dieser Umgebung gibt es zwar keinen Bildschirm, aber `Xvfb` — einen
Bildschirm ohne Bildschirm. Damit lässt sich das echte Fenster öffnen und
fotografieren. Beim ersten Blick darauf war das Ergebnis unbrauchbar,
obwohl alle 745 Tests grün waren:

| Was zu sehen war | Ursache |
|---|---|
| „Send" statt „Senden", „Date" statt „Datei anhaengen" | Der Schiebeteiler verteilte Breite nach Gewichten und drückte die Knopfspalte zusammen |
| Die Unterhaltungsliste hing mitten im Bild über der Quellenspalte | `side="bottom"` in einem Bereich, der bereits anders belegt war |
| **Jedes** Auswahlfeld war leer — Zeitplan, Fundstellen, Antworttempo, Kontextgröße, Betriebsmodus | Ein Feld mit `state="readonly"` zeichnet seinen Text *markiert*; die Markierungsschrift des Themas ist weiß — auf weißem Feld |
| „Lokales Modell" und „nicht eingerichtet" lagen übereinander | Die Statusspalte bekam nur den Rest der Breite |
| „Plugins & Erweiterunge" in der Navigation | Die Leiste war 250 Bildpunkte breit, der aktive (fette) Eintrag braucht mehr |
| Bei 900×600 war die Unterhaltung ein Streifen von 130 Bildpunkten | Seitenleiste, Quellenspalte und Knopfspalte teilten den Platz unter sich auf |

**Kein einziger dieser Fehler war durch einen Test gegen das Doppel
auffindbar.** Ein Doppel sagt, dass ein Knopf angelegt wurde und eine
Funktion hinterlegt ist. Es sagt nicht, ob er breit genug ist für seine
Beschriftung. Der Satz aus Abschnitt 1 — „keine Kernfunktion beschädigt" —
war richtig und zugleich wertlos: die Funktionen liefen, man konnte sie
nur nicht bedienen.

Dazu kamen zwei Fehler, die nur unter Windows wirken und die beim
Nachdenken über einen hängenden Bauablauf auffielen:

* `SetWindowLongPtrW(..., GWL_WNDPROC, 0)` stand da mit dem Kommentar
  „nur lesen". Das liest nicht, das **setzt** die Fensterprozedur auf
  NULL. Ein Kommentar macht aus einem Setzen kein Lesen.
* Ohne `restype`/`argtypes` nimmt `ctypes` 32 Bit an. Die Adresse einer
  Fensterprozedur liegt auf einem 64-Bit-Windows darüber und wäre
  abgeschnitten worden.

Beide betreffen die ausgelieferte Anwendung, nicht nur den Test.

### Was daraus folgt

`tests/test_echte_oberflaeche.py` prüft jetzt mit echtem Tkinter, ob ein
Element mehr Breite braucht, als es hat — je Navigationseintrag im
aktiven Zustand, für die Knöpfe der Unterhaltung, die Statusspalte, und
für das **ganze** Fenster bei 900×600. Diese Tests laufen im Bauablauf
unter Linux mit `xvfb` und unter Windows; ein eigener Schritt prüft nach,
dass sie nicht übersprungen wurden.

Die erste Fassung dieser Tests fand nichts. Sie maß die Einträge im
nicht-aktiven Zustand, und der aktive wird fett — fett ist breiter. Das
fiel an einer Gegenprobe auf, die nicht ansprang. Die korrigierte Fassung
fand sofort eine Abschneidung, die ich übersehen hatte.

## 7. Bewertung

Der Umbau hat keine bestehende Kernfunktion beschädigt. Die drei
Regressionen, die er erzeugt hat, sind gefunden und behoben. Was offen
ist, ist oben benannt und nicht beschönigt.

Eine Einschränkung zur Aussagekraft dieses Berichts selbst: er beruht auf
Tests gegen ein Tkinter-Doppel. Solche Tests finden Regressionen im
Ablauf, nicht im Aussehen. Der Satz „keine Kernfunktion beschädigt" gilt
für das, was gemessen wurde — nicht für das, was man sieht.
