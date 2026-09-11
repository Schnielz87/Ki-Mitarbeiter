# TASK 35 — Die Wartezeit: Hebel 4 ganz, Hebel 3 zur Hälfte

Checkpoint nach Masterprompt Abschnitt 55. Zweig
`claude/portable-ki-buchhalter-xr1qlj`, 11.09.2026.

## 1. Der Anlass

Niels hatte die Wartezeit zurückgestellt, um die Oberfläche und die
Fachlogik vorzuziehen. Beides ist fertig; damit ist sie wieder dran.
`ANTWORTZEIT_KONZEPT.md` nennt vier Hebel — 1 und 2 waren umgesetzt, 3
und 4 offen.

## 2. Hebel 4 — der Antwortspeicher

Dieselbe Frage zweimal zu stellen ist im Büro der Normalfall. Die zweite
Antwort kostet jetzt keine Wartezeit mehr.

* Tabelle `answer_cache` in der Unternehmensdatenbank, Schemafassung 2.
  Kundenbereich, weil eine gespeicherte Antwort Unternehmenswissen
  enthält (Abschnitt 61).
* Schlüssel über Frage, Profil, Wissensstand, Modell, Tempostufe,
  Betriebsart und den Stand des Unternehmensgedächtnisses.
* Höchstens 200 Einträge; die am längsten unbenutzten fallen heraus.
* Abschaltbar (`llm.antwortspeicher`), Stand und „leeren" in den
  Einstellungen.

**Die eine Regel, die alles andere trägt:** eine wiederverwendete
Antwort wird als solche gekennzeichnet, mit dem Datum ihrer Entstehung.
Wer eine Frage zum zweiten Mal stellt, tut das oft, weil sich etwas
geändert hat. Eine gespeicherte Antwort als frisch auszugeben wäre eine
Täuschung — und zwar eine gefährliche (Abschnitt 42, Abschnitt 52).

**Zwei Dinge wandern nicht hinein:**

* Antworten aus dem Notbetrieb. Sie festzuhalten hieße, den Notbetrieb zu
  verewigen — auch dann noch, wenn das Modell längst eingerichtet ist.
* Antworten mit Gesprächsverlauf. Dieselbe Frage meint im nächsten
  Gespräch etwas anderes. Den Verlauf in den Schlüssel zu nehmen wäre
  möglich und nutzlos: er ist nie zweimal gleich.

**Der am leichtesten zu übersehende Punkt** ist der Stand des
Unternehmensgedächtnisses. Wer seinen Kontenrahmen von SKR03 auf SKR04
umstellt, bekommt zu derselben Frage eine andere Antwort. Gemessen wird
er als Anzahl der aktiven Einträge plus jüngstem Änderungszeitpunkt: ein
Zähler allein übersähe eine Änderung, ein Zeitstempel allein eine
Löschung.

## 3. Hebel 3 — Prompt-Anfang wiederverwenden: nur die Messung

Die Anfrage verlangt die Wiederverwendung seit Fassung 14
(`cache_prompt: true`). Was fehlte, war die Antwort auf die Frage, **ob
es wirkt**.

Gemessen wird der Unterschied zwischen zwei Zahlen, die beide vom
Modelldienst kommen: `usage.prompt_tokens` (wieviele Textbausteine die
Frage hat) und `timings.prompt_n` (wieviele davon er verarbeitet hat).
Ist die zweite kleiner, hat er den Rest gemerkt. „Wartezeit messen" zeigt
eine Zeile:

> Prompt-Anfang wiederverwendet: JA — 1000 von 2900 Textbausteinen
> gemerkt

Fehlt eine der beiden Zahlen, steht die Zeile **nicht** da. Es wird
gemessen und nichts geschätzt.

### Der Befund — und er ist unangenehm

Der Bauablauf vom selben Tag hat auf einem echten Windows-Rechner mit
einem echten Modell gemessen. **Der Prompt-Anfang wird nicht
wiederverwendet.** Der zweite Durchgang war in allen vier Tempostufen
genauso langsam wie der erste (25,8 s gegen 25,8 s; 51,5 gegen 50,1),
und es wurden 1227 von 1232 Textbausteinen erneut verarbeitet.

Das ist teuer: „Frage verarbeiten" macht 62 bis 64 Prozent der
Wartezeit aus, und rund tausend dieser Textbausteine sind bei jeder
Frage dieselben. Hebel 3 ist damit der größte verbliebene Posten — und
er liegt brach.

**Die Gegenprobe steht im Bauablauf**, nicht in einer Vermutung: ein
neuer Schritt misst einmal mit und einmal ohne die
Beschleunigungsschalter (`--cache-type-k/v q8_0`) und nennt den Befund
im Klartext. Das ist wörtlich Punkt 2 der Prüfliste aus
`ANTWORTZEIT_KONZEPT.md`. Der nächste Bau beantwortet die Frage.

Bis dahin wird nichts umgestellt. Die Schalter sparen nachweislich
Arbeitsspeicher, und auf einem knappen Rechner entscheidet das über das
Auslagern — das kostet das Zehnfache. Sie abzuschalten, ohne zu wissen,
ob es hilft, wäre ein Tausch ins Blaue.

Punkt 3 der Prüfliste (nativer `/completion`-Weg) bleibt offen.

Damit ist Hebel 3 **zur Hälfte** erledigt: gemessen ist er, behoben
nicht. Das als „umgesetzt" zu verbuchen wäre genau die Scheinerfüllung,
die Abschnitt 52 ausschließt.

## 4. Gegenproben

| Ausgehebelt | Ergebnis |
|---|---|
| Wiederverwendete Antwort ohne Kennzeichnung | 1 Test rot |
| Unternehmenswissen nicht im Schlüssel | 1 Test rot |
| Auch mit Gesprächsverlauf gespeichert | 1 Test rot |
| Speicher wächst unbegrenzt | 1 Test rot |
| Unbekannte Felder brechen den Aufbau | 1 Test rot |
| Messung ohne die nötigen Zahlen | 1 Test rot |
| „wiederverwendet" fest auf wahr | 1 Test rot |
| Modellkennung nur der Anbietername | 1 Test rot |
| Rechenergebnisse nicht mitgespeichert | 1 Test rot |

### Ein Fehler, den eine Gegenprobe gefunden hat

Der Schlüssel enthielt zuerst `self.llm.primary.name` als „Modell". Der
lautet beim mitgelieferten Dienst aber **immer** `local-llama-cpp` —
auch wenn jemand eine andere Modelldatei in den Ordner legt. Der
Speicher hätte weiter mit den Antworten des alten Modells geantwortet,
obwohl ein anderes eingerichtet ist. Jetzt geht ein, was der Anbieter
über sich selbst sagt: Anbieter, Modellname und Pfad.

## 5. Eine Kleinigkeit, die keine ist

Beim Wiederaufbau einer gespeicherten Antwort werden **nur bekannte
Felder** durchgereicht. Kommt in einer späteren Fassung ein Feld hinzu
oder fällt eines weg, würde ein schlichtes `Klasse(**daten)` mit einem
TypeError abbrechen — und zwar mitten in einer Antwort. Ein alter
Eintrag darf höchstens unvollständig sein, nicht tödlich.

Aus demselben Grund wird zum Speichern `dataclasses.asdict` benutzt und
nicht `SourceReference.as_dict()`: letztere gibt deutsche
Schlüsselnamen für die Anzeige aus („nummer", „titel"). Damit ließe sich
kein Quellennachweis wieder aufbauen, ohne die Namen ein zweites Mal zu
pflegen — und zwei Listen von Namen laufen irgendwann auseinander.

## 6. Was das nicht löst

* PORTIVA antwortet auf einem Bürorechner ohne Grafikkarte weiterhin
  nicht so schnell wie ChatGPT. Der Abstand kommt aus der Hardware.
* Eine **neue** Frage dauert genauso lange wie vorher. Der
  Antwortspeicher hilft nur bei Wiederholungen.
* Hebel 3 bleibt unbewiesen, siehe oben.

## 7. Stand

963 Tests bestanden, 2 übersprungen.
