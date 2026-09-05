# Branding-Konzept - PORTIVA

Stand: 05.09.2026 · Branch `claude/portable-ki-buchhalter-xr1qlj`

## Grundsatz: Marke fest, Profil dynamisch

**PORTIVA** ist die Plattformmarke und aendert sich nie. Der
Mitarbeitername kommt aus dem aktiven Berufsprofil. Daraus entsteht der
Fenstertitel:

```
PORTIVA - Buchhalter
PORTIVA - Controller
PORTIVA - Rechtsabteilung
```

Der Profilname steht **nirgends** fest im Programmcode. `pkc.branding.profilname()`
liest ihn aus dem Profil (`short_name`, ersatzweise `display_name`, `name`,
`profile_id`). Ein Profilwechsel aendert damit den Titel, ohne dass die
Anwendung neu gebaut werden muss.

| Bestandteil | Herkunft |
|---|---|
| Markenname `PORTIVA` | `pkc.branding.MARKE`, ueberschreibbar in `config/brand.json` |
| Claim | `Portable KI-Mitarbeiter-Plattform` |
| Profilname | `src/profiles/<profil>/profile.json`, Feld `short_name` |
| Logo, Symbol | `assets/branding/`, relative Pfade |

## Ablage

```
assets/
  branding/
    original/
      portiva_logo_original.png      das unveraenderte Original
      HIER_ORIGINAL_ABLEGEN.md       Anleitung dazu
    portiva_logo_primary.png         abgeleitet
    portiva_logo_light.png           abgeleitet, heller Grund
    portiva_logo_dark.png            abgeleitet, dunkler Grund
    portiva_icon.png                 abgeleitet, quadratisch, 256 px
    portiva_icon.ico                 abgeleitet, 16/24/32/48/64/128/256
```

Das Original wird **nie** ueberschrieben. Ein Test prueft, dass das
Ableitungswerkzeug nicht auf die Originaldatei schreibt.

## Ableitung

```
python tools/branding_ableiten.py
```

Erzeugt alle Varianten aus dem Original. Proportionen bleiben erhalten:
das Hauptlogo wird nur skaliert, das Symbol wird mittig auf eine
durchsichtige quadratische Flaeche gelegt statt gestaucht. Farben und
Formen werden nicht veraendert; die hellen und dunklen Varianten
unterscheiden sich nur im Hintergrund.

Braucht Pillow (`pip install pillow`) - bewusst keine Laufzeitabhaengigkeit
der Anwendung, sondern ein Werkzeug fuer die Einrichtung.

## Portable Pfadlogik

Alle Brandingpfade sind **relativ** zu `assets/`. `Brand.pfad()` weist ab:

* absolute Pfade (ueberleben den Wechsel des Laufwerksbuchstabens nicht)
* Pfade, die aus dem Assetbereich herausfuehren (`../`)

`assets` gehoert zur **Programm**wurzel, nicht zum Kundenbereich: bei
mehreren Kundenbereichen auf einem Datentraeger gibt es trotzdem nur ein
Logo.

## Einbindung in die Oberflaeche

| Ort | Was |
|---|---|
| Splashscreen | Logo, `PORTIVA - <Profil>`, Claim, `Profil: <Name>`, danach die **tatsaechlichen** Pruefergebnisse |
| Startschaltflaeche | `<PROFIL> STARTEN`, aus dem Profil gebildet |
| Hauptfenster, Titelleiste | `PORTIVA - <Profil>` |
| Hauptfenster, Kopfzeile | kleines Logo und Markentitel |
| Fenster- und Taskleistensymbol | `portiva_icon.ico`, ersatzweise `portiva_icon.png` |
| EXE | Symbol eingebettet, sofern die `.ico` beim Bauen vorliegt |
| Systempruefung | eigener Punkt **Branding**: nennt fehlende Dateien |

## Fehlerbehandlung

Fehlt oder beschaedigt ist eine Brandingdatei:

* die Anwendung startet unveraendert
* an Stelle des Logos steht der Schriftzug `PORTIVA - <Profil>`
* die Systempruefung meldet, welche Dateien fehlen, und nennt die Abhilfe
* es wird **kein Ersatzlogo erzeugt** und keine andere Marke verwendet

## Offline und ohne Host-PC

Saemtliche Brandingdateien liegen im portablen Verzeichnis. Es wird nichts
aus dem Netz geladen und nichts aus AppData, Temp, Benutzerprofil oder
Browsercache gelesen.

## Stand der Umsetzung

| Punkt | Stand |
|---|---|
| Marke und Profil getrennt | **umgesetzt und getestet** |
| Fenstertitel `PORTIVA - <Profil>` | **umgesetzt und getestet** |
| Profilwechsel ohne Codeaenderung | **umgesetzt und getestet** |
| relative Pfade, kein Laufwerksbuchstabe | **umgesetzt und getestet** |
| Ortswechsel (anderes Laufwerk) | **umgesetzt und getestet** |
| Fallback ohne Absturz, kein Ersatzlogo | **umgesetzt und getestet** |
| Ableitungswerkzeug, Original unangetastet | **umgesetzt und geprueft** |
| Splashscreen mit Logo und Profil | umgesetzt, am Bildschirm noch nicht gesehen |
| Fenster-, Taskleisten- und EXE-Symbol | umgesetzt, am Bildschirm noch nicht gesehen |
| Originalsymbol im Projekt | **vorhanden** (`portiva_app_icon_512.png`, 512x512, RGBA) |
| Abgeleitete Varianten | **erzeugt und geprueft** |
| Icon 16 bis 256 Pixel | **erzeugt und geprueft** |
| Breites Logo mit Schriftzug | **offen** - siehe unten |

## Was geliefert wurde

`assets/branding/original/portiva_app_icon_512.png` - das quadratische
PORTIVA-Symbol, 512x512, mit Transparenz. Daraus sind alle Varianten
erzeugt.

Eine technische Anpassung war noetig und ist zulaessig: Im Original lag das
Zeichen nicht mittig - 22 Bildpunkte Rand links, 125 rechts. Bei 16 Pixeln
haette das Symbol sichtbar verrutscht ausgesehen. Das Werkzeug schneidet
deshalb den durchsichtigen Rand ab und setzt das Zeichen mittig auf eine
quadratische Flaeche mit gleichmaessigem Rand. **Das Zeichen selbst bleibt
unveraendert**: gleiche Farben, gleiche Formen, gleiches
Seitenverhaeltnis - es faellt nur der ungleiche Leerraum weg. Ein Test
prueft, dass das Ergebnis quadratisch und mittig ist.

## Was noch fehlt

Das **breite Logo mit dem Schriftzug PORTIVA**. Es liegt nicht vor.

Als Hauptlogo dient deshalb derzeit das Symbol; der Schriftzug wird in der
Oberflaeche daneben als Text gesetzt (`PORTIVA - Buchhalter`). Das ist eine
uebliche und zulaessige Darstellung - es wird ausdruecklich **kein**
Schriftzug nachgebaut.

Wird die breite Fassung nachgereicht - unter
`assets/branding/original/`, ein Name wie `portiva_logo_original.png` -,
genuegt ein erneuter Lauf von `tools/branding_ableiten.py`. Das Werkzeug
erkennt beide Dateien getrennt und verwendet dann automatisch das breite
Logo als Hauptlogo und das Symbol weiterhin fuer die Icons.
