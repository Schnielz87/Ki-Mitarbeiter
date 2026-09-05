# Lizenzierung und Kopierschutz

Masterprompt Abschnitte 84 bis 97.

## Das Problem

Ein portables Produkt liegt vollstaendig auf einem Datentraeger. Wer ihn
kopiert, hat scheinbar ein zweites Produkt. Gleichzeitig soll derselbe
Datentraeger an **mehreren** Rechnern laufen - eine Bindung an einen
einzelnen PC waere das Gegenteil von portabel.

Ziel ist deshalb nicht, das Kopieren von Dateien zu verhindern - das ist
technisch nicht garantierbar (Abschnitt 84). Ziel ist:

> **Kopierte Instanz + keine gueltige Lizenz = nicht produktiv nutzbar.**

## Die Loesung: Bindung an den Datentraeger, nicht an den PC

| | |
|---|---|
| Gebunden wird an | die Kennung des **Datentraegers** (Volume-Seriennummer unter Windows, Dateisystem-UUID unter Linux) |
| Nicht gebunden wird an | den Rechner, den Benutzer, die Netzwerkkarte |

Daraus folgt genau das gewuenschte Verhalten:

| Vorgang | Ergebnis |
|---|---|
| Dieselbe SSD an PC A, B und C | Lizenz bleibt gueltig |
| Programmordner auf eine zweite SSD kopieren | **nicht lizenziert** |
| Datentraeger an anderen Laufwerksbuchstaben | Lizenz bleibt gueltig |
| Unternehmensdaten aus einer Sicherung zurueckspielen | erzeugt **keine** zusaetzliche Lizenz |

**Ehrliche Grenze:** Ein bitgenaues Abbild eines ganzen Datentraegers kann die
Kennung reproduzieren. Das Kopieren von Dateien wird verhindert, das Klonen
eines ganzen Volumes nicht vollstaendig. Das ist eine bewusste Abwaegung -
strengere Verfahren (Dongle, Aktivierungspflicht bei jedem Start) wuerden die
Portabilitaet und den Offlinebetrieb beschaedigen.

## Aufbau der Lizenz

```
license/
    license.json      Lizenzdaten im Klartext, fuer den Kunden lesbar
    license.sig       Ed25519-Signatur ueber genau diese Daten
```

Inhalt der Lizenzdatei (Abschnitt 86): Lizenz-ID, Kunde, Kundennummer,
Produkt, Produktversion, Fachmodule, Lizenztyp, erlaubte Instanzen,
Instanz-ID, Fingerabdruck des Datentraegers, Aktivierungsdatum, gegebenenfalls
Ablaufdatum, Wartungsstatus, Herausgeber, Hinweise.

### Warum eine Signatur und keine Konfigurationsdatei

Ein Eintrag wie `licensed=true` in einer Textdatei ist in zehn Sekunden
geaendert (Abschnitt 91). Geprueft wird deshalb eine **Ed25519-Signatur** ueber
die kanonische Darstellung der Lizenzdaten. Jede Aenderung an der Lizenzdatei -
Kundenname, Ablaufdatum, Anzahl der Instanzen, Fingerabdruck - macht die
Signatur ungueltig.

**Der private Signaturschluessel ist niemals Teil der Anwendung.** Ausgeliefert
wird ausschliesslich der oeffentliche Pruefschluessel. Ohne den privaten
Schluessel kann niemand eine gueltige Lizenz erzeugen - auch nicht, wer den
Programmcode vollstaendig liest.

## Offline pruefbar

Der Start braucht **keinen Lizenzserver und keine Internetverbindung**
(Abschnitt 87). Beim Start:

1. Lizenzdatei laden
2. Signatur pruefen
3. Produkt und Fachmodul pruefen
4. Laufzeit pruefen
5. Bindung an den Datentraeger pruefen
6. erst danach die produktive Nutzung freigeben

Ein Test stellt sicher, dass die Pruefung das Netz nicht einmal anfasst.

## Was bei ungueltiger Lizenz passiert - und was nicht

Abschnitt 95 ist eindeutig, und die Umsetzung haelt sich daran:

**Es wird nichts geloescht, nichts gesperrt, nichts verschluesselt.**

Gesperrt wird ausschliesslich die *produktive Nutzung*. Weiterhin moeglich
bleiben:

* Lizenzangaben ansehen (`lizenz info`)
* Unternehmenswissen ansehen (`wissen list`)
* **Unternehmensdaten exportieren** (`kunde export`)
* Sicherung erstellen (`sicherung`)
* Aktivierung vorbereiten (`lizenz anfrage`)

Die Meldung nennt Grund, Instanz-ID und den Weg zur Loesung.

## Ablauf einer Aktivierung

```
Kunde:      PORTABLE_BUCHHALTER_KONSOLE.exe lizenz anfrage --kunde "Muster GmbH" --datei anfrage.json
            (enthaelt Instanz-ID und Fingerabdruck - keine Unternehmensdaten)
                                  |
Hersteller: python tools/lizenz_ausstellen.py ausstellen --anfrage anfrage.json
                                  |
Kunde:      PORTABLE_BUCHHALTER_KONSOLE.exe lizenz aufnehmen --lizenz license.json --signatur license.sig
```

Optional kann spaeter eine Online-Aktivierung ergaenzt werden (Abschnitt 88).
Der Ablauf bleibt derselbe; nur der Weg der Anfrage wird automatisiert. Eine
**dauerhafte** Internetverbindung wird nie verlangt.

## Ersatz bei Defekt oder Verlust

Ein Kopierschutz darf einen zahlenden Kunden nicht aussperren (Abschnitt 93):

```
Alte Instanz deaktivieren  ->  neue Instanz-ID erfragen
->  neue signierte Lizenz ausstellen  ->  Unternehmensdaten aus der Sicherung
```

Der Hersteller fuehrt dazu eine Liste der ausgestellten Lizenzen und
deaktiviert die alte Instanz-ID. Technisch ist der Vorgang derselbe wie eine
Erstaktivierung; organisatorisch braucht es einen belegten Grund.

## Lizenz und Daten sind getrennt

Abschnitt 94: Der Kunde muss seine Unternehmensdaten sichern und
wiederherstellen koennen, **ohne** dadurch Lizenzen zu erzeugen. Deshalb
enthaelt der Datenexport (`kunde export`) ausdruecklich **keine** Lizenz. Ein
Test belegt das.

## Moegliche Lizenzmodelle

Die Technik legt kein Geschaeftsmodell fest (Abschnitte 78, 89). Unterstuetzt
werden ueber die Felder `license_type`, `allowed_instances`, `modules`,
`expiry_date` und `maintenance_until` unter anderem:

pro portabler Instanz · pro KI-Mitarbeiter · pro Fachmodul · pro Unternehmen ·
pro Standort · Mehrfachlizenz · befristet · unbefristet mit Wartungsvertrag

## Stand dieser Fassung

| Punkt | Stand |
|---|---|
| Lizenzpruefung implementiert | **ja** |
| Offline pruefbar | **ja**, getestet |
| Signaturverfahren | **Ed25519**, getestet |
| Kopiertest | **bestanden** (Kopie auf zweiten Datentraeger nicht lizenziert) |
| Manipulationstest | **bestanden** (jede Aenderung faellt auf) |
| Ersatzprozess | technisch umgesetzt und getestet |
| Pruefschluessel des Herausgebers | **noch nicht hinterlegt** - geschaeftliche Entscheidung |
| Lizenzpflicht aktiv | **nein** - diese Fassung ist eine Pilotfassung |

Solange kein Pruefschluessel hinterlegt ist, meldet die Anwendung ehrlich
"nicht pruefbar", statt eine Gueltigkeit vorzutaeuschen.

## Vor der kommerziellen Freigabe

1. Schluesselpaar des Herausgebers erzeugen und den privaten Teil sicher
   verwahren (`tools/lizenz_ausstellen.py schluessel`)
2. Oeffentlichen Pruefschluessel in `src/pkc/licensing/verify.py` eintragen
3. `license.required` auf `true` und `product.stage` auf `commercial` setzen
4. Lizenzbedingungen juristisch pruefen lassen
5. Die sieben Testfaelle aus Abschnitt 96 auf echter Hardware wiederholen
6. Programme signieren (Code-Signing) - siehe SICHERHEITSKONZEPT.md
