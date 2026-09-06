"""Fragetyp-Erkennung und adaptive Antworttiefe.

Anlass: Bisher loeste jede Nachricht eine Fachrecherche aus. Auf "Kannst Du
mir helfen?" antwortete der Buchhalter mit acht Fundstellen aus dem
Umsatzsteuerrecht - unbrauchbar und irrefuehrend, weil es aussieht, als
haette die Frage mit diesen Quellen zu tun.
"""

from __future__ import annotations

import pytest

from pkc.rag.fragetyp import Fragetyp, einstufen
from test_controller import make_controller


# ------------------------------------------------------------ Einstufung
@pytest.mark.parametrize("frage", [
    "Hallo", "Hi", "Guten Morgen", "Danke!", "Vielen Dank", "Tschuess",
    "Was kannst Du?", "Wer bist Du?", "Wie funktionierst Du?",
    "Kannst Du mir helfen?",
    "Kannst Du mir bei meiner Buchhaltung helfen?",
])
def test_smalltalk_loest_keine_recherche_aus(frage):
    einstufung = einstufen(frage)
    assert einstufung.typ is Fragetyp.SMALLTALK, f"{frage!r} -> {einstufung.typ}"
    assert einstufung.braucht_recherche is False


@pytest.mark.parametrize("frage", [
    "Was ist Reverse Charge?",
    "Wie lange muessen Eingangsrechnungen aufbewahrt werden?",
    "Wann ist die Umsatzsteuervoranmeldung faellig?",
    "Welche Pflichtangaben braucht eine Rechnung?",
    "Auf welchen Buchungsbeleg gehoert das?",
])
def test_fachfragen_loesen_recherche_aus(frage):
    einstufung = einstufen(frage)
    assert einstufung.braucht_recherche is True
    assert einstufung.typ in (Fragetyp.FACHLICH, Fragetyp.KOMPLEX)


def test_deutsche_zusammensetzungen_werden_erkannt():
    """Der Fehler der ersten Fassung: \\brechnung\\b greift in
    "Eingangsrechnungen" nicht. Das Deutsche setzt zusammen."""
    for wort in ("Eingangsrechnungen", "Umsatzsteuervoranmeldung",
                 "Buchungsbeleg", "Aufbewahrungsfrist", "Anlagevermoegen"):
        assert einstufen(f"Frage zu {wort}?").braucht_recherche, wort


@pytest.mark.parametrize("frage", [
    "Wir haben eine Rechnung aus Frankreich von einem Unternehmer erhalten, "
    "wie buchen wir das?",
    "Ich habe einen Firmenwagen geleast, wie ist die Vorsteuer zu behandeln "
    "und was brauche ich dafuer?",
])
def test_geschilderte_einzelfaelle_sind_komplex(frage):
    einstufung = einstufen(frage)
    assert einstufung.typ is Fragetyp.KOMPLEX
    assert einstufung.typ.volle_struktur is True


def test_kurze_antwort_im_gespraech_ist_keine_begruessung():
    """"Ja" auf eine Rueckfrage darf nicht als Geplauder gelten."""
    ohne = einstufen("Ja", hat_verlauf=False)
    mit = einstufen("Ja", hat_verlauf=True)
    assert mit.typ is Fragetyp.FACHLICH
    assert mit.braucht_recherche is True
    assert "Rueckfrage" in mit.grund
    assert ohne.typ is not Fragetyp.KOMPLEX


def test_leere_eingabe_bricht_nichts_ab():
    assert einstufen("").typ is Fragetyp.SMALLTALK
    assert einstufen("   ").typ is Fragetyp.SMALLTALK


# ------------------------------------------------------ an der Anwendung
def test_smalltalk_erzeugt_keine_fundstellen(portable_root):
    """Testfall 1 der Vorgabe."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        ergebnis = controller.ask("Kannst Du mir bei meiner Buchhaltung helfen?")
        assert ergebnis.answer.fragetyp is Fragetyp.SMALLTALK
        assert ergebnis.answer.references == [], \
            "Smalltalk darf keine Fundstellen liefern"
    finally:
        controller.shutdown()


def test_fachfrage_erzeugt_weiterhin_fundstellen(portable_root):
    """Testfall 2 - und zugleich Regressionsschutz."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        ergebnis = controller.ask("Was ist Reverse Charge?")
        assert ergebnis.answer.fragetyp.braucht_recherche
        assert ergebnis.answer.references, "die Recherche muss weiter funktionieren"
    finally:
        controller.shutdown()


def test_antworttiefe_steht_im_modellkontext(portable_root):
    """Das Modell muss erfahren, wie ausfuehrlich es antworten soll."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        from pkc.rag.fragetyp import einstufen as _einstufen

        for frage, erwartet in [
            ("Hallo", "keine** Fachfrage"),
            ("Was ist Reverse Charge?", "fachliche Frage"),
        ]:
            bundle = controller.rag.builder.build([], [])
            nachrichten = controller.rag.build_messages(
                frage, bundle, einstufung=_einstufen(frage))
            text = "\n".join(m.content for m in nachrichten if m.role == "system")
            assert "ANTWORTTIEFE" in text
            assert erwartet in text, f"{frage}: {erwartet!r} fehlt"
    finally:
        controller.shutdown()


def test_unternehmenswissen_bleibt_auch_bei_smalltalk(portable_root):
    """Regressionsschutz: der Unternehmenskontext darf nicht wegfallen."""
    controller = make_controller(portable_root)
    controller.bootstrap()
    try:
        controller.remember_manual("company.name", "Unternehmensname",
                                   "Muster GmbH", "profile")
        ergebnis = controller.ask("Hallo")
        assert ergebnis.answer.context is not None
        assert "Muster GmbH" in ergebnis.answer.context.company_block
    finally:
        controller.shutdown()
