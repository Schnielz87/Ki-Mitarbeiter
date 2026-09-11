# TASK 34 — Aufgaben & Automationen (Weg C)

Checkpoint nach Masterprompt Abschnitt 55. Zweig
`claude/portable-ki-buchhalter-xr1qlj`, 11.09.2026, Paketfassung 20.

## 1. Der Anlass

Der letzte der zehn Bereiche, hinter dem nur eine leere Tür stand. Die
Grundsatzfrage war nicht technisch, sondern eine Entscheidung, die Niels
treffen musste: PORTIVA hat keinen Dienst im Hintergrund. Er hat **Weg C**
gewählt — beides, mit Schalter, Vorgabe A („nur bei geöffnetem
Programm").

## 2. Was gebaut wurde

Neues Paket `src/pkc/aufgaben/`:

| Datei | Wofür |
|---|---|
| `ausloeser.py` | Wann eine Aufgabe fällig ist; Nachholen |
| `aktionen.py` | Was sie tun kann, mit vier Kennzeichen je Aktion |
| `modell.py` | `Aufgabe` und `Lauf` |
| `speicher.py` | Anlegen, pausieren, entfernen; Protokoll |
| `planer.py` | Fälligkeit prüfen und ausführen |
| `windows_planung.py` | Weg B — der Eintrag in der Aufgabenplanung |

Dazu der Bereich in der Oberfläche mit der **Aufgabenuhr** (Minutentakt,
Ausführung in eigenem Faden), neun Controller-Methoden und Kapitel 14 der
Bedienungsanleitung mit Bild.

## 3. Die drei Zusicherungen, um die alles kreist

1. **Verpasstes wird einmal nachgeholt, nicht fünfmal.** Fünf
   Sicherungen hintereinander sind keine fünf Sicherungen, sondern eine
   Sicherung und vier Wartezeiten. Fünf Wissensupdates hintereinander
   laden fünfmal dieselben Dateien.
2. **Was nicht laufen konnte, gilt nicht als erledigt.** Ein
   übersprungener Lauf verschiebt die Fälligkeit nicht. Ein
   fehlgeschlagener schon — sonst liefe eine dauerhaft scheiternde
   Aufgabe im Minutentakt weiter.
3. **Aussenwirkung braucht bei jeder Ausführung eine Bestätigung.** Die
   Erlaubnis beim Anlegen genügt nicht, und die von gestern auch nicht.
   Schweigen ist keine Zustimmung: fehlt die Rückfragefunktion, gilt das
   als „nicht bestätigt".

## 4. Die Sicherheitsvorgaben, die hier greifen

* **Abschnitt 20 (keine unkontrollierte Host-Speicherung).** Weg B
  widerspricht dem Grundgedanken und ist deshalb die Ausnahme: nur auf
  ausdrückliche Anweisung, mit vorheriger Klartext-Auskunft (`SPUREN`),
  und das Entfernen wird **geprüft**, nicht behauptet — `schtasks
  /Delete` meldet auch dann Erfolg, wenn es nichts zu löschen gab.
* **Abschnitt 61 (Kundentrennung).** Aufgaben und ihr Protokoll liegen
  unter `workspace/aufgaben`, also im Kundenbereich.
* **Keine Aufgaben ab Werk.** Eine Anwendung, die von selbst
  Automationen anlegt, wäre das Gegenteil dessen, was hier gilt.

## 5. Eigene Fehler beim Bauen

1. **Die Aufgabenuhr legte die ganze Testreihe lahm.** Das Testdoppel
   führt `after`-Rückrufe sofort aus, statt eine Ereignisschleife zu
   betreiben. Eine Uhr, die sich selbst neu stellt, wurde damit zur
   Endlosfolge — 400 Durchläufe mal 50 ms je Fenster.
   Die erste Lösung war falsch: „ab 1000 ms gilt ein `after` als
   Taktgeber". Das Begrüßungsbild schließt sich nach drei Sekunden über
   genau dasselbe `after`, und das ist keine Uhr, sondern ein einmaliger
   Termin — der Test dazu wurde rot. Richtig ist die Unterscheidung am
   Rückruf selbst: stellt ein Rückruf wieder *sich selbst*, wird er nur
   vermerkt.
2. **Mein erster Test der Aufgabenuhr prüfte nichts.** Er rief
   `_aufgabenuhr_schlag(start=True)` von Hand auf — damit lief er auch
   dann durch, wenn das Fenster seinen Startdurchlauf gar nicht als
   solchen ausführt. Eine Gegenprobe sprang nicht an und hat es
   aufgedeckt. Jetzt setzt der Test an einem **zweiten Fenster** an, das
   nach dem Anlegen der Aufgabe geöffnet wird.
3. **Die Tests mit echtem Tk blieben hängen.** Ein echtes
   `messagebox.showinfo` wartet auf einen Klick. Der Ersatz dafür wirkte
   zuerst nicht: die Fixture lädt das Paket `ui` frisch, und der vorher
   gesetzte Ersatz hing am alten Modul. Er war da und wirkte nicht.
4. **„Noch keine Aufgabe angelegt", während zwei darüber standen.** Der
   Hinweis unter der Liste wurde nur bei einer Auswahl aktualisiert.
   Aufgefallen auf dem ersten Bild des fertigen Bereichs.
5. **Das Testdoppel kannte weder `ttk.Radiobutton` noch `trace_add`.**
   Ohne `trace_add` wären die Rückrufe im Test nie ausgelöst worden —
   geprüft wäre dann etwas anderes als das Programm.
6. **Zwei falsche Kapitelverweise** in der Anleitung nach dem
   Umnummerieren. Der Test aus TASK 33, der jede genannte Kapitelnummer
   gegen die Überschriften prüft, hat sie gefunden.

## 6. Gegenproben

| Ausgehebelt | Ergebnis |
|---|---|
| Übersprungener Lauf gilt als erledigt | 2 Tests rot |
| Aussenwirkung ohne Bestätigung | 3 Tests rot |
| Netzprüfung entfernt | 2 Tests rot |
| „Jetzt ausführen" respektiert die Pause | 1 Test rot |
| Entfernen wird behauptet statt geprüft | 1 Test rot |
| Wochentage werden ignoriert | 1 Test rot |
| Startdurchlauf ist keiner (`start=False`) | 1 Test rot |
| Aufgabenuhr wird gar nicht gestartet | 1 Test rot |
| Statuszeile überschreibt die laufende Frage | 1 Test rot |
| Spalte der Aufgabenliste zu schmal | 1 Test rot |

## 7. Was das nicht löst

* **Bedingte Auslöser** („wenn ein neuer Beleg da ist") gibt es nicht.
  Heute: Zeit und Programmstart.
* **Kürzeste Wiederholung ist eine Stunde.**
* **Weg B ist nur mit einem Doppel geprüft**, nicht gegen die echte
  Windows-Aufgabenplanung. Das gehört zur Abnahme nach
  `docs/ABNAHME.md`; hier einen echten Eintrag anzulegen wäre ausgerechnet
  bei dieser Funktion das Letzte, was man will.
* **Eine Aufgabe kann PORTIVA nicht aufwecken**, wenn Weg B aus ist. Das
  ist keine Lücke, sondern die Entscheidung selbst.

## 8. Stand

935 Tests bestanden, 2 übersprungen. Davon fünfzehn mit einem echten
Tk-Fenster (`xvfb-run`, Python 3.12); unter Windows laufen dieselben im
Bauablauf.
