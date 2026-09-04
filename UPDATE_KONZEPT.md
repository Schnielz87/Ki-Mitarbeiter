# Wissensupdate - Konzept

Masterprompt Abschnitte 11, 28, 31.

## Ziel

Online erworbenes Wissen soll **nicht nur online** nutzbar sein. Nach einem
Update liegen die Inhalte lokal vor und stehen ohne Internet zur Verfuegung.

```
Montag  : online erkennt die Anwendung ein neues BMF-Schreiben,
          laedt es, bereitet es auf, indexiert es
Dienstag: kein Internet - der Buchhalter nutzt dieses Schreiben trotzdem
```

## Ein gespeicherter Link ist keine Wissensbasis

Deshalb diese Kette:

```
Quelle -> Abruf -> Original speichern -> Text extrahieren -> normalisieren
       -> Metadaten erzeugen -> in Abschnitte teilen -> indexieren
       -> Wissensstand fortschreiben
```

Jede Stufe hinterlaesst eine Datei auf dem Datentraeger:

| Stufe | Ablage |
|---|---|
| Original, unveraendert | `resources/raw/<Quelle>/<Dokument>.<endung>` |
| Extrahierter Text | `resources/normalized/<Quelle>/<Dokument>.txt` |
| Metadaten | `resources/metadata/<Quelle>/<Dokument>.json` |
| Abschnitte und Index | `resources/index/knowledge.db` |
| Bericht | `updates/<Lauf-ID>/bericht.md` und `.json` |

Das Original wird aufbewahrt, damit die Aufbereitung jederzeit wiederholbar
und nachpruefbar ist.

## Quellenregister

`config/source_registry.json` beschreibt jede Quelle maschinenlesbar:
Kennung, Name, Herausgeber, Prioritaet nach der Quellenhierarchie, Art,
Basisadresse, Lizenz, aktiv ja/nein und die abrufbaren Dokumente.

Enthalten sind Q01 bis Q12: Gesetze im Internet, BMF, ELSTER, BZSt, BFH,
BVerfG, EUR-Lex, EuGH, Bundesgesetzblatt, Unternehmensregister (bewusst
deaktiviert), IHK/DIHK sowie E-Rechnung und XRechnung.

**Alle Eintraege tragen `verified: false`.** Die URLs konnten in der
Entwicklungsumgebung nicht live geprueft werden. Der erste Online-Lauf
validiert jede Adresse und meldet Fehlschlaege im Bericht - er behauptet
keinen Erfolg.

Das Register ist eine gewoehnliche Textdatei und kann erweitert werden, ohne
das Programm zu aendern.

## Inkrementell

Drei Stufen verhindern unnoetige Arbeit:

1. **ETag / If-None-Match** und **Last-Modified / If-Modified-Since** - der
   Server antwortet mit `304 Not Modified`, es wird nichts uebertragen.
2. **SHA-256** ueber den Inhalt - liefert der Server dieselben Bytes ohne
   Cache-Kopf, wird trotzdem nicht neu indexiert.
3. **Dokumentversion** - erst ein tatsaechlich geaenderter Inhalt erhoeht sie.

## Zeitplan

| Einstellung | Bedeutung |
|---|---|
| `manual` (Vorgabe) | nur auf ausdrueckliche Anforderung |
| `weekly` | faellig, wenn das letzte erfolgreiche Update 7 Tage her ist |
| `monthly` | ... 30 Tage |
| `custom` | ... `updates.custom_interval_days` Tage |

**Wichtig und ehrlich:** Ein Update kann nur stattfinden, wenn die Anwendung
laeuft, der Datentraeger angeschlossen und Internet vorhanden ist. Ein
Datentraeger in der Schublade aktualisiert sich nicht. Die Anwendung
behauptet das an keiner Stelle.

## Ablauf eines Laufs

1. Internetverbindung pruefen - ohne Verbindung endet der Lauf mit
   `no_network`, es wird nichts veraendert
2. Quellenregister laden und in die Datenbank uebernehmen
3. **Sicherung** der Wissensdatenbank nach `updates/<Lauf-ID>/`
4. je Dokument: bedingter Abruf, Aenderung erkennen
5. Original speichern
6. extrahieren und normalisieren
7. Metadaten schreiben
8. in Abschnitte teilen und indexieren
9. Einbettungen ergaenzen
10. Integritaet pruefen
11. Bericht schreiben
12. Wissensstand fortschreiben

## Bericht

Je Lauf entstehen `bericht.json` und `bericht.md` mit: Ausloeser, Beginn und
Ende, Gesamtergebnis, Zahlen (geprueft, aktualisiert, unveraendert,
fehlgeschlagen), Hinweisen sowie einer Zeile je Dokument mit Status und
Begruendung.

Moegliche Gesamtergebnisse:

| Ergebnis | Bedeutung |
|---|---|
| `success` | alles abgerufen, keine Fehlschlaege |
| `partial` | teils erfolgreich - Fehlschlaege stehen im Bericht |
| `failed` | kein einziges Dokument abrufbar; **der lokale Stand blieb unveraendert** |
| `no_network` | kein Internet; es wurde nichts abgerufen |
| `rolled_back` | Lauf wurde zurueckgenommen |

## Ruecknahme

Vor jedem Lauf wird die Wissensdatenbank gesichert. `update --zuruecknehmen
<Lauf-ID>` stellt den vorherigen Stand her, sichert den aktuellen vorher als
`knowledge.db.before_rollback` und prueft die zurueckgesetzte Datei auf
Integritaet.

**Das Unternehmensgedaechtnis ist davon nie betroffen** - es liegt in einer
anderen Datenbank.

## Lizenzgrenzen

Es werden nur frei zugaengliche amtliche und offen lizenzierte Inhalte
gespeichert. Entgeltpflichtige oder zugangsbeschraenkte Datenbanken werden
nicht kopiert. Das Unternehmensregister ist deshalb im Register enthalten,
aber **deaktiviert**.

## Geprueft durch

Acht automatische Tests gegen einen echten lokalen HTTP-Server:
Erstlauf mit Ablage und Index, Inkrementalitaet ueber ETag, Neuindexierung
bei geaendertem Inhalt, Wiederauffinden im Index, Offlinelauf ohne
Veraenderung, Trockenlauf ohne Schreiben, vollstaendige Ruecknahme,
Zeitplanlogik.

**Nicht geprueft:** der Abruf von den echten amtlichen Servern. Der
Netzzugang der Entwicklungsumgebung war auf Paketregistries beschraenkt.
Dieser Schritt steht in `docs/ABNAHME.md`.
