"""Die zehn Testfaelle aus Abschnitt 25 der Vorgabe.

Geprueft wird gegen einen Testanbieter, der wie ein Sprachmodell antwortet.
Damit laesst sich pruefen, was ohne echtes Modell pruefbar ist: dass die
richtigen Dinge im Kontext landen, dass die Antwort und nicht die Rohdaten
im Vordergrund steht, und dass der Verlauf beruecksichtigt wird.

Was hier NICHT geprueft werden kann: ob ein echtes Sprachmodell inhaltlich
gut antwortet. Das haengt vom Modell ab und gehoert in die Abnahme.
"""

from __future__ import annotations

import pytest

from pkc.llm.base import ChatMessage, LlmResponse
from pkc.llm.manager import LlmManager
from pkc.rag.fragetyp import Fragetyp
from test_controller import make_controller


class Modelldoppel:
    """Antwortet wie ein Modell und merkt sich, was es bekommen hat."""

    name = "testmodell"
    model = "doppel"

    def __init__(self, antwort: str = "**ERGEBNIS**\n\nEine Antwort mit Beleg [1]."):
        self.antwort = antwort
        self.gesehen: list[list[ChatMessage]] = []

    def available(self):
        return True, "bereit"

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None):
        self.gesehen.append(list(messages))
        return LlmResponse(text=self.antwort, provider=self.name, model=self.model,
                           meta={"generated": True})

    def describe(self):
        return {"anbieter": self.name, "modell": self.model}

    @property
    def kontext(self) -> str:
        """Alles, was das Modell zuletzt als Systemtext bekommen hat."""
        if not self.gesehen:
            return ""
        return "\n".join(m.content for m in self.gesehen[-1] if m.role == "system")

    @property
    def verlauf(self) -> list[ChatMessage]:
        return [m for m in self.gesehen[-1] if m.role in ("user", "assistant")]


@pytest.fixture
def mit_modell(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap()
    doppel = Modelldoppel()
    controller.llm = LlmManager(doppel)
    controller.rag.llm = controller.llm
    try:
        yield controller, doppel
    finally:
        controller.shutdown()


# ------------------------------------------------------------- TEST 1
def test_1_smalltalk_ohne_rohliste(mit_modell):
    controller, doppel = mit_modell
    ergebnis = controller.ask("Kannst Du mir bei meiner Buchhaltung helfen?")

    assert ergebnis.answer.fragetyp is Fragetyp.SMALLTALK
    assert ergebnis.answer.references == []
    assert "**QUELLEN**" not in ergebnis.answer.text
    # Das Modell muss wissen, dass es kurz antworten soll
    assert "keine** Fachfrage" in doppel.kontext or "keine Fachfrage" in doppel.kontext


# ------------------------------------------------------------- TEST 2
def test_2_einfache_fachfrage_bekommt_quellen(mit_modell):
    controller, doppel = mit_modell
    ergebnis = controller.ask("Was ist Reverse Charge?")

    assert ergebnis.answer.model_answered, "die Antwort kommt vom Modell"
    assert ergebnis.answer.references, "es muss recherchiert worden sein"
    # ... und die Fundstellen landen wirklich im Modellkontext (Abschnitt 3)
    assert "Reverse Charge" in doppel.kontext or "13b" in doppel.kontext


# ------------------------------------------------------------- TEST 3
def test_3_komplexer_fall_bekommt_das_fachschema(mit_modell):
    controller, doppel = mit_modell
    controller.ask("Wir haben eine Rechnung aus Frankreich von einem Unternehmer "
                   "erhalten, wie buchen wir das mit der Umsatzsteuer?")
    assert "BUCHUNGSVORSCHLAG" in doppel.kontext, \
        "beim Einzelfall gehoert das volle Schema in den Kontext"


# ------------------------------------------------------------- TEST 4
def test_4_rueckfrage_wird_angewiesen(mit_modell):
    controller, doppel = mit_modell
    controller.ask("Ich habe einen Firmenwagen geleast, wie ist die Vorsteuer zu "
                   "behandeln und was brauche ich dafuer?")
    assert "gezielt nach" in doppel.kontext
    assert "statt zu raten" in doppel.kontext


# ------------------------------------------------------------- TEST 5
def test_5_unternehmensgedaechtnis_im_kontext(mit_modell):
    controller, doppel = mit_modell
    controller.remember_manual("company.chart_of_accounts", "Kontenrahmen",
                               "Das Unternehmen verwendet SKR03.", "accounting")
    controller.ask("Wie soll ich das buchen?")
    assert "SKR03" in doppel.kontext, \
        "der hinterlegte Kontenrahmen muss in die Antwortgenerierung einfliessen"


# ------------------------------------------------------------- TEST 6
def test_6_offline_erzeugt_eine_antwort(mit_modell):
    from pkc.netstate import Mode

    controller, doppel = mit_modell
    controller.set_mode(Mode.OFFLINE)
    ergebnis = controller.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")

    assert ergebnis.answer.model_answered
    assert ergebnis.answer.references, "lokales RAG muss auch offline liefern"
    assert ergebnis.answer.mode == "OFFLINE"


# ------------------------------------------------------------- TEST 7
def test_7_antwort_verweist_auf_quellen(mit_modell):
    controller, doppel = mit_modell
    ergebnis = controller.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")

    assert "[1]" in ergebnis.answer.text
    assert ergebnis.answer.used_references, "die genannte Fundstelle muss zugeordnet sein"
    assert ergebnis.answer.used_references[0].number == 1


# ------------------------------------------------------------- TEST 8
def test_8_ohne_modell_keine_vorgetaeuschte_antwort(portable_root):
    from pkc.llm.providers import RetrievalOnlyProvider

    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        controller.llm = LlmManager(RetrievalOnlyProvider(reason="Test"))
        controller.rag.llm = controller.llm
        ergebnis = controller.ask("Was ist Reverse Charge?")

        assert not ergebnis.answer.model_answered
        assert "keine KI-Antwort" in ergebnis.answer.text
    finally:
        controller.shutdown()


# ------------------------------------------------------------- TEST 9
def test_9_chatverlauf_wird_beruecksichtigt(mit_modell):
    """"Ja" muss sich auf die vorherige Rueckfrage beziehen."""
    controller, doppel = mit_modell
    uid = controller.ensure_conversation()

    controller.ask("Ich habe eine Rechnung aus Frankreich.", conversation_uid=uid)
    controller.ask("Ja", conversation_uid=uid)

    verlauf = " ".join(m.content for m in doppel.verlauf)
    assert "Frankreich" in verlauf, \
        "die vorherige Nachricht muss im Kontext stehen"


# ------------------------------------------------------------- TEST 10
def test_10_markdown_wird_sauber_dargestellt(mit_modell):
    from ui.markdown import als_klartext

    controller, doppel = mit_modell
    doppel.antwort = ("**ERGEBNIS**\n\n## Titel\n- Ein Punkt\n\n"
                      "Mit *Betonung* und Beleg [1].")
    ergebnis = controller.ask("Was ist Reverse Charge?")

    dargestellt = als_klartext(ergebnis.answer.text)
    assert "**" not in dargestellt and "## " not in dargestellt
    assert "ERGEBNIS" in dargestellt and "Titel" in dargestellt
    assert "[1]" in dargestellt, "Belege duerfen nie verlorengehen"


# ------------------------------------------------- Regressionsschutz (26)
def test_bestehende_funktionen_bleiben(mit_modell):
    controller, _ = mit_modell
    ergebnis = controller.ask("Welche Pflichtangaben muss eine Rechnung enthalten?")

    # Gespraech gespeichert
    assert controller.conversations()
    # Quellen vorhanden
    assert ergebnis.answer.references
    # Wissensstand vermerkt
    assert "WISSENSSTAND" in ergebnis.answer.text
    # Protokoll gefuehrt
    assert controller.audit.count() > 0
