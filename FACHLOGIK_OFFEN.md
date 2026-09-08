# Was bei Vorlagen und Aufgaben noch zu tun ist

Stand 08.09.2026. Antwort auf die Frage: *„Was ist mit der Fachlogik,
was muss hier getan werden?"*

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
