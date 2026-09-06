"""Beispielplugin: ein zusaetzliches Ausgabeformat (Kategorie FILE_HANDLER).

Es zeigt den kleinsten sinnvollen Fall der Erweiterung E5: eine neue
Faehigkeit ohne jede Berechtigung. Das Plugin bekommt keinen Zugriff auf
Unternehmensdaten, auf Dateien oder auf das Netz - es wandelt nur ein
Dokument in HTML um.

Der Kern wurde dafuer nicht geaendert (E5.98).
"""

from html import escape

from pkc.artefakte import Schreiber


def _html(dokument) -> bytes:
    teile = [
        "<!doctype html>", '<html lang="de">', "<head>",
        '<meta charset="utf-8">',
        f"<title>{escape(dokument.titel or 'Bericht')}</title>",
        "<style>body{font-family:Segoe UI,Arial,sans-serif;max-width:44em;"
        "margin:2em auto;line-height:1.5;color:#222}"
        "h1{color:#1f4e79}table{border-collapse:collapse}"
        "td,th{border:1px solid #bbb;padding:.3em .6em;text-align:left}"
        "pre{background:#f4f4f4;padding:.6em;overflow-x:auto}</style>",
        "</head>", "<body>",
    ]
    if dokument.titel:
        teile.append(f"<h1>{escape(dokument.titel)}</h1>")
    for block in dokument.bloecke:
        if block.art == "ueberschrift":
            ebene = min(4, block.ebene + 1)
            teile.append(f"<h{ebene}>{escape(block.text)}</h{ebene}>")
        elif block.art == "absatz":
            teile.append(f"<p>{escape(block.text)}</p>")
        elif block.art == "aufzaehlung":
            teile.append("<ul>")
            teile.extend(f"<li>{escape(punkt)}</li>" for punkt in block.punkte)
            teile.append("</ul>")
        elif block.art == "code":
            teile.append(f"<pre>{escape(block.text)}</pre>")
        elif block.art == "tabelle" and block.zeilen:
            teile.append("<table>")
            kopf, *rest = block.zeilen
            teile.append("<tr>" + "".join(f"<th>{escape(z)}</th>" for z in kopf) + "</tr>")
            for zeile in rest:
                teile.append("<tr>" + "".join(f"<td>{escape(z)}</td>" for z in zeile) + "</tr>")
            teile.append("</table>")
    teile += ["</body>", "</html>"]
    return "\n".join(teile).encode("utf-8")


def anmelden(kontext) -> None:
    """Wird beim Laden aufgerufen. Mehr tut das Plugin nicht von selbst."""
    kontext.dateiformat_anmelden(
        Schreiber("html", ".html", "HTML-Seite", _html,
                  "Bericht fuer den Browser, ohne Office")
    )
    kontext.protokollieren("format_angemeldet", "html")
