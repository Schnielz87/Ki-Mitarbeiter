"""Bestandsliste aller Softwarebestandteile (Masterprompt 63, 64).

Die Angaben sind gepflegt, nicht geraten: je Bestandteil ist festgehalten,
unter welcher Lizenz er steht, ob eine **kommerzielle Nutzung** und ob eine
**Weitergabe an Kunden** zulaessig ist. Masterprompt 63 verlangt genau diese
Unterscheidung - eine Komponente darf nicht deshalb ins Produkt, weil sie
kostenlos herunterladbar ist.

Die installierte Version wird zur Laufzeit ermittelt, damit die Liste nicht
veraltet.

**Wichtiger Vorbehalt:** Diese Zusammenstellung ersetzt keine
Rechtsberatung. Sie ist die Arbeitsgrundlage fuer die Pruefung nach
Masterprompt 71, nicht deren Ergebnis.
"""

from __future__ import annotations

import platform
import sqlite3
import sys
from dataclasses import asdict, dataclass, field

CHECK_DATE = "2026-09-05"


@dataclass
class Component:
    name: str
    purpose: str
    licence: str
    commercial_use: str          # ja | nein | zu pruefen
    redistribution: str          # ja | nein | zu pruefen | mit Auflagen
    required: bool
    source: str
    notes: str = ""
    version: str = "nicht ermittelt"
    vendor: str = ""
    checked: str = CHECK_DATE
    kind: str = "bibliothek"     # laufzeit | bibliothek | modell | daten | werkzeug

    def as_dict(self) -> dict:
        return asdict(self)


#: Gepflegte Bestandsliste. Versionen werden zur Laufzeit ergaenzt.
COMPONENTS: list[Component] = [
    Component(
        name="Python", kind="laufzeit",
        purpose="Programmiersprache und Laufzeitumgebung der Anwendung",
        licence="PSF License Agreement", vendor="Python Software Foundation",
        commercial_use="ja", redistribution="ja", required=True,
        source="https://www.python.org/",
        notes="Weitergabe der Laufzeit im gepackten Programm ist zulaessig; "
              "der Lizenztext ist beizulegen.",
    ),
    Component(
        name="SQLite", kind="laufzeit",
        purpose="Eingebettete Datenbank fuer Fach- und Unternehmenswissen",
        licence="Public Domain", vendor="SQLite Consortium",
        commercial_use="ja", redistribution="ja", required=True,
        source="https://www.sqlite.org/",
        notes="Gemeinfrei. Teil der Python-Standardbibliothek.",
    ),
    Component(
        name="Tcl/Tk (Tkinter)", kind="laufzeit",
        purpose="Grafische Benutzeroberflaeche",
        licence="Tcl/Tk License (BSD-artig)", vendor="Tcl Core Team",
        commercial_use="ja", redistribution="ja", required=True,
        source="https://www.tcl.tk/software/tcltk/license.html",
        notes="Teil der Windows-Installation von Python; Lizenzhinweis beilegen.",
    ),
    Component(
        name="cryptography", kind="bibliothek",
        purpose="Geheimnistresor (AES-256-GCM) und Lizenzsignatur (Ed25519)",
        licence="Apache-2.0 ODER BSD-3-Clause", vendor="PyCA",
        commercial_use="ja", redistribution="ja", required=False,
        source="https://cryptography.io/",
        notes="Enthaelt OpenSSL-Bestandteile (Apache-2.0). Hinweistexte beilegen. "
              "Ohne dieses Paket werden keine Geheimnisse gespeichert.",
    ),
    Component(
        name="pypdf", kind="bibliothek",
        purpose="Textextraktion aus PDF-Belegen",
        licence="BSD-3-Clause", vendor="pypdf-Projekt",
        commercial_use="ja", redistribution="ja", required=False,
        source="https://pypdf.readthedocs.io/",
        notes="Optional. Fehlt es, meldet die Anwendung PDF als nicht auswertbar.",
    ),
    Component(
        name="openpyxl", kind="bibliothek",
        purpose="Excel-Import im Connector",
        licence="MIT", vendor="openpyxl-Projekt",
        commercial_use="ja", redistribution="ja", required=False,
        source="https://openpyxl.readthedocs.io/",
        notes="Optional. Alternative ohne dieses Paket: CSV-Export.",
    ),
    Component(
        name="PyInstaller", kind="werkzeug",
        purpose="Erzeugt die Windows-Programme aus dem Quellcode",
        licence="GPL-2.0-or-later MIT Bootloader-Ausnahme",
        vendor="PyInstaller Development Team",
        commercial_use="ja", redistribution="mit Auflagen", required=False,
        source="https://pyinstaller.org/en/stable/license.html",
        notes="WICHTIG: Die Bootloader-Ausnahme erlaubt die Weitergabe der "
              "erzeugten Programme unter eigener Lizenz. Die Ausnahme gilt nur, "
              "solange der Bootloader unveraendert bleibt. Wird er geaendert, "
              "greift die GPL. Vor dem Vertrieb pruefen.",
    ),
    Component(
        name="llama.cpp (llama-server)", kind="laufzeit",
        purpose="Ausfuehrung des lokalen Sprachmodells",
        licence="MIT", vendor="Georgi Gerganov und Mitwirkende",
        commercial_use="ja", redistribution="ja", required=True,
        source="https://github.com/ggml-org/llama.cpp",
        notes="WIRD MITGELIEFERT: die Windows-Fassung enthaelt die fertige "
              "Programmdatei unter runtime/llama. Damit ist der MIT-Hinweis "
              "beizulegen; er liegt als runtime/llama/HERKUNFT.txt bei und "
              "nennt die verwendete Fassung. Fuer llama-cpp-python gibt es "
              "keine fertigen Pakete - es wird nicht verwendet.",
    ),
    Component(
        name="Qwen2.5-Instruct (GGUF)", kind="modell",
        purpose="Lokales Sprachmodell, Profile LIGHT und STANDARD",
        licence="Apache-2.0", vendor="Alibaba Cloud / Qwen-Team",
        commercial_use="ja", redistribution="zu pruefen", required=False,
        source="https://huggingface.co/Qwen",
        notes="Apache-2.0 erlaubt kommerzielle Nutzung. Bei einer Weitergabe DES "
              "MODELLS mit dem Produkt sind die Lizenz- und Hinweispflichten der "
              "konkreten Modellfassung zu pruefen; die Quantisierung stammt oft "
              "von Dritten mit eigenen Bedingungen. Empfehlung: das Modell vom "
              "Kunden beziehen lassen, statt es mitzuliefern.",
    ),
    Component(
        name="Mistral-Nemo-Instruct (GGUF)", kind="modell",
        purpose="Lokales Sprachmodell, Profil HIGH QUALITY",
        licence="Apache-2.0", vendor="Mistral AI / NVIDIA",
        commercial_use="ja", redistribution="zu pruefen", required=False,
        source="https://huggingface.co/mistralai",
        notes="Wie oben: Weitergabe der konkreten Modellfassung gesondert pruefen.",
    ),
    Component(
        name="Gesetze im Internet", kind="daten",
        purpose="Amtliche Gesetzestexte in der lokalen Wissensbasis",
        licence="Amtliches Werk, § 5 UrhG (gemeinfrei)",
        vendor="Bundesministerium der Justiz / juris",
        commercial_use="ja", redistribution="mit Auflagen", required=False,
        source="https://www.gesetze-im-internet.de/",
        notes="Gesetzestexte selbst sind gemeinfrei. Die Aufbereitung des "
              "Portals unterliegt eigenen Nutzungsbedingungen - vor einer "
              "Weitergabe vorbereiteter Bestaende pruefen.",
    ),
    Component(
        name="EUR-Lex", kind="daten",
        purpose="Unionsrecht in der lokalen Wissensbasis",
        licence="Beschluss 2011/833/EU (Wiederverwendung zulaessig)",
        vendor="Amt fuer Veroeffentlichungen der EU",
        commercial_use="ja", redistribution="mit Auflagen", required=False,
        source="https://eur-lex.europa.eu/",
        notes="Wiederverwendung einschliesslich kommerzieller Zwecke zulaessig; "
              "Quellenangabe erforderlich.",
    ),
    Component(
        name="Mitgelieferte Fachmodule", kind="daten",
        purpose="Aufbereitetes Fachwissen fuer den Offlinebetrieb ab Start",
        licence="Bestandteil dieses Produkts", vendor="Hersteller",
        commercial_use="ja", redistribution="ja", required=True,
        source="src/profiles/buchhalter/knowledge/",
        notes="Eigene Erstellung. Sekundaerquelle; amtliche Quellen haben Vorrang.",
    ),
]

#: Pakete, deren installierte Version zur Laufzeit ermittelt wird.
_PACKAGES = {
    "cryptography": "cryptography",
    "pypdf": "pypdf",
    "openpyxl": "openpyxl",
    "PyInstaller": "PyInstaller",
}


def _installed_version(modulname: str) -> str:
    from importlib import metadata

    for kandidat in (modulname, modulname.replace("_", "-")):
        try:
            return metadata.version(kandidat)
        except metadata.PackageNotFoundError:
            continue
    return "nicht installiert"


def collect_components() -> list[Component]:
    """Bestandsliste mit den tatsaechlich vorhandenen Versionen."""
    ergebnis: list[Component] = []
    for eintrag in COMPONENTS:
        kopie = Component(**eintrag.as_dict())
        if kopie.name == "Python":
            kopie.version = platform.python_version()
        elif kopie.name == "SQLite":
            kopie.version = sqlite3.sqlite_version
        elif kopie.name == "Tcl/Tk (Tkinter)":
            try:
                import tkinter
                kopie.version = str(tkinter.TkVersion)
            except Exception:
                kopie.version = "nicht verfuegbar"
        elif kopie.name in _PACKAGES:
            kopie.version = _installed_version(_PACKAGES[kopie.name])
        ergebnis.append(kopie)
    return ergebnis


def open_questions(components: list[Component] | None = None) -> list[str]:
    """Punkte, die vor einem Vertrieb geklaert sein muessen."""
    components = components or collect_components()
    offen = []
    for eintrag in components:
        if eintrag.redistribution in ("zu pruefen", "mit Auflagen"):
            offen.append(f"{eintrag.name}: Weitergabe {eintrag.redistribution} - {eintrag.notes}")
        if eintrag.commercial_use == "zu pruefen":
            offen.append(f"{eintrag.name}: kommerzielle Nutzung noch zu pruefen")
    return offen
