# TASK 32 — Das Modell darf nicht mehr rechnen

Checkpoint nach Masterprompt Abschnitt 55. Stand nach `4fd721e`, Zweig
`claude/portable-ki-buchhalter-xr1qlj`, 09.09.2026.

## 1. Der Anlass

Niels hat dem Buchhalter eine über Gemini erstellte Fallstudie gegeben
(TechMove GmbH, Quartalsabschluss zum 30.09.2026) und die Antwort von
Gemini prüfen lassen. Sie war in fast jedem Punkt falsch:

* 5.995.553,43 € als Ergebnis bei einer Ausgangsbasis von 24.000 €
* 91 Tage ab Jahresbeginn statt 16 Tage ab Vertragsbeginn
* 9 Monate AfA statt 7 (September = neunter Monat des Jahres)
* Rückstellung in den ARAP (Passivposten in einen Aktivposten)
* Umsatzsteuerkonto 4400, Vorsteuerkonto 4410 — beides keine Steuerkonten
* falsches Fazit zur größten Budgetüberschreitung
* **keine Excel-Datei**, obwohl ausdrücklich verlangt

## 2. Die Schlussfolgerung

Nicht „das Modell muss besser rechnen". Ein Sprachmodell rechnet
überhaupt nicht — es sagt das nächste Wort vorher. Es darf also gar nicht
rechnen.

## 3. Erledigte Teilaufgaben

1. `src/pkc/fachrechnen/geld.py` — Beträge als `Decimal`, Netto aus
   Brutto geteilt statt abgezogen.
2. `src/pkc/fachrechnen/abschreibung.py` — lineare AfA monatsgenau ab
   Anschaffungsmonat (§ 7 Abs. 1 EStG).
3. `src/pkc/fachrechnen/abgrenzung.py` — ARAP/PRAP tag- und monatsgenau
   ab Vertragsbeginn, mit Buchungssatz.
4. `src/pkc/fachrechnen/plausibilitaet.py` — Größenordnungswächter.
5. `src/pkc/fachrechnen/aufgabenleser.py` — liest rechenbare Angaben aus
   der Aufgabe; Grundsatz „lieber nichts als etwas Geratenes".
6. `src/pkc/fachrechnen/kontenrahmen.py` — Bereichsprüfung SKR03/SKR04.
7. `src/pkc/fachrechnen/regeln.py` — drei fachliche Regeln mit Grundlage.
8. `src/pkc/artefakte/wunsch.py` — erkennt eine bestellte Datei.
9. Einhängung in `RagEngine.answer()` und `AppController.ask()`.
10. Meldung der erzeugten Datei im Fenster.
11. `FACHPRUEFUNG.md` — was geprüft wird und was nicht.

## 4. Letzter erfolgreicher Testlauf

    python -m pytest -q
    837 bestanden, 2 übersprungen

Davon neu: 24 in `test_fachrechnen.py`, 15 in `test_techmove_fall.py`,
3 in `test_rechenpruefung.py`, 12 in `test_kontenpruefung.py`, 20 in
`test_dateiwunsch.py`.

Elf Gegenproben angesprungen; eine sprang zunächst **nicht** an und
führte zu drei zusätzlichen Testfällen.

## 5. Nicht ausgeführte Prüfungen

* Mit einem **echten** Sprachmodell ist der Fall nicht durchgespielt. Die
  Tests setzen die damalige Falschantwort als Modellausgabe ein — das
  prüft die Wächter, nicht das Modell.
* Ob das Modell die vorgegebenen Werte wirklich übernimmt, statt eigene
  zu erfinden, zeigt erst der Betrieb. Der Abschnitt NACHGERECHNET steht
  unabhängig davon in der Antwort.
* Die erzeugte Excel-Datei ist auf einem echten Windows mit Excel nicht
  geöffnet worden.

## 6. Eigene Fehler in diesem Abschnitt

1. Abschnittstrenner zerriss `(inkl. 19% MwSt.)` — der Fuhrpark fiel
   stillschweigend heraus.
2. „im Voraus bezahlt" als Aufwandsmerkmal — falsch bei Kundenzahlungen.
3. Monatsbasis ergab 13 Monate für eine Jahreslizenz.
4. Monatswert vor der Multiplikation gerundet: 999,99 statt 1.000,00.
5. Die Regeln griffen bei keinem Fall — Muster suchte „rückstellung",
   die Anwendung schreibt „Rueckstellung".
6. Ein Test bemängelte einen richtigen Text: „11 Monate" enthält
   „1 Monate".
7. Eine Gegenprobe sprang nicht an — der Schutz gegen Wissensfragen war
   unbewiesen.

## 7. Genauer Fortsetzungspunkt

**Freigegeben und offen:** Vorlagen (Fachlogik), danach Aufgaben nach
Weg C (Schalter, „nur bei geöffnetem Programm" als Vorgabe).

**Vom Auftraggeber vertagt:** die Wartezeit (Hebel 3 und 4).

**Offen aus diesem Abschnitt:** GuV-Konsolidierung und Budgetabweichung
werden weiter vom Modell geschrieben und nicht nachgerechnet. Eine echte
Excel-Arbeitsmappe mit mehreren Blättern und Formeln gibt es nicht.
