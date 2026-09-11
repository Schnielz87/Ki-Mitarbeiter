# Was bei Vorlagen und Aufgaben noch zu tun ist

Stand 11.09.2026. Antwort auf die Frage: *„Was ist mit der Fachlogik,
was muss hier getan werden?"*

> **Vorlagen sind seit Fassung 19 gebaut.** Was hier ueber sie steht, ist
> als Beschreibung des Zustands ueberholt; es bleibt stehen, weil die
> Erklaerung, was „Fachlogik" heisst, sich daran am besten zeigt. Was
> tatsaechlich entstanden ist, steht unten unter „Was aus den Vorlagen
> geworden ist". Offen ist nur noch **Aufgaben**.

## Vorab: was heißt hier überhaupt „Fachlogik"?

„Fachlogik" ist ein Entwicklerwort und erklärt nichts. Also im Klartext.

Ein Programm hat zwei Hälften:

1. **Was du siehst und anklickst.** Die Navigation links, die Knöpfe, die
   Listen, die Farben. Das ist die Oberfläche — die haben wir gerade neu
   gebaut.
2. **Was das Programm weiß und tut.** Die Regeln der eigentlichen Arbeit.
   Das ist die Fachlogik.

**Ein Bild dazu, das zum Mitarbeiter passt:** Stell dir PORTIVA als ein
Büro mit zehn Türen vor. Die Oberfläche ist der Flur mit den zehn
beschrifteten Türen. Die Fachlogik ist das, was hinter der Tür steht —
der Aktenschrank, die Ablage, und der Kollege, der weiß, was zu tun ist.

Bei acht Türen war das Zimmer eingerichtet. Bei **Vorlagen** und
**Aufgaben** hing das Schild an der Tür, aber der Raum dahinter war
leer. Deshalb stand dort auch offen „Dieser Bereich ist noch nicht
verfügbar" — statt eines Knopfes, der nichts tut.

Bei **Vorlagen** ist das Zimmer inzwischen eingerichtet. Bei
**Aufgaben** hängt das Schild noch allein.

### Woran du den Unterschied siehst

Nimm **„Belege & Dokumente"** — dort ist beides da:

* *Oberfläche:* der Knopf „Datei auswählen", die Tabelle darunter.
* *Fachlogik:* Das Programm **liest** die PDF wirklich, **erkennt**, ob
  es eine Rechnung oder eine Gutschrift ist, **sucht** die passende
  Fundstelle im Fachwissen und **schreibt** ein Ergebnis. Das sind
  Regeln, die jemand hinterlegen musste.

Nimm **„Vorlagen"** — dort ist nur die Oberfläche da. Das Programm weiß
nicht:

* Was ist überhaupt eine Vorlage? Wo liegt sie?
* Woran erkennt es die Stellen, die gefüllt werden müssen?
* Woher kommen die Werte, die hineingehören?
* Was tut es, wenn ein Wert fehlt?

**Das sind die Fragen, die die Fachlogik beantwortet.** Solange sie
unbeantwortet sind, kann dort auch kein Knopf stehen — er wüsste nicht,
was er tun soll.

---

Beide Bereiche sind in der Oberfläche angelegt und sagen offen, dass es
sie noch nicht gibt. Es steht kein Knopf darin, der nichts tut. Was
fehlt, ist die Fachlogik dahinter.

---

## Kurzfassung

| | Vorlagen | Aufgaben & Automationen |
|---|---|---|
| Aufwand | mittel | groß |
| Risiko | gering | **eine Grundsatzentscheidung nötig** |
| Baut auf | Artefakt-Engine (fertig) | Wissenszeitplan (teilweise) |
| Blockiert durch | nichts | siehe „Die eine offene Frage" |

**Mein Vorschlag: Vorlagen zuerst.** Der Unterbau ist da, das Ergebnis
ist sofort sichtbar, und es gibt nichts zu entscheiden. Aufgaben braucht
vorher eine Antwort von dir.

---

## 1. Vorlagen

### Was schon da ist

Die Artefakt-Engine erzeugt bereits neun Formate — txt, md, json, csv,
xlsx, docx, pptx, pdf und (per Plugin) html. Sie kann Überschriften,
Absätze, Aufzählungen und Tabellen. Jede erzeugte Datei bekommt eine
Fassungsnummer und eine Prüfsumme und landet in „Arbeitsergebnisse".

Das heißt: **Dateien erzeugen kann PORTIVA schon.** Was fehlt, ist die
Verwaltung wiederverwendbarer Vorlagen davor.

### Was fehlt

1. **Ein Vorlagenspeicher.** Ein Ordner auf dem Datenträger plus ein
   Verzeichnis, das Name, Kategorie, Format und Beschreibung führt.
   Analog zum Artefaktwerk, das es schon gibt.
2. **Platzhalter.** Eine Vorlage braucht Stellen, die gefüllt werden:
   `{{firma.name}}`, `{{zeitraum}}`, `{{ergebnis}}`. Ohne Platzhalter ist
   eine Vorlage nur eine Datei.
3. **Das Füllen.** Die Werte kommen aus drei Quellen: dem
   Unternehmensgedächtnis, dem aktiven Profil und der letzten Antwort.
   Was sich nicht auflösen lässt, muss **stehen bleiben und markiert
   werden** — nicht stillschweigend leer.
4. **Vorschau vor dem Erzeugen.** Der Auftrag verlangt sie ausdrücklich.
5. **Eigene Vorlagen aufnehmen.** Eine .docx hereinziehen, Platzhalter
   erkennen, ins Verzeichnis übernehmen.

### Wo es heikel wird

Beim Füllen aus dem Unternehmensgedächtnis greift die Kundentrennung:
Wissen von Kunde A darf unter keinen Umständen in eine Vorlage für
Kunde B geraten. Das ist bereits abgesichert und getestet — der
Vorlagenteil muss denselben Weg benutzen und darf nicht daran vorbei.

Zweitens: eine gefüllte Vorlage sieht aus wie ein fertiges Dokument. Sie
braucht denselben Freigabehinweis wie eine Antwort — fachliche Zuarbeit,
Prüfung durch einen Menschen.

---

## 2. Aufgaben & Automationen

### Was schon da ist

Die Wissensaktualisierung hat einen Zeitplan: Intervall, Fälligkeit,
letzte und nächste Prüfung, Nachholen nach einer Pause. Das läuft und
ist geprüft. Es ist aber **ein** Zeitplan für **eine** Aufgabe.

### Was fehlt

1. **Ein Aufgabenspeicher** mit Auslöser, Aktion, Profil, Zustand.
2. **Auslöser**: zu einer Uhrzeit, in einem Intervall, beim Start, oder
   wenn etwas eintritt (neuer Beleg, Wissensstand älter als X).
3. **Aktionen**: Wissen aktualisieren, Bericht erzeugen, Belegordner
   einlesen, Sicherung anlegen.
4. **Ausführung mit Protokoll** — was lief wann, mit welchem Ergebnis.
5. **Freigabepflicht.** Eine Automation, die ungefragt etwas nach außen
   schickt oder ins Gedächtnis schreibt, ist genau das, was die
   Sicherheitsvorgaben verbieten. Jede Aktion braucht eine ausdrückliche
   Erlaubnis beim Anlegen — und Aktionen mit Außenwirkung eine erneute
   Bestätigung bei jeder Ausführung.

### Die eine offene Frage — dazu brauche ich deine Entscheidung

**PORTIVA läuft nur, solange es geöffnet ist.** Es ist eine portable
Anwendung ohne Dienst im Hintergrund. Damit gibt es genau drei
Möglichkeiten, und sie unterscheiden sich stark:

| Weg | Was er bedeutet | Preis |
|---|---|---|
| **A — Nur bei geöffnetem Programm** | Aufgaben laufen, während PORTIVA offen ist. Verpasste Termine werden beim nächsten Start nachgeholt. | Ehrlich und portabel. Aber: nachts läuft nichts. |
| **B — Windows-Aufgabenplanung** | PORTIVA trägt sich in die Aufgabenplanung von Windows ein und startet sich selbst. | Läuft auch ohne offenes Fenster. Aber: hinterlässt eine Spur auf dem fremden Rechner — das widerspricht dem Grundgedanken „portabel, keine unkontrollierte Ablage auf dem Wirtsrechner". |
| **C — Beides, mit Schalter** | Vorgabe ist A. Wer B will, schaltet es ausdrücklich ein und wird darauf hingewiesen, was dabei auf dem Rechner zurückbleibt. | Mehr Arbeit, aber die Entscheidung liegt beim Anwender. |

**Meine Empfehlung: C**, mit A als Vorgabe. Der Grund: ein
Buchhalter-Rechner in einer Kanzlei läuft ohnehin tagsüber, damit deckt
A den Normalfall ab. Wer eine nächtliche Auswertung braucht, soll sie
bekommen — aber wissen, dass dafür etwas auf dem Rechner eingetragen
wird.

**Ohne deine Antwort auf diese Frage fange ich mit Aufgaben nicht an.**
Sie entscheidet über die halbe Architektur, und sie nachträglich zu
drehen wäre teuer.

---

## 3. Was ich vorschlage

1. **Vorlagen bauen** — in sich abgeschlossen, kein offener Punkt.
2. **Danach Aufgaben**, sobald du A, B oder C entschieden hast.
3. **Vorher aber**, wenn du mich fragst: die Wartezeit. Sie ist das,
   was dich im täglichen Gebrauch am meisten stört, und sie ist heute
   der schwächste Punkt der Anwendung. Vorlagen und Aufgaben machen ein
   langsames Programm nicht schneller.

Die Reihenfolge ist dein Ruf — ich sage nur, wie ich sie sähe.


---

## 4. Was aus den Vorlagen geworden ist

Gebaut in Fassung 19. Die vier Fragen von oben haben jetzt Antworten:

| Frage von oben | Antwort |
|---|---|
| Was ist eine Vorlage, wo liegt sie? | Ein Text mit Platzhaltern. Als lesbare `.md`-Datei unter `workspace/vorlagen` — im Kundenbereich, nicht im Programmordner. |
| Woran erkennt es die Stellen? | An doppelten geschweiften Klammern: `{{firma.name}}`. |
| Woher kommen die Werte? | Drei Quellen in fester Rangfolge: Eingabe des Menschen, Unternehmensgedächtnis, Datum. |
| Was tut es, wenn ein Wert fehlt? | **Der Platzhalter bleibt stehen.** Sichtbar in der Datei, und die Anwendung sagt, welche es waren. |

Die letzte Zeile ist die wichtigste und war die eigentliche
Entscheidung. Ein Brief mit „Sehr geehrte Damen und Herren der
{{firma.name}}," fällt beim Durchlesen auf. Einer, in dem der Name
stillschweigend fehlt, geht raus.

**Was dazugekommen ist**

* Sechs mitgelieferte Vorlagen (Mandantenbrief, Belege nachfordern,
  Monatsabschluss-Checkliste, Anlagenverzeichnis mit AfA,
  Umsatzsteuer-Voranmeldung, Aktennotiz).
* Der Bereich in der Oberfläche: Liste links, Vorlage rechts. Gefragt
  wird nur nach dem, was das Unternehmensgedächtnis nicht schon
  beantwortet.
* Vorschau vor dem Erzeugen — der Auftrag verlangt sie, und sie hat
  einen Zweck: eine gefüllte Vorlage sieht aus wie ein fertiges
  Dokument.
* Eigene Vorlagen aufnehmen (Textdateien).
* Kapitel 13 der Bedienungsanleitung, mit Bild.

**Was ausdrücklich nicht geht**

* **Word-Dateien als Vorlage.** Den Text könnte man herauslösen, die
  Formatierung nicht. Eine Vorlage, die ihr Aussehen verliert, ist als
  Vorlage wertlos. Das steht als Satz in der Anwendung, nicht als
  stilles Scheitern.
* **Wiederholte Blöcke.** `{{beleg.1}}`, `{{beleg.2}}`, `{{beleg.3}}` —
  die Anzahl steht in der Vorlage fest. Eine Liste beliebiger Länge zu
  füllen wäre der nächste Schritt und ist heute nicht gebaut.
* **Rechnen in der Vorlage.** Eine Vorlage setzt Werte ein; sie summiert
  nicht. Gerechnet wird in `pkc.fachrechnen`, und das Ergebnis kommt als
  Wert herein.

## 5. Aufgaben: die Entscheidung steht, gebaut ist noch nichts

Du hast **Weg C** gewählt — beides, mit Schalter, Vorgabe ist A
(„nur bei geöffnetem Programm"). Damit ist die Grundsatzfrage vom Tisch.
Was noch zu bauen ist, steht unverändert oben unter Abschnitt 2.
