# TASK 33 — Vorlagen: das Schild an der Tür hat jetzt ein Zimmer

Checkpoint nach Masterprompt Abschnitt 55. Zweig
`claude/portable-ki-buchhalter-xr1qlj`, 11.09.2026, Paketfassung 19.

## 1. Der Anlass

Niels hat gefragt, was „Fachlogik" eigentlich heißt und was dort zu tun
sei. Die Antwort stand in `FACHLOGIK_OFFEN.md`: von zehn Bereichen waren
acht eingerichtet, bei **Vorlagen** und **Aufgaben** hing nur das Schild
an der Tür. Auf die Frage nach der Reihenfolge hat er geantwortet „nimm
deinen Vorschlag" — also Vorlagen zuerst, Aufgaben nach Weg C, sobald
Vorlagen stehen.

## 2. Was gebaut wurde

Neues Paket `src/pkc/vorlagen/`:

| Datei | Wofür |
|---|---|
| `platzhalter.py` | `{{name}}` finden und füllen; was fehlt, bleibt stehen |
| `modell.py` | `Vorlage` und `Vorschau` |
| `speicher.py` | Aufnehmen, finden, entfernen; Verzeichnis + Rumpfdateien |
| `werte.py` | Werte aus Eingabe, Unternehmensgedächtnis und Datum |
| `werk.py` | Vorschau und Erzeugen über die Artefakt-Engine |
| `mitgeliefert.py` | Übernahme der ausgelieferten Vorlagen, ohne eigene zu überschreiben |

Dazu sechs mitgelieferte Vorlagen unter `assets/vorlagen/`, der Bereich
in der Oberfläche (`_build_templates_tab` in `src/ui/tk_app.py`), sechs
Methoden am Controller und Kapitel 13 der Bedienungsanleitung mit Bild.

## 3. Die eine Entscheidung, um die es ging

**Ein Platzhalter ohne Wert bleibt stehen.** Er wird nicht durch Leere
ersetzt.

Der Grund ist nicht technisch. Ein Brief mit „Sehr geehrte Damen und
Herren der {{firma.name}}," fällt beim Durchlesen auf. Einer, in dem der
Name stillschweigend fehlt, geht raus. Ein sichtbarer Fehler ist besser
als ein unsichtbarer — dasselbe Prinzip wie bei den Rechenprüfungen aus
TASK 32.

Deshalb verhindern offene Stellen das Erzeugen auch **nicht**. Ein
Entwurf, in dem drei Stellen von Hand zu ergänzen sind, ist ein
gebräuchliches Arbeitsergebnis. Das Erzeugen zu verweigern wäre
bevormundend.

## 4. Die Sicherheitsvorgaben, die hier greifen

* **Abschnitt 61 (Kundentrennung).** Vorlagen liegen unter
  `workspace/vorlagen` und damit im Kundenbereich. Eine Vorlage trägt
  Briefkopf und Formulierungen eines bestimmten Unternehmens; sie hat
  bei einem anderen nichts zu suchen. `werte.py` liest ausschließlich
  aus dem übergebenen Gedächtnis — es gibt dort keinen Weg zu einem
  anderen.
* **Abschnitt 20 (keine unkontrollierte Host-Speicherung).** Nichts
  liegt im Programmordner, nichts auf dem Wirtsrechner.
* **Freigabepflicht.** Jede aus einer Vorlage erzeugte Datei trägt den
  Hinweis, dass sie fachliche Zuarbeit ist und von einem Menschen zu
  prüfen ist. Sie sieht aus wie ein fertiges Dokument — sie ist keines.

## 5. Eigene Fehler beim Bauen

1. **Der erste Aufbau benutzte ein `PanedWindow`.** Mein eigener
   `OBERFLAECHEN_STANDARD.md` verbietet das, und der Test dazu hat es
   sofort gefunden. Ersetzt durch `grid` mit `minsize`.
2. **Die Spaltenbreite in der Liste war zu klein.** Auf dem ersten Bild
   des fertigen Bereichs stand „Umsatzsteuer-Voranmeldung - Abgab", und
   der Breitentest daneben war **grün**: eine Treeview-Spalte ist nie
   „zu schmal", sie schneidet den Zelltext ab und meldet nichts.
   `winfo_reqwidth` fällt darauf herein. Neuer Test
   `test_die_vorlagenliste_beschneidet_keinen_namen` misst die
   Textbreite in der tatsächlichen Schrift gegen die Spaltenbreite.
3. **Das Testdoppel verschluckte `iid`.** `ttk.Treeview.insert(iid=...)`
   vergab im Doppel immer einen eigenen Schlüssel. Die Oberfläche liest
   aus der Auswahl die Kennung der Vorlage — im Test hätte also etwas
   anderes geprüft als im Programm. Im Doppel behoben.
4. **Ein Test war allein grün und im Verbund rot.**
   `tkfont.nametofont(...)` ohne `root` sucht das „Standardfenster";
   hatte ein früherer Test seines schon zerstört, brach die
   Schriftabfrage ab.
5. **Der Mandantenbrief benutzte `{{kanzlei.*}}`.** Das Gedächtnis führt
   `company.*`, deutsch `firma.*`. Die Felder wären also nie automatisch
   gefüllt worden — die Vorlage hätte funktioniert und trotzdem nichts
   von dem gezeigt, wofür sie da ist. Auf `{{firma.*}}` umgestellt.
6. **Ein falscher Kapitelverweis in der Anleitung** („Lizenz — siehe
   Kapitel 14", das ist der Betriebsmodus). Er stand schon vorher da.
   Gefunden durch einen neuen Test, der jede genannte Kapitelnummer
   gegen die vorhandenen Überschriften prüft.

## 6. Gegenproben

Jede Zusicherung einzeln ausgehebelt; jede Gegenprobe ist angesprungen:

| Ausgehebelt | Test, der ansprang |
|---|---|
| Fehlender Wert wird zu Leere | 5 Tests |
| Leerer Wert gilt als Wert | `test_ein_leerer_wert_gilt_nicht_als_wert` |
| Ausbruch aus dem Vorlagenordner | `test_eine_kennung_kann_nicht_aus_dem_ordner_ausbrechen` |
| Mitgelieferte Vorlage doch löschbar | `test_eine_mitgelieferte_vorlage_laesst_sich_nicht_entfernen` |
| Eigene Änderung wird überschrieben | `test_eine_eigene_aenderung_wird_nicht_ueberschrieben` |
| Kein Freigabehinweis | `test_die_erzeugte_datei_traegt_den_freigabehinweis` |
| Spalte zu schmal | `test_die_vorlagenliste_beschneidet_keinen_namen` |
| Knopfbeschriftung zu lang | `test_der_vorlagenbereich_schneidet_nichts_ab` |
| Falscher Kapitelverweis | `test_die_kapitelnummern_der_verweise_stimmen` |
| Kapitel 13 fehlt | `test_die_anleitung_erklaert_die_vorlagen` |

## 7. Was das nicht löst

* **Word-Dateien als Vorlage** gehen nicht. Der Text ließe sich
  herauslösen, die Formatierung nicht. Die Anwendung sagt das als Satz,
  statt still ein schlechtes Ergebnis zu liefern.
* **Wiederholte Blöcke** (`{{beleg.1}}` … `{{beleg.3}}`) sind in der
  Anzahl fest. Eine Liste beliebiger Länge zu füllen ist nicht gebaut.
* **Rechnen in der Vorlage** gibt es nicht. Eine Vorlage setzt Werte
  ein; gerechnet wird in `pkc.fachrechnen`.
* **Aufgaben & Automationen** sind weiterhin nicht gebaut. Die
  Grundsatzentscheidung steht (Weg C, Vorgabe A), der Bau nicht.
* Nicht geprüft: die erzeugte .docx in echtem Microsoft Word. Das gehört
  zur Abnahme nach `docs/ABNAHME.md`.

## 8. Stand

886 Tests bestanden, 2 übersprungen. Davon zwölf mit einem echten
Tk-Fenster (`xvfb-run`, Python 3.12); unter Windows laufen dieselben im
Bauablauf.
