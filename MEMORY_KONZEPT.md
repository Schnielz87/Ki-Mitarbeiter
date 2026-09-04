# Unternehmensgedaechtnis - Konzept

Masterprompt Abschnitte 13 bis 20.

## Warum es das gibt

Ein Chatverlauf ist kein Gedaechtnis. Sagt der Nutzer heute „Wir verwenden
SKR03", muss der Buchhalter das naechste Woche, auf einem anderen Rechner und
ohne Internet noch wissen. Deshalb liegen dauerhaft relevante Angaben
**strukturiert in einer Datenbank auf dem Datentraeger** - nicht im
Modellkontext, nicht im Arbeitsspeicher, nicht im Chatverlauf.

## Strikte Trennung (Abschnitt 14)

| | Fachwissen | Unternehmenswissen |
|---|---|---|
| Datei | `resources/index/knowledge.db` | `database/company.db` |
| Inhalt | Gesetze, Erlasse, Rechtsprechung, Fachmodule | Kontenrahmen, Prozesse, Regeln, Ansprechpartner |
| Beispiel | „Voraussetzungen des innergemeinschaftlichen Erwerbs" | „Unternehmen X verwendet SKR03" |
| Ersetzbar | ja, jederzeit neu aufbaubar | **nein**, nicht wiederbeschaffbar |
| Bei einem Update | wird ersetzt | wird **nicht angefasst** |

Diese Trennung ist der Grund, warum ein fehlgeschlagenes Wissensupdate das
Unternehmenswissen nicht gefaehrden kann. Ein Test prueft genau das:
Loeschen der gesamten Fachwissensdatenbank laesst das Unternehmenswissen
unberuehrt.

## Was gespeichert wird

Kategorien: Stammdaten, Organisation, Personen, Buchhaltung, Steuer,
Prozesse, Regeln, Freigaben, Kunden, Lieferanten, wiederkehrende
Sachverhalte, Dokumente, Vorlagen, Praeferenzen, ERP-Konfiguration.

Je Eintrag (Abschnitt 17):

| Feld | Bedeutung |
|---|---|
| `mem_key` | stabiler fachlicher Schluessel, z.B. `company.chart_of_accounts` |
| `title`, `content` | Titel und Inhalt |
| `value_json` | optional strukturiert |
| `category` | Kategorie |
| `status` | active, archived, superseded |
| `version` | Fassungsnummer, steigt bei jeder inhaltlichen Aenderung |
| `confidence` | wie sicher die Angabe erkannt wurde |
| `source`, `origin` | woher (Chat, Onboarding, Import, Agent) |
| `valid_from`, `valid_to`, `review_at` | Zeitbezug und Wiedervorlage |
| `created_at`, `updated_at`, `created_by` | Entstehung |

## Versionierung statt Ueberschreiben (Abschnitt 16)

Eine Aenderung ueberschreibt nichts. Der alte Stand wird auf `superseded`
gesetzt, der neue als Version n+1 angelegt, und beide Schritte landen in
`memory_history` mit Zeitpunkt, Urheber und Grund.

```
v1 SKR03  (create,  2026-09-04)   -> superseded
v2 SKR04  (update,  2026-11-02)   -> active
```

Der Verlauf ist in der Oberflaeche einsehbar (**Unternehmenswissen →
Verlauf**) und ueber `wissen history <schluessel>`.

Ein identischer Inhalt erzeugt **keine** neue Version - sonst wuerde der
Verlauf durch Wiederholungen unbrauchbar.

## Loeschen

Standard ist **Archivieren**: der Eintrag verschwindet aus dem aktiven
Bestand, bleibt aber nachvollziehbar und ist wiederherstellbar. Endgueltiges
Loeschen ist moeglich (`--endgueltig`), wird aber protokolliert.

## Automatische Erkennung (Abschnitt 15)

Beim Absenden einer Nachricht prueft eine **regelbasierte** Erkennung, ob
darin eine dauerhaft relevante Angabe steckt. Regelbasiert, weil das auch
ohne Sprachmodell funktionieren, deterministisch sein und automatisch
getestet werden koennen muss.

Unterschieden wird:

| Dauerhaft | Einmalig |
|---|---|
| „Wir verwenden grundsaetzlich SKR03." | „Pruefe diese Rechnung." |
| „Rechnungen ab 5.000 EUR muessen freigegeben werden." | „Wie wird ein ig. Erwerb gebucht?" |
| „Merke dir: Meier GmbH immer auf Kostenstelle 4711." | „Was waere, wenn ..." |

Merkmale fuer Dauerhaftigkeit: „grundsaetzlich", „immer", „in der Regel",
„standardmaessig", „bei uns gilt", „merke dir", „unsere Regel" und
aehnliche. Gegenmerkmale: „diese Rechnung", „einmalig", „testweise",
„angenommen"; Fragen werden nicht gespeichert.

**Bei Unsicherheit wird gefragt, nicht gespeichert.** Die Rueckfrage nennt
den erkannten Inhalt, die Kategorie und den Grund der Erkennung. Das
Verhalten laesst sich in den Einstellungen aendern
(`memory.confirm_before_store`).

## Verwendung in einer Antwort

Bei jeder Frage fliessen ein:

1. gezielte Treffer aus der Volltextsuche im Gedaechtnis
2. die wohlbekannten Stammdaten (Kontenrahmen, Rechtsform, USt-Status ...)

Sie stehen im Modellkontext in einem eigenen, klar gekennzeichneten Block
mit dem Hinweis, dass sie Vorrang vor allgemeinen Annahmen haben.

## Export und Lesbarkeit

`company/unternehmensprofil.json` (maschinenlesbar) und
`company/unternehmensprofil.md` (lesbar, nach Kategorien gegliedert) werden
beim Onboarding und auf Wunsch geschrieben. Damit ist das Gedaechtnis auch
ohne die Anwendung einsehbar - wichtig fuer Nachvollziehbarkeit und
Datenauskunft.

## Was ausdruecklich **nicht** ins Gedaechtnis gehoert

Passwoerter, API-Schluessel, Tokens und Zugangsdaten. Die gehoeren in den
verschluesselten Tresor (`SICHERHEITSKONZEPT.md`).

## Geprueft durch

* Anlegen, Aendern, Verlauf, Archivieren, Wiederherstellen, Suche
* Erkennung dauerhafter Angaben inklusive Abgrenzung zu Einzelfaellen
* Speichern, Programm beenden, neu starten - Angabe ist wieder da
* Datentraeger an einen anderen Ort verschieben - Angabe ist wieder da
* Rueckfrage vor dem Speichern (Ja speichert, Nein speichert nicht)
* Unternehmenswissen ueberlebt den Verlust der gesamten Fachwissensdatenbank
