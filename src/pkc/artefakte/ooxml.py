"""Word-, Excel- und PowerPoint-Dateien ohne Fremdpaket schreiben (E4).

Diese drei Formate sind ZIP-Archive mit XML darin (Office Open XML). Sie
lassen sich deshalb mit der Standardbibliothek erzeugen - ohne installiertes
Microsoft Office und ohne Internet, wie es die Erweiterung verlangt.

Bewusst schlicht: Ueberschriften, Absaetze, Aufzaehlungen und Tabellen. Keine
Formatvorlagen aus fremden Dateien, keine Bilder, keine Diagramme. Wer mehr
braucht, ergaenzt einen eigenen Dateihandler - dafuer ist die Registrierung
in ``schreiber.py`` da.

Geprueft ist, dass die erzeugten Dateien von den ueblichen Lesebibliotheken
(python-docx, openpyxl, python-pptx) wieder eingelesen werden koennen. Ob
Microsoft Office sie anzeigt, laesst sich nur auf einem Windows-Rechner
feststellen; das gehoert zur Abnahme.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from .modell import Dokument

_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
_NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _jetzt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _kern(titel: str, angaben: dict) -> str:
    """docProps/core.xml - die Metadaten, die jede Datei tragen soll."""
    zeit = _jetzt()
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties '
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"<dc:title>{escape(titel)}</dc:title>"
        f"<dc:creator>{escape(angaben.get('ersteller', 'PORTIVA'))}</dc:creator>"
        f"<cp:lastModifiedBy>{escape(angaben.get('ersteller', 'PORTIVA'))}</cp:lastModifiedBy>"
        f"<dc:description>{escape(angaben.get('beschreibung', ''))}</dc:description>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{zeit}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{zeit}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def _packen(teile: dict[str, str | bytes]) -> bytes:
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as archiv:
        for name, inhalt in teile.items():
            archiv.writestr(name, inhalt if isinstance(inhalt, bytes)
                            else inhalt.encode("utf-8"))
    return puffer.getvalue()


# -- Word ---------------------------------------------------------------

_DOCX_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:styles xmlns:w="{_NS_W}">'
    '<w:docDefaults><w:rPrDefault><w:rPr>'
    '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/>'
    '</w:rPr></w:rPrDefault></w:docDefaults>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/></w:style>'
    '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/>'
    '<w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="44"/>'
    '<w:color w:val="1F4E79"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>'
    '<w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="32"/>'
    '<w:color w:val="1F4E79"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/>'
    '<w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/>'
    '<w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="ListParagraph">'
    '<w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/></w:style>'
    "</w:styles>"
)


def _w_absatz(text: str, stil: str = "", einzug: int = 0, fest: bool = False) -> str:
    eigenschaften = ""
    if stil or einzug:
        eigenschaften = "<w:pPr>"
        if stil:
            eigenschaften += f'<w:pStyle w:val="{stil}"/>'
        if einzug:
            eigenschaften += f'<w:ind w:left="{einzug}"/>'
        eigenschaften += "</w:pPr>"
    lauf = ""
    if fest:
        lauf = '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/></w:rPr>'
    return (f"<w:p>{eigenschaften}<w:r>{lauf}"
            f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')


def _w_tabelle(zeilen: list[list[str]]) -> str:
    if not zeilen:
        return ""
    spalten = max(len(z) for z in zeilen)
    breite = int(9360 / spalten)
    raender = ("<w:tblBorders>" + "".join(
        f'<w:{kante} w:val="single" w:sz="4" w:color="BFBFBF"/>'
        for kante in ("top", "left", "bottom", "right", "insideH", "insideV")
    ) + "</w:tblBorders>")
    raus = ["<w:tbl><w:tblPr>" + '<w:tblW w:w="0" w:type="auto"/>' + raender
            + "</w:tblPr><w:tblGrid>"
            + f'<w:gridCol w:w="{breite}"/>' * spalten + "</w:tblGrid>"]
    for nummer, zeile in enumerate(zeilen):
        gefuellt = list(zeile) + [""] * (spalten - len(zeile))
        raus.append("<w:tr>")
        for wert in gefuellt:
            fett = "<w:rPr><w:b/></w:rPr>" if nummer == 0 else ""
            raus.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{breite}" w:type="dxa"/></w:tcPr>'
                f"<w:p><w:r>{fett}"
                f'<w:t xml:space="preserve">{escape(wert)}</w:t></w:r></w:p></w:tc>'
            )
        raus.append("</w:tr>")
    raus.append("</w:tbl>")
    return "".join(raus)


def docx_bytes(dokument: Dokument) -> bytes:
    koerper: list[str] = []
    if dokument.titel:
        koerper.append(_w_absatz(dokument.titel, "Title"))
    for block in dokument.bloecke:
        if block.art == "ueberschrift":
            koerper.append(_w_absatz(block.text, f"Heading{min(3, max(1, block.ebene))}"))
        elif block.art == "absatz":
            koerper.append(_w_absatz(block.text))
        elif block.art == "aufzaehlung":
            for punkt in block.punkte:
                koerper.append(_w_absatz(f"- {punkt}", "ListParagraph", einzug=360))
        elif block.art == "code":
            for zeile in block.text.splitlines():
                koerper.append(_w_absatz(zeile, einzug=360, fest=True))
        elif block.art == "tabelle":
            koerper.append(_w_tabelle(block.zeilen))
            koerper.append(_w_absatz(""))

    dokument_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{_NS_W}" xmlns:r="{_NS_R}"><w:body>'
        + "".join(koerper)
        + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
          '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/>'
          "</w:sectPr></w:body></w:document>"
    )

    return _packen({
        "[Content_Types].xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
            'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.'
            'openxmlformats-package.core-properties+xml"/></Types>',
        "_rels/.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/'
            'relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            "</Relationships>",
        "word/_rels/document.xml.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>",
        "word/document.xml": dokument_xml,
        "word/styles.xml": _DOCX_STYLES,
        "docProps/core.xml": _kern(dokument.titel, dokument.angaben),
    })


# -- Excel --------------------------------------------------------------

def _zahl(wert: str) -> float | None:
    """Erkennt einen Betrag - und nur den.

    Bewusst eng: umgewandelt wird nur, was ein Dezimalkomma oder ein
    Waehrungszeichen traegt. Eine Kontonummer, eine Belegnummer oder eine
    Postleitzahl bleibt damit Text und verliert keine fuehrende Null. Lieber
    eine Zahl zu wenig als eine veraenderte Nummer in der Buchhaltung.
    """
    roh = wert.strip()
    waehrung = "EUR" in roh or "\u20ac" in roh
    roh = roh.replace("EUR", "").replace("\u20ac", "").strip()
    if not roh or ("," not in roh and not waehrung):
        return None
    if "," in roh:                      # deutsches Format: 1.234,56
        roh = roh.replace(".", "").replace(",", ".")
    try:
        return float(roh)
    except ValueError:
        return None


def _spaltenname(nummer: int) -> str:
    name = ""
    while nummer > 0:
        nummer, rest = divmod(nummer - 1, 26)
        name = chr(ord("A") + rest) + name
    return name


def xlsx_bytes(dokument: Dokument) -> bytes:
    """Schreibt die Tabellen des Dokuments in ein Arbeitsblatt.

    Enthaelt das Dokument keine Tabelle, kommt der Text zeilenweise in die
    erste Spalte. So entsteht nie eine leere Datei, die aussieht, als sei
    etwas verlorengegangen.
    """
    zeilen: list[tuple[list[str], bool]] = []
    if dokument.titel:
        zeilen.append(([dokument.titel], True))
        zeilen.append(([], False))

    hat_tabelle = any(b.art == "tabelle" for b in dokument.bloecke)
    for block in dokument.bloecke:
        if block.art == "tabelle":
            for nummer, zeile in enumerate(block.zeilen):
                zeilen.append((list(zeile), nummer == 0))
            zeilen.append(([], False))
        elif not hat_tabelle:
            if block.art == "ueberschrift":
                zeilen.append(([block.text], True))
            elif block.art == "absatz":
                zeilen.append(([block.text], False))
            elif block.art == "aufzaehlung":
                zeilen.extend(([f"- {punkt}"], False) for punkt in block.punkte)
            elif block.art == "code":
                zeilen.extend(([z], False) for z in block.text.splitlines())

    blatt = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             f'<worksheet xmlns="{_NS_S}"><sheetData>']
    for nummer, (werte, fett) in enumerate(zeilen, start=1):
        if not werte:
            continue
        felder = []
        for spalte, wert in enumerate(werte, start=1):
            bezug = f"{_spaltenname(spalte)}{nummer}"
            stil = ' s="1"' if fett else ""
            zahl = _zahl(wert)
            if zahl is None:
                felder.append(f'<c r="{bezug}"{stil} t="inlineStr"><is><t '
                              f'xml:space="preserve">{escape(wert)}</t></is></c>')
            else:
                felder.append(f'<c r="{bezug}"{stil}><v>{zahl!r}</v></c>')
        blatt.append(f'<row r="{nummer}">' + "".join(felder) + "</row>")
    blatt.append("</sheetData></worksheet>")

    return _packen({
        "[Content_Types].xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
            'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.'
            'openxmlformats-package.core-properties+xml"/></Types>',
        "_rels/.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/'
            'relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            "</Relationships>",
        "xl/workbook.xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<workbook xmlns="{_NS_S}" xmlns:r="{_NS_R}"><sheets>'
            '<sheet name="Blatt1" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>",
        "xl/worksheets/sheet1.xml": "".join(blatt),
        "xl/styles.xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<styleSheet xmlns="{_NS_S}">'
            '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
            '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>'
            "</cellStyleXfs>"
            '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
            "</cellXfs>"
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/>'
            "</cellStyles></styleSheet>",
        "docProps/core.xml": _kern(dokument.titel, dokument.angaben),
    })


# -- PowerPoint ---------------------------------------------------------

#: Foliengroesse 16:9 in EMU (1 cm = 360000 EMU).
_FOLIE_BREITE, _FOLIE_HOEHE = 12192000, 6858000

_THEMA = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<a:theme xmlns:a="{_NS_A}" name="PORTIVA"><a:themeElements>'
    '<a:clrScheme name="PORTIVA">'
    '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
    '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
    '<a:dk2><a:srgbClr val="1F4E79"/></a:dk2><a:lt2><a:srgbClr val="EEF3F8"/></a:lt2>'
    '<a:accent1><a:srgbClr val="1F4E79"/></a:accent1>'
    '<a:accent2><a:srgbClr val="2E75B6"/></a:accent2>'
    '<a:accent3><a:srgbClr val="9DC3E6"/></a:accent3>'
    '<a:accent4><a:srgbClr val="7F7F7F"/></a:accent4>'
    '<a:accent5><a:srgbClr val="404040"/></a:accent5>'
    '<a:accent6><a:srgbClr val="C00000"/></a:accent6>'
    '<a:hlink><a:srgbClr val="0563C1"/></a:hlink>'
    '<a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme>'
    '<a:fontScheme name="PORTIVA">'
    '<a:majorFont><a:latin typeface="Calibri Light"/><a:ea typeface=""/>'
    '<a:cs typeface=""/></a:majorFont>'
    '<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/>'
    '<a:cs typeface=""/></a:minorFont></a:fontScheme>'
    '<a:fmtScheme name="PORTIVA">'
    '<a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
    '<a:lnStyleLst>'
    '<a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    "</a:lnStyleLst>"
    '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>'
    '<a:effectStyle><a:effectLst/></a:effectStyle>'
    '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
    '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>'
    "</a:fmtScheme></a:themeElements></a:theme>"
)

_LEERE_FOLIE = (
    '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/>'
    '<p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>{formen}</p:spTree></p:cSld>'
    '<p:clrMapOvr><a:overrideClrMapping bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" '
    'accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" '
    'accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
    "</p:clrMapOvr>"
)


def _p_form(kennung: int, name: str, x: int, y: int, breite: int, hoehe: int,
            absaetze: str) -> str:
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{kennung}" name="{escape(name)}"/>'
        '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{breite}" cy="{hoehe}"/>'
        '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="square"><a:normAutofit/></a:bodyPr><a:lstStyle/>'
        f"{absaetze}</p:txBody></p:sp>"
    )


def _p_absatz(text: str, groesse: int, fett: bool = False, punkt: bool = False,
              farbe: str = "404040") -> str:
    aufzaehlung = '<a:buChar char="-"/>' if punkt else "<a:buNone/>"
    return (
        f'<a:p><a:pPr marL="{"285750" if punkt else "0"}" '
        f'indent="{"-285750" if punkt else "0"}">{aufzaehlung}</a:pPr>'
        f'<a:r><a:rPr lang="de-DE" sz="{groesse}" b="{1 if fett else 0}" dirty="0">'
        f'<a:solidFill><a:srgbClr val="{farbe}"/></a:solidFill></a:rPr>'
        f"<a:t>{escape(text)}</a:t></a:r></a:p>"
    )


def _folien(dokument: Dokument) -> list[tuple[str, list[str]]]:
    """Teilt das Dokument in Folien: Ueberschrift plus Stichpunkte."""
    folien: list[tuple[str, list[str]]] = []
    titel = dokument.titel or "Bericht"
    punkte: list[str] = []
    for block in dokument.bloecke:
        if block.art == "ueberschrift":
            folien.append((titel, punkte))
            titel, punkte = block.text, []
        elif block.art == "absatz":
            punkte.append(block.text)
        elif block.art == "aufzaehlung":
            punkte.extend(block.punkte)
        elif block.art == "tabelle":
            for zeile in block.zeilen:
                punkte.append(" | ".join(zeile))
        elif block.art == "code":
            punkte.extend(block.text.splitlines())
    folien.append((titel, punkte))

    # Zu viele Stichpunkte werden auf Folgefolien verteilt - lieber eine
    # Folie mehr als eine unlesbare.
    verteilt: list[tuple[str, list[str]]] = []
    for kopf, inhalte in folien:
        inhalte = [i for i in inhalte if i.strip()]
        if not inhalte:
            verteilt.append((kopf, []))
            continue
        for nummer in range(0, len(inhalte), 7):
            teil = inhalte[nummer:nummer + 7]
            verteilt.append((kopf if nummer == 0 else f"{kopf} (Fortsetzung)", teil))
    return verteilt


def pptx_bytes(dokument: Dokument) -> bytes:
    folien = _folien(dokument)
    teile: dict[str, str | bytes] = {}

    folien_xml = []
    for nummer, (kopf, punkte) in enumerate(folien, start=1):
        formen = _p_form(2, "Titel", 838200, 550000, _FOLIE_BREITE - 1676400, 1000000,
                         _p_absatz(kopf, 3200, fett=True, farbe="1F4E79"))
        if punkte:
            absaetze = "".join(_p_absatz(p, 1800, punkt=True) for p in punkte)
            formen += _p_form(3, "Inhalt", 838200, 1750000,
                              _FOLIE_BREITE - 1676400, _FOLIE_HOEHE - 2300000, absaetze)
        folien_xml.append(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:sld xmlns:a="{_NS_A}" xmlns:r="{_NS_R}" xmlns:p="{_NS_P}">'
            + _LEERE_FOLIE.format(formen=formen) + "</p:sld>"
        )
        teile[f"ppt/slides/slide{nummer}.xml"] = folien_xml[-1]
        teile[f"ppt/slides/_rels/slide{nummer}.xml.rels"] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/slideLayout" '
            'Target="../slideLayouts/slideLayout1.xml"/></Relationships>'
        )

    folienliste = "".join(
        f'<p:sldId id="{255 + nummer}" r:id="rId{nummer + 1}"/>'
        for nummer in range(1, len(folien) + 1)
    )
    folienbezuege = "".join(
        f'<Relationship Id="rId{nummer + 1}" Type="http://schemas.openxmlformats.org/'
        f'officeDocument/2006/relationships/slide" Target="slides/slide{nummer}.xml"/>'
        for nummer in range(1, len(folien) + 1)
    )
    folienueberschreibungen = "".join(
        f'<Override PartName="/ppt/slides/slide{nummer}.xml" ContentType="application/vnd.'
        'openxmlformats-officedocument.presentationml.slide+xml"/>'
        for nummer in range(1, len(folien) + 1)
    )

    teile.update({
        "[Content_Types].xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
            'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.theme+xml"/>'
            + folienueberschreibungen +
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.'
            'openxmlformats-package.core-properties+xml"/></Types>',
        "_rels/.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/officeDocument" '
            'Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.'
            'openxmlformats.org/package/2006/relationships/metadata/core-properties" '
            'Target="docProps/core.xml"/></Relationships>',
        "ppt/presentation.xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:presentation xmlns:a="{_NS_A}" xmlns:r="{_NS_R}" xmlns:p="{_NS_P}">'
            '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/>'
            "</p:sldMasterIdLst>"
            f"<p:sldIdLst>{folienliste}</p:sldIdLst>"
            f'<p:sldSz cx="{_FOLIE_BREITE}" cy="{_FOLIE_HOEHE}"/>'
            '<p:notesSz cx="6858000" cy="9144000"/></p:presentation>',
        "ppt/_rels/presentation.xml.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/slideMaster" '
            'Target="slideMasters/slideMaster1.xml"/>' + folienbezuege +
            f'<Relationship Id="rId{len(folien) + 2}" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
            "</Relationships>",
        "ppt/slideMasters/slideMaster1.xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:sldMaster xmlns:a="{_NS_A}" xmlns:r="{_NS_R}" xmlns:p="{_NS_P}">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/>'
            '<p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" '
            'accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" '
            'accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/>'
            "</p:sldLayoutIdLst></p:sldMaster>",
        "ppt/slideMasters/_rels/slideMaster1.xml.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/slideLayout" '
            'Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'theme" Target="../theme/theme1.xml"/></Relationships>',
        "ppt/slideLayouts/slideLayout1.xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:sldLayout xmlns:a="{_NS_A}" xmlns:r="{_NS_R}" xmlns:p="{_NS_P}" '
            'type="blank" preserve="1"><p:cSld name="Leer"><p:spTree><p:nvGrpSpPr>'
            '<p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
            "</p:spTree></p:cSld></p:sldLayout>",
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.'
            'org/officeDocument/2006/relationships/slideMaster" '
            'Target="../slideMasters/slideMaster1.xml"/></Relationships>',
        "ppt/theme/theme1.xml": _THEMA,
        "docProps/core.xml": _kern(dokument.titel, dokument.angaben),
    })
    return _packen(teile)
