# Das Erscheinungsbild von PORTIVA — verbindlich für jeden Mitarbeiter

Freigegeben am 08.09.2026 von Niels. Dieses Dokument ist die
**verbindliche Vorgabe** für jedes künftige Mitarbeiterprofil — Buchhalter,
Personaler, Einkäufer, was auch immer dazukommt.

Der Grund für ein solches Dokument: Ein Erscheinungsbild, das nur in
einem Programm steckt, hält genau so lange, bis jemand das nächste
Programm daneben baut. Was hier steht, gilt für alle.

---

## 1. Der Kern in einem Satz

**Die Schale ist für alle Profile dieselbe. Nur der Inhalt der Bereiche
wechselt.**

Ein neues Mitarbeiterprofil erbt Navigation, Kopfzeile, Farben,
Schriften und Knopfformen. Es bringt eigene Bereiche und eigene
Fachlogik mit — aber kein eigenes Aussehen.

## 2. Wo das Aussehen festgelegt ist

| Datei | Wofür |
|---|---|
| `src/ui/stil.py` | Farben, Schriften, Knopfformen, Tabellen, Eingabefelder. **Die einzige Stelle**, an der Farben stehen. |
| `src/ui/schale.py` | Navigationsleiste, Kopfzeile, Fußzeile, `Kartenwahl` |
| `src/ui/quellenpanel.py` | Quellen als Karten, Recherche-Details |
| `src/ui/startbild.py` | Begrüßungsbild beim Start |
| `assets/branding/` | Logo in drei Fassungen, Symbol als `.ico` und `.png` |

**Wer eine Farbe ändern will, ändert sie in `stil.py` — nirgends sonst.**
Eine Farbe, die an zwei Stellen steht, steht nach dem dritten Umbau an
zwei verschiedenen Stellen verschieden.

## 3. Die Farben

| Zweck | Wert | Verwendung |
|---|---|---|
| Marineblau | `#17202e` | Seitenleiste, Überschriften |
| Blau (Betonung) | `#1e6fd9` | aktiver Bereich, betonte Knöpfe, Verweise |
| Blau dunkel | `#1857ab` | Mauszeiger über einem betonten Knopf |
| Blau hell | `#e8f0fb` | Füllung hinter Betontem, eigene Frage im Chat |
| Grund | `#f5f7fa` | Fläche der Seite — **nicht weiß**, sonst heben sich Karten nicht ab |
| Karte | `#ffffff` | Fläche der Karten und Tabellen |
| Rand | `#dfe5ec` | Kartenrand, Trennlinien |
| Text | `#14243c` | Überschriften und wichtiger Text |
| Leise | `#5b6b80` | Untertitel, Einheiten, Erläuterungen |
| Gut / Warnung / Fehler | `#1e7d4f` / `#9a6b00` / `#b3261e` | Statuswerte |

Die Farben stammen aus dem PORTIVA-Logo, nicht aus freier Wahl: das
Marineblau ist das des Schriftzugs, das helle Blau das der drei Punkte.

## 4. Die Bausteine

**Seitenleiste.** Dunkel, feste Breite (290 offen, 56 eingeklappt), Logo
oben, Profil und Lage unten. Der aktive Eintrag liegt auf einer blauen
Fläche — kein Eintrag hat einen Rahmen. Die kurze Bezeichnung steht in
der Leiste, die lange als Überschrift.

**Kopfzeile.** Links Titel und ein Satz, was der Bereich tut. Rechts
Statuschips und das Auswahlfeld für den Betriebsmodus. Jede Angabe steht
**einmal** — nicht als Chip und daneben nochmal als Feld.

**Karten.** Weiß auf hellem Grund, ein Bildpunkt Rand in `#dfe5ec`,
innen 14 Bildpunkte Abstand. Titel fett, Untertitel leise darunter.

**Knöpfe.** Flach, weiß, ein Rand. Genau ein betonter Knopf je Ansicht
(`Betont.TButton`, blau gefüllt) — der, den man meistens drückt.
Verweise ohne Rahmen in Blau (`Verweis.TButton`).

**Tabellen.** Weiße Zeilen, keine Rillen, Zeilenhöhe 26. Kopfzeile leise
und fett auf hellem Grund.

## 5. Was auf keinen Fall passieren darf

Diese Liste steht hier, weil jeder Punkt darin schon einmal passiert ist:

1. **Kein `highlightthickness=0` an einem Knopf, um einen Rahmen
   loszuwerden.** Das nimmt der Tastatur die Bedienbarkeit. Den Rahmen
   unsichtbar machen (`highlightbackground` = Hintergrundfarbe,
   `highlightcolor` = Blau), nicht abschalten.
2. **Kein `state="readonly"`-Auswahlfeld ohne gesetzte
   Markierungsfarben.** Sonst zeichnet Tk den Text weiß auf weiß und das
   Feld sieht leer aus, obwohl ein Wert darinsteht.
3. **Kein `ttk.PanedWindow`, wo eine feste Spaltenbreite gebraucht
   wird.** Der Schiebeteiler verteilt nach Gewichten und quetscht
   Beschriftungen ab. `grid` mit `minsize`.
4. **Kein Text ohne `wraplength` in einer Fläche mit fester Breite.**
   Tk bricht nicht um, Tk schneidet ab.
5. **Keine Breite aus dem Bauch.** Wenn eine Spalte breit genug sein
   muss, wird die benötigte Breite gemessen (`winfo_reqwidth`) und der
   Wert mit der Messung begründet.

## 6. Wie ein neues Profil aussieht

Ein neues Mitarbeiterprofil legt in `profile.json` unter `navigation`
fest, welche Bereiche es zeigt. Steht dort nichts, bekommt es alle.

```json
{ "navigation": ["unterhaltung", "unternehmenswissen", "belege", "einstellungen"] }
```

Es erbt damit automatisch: Begrüßungsbild, Seitenleiste, Kopfzeile,
Farben, Schriften, Knopfformen, Quellenpanel und die Anpassung an
schmale Fenster. Es muss nichts davon nachbauen.

## 7. Wie das durchgesetzt wird — nicht nur gemeint

Ein Standard, der nur in einem Dokument steht, ist eine Bitte. Diese
Prüfungen laufen bei jedem Bauablauf:

| Test | Hält fest |
|---|---|
| `test_echte_oberflaeche.py` | Mit **echtem** Tkinter: kein Text wird abgeschnitten — je Navigationseintrag im aktiven Zustand, in der Statusspalte, und im ganzen Fenster bei 900×600 |
| `test_keine_toten_knoepfe.py` | Jeder Knopf hat eine hinterlegte Funktion |
| `test_schale.py` | Jeder Bereich ist über die Navigation erreichbar |
| `test_anleitung.py` | Die Anleitung nennt keinen Knopf, den es nicht gibt |
| Bauablauf Linux | Führt die echten Oberflächentests unter `xvfb` aus und prüft ausdrücklich nach, dass sie **nicht übersprungen** wurden |
| Bauablauf Windows | Führt sie zusätzlich auf einem echten Windows aus |

Die Bilder aller Ansichten entstehen mit
`tools/oberflaeche_fotografieren.py` und liegen in `docs/Oberflaeche/`.
Sie gehen in die Betriebsanleitung ein; fehlt eines, bricht deren
Erzeugung mit einer Fehlermeldung ab.

## 8. Was hier bewusst offen bleibt

Wie Schriftglättung und Farben auf einem echten Windows-Bildschirm
wirken, ist nicht geprüft. Die Bilder entstehen unter Linux mit einer
Ersatzschrift für Segoe UI. Das ist keine Vermutung, sondern eine
bekannte Lücke — und der Grund, warum die Oberflächentests zusätzlich
auf dem Windows-Baurechner laufen.
