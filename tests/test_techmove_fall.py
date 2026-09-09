"""Der gemeldete Fall - die ganze Aufgabe durch die ganze Anwendung.

Der Auftraggeber hat dem Buchhalter eine Fallstudie gegeben. Die Antwort
war in fast jedem Punkt falsch. Dieser Test stellt dieselbe Aufgabe und
prueft, dass die richtigen Zahlen jetzt in der Antwort stehen - **auch
dann, wenn das Sprachmodell weiterhin Unsinn schreibt**.

Das ist der Kern der Loesung: Die Anwendung verlaesst sich nicht mehr
darauf, dass das Modell richtig rechnet. Sie rechnet selbst und stellt
das Ergebnis daneben.
"""

from __future__ import annotations

import pytest

from pkc.llm.base import LlmResponse
from pkc.llm.manager import LlmManager
from test_controller import make_controller

#: Die Aufgabe, gekuerzt auf die rechenbaren Teile - Wortlaut wie gestellt.
AUFGABE = """Jahresabschluss-Vorbereitung der TechMove GmbH.
Stichtag: 30. September 2026.

Teil A: Anlagenbuchhaltung. Erstelle einen linearen Abschreibungsplan.
* Anlage 1: Fuhrpark (Lieferwagen) | Anschaffung: 15.03.2026 | Brutto-Kaufpreis: 53.550 EUR (inkl. 19% MwSt.) | Nutzungsdauer: 5 Jahre.
* Anlage 2: IT-Infrastruktur (Server) | Anschaffung: 01.07.2026 | Netto-Kaufpreis: 12.000 EUR | Nutzungsdauer: 3 Jahre.

Teil B: Rechnungsabgrenzung.
1. Versicherung: Am 01.08.2026 wurde die Jahresversicherung fuer die Lagerhalle im Voraus bezahlt: 14.400 EUR netto (Zeitraum: 01.08.2026 bis 31.07.2027).
2. Software-Erloese: Ein Kunde hat am 15.09.2026 eine Jahreslizenz im Voraus bezahlt: 24.000 EUR netto (Zeitraum: 15.09.2026 bis 14.09.2027).
"""

#: Genau der Unsinn, den das Modell wirklich geschrieben hat.
DAMALIGE_FALSCHANTWORT = (
    "**ERGEBNIS**\n\n"
    "Der Tagesbasis-Verbrauch betraegt 24.000 EUR / 365 Tage = 65,753425 EUR "
    "pro Tag. Fuer den 30.09.2026, das 91. Tag des Jahres, ergibt sich ein "
    "periodengerechter Betrag von 5.995.553,43 EUR. Die Rueckstellung von "
    "8.500 EUR muss in den ARAP umgebucht werden."
)


class Modelldoppel:
    name, model = "testmodell", "doppel"

    def __init__(self, antwort):
        self.antwort = antwort
        self.gesehen = []

    def available(self):
        return True, "bereit"

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None):
        self.gesehen.append(list(messages))
        return LlmResponse(text=self.antwort, provider=self.name,
                           model=self.model, meta={"generated": True})

    def describe(self):
        return {"anbieter": self.name, "modell": self.model}

    @property
    def systemtext(self) -> str:
        return "\n".join(m.content for m in self.gesehen[-1] if m.role == "system")


@pytest.fixture
def buchhalter(portable_root):
    erzeugt = []

    def bauen(antwort=DAMALIGE_FALSCHANTWORT):
        controller = make_controller(portable_root)
        controller.bootstrap()
        doppel = Modelldoppel(antwort)
        controller.llm = LlmManager(doppel)
        controller.rag.llm = controller.llm
        erzeugt.append(controller)
        return controller, doppel

    yield bauen
    for c in erzeugt:
        c.shutdown()


# -- Die vier Sollwerte aus der Musterloesung --------------------------
@pytest.mark.parametrize("wert,wofuer", [
    ("5.250,00", "AfA Fuhrpark: 7 Monate x 750 EUR"),
    ("39.750,00", "Buchwert Fuhrpark"),
    ("1.000,00", "AfA Server: 3 Monate"),
    ("11.000,00", "Buchwert Server"),
    ("22.947,95", "PRAP Software taggenau"),
    ("12.000,00", "ARAP Versicherung monatsgenau"),
    ("45.000,00", "Netto aus 53.550 brutto"),
])
def test_die_richtigen_zahlen_stehen_in_der_antwort(buchhalter, wert, wofuer):
    """Auch wenn das Modell weiterhin Unsinn schreibt.

    Der Rechenweg kommt von der Anwendung, nicht vom Modell. Er steht
    unter der Antwort, und zwar unabhaengig davon, was darueber steht.
    """
    controller, _ = buchhalter()
    ergebnis = controller.ask(AUFGABE)
    # Die Anwendung schreibt Betraege ohne Tausenderpunkt (45000.00);
    # geprueft wird gegen beide Schreibweisen.
    ohne_punkt = wert.replace(".", "").replace(",", ".")
    text = ergebnis.answer.text
    assert wert in text or ohne_punkt in text, (
        f"{wofuer}: weder {wert} noch {ohne_punkt} steht in der Antwort.")


def test_der_rechenweg_wird_als_eigener_abschnitt_gekennzeichnet(buchhalter):
    """Damit niemand ihn fuer Modelltext haelt."""
    controller, _ = buchhalter()
    text = controller.ask(AUFGABE).answer.text
    assert "**NACHGERECHNET**" in text
    assert "nicht das Sprachmodell" in text
    assert "gilt diese Rechnung" in text


def test_die_sieben_monate_stehen_im_rechenweg(buchhalter):
    """Der Fehler war: neun Monate, weil September der neunte Monat ist."""
    controller, _ = buchhalter()
    text = controller.ask(AUFGABE).answer.text
    assert "03/2026 bis 09/2026" in text
    assert "Anschaffungsmonat zaehlt voll" in text


def test_die_sechzehn_tage_stehen_im_rechenweg(buchhalter):
    """Der Fehler war: 91 Tage ab Jahresbeginn statt 16 ab Vertragsbeginn."""
    controller, _ = buchhalter()
    text = controller.ask(AUFGABE).answer.text
    assert "16 Tage" in text, "die verbrauchten Tage muessen dastehen"
    assert "349 Tage" in text, "die abzugrenzenden Tage muessen dastehen"


def test_die_unmoegliche_zahl_bekommt_weiterhin_einen_hinweis(buchhalter):
    """Rechnen und Pruefen greifen beide, nicht nur eines von beidem."""
    controller, _ = buchhalter()
    ergebnis = controller.ask(AUFGABE)
    hinweise = " ".join(ergebnis.answer.warnings)
    assert "5.995.553,43" in hinweise
    assert "Rechenfehler" in hinweise


def test_das_modell_bekommt_die_werte_als_bindende_vorgabe(buchhalter):
    """Es soll formulieren, nicht rechnen - dafuer muss es sie kennen."""
    controller, doppel = buchhalter()
    controller.ask(AUFGABE)
    system = doppel.systemtext
    assert "BEREITS AUSGERECHNET" in system
    assert "5.250,00" in system, "die AfA muss in der Vorgabe stehen"
    assert "22.947,95" in system, "die Abgrenzung muss in der Vorgabe stehen"
    assert "nicht nach" in system, "es muss ausdruecklich dastehen"


def test_die_richtung_der_abgrenzung_wird_bestimmt(buchhalter):
    """Software-Erloese sind PRAP, die Versicherung ist ARAP."""
    controller, _ = buchhalter()
    text = controller.ask(AUFGABE).answer.text
    assert "Ertrag an PRAP" in text, "Kundenzahlung ist ein PRAP"
    assert "ARAP an Aufwand" in text, "die Versicherung ist ein ARAP"


def test_eine_gewoehnliche_frage_bekommt_keinen_rechenweg(buchhalter):
    """Der Abschnitt darf nicht unter jeder Antwort stehen."""
    controller, _ = buchhalter("**ERGEBNIS**\n\nEine Rechnung braucht "
                               "Pflichtangaben nach § 14 UStG.")
    text = controller.ask("Welche Pflichtangaben muss eine Rechnung "
                          "enthalten?").answer.text
    assert "**NACHGERECHNET**" not in text


def test_keine_dreizehn_monate_fuer_eine_jahreslizenz(buchhalter):
    """Der Zeitraum 15.09. bis 14.09. beruehrt 13 Kalendermonate.

    Das ist rechnerisch richtig und fachlich unbrauchbar. Bei einem
    Zeitraum, der nicht am Monatsersten beginnt, wird die monatsweise
    Aufteilung deshalb gar nicht erst angeboten - mit Begruendung.
    """
    controller, _ = buchhalter()
    text = controller.ask(AUFGABE).answer.text
    assert "13 Monate" not in text
    assert "nicht sinnvoll" in text
    # Die Versicherung deckt volle Monate ab - dort steht beides.
    assert "12 Monate" in text


# -- Die bestellte Datei -----------------------------------------------
def _zellen(pfad) -> str:
    """Liest den Textinhalt einer XLSX-Datei - ohne fremde Bibliothek."""
    import re
    import zipfile

    with zipfile.ZipFile(pfad) as archiv:
        roh = archiv.read("xl/worksheets/sheet1.xml").decode("utf-8")
    return re.sub(r"<[^>]+>", " ", roh)


def test_die_bestellte_arbeitsmappe_enthaelt_die_berechneten_werte(buchhalter):
    """Nicht nur den Antworttext, sondern eine Tabelle mit den Zahlen.

    Der Unterschied ist der zwischen einer Textdatei mit der Endung
    .xlsx und einer Tabelle, mit der man weiterarbeiten kann. Wer eine
    Excel-Arbeitsmappe bestellt, meint das zweite.
    """
    controller, _ = buchhalter()
    ergebnis = controller.ask(
        AUFGABE + "\n\nErstelle dazu bitte eine Excel-Arbeitsmappe.")

    assert ergebnis.datei_fehler == "", ergebnis.datei_fehler
    assert ergebnis.datei is not None, "es wurde keine Datei erzeugt"
    assert ergebnis.datei.pfad.suffix == ".xlsx"

    inhalt = _zellen(ergebnis.datei.pfad)
    # Die Kennzeichnung
    assert "Angabe" in inhalt and "Wert" in inhalt, "es fehlt die Tabelle"

    # Und die Werte - jeder einzelne als Zahlenzelle, nicht als Text.
    # Ein blosses "irgendwo steht ein <v>" hat hier nichts geprueft: eine
    # Gegenprobe, die einen Betrag wieder als Text schrieb, lief durch,
    # weil die uebrigen Zellen noch Zahlen waren.
    zahlen = _zahlenzellen(ergebnis.datei.pfad)
    for wert in ("45000", "5250", "39750", "22947.95", "12000"):
        assert wert in inhalt, f"{wert} fehlt in der Arbeitsmappe"
        assert any(_gleich(wert, gefunden) for gefunden in zahlen), (
            f"{wert} steht als Text in der Zelle - so kann Excel nicht "
            f"damit rechnen. Zahlenzellen: {sorted(zahlen)}")


def _gleich(erwartet: str, gefunden: str) -> bool:
    """45000 und 45000.00 sind derselbe Betrag."""
    from decimal import Decimal, InvalidOperation

    try:
        return Decimal(erwartet) == Decimal(gefunden)
    except InvalidOperation:                    # pragma: no cover - defensiv
        return False


def _zahlenzellen(pfad) -> set[str]:
    """Alle Werte, die als Zahl in einer Zelle stehen (<v>...</v>)."""
    import re
    import zipfile

    with zipfile.ZipFile(pfad) as archiv:
        roh = archiv.read("xl/worksheets/sheet1.xml").decode("utf-8")
    return set(re.findall(r"<v>([^<]+)</v>", roh))


def test_ohne_rechnung_bleibt_es_beim_antworttext(buchhalter):
    """Kein leerer Tabellenkopf unter jeder beliebigen Datei."""
    controller, _ = buchhalter("**ERGEBNIS**\n\nEine Rechnung braucht "
                               "Pflichtangaben nach § 14 UStG.")
    ergebnis = controller.ask(
        "Welche Pflichtangaben muss eine Rechnung enthalten? "
        "Erstelle mir das bitte als Excel-Tabelle.")
    assert ergebnis.datei is not None
    inhalt = _zellen(ergebnis.datei.pfad)
    assert "Angabe   Wert" not in inhalt
