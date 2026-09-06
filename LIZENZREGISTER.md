# Lizenzregister

Stand: 2026-09-06 · erzeugt aus der tatsaechlich vorhandenen Installation

Masterprompt 63 verlangt die Unterscheidung zwischen **Nutzung im eigenen
Projekt** und **Weitergabe an Kunden**. Eine Komponente darf nicht deshalb
in ein kommerzielles Produkt, weil sie kostenlos herunterladbar ist.

> Diese Zusammenstellung ist die Arbeitsgrundlage fuer die rechtliche
> Pruefung nach Masterprompt 71 - **nicht deren Ergebnis**. Sie ersetzt
> keine Rechtsberatung.

## Bestandteile

| Komponente | Version | Herausgeber | Lizenz | Kommerziell | Weitergabe | Pflicht |
|---|---|---|---|---|---|---|
| Python | 3.11.15 | Python Software Foundation | PSF License Agreement | ja | ja | ja |
| SQLite | 3.45.1 | SQLite Consortium | Public Domain | ja | ja | ja |
| Tcl/Tk (Tkinter) | nicht verfuegbar | Tcl Core Team | Tcl/Tk License (BSD-artig) | ja | ja | ja |
| cryptography | 41.0.7 | PyCA | Apache-2.0 ODER BSD-3-Clause | ja | ja | optional |
| pypdf | 6.17.0 | pypdf-Projekt | BSD-3-Clause | ja | ja | optional |
| openpyxl | 3.1.5 | openpyxl-Projekt | MIT | ja | ja | optional |
| PyInstaller | nicht installiert | PyInstaller Development Team | GPL-2.0-or-later MIT Bootloader-Ausnahme | ja | mit Auflagen | optional |
| llama.cpp (llama-server) | nicht ermittelt | Georgi Gerganov und Mitwirkende | MIT | ja | ja | ja |
| Qwen2.5-Instruct (GGUF) | nicht ermittelt | Alibaba Cloud / Qwen-Team | Apache-2.0 | ja | zu pruefen | optional |
| Mistral-Nemo-Instruct (GGUF) | nicht ermittelt | Mistral AI / NVIDIA | Apache-2.0 | ja | zu pruefen | optional |
| Gesetze im Internet | nicht ermittelt | Bundesministerium der Justiz / juris | Amtliches Werk, § 5 UrhG (gemeinfrei) | ja | mit Auflagen | optional |
| EUR-Lex | nicht ermittelt | Amt fuer Veroeffentlichungen der EU | Beschluss 2011/833/EU (Wiederverwendung zulaessig) | ja | mit Auflagen | optional |
| Mitgelieferte Fachmodule | nicht ermittelt | Hersteller | Bestandteil dieses Produkts | ja | ja | ja |

## Hinweise je Bestandteil

### Python

* Zweck: Programmiersprache und Laufzeitumgebung der Anwendung
* Art: laufzeit
* Quelle: https://www.python.org/
* Geprueft am: 2026-09-05

Weitergabe der Laufzeit im gepackten Programm ist zulaessig; der Lizenztext ist beizulegen.

### SQLite

* Zweck: Eingebettete Datenbank fuer Fach- und Unternehmenswissen
* Art: laufzeit
* Quelle: https://www.sqlite.org/
* Geprueft am: 2026-09-05

Gemeinfrei. Teil der Python-Standardbibliothek.

### Tcl/Tk (Tkinter)

* Zweck: Grafische Benutzeroberflaeche
* Art: laufzeit
* Quelle: https://www.tcl.tk/software/tcltk/license.html
* Geprueft am: 2026-09-05

Teil der Windows-Installation von Python; Lizenzhinweis beilegen.

### cryptography

* Zweck: Geheimnistresor (AES-256-GCM) und Lizenzsignatur (Ed25519)
* Art: bibliothek
* Quelle: https://cryptography.io/
* Geprueft am: 2026-09-05

Enthaelt OpenSSL-Bestandteile (Apache-2.0). Hinweistexte beilegen. Ohne dieses Paket werden keine Geheimnisse gespeichert.

### pypdf

* Zweck: Textextraktion aus PDF-Belegen
* Art: bibliothek
* Quelle: https://pypdf.readthedocs.io/
* Geprueft am: 2026-09-05

Optional. Fehlt es, meldet die Anwendung PDF als nicht auswertbar.

### openpyxl

* Zweck: Excel-Import im Connector
* Art: bibliothek
* Quelle: https://openpyxl.readthedocs.io/
* Geprueft am: 2026-09-05

Optional. Alternative ohne dieses Paket: CSV-Export.

### PyInstaller

* Zweck: Erzeugt die Windows-Programme aus dem Quellcode
* Art: werkzeug
* Quelle: https://pyinstaller.org/en/stable/license.html
* Geprueft am: 2026-09-05

WICHTIG: Die Bootloader-Ausnahme erlaubt die Weitergabe der erzeugten Programme unter eigener Lizenz. Die Ausnahme gilt nur, solange der Bootloader unveraendert bleibt. Wird er geaendert, greift die GPL. Vor dem Vertrieb pruefen.

### llama.cpp (llama-server)

* Zweck: Ausfuehrung des lokalen Sprachmodells
* Art: laufzeit
* Quelle: https://github.com/ggml-org/llama.cpp
* Geprueft am: 2026-09-05

WIRD MITGELIEFERT: die Windows-Fassung enthaelt die fertige Programmdatei unter runtime/llama. Damit ist der MIT-Hinweis beizulegen; er liegt als runtime/llama/HERKUNFT.txt bei und nennt die verwendete Fassung. Fuer llama-cpp-python gibt es keine fertigen Pakete - es wird nicht verwendet.

### Qwen2.5-Instruct (GGUF)

* Zweck: Lokales Sprachmodell, Profile LIGHT und STANDARD
* Art: modell
* Quelle: https://huggingface.co/Qwen
* Geprueft am: 2026-09-05

Apache-2.0 erlaubt kommerzielle Nutzung. Bei einer Weitergabe DES MODELLS mit dem Produkt sind die Lizenz- und Hinweispflichten der konkreten Modellfassung zu pruefen; die Quantisierung stammt oft von Dritten mit eigenen Bedingungen. Empfehlung: das Modell vom Kunden beziehen lassen, statt es mitzuliefern.

### Mistral-Nemo-Instruct (GGUF)

* Zweck: Lokales Sprachmodell, Profil HIGH QUALITY
* Art: modell
* Quelle: https://huggingface.co/mistralai
* Geprueft am: 2026-09-05

Wie oben: Weitergabe der konkreten Modellfassung gesondert pruefen.

### Gesetze im Internet

* Zweck: Amtliche Gesetzestexte in der lokalen Wissensbasis
* Art: daten
* Quelle: https://www.gesetze-im-internet.de/
* Geprueft am: 2026-09-05

Gesetzestexte selbst sind gemeinfrei. Die Aufbereitung des Portals unterliegt eigenen Nutzungsbedingungen - vor einer Weitergabe vorbereiteter Bestaende pruefen.

### EUR-Lex

* Zweck: Unionsrecht in der lokalen Wissensbasis
* Art: daten
* Quelle: https://eur-lex.europa.eu/
* Geprueft am: 2026-09-05

Wiederverwendung einschliesslich kommerzieller Zwecke zulaessig; Quellenangabe erforderlich.

### Mitgelieferte Fachmodule

* Zweck: Aufbereitetes Fachwissen fuer den Offlinebetrieb ab Start
* Art: daten
* Quelle: src/profiles/buchhalter/knowledge/
* Geprueft am: 2026-09-05

Eigene Erstellung. Sekundaerquelle; amtliche Quellen haben Vorrang.

## Vor einem Vertrieb zu klaeren

1. PyInstaller: Weitergabe mit Auflagen - WICHTIG: Die Bootloader-Ausnahme erlaubt die Weitergabe der erzeugten Programme unter eigener Lizenz. Die Ausnahme gilt nur, solange der Bootloader unveraendert bleibt. Wird er geaendert, greift die GPL. Vor dem Vertrieb pruefen.
2. Qwen2.5-Instruct (GGUF): Weitergabe zu pruefen - Apache-2.0 erlaubt kommerzielle Nutzung. Bei einer Weitergabe DES MODELLS mit dem Produkt sind die Lizenz- und Hinweispflichten der konkreten Modellfassung zu pruefen; die Quantisierung stammt oft von Dritten mit eigenen Bedingungen. Empfehlung: das Modell vom Kunden beziehen lassen, statt es mitzuliefern.
3. Mistral-Nemo-Instruct (GGUF): Weitergabe zu pruefen - Wie oben: Weitergabe der konkreten Modellfassung gesondert pruefen.
4. Gesetze im Internet: Weitergabe mit Auflagen - Gesetzestexte selbst sind gemeinfrei. Die Aufbereitung des Portals unterliegt eigenen Nutzungsbedingungen - vor einer Weitergabe vorbereiteter Bestaende pruefen.
5. EUR-Lex: Weitergabe mit Auflagen - Wiederverwendung einschliesslich kommerzieller Zwecke zulaessig; Quellenangabe erforderlich.

## Nicht enthalten

Es werden keine kostenpflichtigen oder zugangsbeschraenkten Datenbanken
kopiert. Das Unternehmensregister ist im Quellenregister deshalb
ausdruecklich deaktiviert.
