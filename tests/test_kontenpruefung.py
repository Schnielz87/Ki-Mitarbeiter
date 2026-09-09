"""Erfundene Kontonummern und fachliche Widersprueche.

Zwei weitere Fehler aus dem gemeldeten Fall:

* *"Die Umsatzsteuer wird an der Umsatzsteuerkonto 4400 abgerechnet.
  Die Vorsteuer wird an der Vorsteuerkonto 4410 abgerechnet."* - beides
  sind in keinem der beiden gebraeuchlichen Kontenrahmen Steuerkonten.
* *"Rueckstellung ... 8.500 EUR netto muessen in den ARAP umgebucht
  werden."* - eine Rueckstellung ist ein Passivposten, ein ARAP ein
  Aktivposten.

Der zweite Fehler ist nicht falsch gerechnet, sondern falsch gedacht.
Kein Rechenwerk faengt das ab; dafuer braucht es Regeln.
"""

from __future__ import annotations

import pytest

from pkc.fachrechnen import pruefe_konten, pruefe_regeln, rahmen_erkennen
from pkc.llm.base import LlmResponse
from pkc.llm.manager import LlmManager
from test_controller import make_controller


# -- Kontonummern ------------------------------------------------------
def test_die_gemeldeten_kontonummern_werden_bemaengelt():
    """4400 und 4410 als Steuerkonten - der gemeldete Fall."""
    befunde = pruefe_konten(
        "Die Umsatzsteuer wird an der Umsatzsteuerkonto 4400 abgerechnet. "
        "Die Vorsteuer wird an der Vorsteuerkonto 4410 abgerechnet.")
    nummern = {b.nummer for b in befunde}
    assert nummern == {"4400", "4410"}, f"gefunden: {nummern}"
    text = " ".join(b.text for b in befunde)
    assert "Verbindlichkeit" in text, "die Begruendung muss dastehen"
    assert "1776" in text and "3806" in text, (
        "der Hinweis auf das uebliche Konto muss dabeistehen")


@pytest.mark.parametrize("satz", [
    "Gebucht wird auf Umsatzsteuerkonto 1776 und Vorsteuerkonto 1576.",
    "Die Umsatzsteuer laeuft ueber Konto 3806, die Vorsteuer ueber Konto 1406.",
])
def test_richtige_konten_werden_nicht_bemaengelt(satz):
    """Ein Waechter, der bei richtigen Konten anschlaegt, wird ignoriert."""
    assert pruefe_konten(satz) == []


def test_ohne_kontobezeichnung_wird_nichts_geprueft():
    """Sonst waere jede Jahreszahl ein Konto."""
    assert pruefe_konten("Im Jahr 2026 betrug die Umsatzsteuer 4400 EUR.") == []


def test_bei_unbekanntem_rahmen_wird_nur_bemaengelt_was_in_beiden_falsch_ist():
    """Ein Vorwurf, der nur unter einer Annahme stimmt, ist kein Vorwurf.

    8400 ist im SKR03 ein Erloeskonto - im SKR04 liegt die 8 in einem
    Bereich, den dieses Modul nicht fuehrt. Also wird nichts behauptet.
    """
    assert pruefe_konten("Gebucht auf Umsatzsteuerkonto 8400") == []


def test_der_rahmen_wird_aus_einer_angabe_gelesen():
    assert rahmen_erkennen("Wir buchen nach SKR03.") == "SKR03"
    assert rahmen_erkennen("SKR 04, DATEV") == "SKR04"
    assert rahmen_erkennen("Eigener Kontenrahmen") is None
    assert rahmen_erkennen(None) is None


# -- Fachliche Regeln --------------------------------------------------
def test_rueckstellung_im_arap_wird_bemaengelt():
    """Der gemeldete Fall - in beiden Umlautschreibweisen."""
    for satz in ("Rueckstellung der Lieferantenrechnungen: 8.500 EUR muessen "
                 "in den ARAP umgebucht werden.",
                 "Die Rückstellung gehoert in den aktiven "
                 "Rechnungsabgrenzungsposten."):
        befunde = pruefe_regeln(satz)
        assert befunde, f"nicht erkannt: {satz}"
        assert "§ 249 HGB" in befunde[0].text
        assert "§ 250" in befunde[0].text


def test_ein_satz_der_den_unterschied_erklaert_ist_kein_fehler():
    """Sonst kann die Anwendung den Unterschied nicht mehr erklaeren."""
    for satz in ("Eine Rueckstellung ist kein ARAP - sie steht auf der "
                 "Passivseite.",
                 "Der Unterschied zwischen Rueckstellung und ARAP liegt in "
                 "der Bilanzseite.",
                 "Eine Rueckstellung ist kein Aktivposten."):
        assert pruefe_regeln(satz) == [], f"Fehlalarm bei: {satz}"


def test_die_rueckstellung_als_aktivposten_wird_bemaengelt():
    befunde = pruefe_regeln("Die Rueckstellung ist ein Aktivposten.")
    assert befunde and "Passivseite" in befunde[0].text


def test_weit_auseinanderliegende_begriffe_loesen_nichts_aus():
    """Zwei Absaetze weiter sagt das nichts - im selben Satz sagt es viel."""
    text = ("Die Rueckstellung betraegt 8.500 EUR.\n\n"
            "Getrennt davon ist der ARAP von 12.000 EUR zu bilden.")
    assert pruefe_regeln(text) == []


# -- Durch die ganze Anwendung -----------------------------------------
class Modelldoppel:
    name, model = "testmodell", "doppel"

    def __init__(self, antwort):
        self.antwort = antwort

    def available(self):
        return True, "bereit"

    def generate(self, messages, max_tokens=1024, temperature=0.2, stop=None):
        return LlmResponse(text=self.antwort, provider=self.name,
                           model=self.model, meta={"generated": True})

    def describe(self):
        return {"anbieter": self.name, "modell": self.model}


DAMALS = (
    "**ERGEBNIS**\n\nDie Rueckstellung der Lieferantenrechnungen von "
    "8.500 EUR muss in den ARAP umgebucht werden. Die Umsatzsteuer wird "
    "an der Umsatzsteuerkonto 4400 abgerechnet. Die Vorsteuer wird an "
    "der Vorsteuerkonto 4410 abgerechnet."
)


def test_beide_fehler_werden_dem_anwender_gemeldet(portable_root):
    controller = make_controller(portable_root)
    controller.bootstrap()
    controller.llm = LlmManager(Modelldoppel(DAMALS))
    controller.rag.llm = controller.llm
    try:
        ergebnis = controller.ask(
            "Wie buche ich die Rueckstellung fuer ausstehende "
            "Lieferantenrechnungen von 8.500 EUR netto?")
        hinweise = " ".join(ergebnis.answer.warnings)
        assert "4400" in hinweise, "das erfundene Steuerkonto muss auffallen"
        assert "4410" in hinweise
        assert "§ 249 HGB" in hinweise, "der Denkfehler muss auffallen"
        # Und die Hinweise stehen im ausgelieferten Text, nicht nur in
        # einem Feld, das niemand ansieht.
        assert "4400" in ergebnis.answer.text
    finally:
        controller.shutdown()


def test_der_kontenrahmen_des_betriebs_wird_beruecksichtigt(portable_root):
    """Steht SKR03 im Unternehmenswissen, wird dagegen geprueft."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    controller.llm = LlmManager(Modelldoppel("**ERGEBNIS**\n\nOk."))
    controller.rag.llm = controller.llm
    try:
        controller.memory.put(
            "company.chart_of_accounts", "Kontenrahmen",
            "Wir buchen nach SKR03.", category="accounting", source="Test")
        assert controller.rag._kontenrahmen() == "SKR03"

        # Und ohne Angabe wird nichts angenommen.
        controller.memory.archive("company.chart_of_accounts", reason="Test")
        assert controller.rag._kontenrahmen() is None
    finally:
        controller.shutdown()
