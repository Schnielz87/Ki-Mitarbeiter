"""Markdown-Darstellung (Abschnitt 7).

Das Sprachmodell antwortet in Markdown. Ungerendert stuenden ** und # roh
im Fenster. Die Vorgabe verlangt: entweder richtig darstellen oder
umwandeln - aber keine Rohzeichen.
"""

from __future__ import annotations

import pytest

from ui.markdown import Stueck, als_klartext, zerlegen


def _stil_von(stuecke, text):
    for stueck in stuecke:
        if text in stueck.text:
            return stueck.stil
    return None


# ------------------------------------------------------- keine Rohzeichen
@pytest.mark.parametrize("markdown, darf_nicht_enthalten", [
    ("**ERGEBNIS**", "**"),
    ("## Ueberschrift", "#"),
    ("- Erster Punkt", "- "),
    ("Der Befehl `modell pruefen`", "`"),
    ("Ein *kursives* Wort", "*"),
])
def test_keine_rohzeichen_im_klartext(markdown, darf_nicht_enthalten):
    ergebnis = als_klartext(markdown)
    assert darf_nicht_enthalten not in ergebnis, f"{markdown!r} -> {ergebnis!r}"


def test_inhalt_bleibt_vollstaendig():
    """Die Umwandlung darf nichts verschlucken."""
    assert "ERGEBNIS" in als_klartext("**ERGEBNIS**")
    assert "Ueberschrift" in als_klartext("## Ueberschrift")
    assert "Erster Punkt" in als_klartext("- Erster Punkt")
    assert "modell pruefen" in als_klartext("Der Befehl `modell pruefen`")


# ------------------------------------------------------------------ Stile
def test_fettdruck_wird_erkannt():
    assert _stil_von(zerlegen("**ERGEBNIS**"), "ERGEBNIS") == "fett"


def test_ueberschriften_werden_erkannt():
    assert _stil_von(zerlegen("# Gross"), "Gross") == "ueberschrift1"
    assert _stil_von(zerlegen("## Gross"), "Gross") == "ueberschrift1"
    assert _stil_von(zerlegen("### Klein"), "Klein") == "ueberschrift2"


def test_kursiv_und_code():
    assert _stil_von(zerlegen("Ein *kursives* Wort"), "kursives") == "kursiv"
    assert _stil_von(zerlegen("Der `Befehl` hier"), "Befehl") == "code"


def test_fett_in_ueberschrift_bleibt_ueberschrift():
    """Sonst wechselte mitten in der Zeile die Schriftgroesse."""
    assert _stil_von(zerlegen("## **Wichtig**"), "Wichtig") == "ueberschrift1"


def test_aufzaehlung_bekommt_ein_zeichen():
    text = als_klartext("- Erstens\n- Zweitens")
    assert "•" in text
    assert "Erstens" in text and "Zweitens" in text


def test_nummerierte_liste_behaelt_ihre_nummern():
    text = als_klartext("1. Rechnung pruefen\n2. Buchen")
    assert "1." in text and "2." in text
    assert "Rechnung pruefen" in text


def test_tabellentrenner_wird_weggelassen():
    """Die Zeile |---|---| traegt nichts bei und saehe nach Salat aus."""
    text = als_klartext("| A | B |\n|---|---|\n| 1 | 2 |")
    assert "---" not in text
    assert "A" in text and "1" in text


def test_codeblock_bleibt_erhalten():
    text = als_klartext("```\nx = 1\n```")
    assert "x = 1" in text
    assert "```" not in text


# ------------------------------------------------------------- Randfaelle
def test_leerer_text_bricht_nichts_ab():
    assert zerlegen("") == []
    assert als_klartext("") == ""


def test_text_ohne_markdown_bleibt_unveraendert():
    schlicht = "Ein ganz normaler Satz ohne Auszeichnung."
    assert als_klartext(schlicht) == schlicht


def test_unpaariges_sternchen_zerstoert_nichts():
    """Ein einzelnes * darf den Text nicht verschlucken."""
    assert "3 * 4" in als_klartext("3 * 4 ist 12")


def test_echte_fachantwort():
    """Gegen eine Antwort, wie das Modell sie liefern wuerde."""
    antwort = (
        "**ERGEBNIS**\n\n"
        "Der Vorsteuerabzug setzt eine *ordnungsgemaesse* Rechnung voraus [1].\n\n"
        "## Voraussetzungen\n"
        "- vollstaendige Anschrift\n"
        "- fortlaufende Nummer\n\n"
        "**QUELLEN**\n"
        "[1] UStG § 15\n"
    )
    text = als_klartext(antwort)
    assert "**" not in text and "##" not in text
    assert "ERGEBNIS" in text and "QUELLEN" in text
    assert "[1]" in text, "Quellenverweise muessen erhalten bleiben"
    assert "UStG § 15" in text
