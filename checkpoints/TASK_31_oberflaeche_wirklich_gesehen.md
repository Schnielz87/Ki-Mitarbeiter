# TASK 31 — Die Oberfläche zum ersten Mal wirklich gesehen

Checkpoint nach Masterprompt Abschnitt 55. Stand `f238860`, Zweig
`claude/portable-ki-buchhalter-xr1qlj`, 08.09.2026.

Der in Abschnitt 55 genannte Pfad `D:\Ki-Agent\checkpoints` existiert in
dieser Umgebung nicht und wurde nicht angelegt; der Checkpoint liegt im
Repository unter `checkpoints/`.

---

## 1. Der Anlass

Der Auftraggeber meldete: „Das Layout sieht immer noch gleich aus" und
„beim Start kommt das Logo nicht", mit einem Bildschirmfoto.

Das Bildschirmfoto zeigte Karteireiter, „Strg+Eingabe sendet" und das
alte Quellenfeld — den Stand **vor** dem Umbau. In der Statuszeile stand
`Portable-Buchhalter-Windows_V14`. Es war also eine ältere Fassung.

Das allein wäre eine bequeme Erklärung gewesen. Sie stimmt auch — aber
sie ist nicht die ganze Wahrheit.

## 2. Was der erste Blick auf das echte Fenster zeigte

In dieser Umgebung gibt es keinen Bildschirm, aber `Xvfb`. Damit lässt
sich ein echtes Tkinter-Fenster öffnen und fotografieren. Das Ergebnis
war unbrauchbar, obwohl 745 Tests grün waren:

| Was zu sehen war | Ursache |
|---|---|
| „Send" statt „Senden", „Date" statt „Datei anhaengen" | Schiebeteiler verteilte Breite nach Gewichten |
| Unterhaltungsliste mitten im Bild über der Quellenspalte | `side="bottom"` in einem anders belegten Bereich |
| **Jedes** Auswahlfeld leer | `state="readonly"` zeichnet Text markiert; Markierungsschrift weiß auf weißem Feld |
| „Lokales Modell" und „nicht eingerichtet" übereinander | Statusspalte bekam nur den Rest der Breite |
| „Plugins & Erweiterunge" in der Navigation | Leiste 250 breit, aktiver (fetter) Eintrag braucht mehr |
| Bei 900×600 war die Unterhaltung 130 Bildpunkte breit | Seitenleiste + Quellenspalte + Knopfspalte teilten den Platz |

Dazu zwei Fehler, die nur unter Windows wirken:

* `SetWindowLongPtrW(..., GWL_WNDPROC, 0)` mit dem Kommentar „nur lesen".
  Das **setzt** die Fensterprozedur auf NULL.
* Ohne `restype`/`argtypes` nimmt `ctypes` 32 Bit an — die Adresse einer
  Fensterprozedur auf 64-Bit-Windows wäre abgeschnitten worden.

## 3. Erledigte Teilaufgaben

1. `src/ui/stil.py` (neu) — Farben, Schriften, Knopfformen an einer
   Stelle. ttk-Thema `clam`, weil nur das Farben durchlässt.
2. Unterhaltung und Einstellungen von `PanedWindow`/`pack` auf `grid`
   mit festen Spaltenbreiten.
3. Markierungsfarben für Auswahlfelder gesetzt.
4. `Startbild.schliessen()` räumt das selbst erzeugte Wurzelfenster mit
   ab — sonst hängen später erzeugte Variablen am alten Fenster.
5. Seitenleiste 250 → 290, ohne Rahmenkästen, mit Kurzbezeichnungen.
6. Betriebsmodus-Chip entfallen (stand doppelt).
7. `Kartenwahl` (neu, in `schale.py`) — Einstellungsgruppen als Karten
   statt Karteireiter, gleiche Schnittstelle wie `ttk.Notebook`.
8. Anpassung an schmale Fenster: unter 1150 weicht die Quellenspalte,
   unter 1000 klappt die Navigation zusammen.
9. `tools/oberflaeche_fotografieren.py` (neu) — nimmt alle Ansichten auf.
10. Elf Bildschirmfotos in der Betriebsanleitung, mit Beschriftung.
11. `PAKETFASSUNG` — fortlaufende Nummer im Paketnamen (`_V15`).
12. Zwei Windows-Fehler in `dateiablage.py` behoben,
    `PORTIVA_KEINE_DATEIABLAGE` als Abschalter.

## 4. Letzter erfolgreicher Testlauf

    python -m pytest -q
    754 bestanden, 2 übersprungen

    xvfb-run -a python -m pytest -q tests/test_echte_oberflaeche.py
    7 bestanden

Bauablauf Linux mit `xvfb`: grün, einschließlich der Prüfung, dass die
echten Oberflächentests **nicht übersprungen** wurden.

## 5. Nicht ausgeführte Prüfungen

* Wie Schriftglättung und Farben auf einem echten Windows-Bildschirm
  wirken. Die Bilder hier entstehen mit einer Ersatzschrift, nicht mit
  Segoe UI.
* Drag & Drop mit einer echten Maus. Der Code ist nicht mehr
  offensichtlich falsch — erprobt ist er nicht.
* Windows-Skalierung 100 / 125 / 150 %.

## 6. Eigene Fehler in diesem Abschnitt

1. **Die erste Fassung der neuen Tests fand nichts.** Sie maß die
   Navigationseinträge im nicht-aktiven Zustand; der aktive wird fett,
   und fett ist breiter. Aufgefallen an einer Gegenprobe, die nicht
   ansprang. Die korrigierte Fassung fand sofort eine Abschneidung, die
   ich übersehen hatte („Einstellungen & Status", 241 statt 234).
2. **Eine erste Gegenprobe war falsch gewählt.** Ich verkleinerte eine
   `minsize`, um eine Abschneidung zu erzwingen — `minsize` ist ein
   Minimum, die Spalte wuchs einfach. Die Probe konnte gar nicht
   anspringen.
3. **Der Bericht behauptete „keine Kernfunktion beschädigt".** Das war
   richtig und zugleich wertlos: die Funktionen liefen, man konnte sie
   nur nicht bedienen.
4. **Das Werkzeug zur Bildaufnahme erzeugte selbst den Fehler**, den es
   zeigen sollte: das Begrüßungsbild ließ ein Wurzelfenster stehen, und
   die Auswahlfelder waren deshalb im Bild leer. Der zugrunde liegende
   Fehler war aber echt und steckte in der Anwendung.

## 7. Genauer Fortsetzungspunkt

Offen und **nicht freigegeben**: Vorlagen und Aufgaben (neue Fachlogik).

Offen und angekündigt: die Wartezeit. Hebel 3 (Wiederverwendung des
Prompt-Anfangs) und 4 (Antwortspeicher) sind nicht umgesetzt. Der
Auftraggeber hat das ausdrücklich vertagt.

Ebenfalls offen: sieben Adressen im Quellenregister antworten mit
HTTP 404 (BMF, ELSTER, BZSt ×2, BVerfG, BGBl, DIHK).
