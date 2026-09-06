"""Datei- und Artefakterzeugung (Erweiterung E4).

Geprueft wird nicht nur, dass eine Datei entsteht, sondern dass sie von den
ueblichen Lesebibliotheken wieder eingelesen werden kann - eine Datei mit der
richtigen Endung, die kein Programm oeffnet, waere eine Scheinerfuellung.

Nicht geprueft (und auch nicht behauptet): dass Microsoft Word, Excel und
PowerPoint die Dateien anzeigen. Das laesst sich nur auf einem Windows-Rechner
feststellen und gehoert zur Abnahme nach docs/ABNAHME.md.
"""

from __future__ import annotations

import json
import zipfile

import pytest

from pkc.artefakte import (
    ArtefaktFehler, Artefaktwerk, Dokument, Schreiber, abmelden, aus_markdown,
    dateiname, formate, registrieren,
)

ANTWORT = (
    "## Ergebnis\n"
    "Die Rechnung aus Frankreich ist beim Leistungsempfaenger zu versteuern [1].\n\n"
    "- Reverse Charge pruefen\n"
    "- Umsatzsteuer-Identifikationsnummer erfassen\n\n"
    "| Konto | Beleg | Betrag |\n"
    "|---|---|---|\n"
    "| 1200 | 0042 | 1.234,56 |\n\n"
    "**QUELLEN**\n"
    "[1] UStG Paragraf 13b\n"
)


@pytest.fixture
def werk(portable_root):
    return Artefaktwerk(portable_root, profil="Buchhalter")


# -- Das Dokumentmodell --------------------------------------------------

def test_markdown_wird_zu_bloecken():
    dokument = aus_markdown(ANTWORT, titel="Antwort")
    arten = [block.art for block in dokument.bloecke]
    assert "ueberschrift" in arten and "aufzaehlung" in arten and "tabelle" in arten
    tabelle = dokument.tabellen[0]
    assert tabelle[0] == ["Konto", "Beleg", "Betrag"]
    assert not any("**" in block.text for block in dokument.bloecke), \
        "Auszeichnungszeichen duerfen nicht in der Datei landen"


def test_fundstellen_bleiben_einzelne_zeilen():
    dokument = aus_markdown("**QUELLEN**\n[1] UStG\n[2] AO\n")
    absaetze = [b.text for b in dokument.bloecke if b.art == "absatz"]
    assert absaetze == ["[1] UStG", "[2] AO"]


# -- Die einzelnen Formate ----------------------------------------------

def test_alle_geforderten_formate_sind_da():
    """E4 nennt acht Formate als Mindestumfang."""
    vorhanden = {s.kuerzel for s in formate()}
    assert {"xlsx", "csv", "docx", "pptx", "pdf", "txt", "md", "json"} <= vorhanden


def test_txt_md_und_json(werk):
    text = werk.erzeugen(ANTWORT, "txt", name="Probe")
    assert "Reverse Charge pruefen" in text.pfad.read_text(encoding="utf-8")

    md = werk.erzeugen(ANTWORT, "md", name="Probe")
    inhalt = md.pfad.read_text(encoding="utf-8")
    assert "| Konto | Beleg | Betrag |" in inhalt

    daten = json.loads(werk.erzeugen(ANTWORT, "json", name="Probe").pfad.read_text("utf-8"))
    assert daten["bloecke"][0]["art"] == "ueberschrift"


def test_csv_traegt_die_tabelle(werk):
    artefakt = werk.erzeugen(ANTWORT, "csv", name="Buchungen")
    roh = artefakt.pfad.read_bytes()
    assert roh.startswith(b"\xef\xbb\xbf"), "Excel braucht die Byte-Order-Marke"
    text = roh.decode("utf-8-sig")
    assert text.splitlines()[0] == "Konto;Beleg;Betrag"


def test_xlsx_ist_lesbar_und_rechnet_mit_betraegen(werk):
    openpyxl = pytest.importorskip("openpyxl")
    artefakt = werk.erzeugen(ANTWORT, "xlsx", name="Auswertung")
    blatt = openpyxl.load_workbook(artefakt.pfad).active
    werte = [zeile for zeile in blatt.iter_rows(values_only=True)]
    flach = [z for zeile in werte for z in zeile if z is not None]
    assert "Konto" in flach
    assert 1234.56 in flach, "Betraege muessen Zahlen sein, sonst rechnet Excel nicht"
    assert "0042" in flach, "eine Belegnummer darf ihre fuehrende Null nicht verlieren"


def test_docx_ist_lesbar_und_hat_gliederung(werk):
    docx = pytest.importorskip("docx")
    artefakt = werk.erzeugen(ANTWORT, "docx", name="Bericht")
    dokument = docx.Document(str(artefakt.pfad))
    stile = {absatz.style.name for absatz in dokument.paragraphs}
    assert "Title" in stile and any(s.startswith("Heading") for s in stile)
    assert len(dokument.tables) == 1
    assert dokument.core_properties.title == "Bericht"


def test_pptx_ist_lesbar(werk):
    pptx = pytest.importorskip("pptx")
    artefakt = werk.erzeugen(ANTWORT, "pptx", name="Vortrag")
    praesentation = pptx.Presentation(str(artefakt.pfad))
    assert len(praesentation.slides) >= 1
    texte = [form.text_frame.text for folie in praesentation.slides
             for form in folie.shapes if form.has_text_frame]
    assert any("Ergebnis" in t for t in texte)


def test_pdf_ist_lesbar(werk):
    pypdf = pytest.importorskip("pypdf")
    artefakt = werk.erzeugen(ANTWORT, "pdf", name="Bericht")
    leser = pypdf.PdfReader(str(artefakt.pfad))
    assert len(leser.pages) >= 1
    text = leser.pages[0].extract_text()
    assert "Reverse Charge" in text
    assert leser.metadata.title == "Bericht"


def test_office_dateien_sind_gueltige_pakete(werk):
    """Ohne die Beziehungsdateien oeffnet Office gar nichts."""
    erwartet = {
        "docx": ["[Content_Types].xml", "_rels/.rels", "word/document.xml"],
        "xlsx": ["[Content_Types].xml", "_rels/.rels", "xl/workbook.xml"],
        "pptx": ["[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml",
                 "ppt/slideMasters/slideMaster1.xml", "ppt/theme/theme1.xml"],
    }
    for format, teile in erwartet.items():
        artefakt = werk.erzeugen(ANTWORT, format, name=f"Paket_{format}")
        with zipfile.ZipFile(artefakt.pfad) as archiv:
            inhalt = set(archiv.namelist())
            assert archiv.testzip() is None
            for teil in teile:
                assert teil in inhalt, f"{teil} fehlt in der {format}-Datei"


# -- Die Engine ----------------------------------------------------------

def test_dateien_liegen_im_kundenbereich(werk, portable_root):
    artefakt = werk.erzeugen("Text", "txt", name="Ablage")
    assert artefakt.pfad.is_relative_to(portable_root.root)
    assert "workspace" in artefakt.pfad.parts, \
        "erzeugte Dateien sind Kundendaten und gehoeren nicht in den Programmordner"


def test_nichts_wird_stillschweigend_ueberschrieben(werk):
    erste = werk.erzeugen("Erster Inhalt", "txt", name="Bericht")
    zweite = werk.erzeugen("Zweiter Inhalt", "txt", name="Bericht")
    assert erste.pfad != zweite.pfad
    assert zweite.version == 2 and "_v2" in zweite.pfad.name
    assert "Erster Inhalt" in erste.pfad.read_text(encoding="utf-8")


def test_ueberschreiben_nur_auf_anweisung(werk):
    erste = werk.erzeugen("Erster Inhalt", "txt", name="Bericht")
    zweite = werk.erzeugen("Neuer Inhalt", "txt", name="Bericht", ueberschreiben=True)
    assert erste.pfad == zweite.pfad
    assert "Neuer Inhalt" in zweite.pfad.read_text(encoding="utf-8")


def test_verzeichnis_haelt_die_erzeugten_dateien_fest(werk):
    werk.erzeugen("A", "txt", name="Eins")
    werk.erzeugen("B", "md", name="Zwei")
    liste = werk.liste()
    assert [eintrag["format"] for eintrag in liste] == ["md", "txt"]
    assert all(eintrag["vorhanden"] for eintrag in liste)
    assert all(eintrag["pruefsumme"] for eintrag in liste)


def test_dateinamen_sind_auf_jedem_system_zulaessig():
    assert dateiname('Rechnung 1/2026: "Muster" GmbH') == "Rechnung_1_2026_Muster_GmbH"
    assert dateiname("Umsatzsteuervoranmeldung fuer Maerz") .startswith("Umsatzsteuer")
    assert dateiname("CON") == "artefakt", "unter Windows belegte Namen sind gesperrt"
    assert dateiname("") == "artefakt"
    assert ".." not in dateiname("../../etc/passwd")


def test_unbekanntes_format_wird_verstaendlich_gemeldet(werk):
    with pytest.raises(ArtefaktFehler) as fehler:
        werk.erzeugen("Text", "dwg", name="Zeichnung")
    assert "dwg" in str(fehler.value) and "Moeglich sind" in str(fehler.value)


def test_kein_halbes_artefakt_bei_fehler(werk):
    """Bricht das Schreiben ab, darf keine Bruchstueckdatei zurueckbleiben."""
    def kaputt(dokument):
        raise RuntimeError("Formatfehler")

    registrieren(Schreiber("kaputt", ".kaputt", "Testformat", kaputt))
    try:
        with pytest.raises(ArtefaktFehler):
            werk.erzeugen("Text", "kaputt", name="Halb")
        vorhanden = list(werk.ordner.glob("Halb*"))
        assert not vorhanden, f"Reste geblieben: {vorhanden}"
    finally:
        abmelden("kaputt")


def test_eigener_dateihandler_kann_angemeldet_werden():
    """E4: ein neues Format darf keinen neuen Programmstand erfordern."""
    registrieren(Schreiber("xml", ".xml", "XML", lambda d: b"<xml/>"))
    try:
        assert "xml" in {s.kuerzel for s in formate()}
        with pytest.raises(ValueError):
            registrieren(Schreiber("xml", ".xml", "Zweiter", lambda d: b""))
    finally:
        abmelden("xml")


def test_dokument_ohne_tabelle_kommt_trotzdem_nach_excel(werk):
    openpyxl = pytest.importorskip("openpyxl")
    artefakt = werk.erzeugen("Nur ein Satz ohne Tabelle.", "xlsx", name="Ohne")
    blatt = openpyxl.load_workbook(artefakt.pfad).active
    werte = [z for zeile in blatt.iter_rows(values_only=True) for z in zeile if z]
    assert any("Nur ein Satz" in str(w) for w in werte)


def test_leeres_dokument_erzeugt_trotzdem_eine_datei(werk):
    artefakt = werk.erzeugen(Dokument(titel="Leer"), "pdf", name="Leer")
    assert artefakt.pfad.is_file() and artefakt.groesse > 0
