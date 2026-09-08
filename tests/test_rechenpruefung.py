"""Der gemeldete Fehlschlag - einmal ganz durch die Anwendung.

``test_fachrechnen.py`` prueft die Rechenwege fuer sich. Hier geht es um
die Frage danach: Was passiert, wenn das Sprachmodell trotzdem eine
unmoegliche Zahl schreibt? Kommt sie beim Anwender an, als waere sie ein
Ergebnis - oder steht ein Hinweis daneben?

Der Anlass: Auf eine Aufgabe mit 24.000 EUR Jahreslizenz antwortete das
Modell mit 5.995.553,43 EUR. Die Anwendung lieferte das aus. Genau das
darf nicht mehr passieren.
"""

from __future__ import annotations

import pytest

from pkc.llm.base import ChatMessage, LlmResponse
from pkc.llm.manager import LlmManager
from test_controller import make_controller


class Modelldoppel:
    """Ein Modell, das genau das schreibt, was man ihm vorgibt."""

    name = "testmodell"
    model = "doppel"

    def __init__(self, antwort: str):
        self.antwort = antwort

    def available(self):
        return True, "bereit"

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None):
        return LlmResponse(text=self.antwort, provider=self.name,
                           model=self.model, meta={"generated": True})

    def describe(self):
        return {"anbieter": self.name, "modell": self.model}


@pytest.fixture
def mit_antwort(portable_root):
    """Baut einen Buchhalter, dessen Modell eine feste Antwort gibt."""
    def bauen(antwort: str):
        controller = make_controller(portable_root)
        controller.bootstrap()
        controller.llm = LlmManager(Modelldoppel(antwort))
        controller.rag.llm = controller.llm
        return controller

    gebaut = []

    def merken(antwort):
        c = bauen(antwort)
        gebaut.append(c)
        return c

    yield merken
    for c in gebaut:
        c.shutdown()


#: Die Aufgabe, wie sie gestellt wurde - gekuerzt auf das Rechenbare.
AUFGABE = (
    "Ein Kunde hat am 15.09.2026 eine Jahreslizenz im Voraus bezahlt: "
    "24.000 EUR netto fuer den Zeitraum 15.09.2026 bis 14.09.2027. "
    "Welcher Betrag muss zum 30.09.2026 abgegrenzt werden?"
)


def test_die_sechs_millionen_kommen_nicht_unkommentiert_beim_anwender_an(mit_antwort):
    """Der Fall, der alles ausgeloest hat.

    Geprueft wird nicht, dass die Zahl verschwindet - sie steht in der
    Antwort des Modells und wird nicht heimlich veraendert. Geprueft
    wird, dass ein Hinweis danebensteht.
    """
    controller = mit_antwort(
        "**ERGEBNIS**\n\nFuer den 30.09.2026 ergibt sich ein "
        "periodengerechter Betrag von 5.995.553,43 EUR.")
    ergebnis = controller.ask(AUFGABE)

    hinweise = " ".join(ergebnis.answer.warnings)
    assert "5.995.553,43" in hinweise, (
        "Die unmoegliche Zahl muss im Hinweis benannt werden - sonst weiss "
        "niemand, welche Zahl gemeint ist.")
    assert "Rechenfehler" in hinweise
    # Und der Hinweis muss auch im ausgelieferten Text stehen, nicht nur
    # in einem Feld, das niemand ansieht.
    assert "5.995.553,43" in ergebnis.answer.text


def test_eine_richtige_antwort_bekommt_keinen_fehlalarm(mit_antwort):
    """Ein Waechter, der immer anschlaegt, wird weggeklickt."""
    controller = mit_antwort(
        "**ERGEBNIS**\n\nAbzugrenzen sind 22.947,95 EUR als PRAP; "
        "1.052,05 EUR gehoeren in die laufende Periode.")
    ergebnis = controller.ask(AUFGABE)

    hinweise = " ".join(ergebnis.answer.warnings)
    assert "Rechenfehler" not in hinweise, (
        f"Fehlalarm bei einer richtigen Antwort: {hinweise}")


def test_die_pruefung_laeuft_auch_ohne_zahlen_in_der_frage(mit_antwort):
    """Ohne Massstab kein Verdacht - und kein Absturz."""
    controller = mit_antwort("**ERGEBNIS**\n\nEin ARAP ist ein Aktivposten.")
    ergebnis = controller.ask("Was ist ein aktiver Rechnungsabgrenzungsposten?")
    assert "Rechenfehler" not in " ".join(ergebnis.answer.warnings)
