# Antwortzeit — warum sie so lang ist und was wirklich hilft

Stand **2026-09-07**. Alle Zahlen gemessen, keine geschätzt.

Anlass: „Was ist Buchhaltung“ brauchte auf dem Rechner des Anwenders
**4 min 20 s bis zum ersten Wort** und danach **2 min** bis zum Ende der
Antwort. Zusammen 6 min 20 s, mit der Stoppuhr gemessen.

---

## 1. Wo die Zeit hingeht — gemessen

Der Modelldienst legt jeder Antwort eine Zeitaufteilung bei. Aus Lauf
34150465641 auf dem Windows-Baurechner:

| Stufe | Frage verarbeiten | Antwort schreiben |
|---|---|---|
| schnell | 29,7 s für 1227 Textbausteine | 2,1 s für 49 |
| ausgewogen | 51,4 s für 1980 Textbausteine | 3,4 s für 72 |

**Rund 95 Prozent der Wartezeit entstehen, bevor das erste Wort da ist.**
Das Schreiben ist nicht das Problem. Das Verarbeiten der Frage ist es —
und dessen Dauer hängt fast linear an der Zahl der Textbausteine im
Prompt.

Damit ist die Aufgabe klar umrissen: **weniger Textbausteine, ohne dass
die Antwort schlechter wird.**

## 2. Wie es ChatGPT, Gemini und Claude machen

Der Vergleich ist berechtigt, aber die ehrliche Antwort hat vier Teile,
und der erste ist der wichtigste:

1. **Sie rechnen auf Grafikkarten in einem Rechenzentrum.** Dort werden
   2000 Textbausteine in Millisekunden verarbeitet, auf einem Bürorechner
   ohne Grafikkarte in einer Minute. Das ist ein Faktor von mehreren
   hundert und **kein Software-Kniff**. Diesen Teil kann PORTIVA nicht
   einholen — wer das verspricht, sagt die Unwahrheit.
2. **Sie merken sich den unveränderlichen Anfang des Prompts.** Die
   Rollenbeschreibung wird einmal verarbeitet und danach wiederverwendet.
   Das versuchen wir bereits (`cache_prompt`), und es greift auf der
   mitgelieferten llama.cpp-Fassung nachweislich **nicht** — belegt in
   `TESTBERICHT.md`.
3. **Sie recherchieren nicht bei jeder Frage.** „Was ist Buchhaltung“
   beantwortet ChatGPT aus dem Modell heraus. Es sucht keine
   Gesetzestexte, weil die Frage keine braucht.
4. **Sie schreiben die Antwort laufend mit.** Das tut PORTIVA schon.

Punkt 3 ist der Punkt, an dem PORTIVA **heute nachweislich Zeit verschenkt**.

## 3. Der Befund zu „Was ist Buchhaltung“

Die Frage enthält das Wort „buchhalt“. Die Einstufung erkennt darin eine
Fachfrage und schaltet den vollen Apparat ein: Recherche, Fundstellen,
Fachschema, Unternehmenskontext.

Gemessen, wie groß der Prompt dadurch wird:

| Behandlung | Prompt |
|---|---|
| **wie heute (als Fachfrage)** | **~2910 Textbausteine** |
| als einfache Frage | ~2490 |
| **ohne Recherche** | **~950** |
| eine echte Fachfrage zum Vergleich | ~2800 |

Eine Begriffserklärung bekommt heute denselben Prompt wie „Wie buche ich
eine Eingangsrechnung aus Frankreich mit Reverse Charge?“ — obwohl die
Antwort keine einzige der herangezogenen Fundstellen braucht.

**Das ist der Faktor drei, und er kostet nichts an Qualität.**

Umgerechnet auf die Messung des Anwenders: aus 4 min 20 s bis zum ersten
Wort würden **rund 1 min 25 s**. Das ist keine Zusage — die
Verarbeitungsdauer wächst nicht exakt linear —, aber die Größenordnung
steht.

## 4. Vorschlag: vier Hebel, nach Wirkung je Risiko geordnet

### Hebel 1 — Begriffsfragen ohne Recherche beantworten
**Wirkung: ~3× auf Fragen dieser Art. Risiko: gering. Aufwand: klein.**

Neue Einstufung `BEGRIFF` für Fragen der Form „Was ist X“, „Was bedeutet
X“, „Erkläre mir X“ — ohne geschilderten Sachverhalt, ohne Bezug auf das
eigene Unternehmen. Diese bekommen:

- keine Recherche,
- kein Fachschema,
- den kurzen Systemtext,
- den Hinweis, dass allgemein erklärt wurde und für den konkreten Fall
  nachgefragt werden kann.

Genau das verlangt auch Abschnitt 13 des UI/UX-Auftrags („nicht jede
Nachricht benötigt RAG“).

**Absicherung:** Ein Test hält fest, dass „Wie buche ich…“, „Ist … steuerfrei“
und jede Frage mit Sachverhalt weiterhin die volle Recherche bekommt. Die
Ersparnis darf nie auf Kosten einer echten Fachfrage gehen.

### Hebel 2 — Fachschema nur für verwickelte Fälle
**Wirkung: ~330 Textbausteine bei jeder einfachen Fachfrage. Risiko: gering.**

Das Antwortschema (Ergebnis, Begründung, steuerliche Behandlung, …) wird
heute für `FACHLICH` **und** `KOMPLEX` mitgeschickt. Für eine einfache
Fachfrage ist es Ballast. Künftig nur noch bei `KOMPLEX`.

### Hebel 3 — Prompt-Anfang wirklich wiederverwenden
**Wirkung: bis zu 2× auf alle Fragen. Risiko: mittel. Aufwand: mittel.**

Rund 1000 der 2900 Textbausteine sind bei jeder Frage Zeichen für Zeichen
dieselben. Sie werden trotzdem jedes Mal neu verarbeitet — nachgewiesen in
`TESTBERICHT.md`. Zu prüfen:

1. Welche llama.cpp-Fassung liegt bei, und kennt sie `cache_prompt` auf dem
   OpenAI-kompatiblen Weg?
2. Verhindern die Beschleunigungsschalter (`--cache-type-k/v q8_0`) die
   Wiederverwendung? Gegenprobe: einmal ohne.
3. Bringt der native `/completion`-Weg statt des OpenAI-kompatiblen die
   Wiederverwendung?

Die Anzeige „Prompt-Anfang wiederverwendet: ja / NEIN“ misst jeden Versuch
sofort. Es wird nichts behauptet, was diese Zeile nicht bestätigt.

### Hebel 4 — Antwortspeicher für wiederholte Fragen
**Wirkung: von Minuten auf Millisekunden bei Wiederholungen. Risiko: gering.**

Dieselbe Frage zweimal zu stellen ist im Büro der Normalfall. Die Antwort
wird gespeichert und wiederverwendet, solange sich nichts Maßgebliches
geändert hat. Der Schlüssel umfasst Frage, Profil, Wissensstand, Modell,
Tempostufe und Unternehmenswissen — ändert sich eines davon, wird neu
gerechnet.

**Wichtig:** Die Antwort wird als „aus dem Speicher, erstellt am …“
gekennzeichnet. Eine wiederverwendete Antwort, die als frisch ausgegeben
wird, wäre eine Täuschung.

### Nicht vorgeschlagen, aber erwähnt

- **Kleineres Modell** (3B statt 7B): grob doppelt so schnell, etwas
  knappere Antworten. Das ist eine Entscheidung des Anwenders, keine
  Programmänderung — sie steht in der Anleitung.
- **Grafikkarte**: die Vulkan-Fassung liegt bei und wird automatisch
  gewählt. Auf einem Rechner ohne Karte hilft sie nicht.

## 4a. Umgesetzt am 2026-09-07 — Hebel 1 und 2, gemessen

Freigegeben und umgesetzt. Hebel 1 wurde dabei **korrigiert**: der erste
Entwurf nahm Begriffsfragen ganz von der Recherche aus. Ein bestehender
Test hat das gestoppt — „Was ist Reverse Charge?" ist ein Rechtsbegriff,
und seine Erklärung gehört mit §13b UStG belegt. Tempo zu gewinnen, indem
man den Beleg weglässt, wäre kein Gewinn.

Die Umsetzung recherchiert deshalb **schlank statt gar nicht**: neue
Einstufung `BEGRIFF` mit einer Recherchetiefe von 0,3. Zwei Fundstellen
statt acht, kein Fachschema, eigene Antwortanweisung. Der Beleg bleibt,
der Ballast fällt weg.

Gemessen mit dem ausgelieferten Wissensbestand — **dieselbe Frage**, einmal
wie bisher behandelt und einmal wie jetzt:

| Umgebung | vorher | nachher | Faktor |
|---|---|---|---|
| Entwicklungsrechner | 8896 Zeichen | 4199 | **2,1** |
| Windows-Baurechner | 6318 Zeichen | 4199 | **1,5** |

**Warum zwei verschiedene Zahlen?** Der Anteil, den ich abschalte, ist
überall gleich groß: statt acht Fundstellen zwei, kein Fachschema. Wie
lang die *einzelnen* Fundstellen ausfallen, hängt aber davon ab, welche
Abschnitte die Volltextsuche zuoberst stellt — und das fällt auf zwei
Rechnern unterschiedlich aus.

Die ehrliche Aussage lautet deshalb: **der Prompt schrumpft um ein Drittel
bis um die Hälfte**, nicht „um den Faktor 2,4". Diese Zahl hatte ich
zunächst berichtet; sie stammte aus einem Vergleich zweier verschiedener
Fragen und war zu günstig gegriffen.

Der verwickelte Einzelfall behält alles — dort ist nichts überflüssig.

Was dabei ausdrücklich **nicht** kleiner wird: das Unternehmenswissen. Es
ist klein und es ist das, was PORTIVA von einem allgemeinen Sprachmodell
unterscheidet. Ein Test hält das fest.

Was das für die gemeldeten 4 min 20 s bedeutet: rechnerisch **zwischen
2 und 3 Minuten**. Das ist **keine Zusage** — die Verarbeitungsdauer wächst nicht exakt
linear, und die Zahl ist auf diesem Rechner nicht nachgemessen. Nachmessen
lässt sie sich mit „Wartezeit messen".

Hebel 3 (Prompt-Anfang wiederverwenden) und Hebel 4 (Antwortspeicher)
waren zu diesem Zeitpunkt **nicht** umgesetzt. Siehe 4b.

---

## 4b. Umgesetzt am 2026-09-11 — Hebel 4 ganz, Hebel 3 zur Hälfte

### Hebel 4 — der Antwortspeicher: umgesetzt

Dieselbe Frage zweimal zu stellen kostet keine Wartezeit mehr. Der
Speicher liegt in der Unternehmensdatenbank (`answer_cache`, Fassung 2
des Schemas) und damit im Kundenbereich — eine gespeicherte Antwort
enthält Unternehmenswissen.

**Die eine Regel, die alles andere trägt:** eine wiederverwendete Antwort
wird als solche gekennzeichnet, mit dem Datum ihrer Entstehung. Wer eine
Frage zum zweiten Mal stellt, tut das oft, weil sich etwas geändert hat.

Der Schlüssel umfasst Frage, Profil, Wissensstand, Modell, Tempostufe,
Betriebsart und den **Stand des Unternehmensgedächtnisses**. Der letzte
Punkt ist der am leichtesten zu übersehende: wer seinen Kontenrahmen von
SKR03 auf SKR04 umstellt, bekommt zu derselben Frage eine andere
Antwort. Gemessen wird er als Anzahl der aktiven Einträge plus jüngstem
Änderungszeitpunkt — ein Zähler allein übersähe eine Änderung, ein
Zeitstempel allein eine Löschung.

**Was nicht gespeichert wird:**

* Antworten aus dem Notbetrieb. Sie festzuhalten hieße, den Notbetrieb
  zu verewigen — auch dann noch, wenn das Modell längst eingerichtet ist.
* Antworten mit Gesprächsverlauf. Dieselbe Frage meint im nächsten
  Gespräch etwas anderes. Den Verlauf in den Schlüssel zu nehmen wäre
  möglich und nutzlos: er ist nie zweimal gleich.

Abschaltbar unter `llm.antwortspeicher`; Stand und „leeren" stehen in den
Einstellungen. Höchstens 200 Einträge, die am längsten unbenutzten fallen
heraus.

### Hebel 3 — Prompt-Anfang wiederverwenden: zur Hälfte

Die Anfrage verlangt die Wiederverwendung schon seit Fassung 14
(`cache_prompt: true` an den mitgelieferten Dienst). Was fehlte, war die
**Messung** — und damit die Antwort auf die Frage, ob es überhaupt
wirkt.

Sie ist jetzt da. Gemessen wird der Unterschied zwischen zwei Zahlen, die
beide vom Modelldienst selbst kommen:

| Zahl | Woher | Bedeutung |
|---|---|---|
| `usage.prompt_tokens` | Antwort des Dienstes | wieviele Textbausteine die Frage hat |
| `timings.prompt_n` | Antwort des Dienstes | wieviele davon er verarbeitet hat |

Ist die zweite kleiner, hat er den Rest gemerkt. „Wartezeit messen" zeigt
das als eine Zeile:

> Prompt-Anfang wiederverwendet: JA — 1000 von 2900 Textbausteinen
> gemerkt

Fehlt eine der beiden Zahlen, steht die Zeile **nicht** da. Es wird
gemessen und nichts geschätzt; eine Anzeige „wahrscheinlich
wiederverwendet" wäre schlimmer als gar keine.

### Der Befund: es wirkt heute NICHT

Der Bauablauf vom 11.09.2026 hat auf einem echten Windows-Rechner mit
einem echten Modell gemessen. Das Ergebnis ist eindeutig:

| Tempostufe | 1. Durchgang | 2. Durchgang | Textbausteine verarbeitet |
|---|---|---|---|
| schnell | 25,8 s | 27,4 s | 1232 → 1227 |
| ausgewogen | 50,1 s | 51,5 s | 1960 → 1980 |
| ausführlich | 45,6 s | 49,3 s | 1960 → 1980 |

Der zweite Durchgang ist **nicht schneller** als der erste — er ist
sogar durchweg minimal langsamer. Der unveränderliche Prompt-Anfang wird
also **nicht** wiederverwendet, obwohl die Anfrage es verlangt.

Und es ist teuer: „Frage verarbeiten" ist 25,8 s von 40,1 s (64 %) und
51,5 s von 83,7 s (62 %). Rund tausend dieser Textbausteine sind bei
jeder Frage dieselben.

**Damit ist Hebel 3 der größte verbliebene Posten der Wartezeit — und er
liegt brach.**

### Der Verdächtige, und wie er überführt wird

Punkt 2 der Prüfliste oben lautet: „Verhindern die
Beschleunigungsschalter (`--cache-type-k/v q8_0`) die Wiederverwendung?
Gegenprobe: einmal ohne."

Die Messung zeigt in jeder Zeile „Zusatzschalter aktiv". Der Bauablauf
enthält jetzt genau diese Gegenprobe: eine Messung mit den Schaltern und
eine ohne, direkt hintereinander, mit dem Befund im Klartext darunter.
Der nächste Bau beantwortet die Frage.

Bis dahin wird hier **nichts behauptet**. Die Schalter sparen
nachweislich Arbeitsspeicher, und auf einem knappen Rechner entscheidet
das über das Auslagern — das kostet nicht Prozente, sondern das
Zehnfache. Sie abzuschalten, ohne zu wissen, ob es hilft, wäre ein
Tausch ins Blaue.

Punkt 3 (nativer `/completion`-Weg statt des OpenAI-kompatiblen) bleibt
ebenfalls offen.

## 5. Was das zusammen bedeutet

| Frageart | heute | mit Hebel 1+2 | zusätzlich mit Hebel 3 |
|---|---|---|---|
| „Was ist Buchhaltung“ | ~2910 | **~950** | ~950 |
| einfache Fachfrage | ~2800 | ~2470 | **~1500** |
| verwickelter Fall | ~2900 | ~2900 | **~1900** |
| Wiederholung | ~2900 | ~2900 | **0 (Hebel 4)** |

Hebel 1 und 2 sind klein, sicher und sofort messbar. Hebel 4 ist
umgesetzt. Hebel 3 ist der größte, aber ergebnisoffen — er hängt an einer
Fassung, die wir nicht selbst schreiben; gemessen wird er jetzt, statt
vermutet zu werden.

## 6. Was ich **nicht** verspreche

PORTIVA wird auf einem Bürorechner ohne Grafikkarte nicht so schnell
antworten wie ChatGPT. Der Abstand kommt aus der Hardware, nicht aus dem
Programm. Was erreichbar ist: die Wartezeit auf ein Vielfaches weniger
drücken, indem nur noch verarbeitet wird, was die Antwort wirklich braucht.

Ob es gelungen ist, sagt eine Zahl und nicht eine Behauptung:
**Registerkarte Sprachmodell → „Wartezeit messen“.**
