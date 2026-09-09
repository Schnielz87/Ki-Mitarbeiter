# Was PORTIVA an einer Antwort prüft — und was nicht

Entstanden am 09.09.2026 aus einem gemeldeten Fehlschlag. Niels hat dem
Buchhalter eine Fallstudie gegeben; die Antwort war in fast jedem Punkt
falsch. Dieses Dokument hält fest, was daraus folgte.

---

## Der Kern in einem Satz

**Das Sprachmodell darf nicht rechnen.**

Ein Sprachmodell rechnet nicht — es sagt das nächste Wort vorher, und
eine Zahl ist für es ein Wort wie jedes andere. Bei einfachen Zahlen geht
das oft gut. Bei einer Abgrenzung über zwei Kalenderjahre geht es schief,
und zwar lautlos: es kommt eine Zahl heraus, die aussieht wie ein
Ergebnis.

Aus 24.000 € wurden 5.995.553,43 €. Die Anwendung hat das ausgeliefert.

---

## Die fünf Fehler des gemeldeten Falls

| Was das Modell schrieb | Was richtig ist | Jetzt |
|---|---|---|
| 5.995.553,43 € aus 24.000 € | 22.947,95 € | ausgerechnet **und** bemängelt |
| 91 Tage ab Jahresbeginn | 16 Tage ab Vertragsbeginn | ausgerechnet |
| 9 Monate AfA (September = 9. Monat) | 7 Monate (März–September) | ausgerechnet |
| Rückstellung in den ARAP | Rückstellung ist ein Passivposten | bemängelt |
| Umsatzsteuerkonto 4400, Vorsteuer 4410 | in keinem Rahmen Steuerkonten | bemängelt |
| *(keine Excel-Datei erzeugt)* | war ausdrücklich verlangt | wird erzeugt |

---

## Die vier Stufen

### 1. Ausrechnen statt raten — `src/pkc/fachrechnen/`

Was sich eindeutig ausrechnen lässt, rechnet die **Anwendung** aus, bevor
das Modell anfängt:

* **Netto aus Brutto** — geteilt durch 1,19, nicht 19 % abgezogen. Der
  Unterschied bei 53.550 € beträgt 1.624,50 €.
* **Lineare AfA, monatsgenau** — gezählt ab dem *Anschaffungsmonat*, der
  voll mitzählt (§ 7 Abs. 1 EStG). Nicht ab Jahresbeginn.
* **ARAP und PRAP** — tag- oder monatsgenau, immer ab *Vertragsbeginn*,
  mit Buchungssatz in der richtigen Richtung.

Jede Rechnung liefert ihren Rechenweg mit. Ein Ergebnis ohne Rechenweg
kann ein Mensch nicht prüfen — und prüfen muss es ein Mensch.

**Grundsatz: lieber nichts als etwas Geratenes.** Gerechnet wird nur,
wenn alle nötigen Angaben in *einem* Abschnitt stehen. Fehlt das
Anschaffungsdatum, die Nutzungsdauer oder der Stichtag, entsteht kein
Ergebnis. Ein falsches Ergebnis mit Rechenweg wäre schlimmer als gar
keines — es sieht geprüft aus.

Die Werte gehen **zweimal** in die Antwort: vorher als bindende Vorgabe
an das Modell („bereits ausgerechnet — nicht nachrechnen"), und nachher
als eigener Abschnitt **NACHGERECHNET** unter der Antwort. Der steht auch
dann da, wenn das Modell etwas anderes behauptet. Dann sieht man den
Widerspruch, statt der falschen Zahl zu glauben.

### 2. Größenordnung — `plausibilitaet.py`

Eine Zahl, die um Größenordnungen über allem liegt, was in der Aufgabe
steht, bekommt einen Hinweis. Der Maßstab kommt aus der Frage; steht dort
keine Zahl, wird nicht geprüft — ohne Maßstab wäre ein Verdacht geraten.

Das ersetzt keine fachliche Prüfung. Eine Abgrenzung von 12.000 € statt
22.947,95 € ist plausibel und trotzdem falsch. Dagegen hilft nur Stufe 1.

### 3. Kontonummern — `kontenrahmen.py`

In zwei Stufen, und die Trennung ist wichtig:

**Belastbar ist die Bereichsprüfung.** Beide gebräuchlichen Kontenrahmen
sind nach Kontenklassen geordnet, und diese Ordnung steht fest: im SKR03
sind die 4000er *betriebliche Aufwendungen*, im SKR04 sind sie *Erträge*.
Eine Umsatzsteuerschuld ist weder das eine noch das andere — sie ist eine
Verbindlichkeit. Die 4400 fällt damit in beiden Rahmen auf, ohne dass man
ein einziges Einzelkonto kennen müsste.

**Nur ein Hinweis** ist die hinterlegte Auswahl gebräuchlicher Konten
(„üblich ist dafür SKR03: 1776"). Sie ist ausdrücklich **kein
vollständiger Kontenrahmen**, und eine Nummer gilt nie als falsch, nur
weil sie darin fehlt.

> Diese Zurückhaltung ist Absicht. Eine Anwendung, die erfundene
> Kontonummern anmahnt, indem sie selbst welche erfindet, wäre genau der
> Fehler, den sie verhindern soll.

Welcher Rahmen gilt, kommt aus dem Unternehmensgedächtnis
(`company.chart_of_accounts`). Steht dort nichts, wird gegen beide
geprüft und nur bemängelt, was in **beiden** nicht passt.

### 4. Denkfehler — `regeln.py`

„Rückstellung in den ARAP" ist nicht falsch gerechnet, sondern falsch
gedacht. Kein Rechenwerk fängt das ab; dafür braucht es Regeln.

Der Maßstab für eine Regel hier: **sie muss ohne Kenntnis des
Einzelfalls entscheidbar sein.** „Eine Rückstellung ist kein ARAP" gilt
immer. „Diese Rückstellung ist zu hoch" gilt nur mit Kenntnis des
Sachverhalts — so etwas steht nicht drin.

Jede Regel nennt ihre Grundlage (§ 249 HGB, § 250 HGB). Wo kein Paragraf
danebensteht, steht auch keiner da.

Ein Satz, der den Unterschied gerade *erklärt* („eine Rückstellung ist
kein ARAP"), löst nichts aus — sonst könnte die Anwendung den Unterschied
nicht mehr erklären.

---

## Was das **nicht** löst

Damit sich niemand in falscher Sicherheit wiegt:

1. **Nur eindeutig Rechenbares wird ausgerechnet.** GuV-Konsolidierung,
   Budgetabweichung, das Management-Fazit — dort schreibt weiter das
   Modell, und dort kann es weiter irren.
2. **Die Regeln decken drei Fälle ab**, nicht das Buchhaltungsrecht.
3. **Die Kontenprüfung greift nur bei Umsatz- und Vorsteuer**, und nur
   wenn die Nummer ausdrücklich als Konto bezeichnet ist.
4. **Die erzeugte Excel-Datei enthält die Antwort als Tabelle** — nicht
   vier verknüpfte Blätter mit Formeln und bedingter Formatierung. Das
   wäre Vorlagen-Fachlogik und ist nicht gebaut.
5. **Ein falsches Ergebnis in plausibler Größenordnung fällt nicht auf.**

Der Freigabehinweis unter jeder Antwort gilt unverändert: fachliche
Zuarbeit ohne Gewähr, Prüfung und Freigabe durch einen verantwortlichen
Menschen.

---

## Wie das geprüft wird

| Testdatei | Was sie festhält |
|---|---|
| `test_fachrechnen.py` | 24 Prüfungen der Rechenwege, Sollwerte aus der mitgelieferten Musterlösung |
| `test_techmove_fall.py` | Die ganze Aufgabe durch die ganze Anwendung — mit genau der damaligen Falschantwort als Modellausgabe |
| `test_rechenpruefung.py` | Die unmögliche Zahl kommt nicht unkommentiert beim Anwender an |
| `test_kontenpruefung.py` | Erfundene Konten und Denkfehler |
| `test_dateiwunsch.py` | Eine bestellte Datei entsteht wirklich — und eine Wissensfrage bestellt nichts |

Zu jedem Wächter gibt es eine Gegenprobe: der Wächter wird abgeschaltet,
und der Test muss fehlschlagen. Ein Test, der auch ohne den Wächter
besteht, prüft ihn nicht.

## Eigene Fehler beim Bauen

Sie stehen hier, weil sie zeigen, wie leicht so etwas passiert:

* Der Abschnittstrenner zerriss `(inkl. 19% MwSt.)` am Punkt vor einer
  Ziffer — **der Fuhrpark fiel stillschweigend heraus.** Kein Fehler,
  einfach kein Ergebnis.
* „im Voraus bezahlt" stand als Merkmal für einen Aufwand. Falsch: in
  „ein Kunde hat im Voraus bezahlt" haben *wir* kassiert.
* Die Monatsbasis ergab für eine Jahreslizenz **13 Monate** —
  rechnerisch richtig, fachlich unbrauchbar.
* Der Monatswert wurde vor der Multiplikation gerundet: 999,99 € statt
  1.000,00 €.
* Die Regeln griffen bei **keinem** Fall, weil das Muster „rückstellung"
  suchte und die Anwendung „Rueckstellung" schreibt.
* Eine Gegenprobe sprang nicht an: der Schutz gegen Wissensfragen war
  eingebaut, aber unbewiesen. Eingebauter Code, den kein Test braucht,
  ist kein Schutz — nur eine Vermutung.
