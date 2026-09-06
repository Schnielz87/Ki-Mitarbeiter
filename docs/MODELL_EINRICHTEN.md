# Sprachmodell einrichten

Ohne lokales Sprachmodell recherchiert der Buchhalter zwar in seinen Quellen
und zeigt die Fundstellen an, **formuliert aber keine Fachantwort**. Er sagt
das dann auch deutlich. Diese Anleitung schliesst die Luecke.

Einmaliger Aufwand: ein Befehl plus Downloadzeit. Die Modelldatei ist je
nach Auswahl 0,4 bis 9 GB gross.

---

## Der kurze Weg - im Fenster

1. Registerkarte **Sprachmodell** oeffnen.
2. Oben steht, was der Rechner hergibt und welches Modell dazu passt; die
   Vorauswahl ist bereits die Empfehlung.
3. **Sprachmodell einrichten** anklicken. Die Rueckfrage nennt Groesse,
   Lizenz, Herkunft und Pruefstand der Bezugsquelle - erst ein "Ja" startet
   den Download.

Danach bindet die Anwendung das Modell ein und stellt ihm selbst eine
kleine Frage. Erst wenn die beantwortet ist, meldet sie **"Das Sprachmodell
ist einsatzbereit."**

---

## Nur einmal - nicht bei jedem Start

Das Modell wird **einmal** geladen. Danach liegt es in `models\` **auf dem
Datentraeger**, nicht auf dem Rechner. Es bleibt dort ueber Neustarts, an
jedem anderen Rechner, unter jedem Laufwerksbuchstaben - und alle
Kundenbereiche teilen sich dieselbe Datei.

Warum liegt es dann nicht gleich im Paket? Es ist bis zu neun Gigabyte
gross, und unter welcher Lizenz Sie ein Modell einsetzen, ist Ihre
Entscheidung.

## Sie haben das Modell schon? Dann nicht noch einmal laden

Fuer einen zweiten Datentraeger, ein Buero mit gesperrtem Download oder eine
Leitung, ueber die 4,7 GB nicht zweimal gehen:

Registerkarte **Sprachmodell** -> **Vorhandene Modelldatei uebernehmen** ->
die `.gguf`-Datei auswaehlen. Oder in der Konsole:

```
PORTABLE_BUCHHALTER_KONSOLE.exe modell uebernehmen --datei D:\modell.gguf
```

Die Datei wird **kopiert**, nicht verknuepft. Ein Verweis auf ein
Netzlaufwerk waere kleiner - aber dann liefe der Datentraeger nicht mehr
fuer sich allein, und genau das ist der Sinn dieser Anwendung. Internet
braucht es dafuer nicht; das geht auch im Betriebsmodus OFFLINE.

## Derselbe Weg in der Konsole

```
PORTABLE_BUCHHALTER_KONSOLE.exe modell empfehlen
PORTABLE_BUCHHALTER_KONSOLE.exe modell einrichten --bestaetigen
```

Der erste Befehl sieht sich den Rechner an und zeigt die hinterlegten
Bezugsquellen mit Groesse, Lizenz und Pruefstand. Der zweite laedt das zur
Hardware passende Modell, prueft die Pruefsumme, bindet es ein und stellt
ihm zum Schluss eine kleine Frage. Erst wenn die beantwortet ist, meldet er
**"Das Sprachmodell ist einsatzbereit."**

Danach beantwortet der Buchhalter Fachfragen mit einer formulierten Antwort
statt mit dem Hinweis, dass kein Modell da ist.

---

## Was dabei schon fertig ist

**Der Modelldienst liegt bei.** Unter `runtime\llama` liegt `llama-server`
aus dem Projekt llama.cpp (MIT-Lizenz, Herkunft in
`runtime\llama\HERKUNFT.txt`). Sie muessen nichts installieren, nichts
uebersetzen und keinen Compiler einrichten.

Die Anwendung startet den Dienst selbst - und zwar erst bei der ersten
Frage, damit der Programmstart nicht jedes Mal auf das Laden eines mehrere
Gigabyte grossen Modells wartet. Er hoert nur auf dem eigenen Rechner
(127.0.0.1), oeffnet kein zweites Fenster und wird beim Beenden der
Anwendung mit heruntergefahren.

**Warum nicht llama-cpp-python?** Dafuer gibt es keine fertigen Pakete. Es
muesste auf Ihrem Rechner uebersetzt werden. Fuer eine Anwendung, die per
Doppelklick laufen soll, ist das kein Weg.

---

## Die Auswahl

| Profil | Modell | Bedarf | Einschaetzung |
|---|---|---|---|
| `probe` | 0,5B, 0,49 GB | ab 2 GB RAM | Nur zum Ausprobieren. Fuer Fachfragen **nicht** geeignet. |
| `light` | 3B, 2,10 GB | ab 6 GB RAM | Fuer aeltere Buerorechner. Lizenz beachten - nicht Apache-2.0. |
| `standard` | 7B, 4,68 GB (2 Teildateien) | ab 12 GB RAM | **Empfehlung.** Brauchbare deutsche Sprachqualitaet. |
| `high` | 14B, 8,99 GB (3 Teildateien) | ab 24 GB RAM | Beste Qualitaet dieser Auswahl. Auf reiner CPU langsam. |

Die Groessen sind keine Schaetzung: sie stammen aus dem Windows-Bauablauf,
der jede Adresse abgerufen hat.

**Teildateien.** Die beiden grossen Modelle liegen beim Anbieter in mehreren
Dateien vor (`...-00001-of-00002.gguf` und so weiter). Die Anwendung laedt
alle Teile und legt sie zusammen in `models\` ab; geoeffnet wird der erste
Teil, den Rest findet llama.cpp selbst. Die Teile duerfen weder umbenannt
noch getrennt werden.

Ein anderes Profil waehlen:

```
PORTABLE_BUCHHALTER_KONSOLE.exe modell einrichten --profil light --bestaetigen
```

Wichtig ist das Dateiformat **GGUF**. Andere Formate (safetensors, GPTQ,
AWQ) funktionieren mit llama.cpp nicht.

---

## Was die Anwendung dabei nicht tut

* **Sie laedt nichts ohne Ihre Bestaetigung.** Ohne `--bestaetigen` nennt
  sie nur Groesse, Lizenz und Pruefstand der Quelle und hoert auf.
* **Sie laedt nichts im Betriebsmodus OFFLINE.** Dafuer erst auf HYBRID
  oder ONLINE umschalten.
* **Sie behauptet keine gepruefte Quelle.** Steht bei einer Bezugsquelle
  "nicht geprueft", dann wurde ihre Adresse in diesem Programmstand nicht
  abgerufen - und die geladene Datei wird nicht gegen eine hinterlegte
  Pruefsumme geprueft. Das steht dann auch dabei. Umgekehrt nennt eine
  gepruefte Quelle den Bauablauf, in dem sie abgerufen wurde - man kann also
  nachsehen, statt es glauben zu muessen.
* **Sie prueft die Pruefsumme nur, wo es eine gibt.** Zur Zeit ist das das
  Probemodell. Bei den Modellen in Teildateien bildet der Bauablauf keine
  Gesamtpruefsumme; dort steht deshalb ausdruecklich, dass beim Laden nicht
  auf Unversehrtheit geprueft wird.
* **Sie faengt zu wenig Platz vorher ab**, statt mittendrin abzubrechen.

---

## Eigene Bezugsquelle

Wer ein anderes Modell verwenden will - etwa ein firmeninternes oder ein
Modell mit anderer Lizenz:

```
PORTABLE_BUCHHALTER_KONSOLE.exe modell laden --url <Adresse> [--pruefsumme <sha256>]
```

Oder ganz ohne Befehl: die GGUF-Datei einfach nach `models\` kopieren. Die
Anwendung findet sie beim naechsten Start - oder sofort ueber **Lage neu
pruefen** in der Registerkarte.

Die hinterlegten Bezugsquellen stehen in `config\model_catalog.json` und
lassen sich dort ergaenzen, ohne die Anwendung neu zu bauen.

---

## Nachsehen, ob es laeuft

```
PORTABLE_BUCHHALTER_KONSOLE.exe modell status
PORTABLE_BUCHHALTER_KONSOLE.exe modell pruefen
```

`status` sagt, was da ist und was fehlt. `pruefen` stellt dem Modell eine
Frage und nennt Antwortzeit und Geschwindigkeit in Token je Sekunde.

---

## Wenn es klemmt

| Meldung | Bedeutung | Was zu tun ist |
|---|---|---|
| "Es fehlt: die Modelldatei" | Es liegt kein GGUF-Modell in `models\` | `modell einrichten --bestaetigen` |
| "Es fehlt: der Modelldienst (runtime/llama)" | Der Ordner `runtime\llama` fehlt im Paket | Das vollstaendige Windows-Paket verwenden; der Dienst liegt dort bei |
| "Der Modelldienst ist nicht hochgekommen" | Der Dienst konnte das Modell nicht laden | Die Meldung nennt die letzte Ausgabe des Dienstes. Meist zu wenig Arbeitsspeicher - ein kleineres Profil waehlen. Ausfuehrlich in `logs\llama-server.log` |
| Die erste Antwort dauert sehr lange | Das Modell wird geladen | Einmalig. Die folgenden Antworten kommen deutlich schneller |
| Antworten sind fachlich duenn | Das Modell ist zu klein | `probe` ist ausdruecklich nicht fuer Fachfragen gedacht. `standard` verwenden |

---

## Zur Einordnung

Die Kette - Dienst starten, warten bis er bereit ist, fragen, schrittweise
ausgeben, abbrechen, beenden - ist automatisch geprueft. Mit einem echten
GGUF-Modell laeuft sie im Windows-Bauablauf.

Die **fachliche Guete** der Antworten haengt vom gewaehlten Modell ab und
ist damit nicht Sache des Programms. Sie gehoert in die Abnahme
(`docs/ABNAHME.md`, Punkte C und D). Auch mit gutem Modell gilt
unveraendert: jede Antwort ist fachliche Zuarbeit und braucht die Pruefung
durch einen verantwortlichen Menschen.
