"""Der Antwortspeicher - Hebel 4 aus ANTWORTZEIT_KONZEPT.md.

Dieselbe Frage zweimal zu stellen ist im Buero der Normalfall. Die zweite
Antwort soll nicht noch einmal Minuten dauern.

Die zwei Zusicherungen, um die alles kreist:

1. **Eine wiederverwendete Antwort wird als solche gekennzeichnet.** Wer
   eine Frage zum zweiten Mal stellt, tut das oft, weil sich etwas
   geaendert hat. Eine gespeicherte Antwort als frisch auszugeben waere
   eine Taeuschung.
2. **Aendert sich etwas Massgebliches, wird neu gerechnet.** Vor allem
   das Unternehmensgedaechtnis - wer seinen Kontenrahmen umstellt,
   bekommt zu derselben Frage eine andere Antwort.
"""

from __future__ import annotations

import pytest

from pkc.rag.antwortspeicher import Antwortspeicher, frage_vereinheitlichen
from test_controller import make_controller


@pytest.fixture
def controller(portable_root):
    steuerung = make_controller(portable_root)
    steuerung.bootstrap()
    yield steuerung
    steuerung.shutdown()


class Zaehler:
    """Zaehlt, wie oft das Sprachmodell wirklich gefragt wurde."""

    def __init__(self, rag):
        self.rag = rag
        self.echt = rag.answer
        self.aufrufe = 0

    def __call__(self, *args, **kwargs):
        self.aufrufe += 1
        return self.echt(*args, **kwargs)


@pytest.fixture
def gezaehlt(controller):
    zaehler = Zaehler(controller.rag)
    controller.rag.answer = zaehler
    return controller, zaehler


FRAGE = "Welche Pflichtangaben muss eine Rechnung enthalten?"


# -- Der Schluessel ------------------------------------------------------

def test_gross_und_kleinschreibung_sind_dieselbe_frage():
    assert (frage_vereinheitlichen("Was ist  Buchhaltung?")
            == frage_vereinheitlichen("was ist buchhaltung?"))


def test_zahlen_bleiben_unterscheidbar():
    """"10.000" und "10000" sind nicht dieselbe Angabe."""
    assert (frage_vereinheitlichen("Buchung ueber 10.000 EUR")
            != frage_vereinheitlichen("Buchung ueber 10000 EUR"))


def test_der_schluessel_haengt_an_allem_was_die_antwort_aendert(portable_root):
    speicher = Antwortspeicher(None)
    grund = dict(profil="buchhalter", wissensstand="2026-09-01",
                 modell="mistral", tempo="normal", betriebsart="OFFLINE",
                 gedaechtnis="3@2026-09-01")
    basis = speicher.schluessel(FRAGE, **grund)
    for feld, anders in (("profil", "jurist"),
                         ("wissensstand", "2026-09-08"),
                         ("modell", "llama"),
                         ("tempo", "gruendlich"),
                         ("betriebsart", "ONLINE"),
                         ("gedaechtnis", "4@2026-09-08")):
        geaendert = dict(grund, **{feld: anders})
        assert speicher.schluessel(FRAGE, **geaendert) != basis, (
            f"Eine Aenderung an „{feld}“ muss einen anderen Schluessel "
            "ergeben - sonst antwortet der Speicher mit dem Stand von "
            "vorgestern.")


# -- Wiederverwendung ----------------------------------------------------

def test_dieselbe_frage_wird_nicht_zweimal_gerechnet(gezaehlt):
    steuerung, zaehler = gezaehlt
    steuerung.ask(FRAGE, use_history=False)
    assert zaehler.aufrufe == 1

    steuerung.ask(FRAGE, use_history=False)
    assert zaehler.aufrufe == 1, "die zweite Frage muss aus dem Speicher kommen"


def test_die_wiederverwendete_antwort_ist_gekennzeichnet(gezaehlt):
    """Die wichtigste Zusicherung dieser Datei."""
    steuerung, _ = gezaehlt
    erste = steuerung.ask(FRAGE, use_history=False).answer.text
    assert "Antwortspeicher" not in erste

    zweite = steuerung.ask(FRAGE, use_history=False).answer.text
    assert "Aus dem Antwortspeicher" in zweite
    assert "erstellt" in zweite, "es muss dastehen, wann sie entstand"


def test_der_inhalt_bleibt_derselbe(gezaehlt):
    steuerung, _ = gezaehlt
    erste = steuerung.ask(FRAGE, use_history=False).answer
    zweite = steuerung.ask(FRAGE, use_history=False).answer
    assert zweite.text.startswith(erste.text.rstrip()[:80])
    assert len(zweite.references) == len(erste.references)


def test_die_quellennachweise_ueberstehen_den_speicher(gezaehlt):
    steuerung, _ = gezaehlt
    erste = steuerung.ask(FRAGE, use_history=False).answer
    if not erste.references:
        pytest.skip("zu dieser Frage gab es keine Fundstellen")
    zweite = steuerung.ask(FRAGE, use_history=False).answer
    assert [r.reference for r in zweite.references] == \
        [r.reference for r in erste.references]
    assert [r.title for r in zweite.references] == \
        [r.title for r in erste.references]


def test_eine_andere_frage_wird_gerechnet(gezaehlt):
    steuerung, zaehler = gezaehlt
    steuerung.ask(FRAGE, use_history=False)
    steuerung.ask("Was ist eine Rueckstellung?", use_history=False)
    assert zaehler.aufrufe == 2


def test_geaendertes_unternehmenswissen_laesst_neu_rechnen(gezaehlt):
    """Wer seinen Kontenrahmen umstellt, bekommt eine andere Antwort."""
    steuerung, zaehler = gezaehlt
    steuerung.ask(FRAGE, use_history=False)
    assert zaehler.aufrufe == 1

    steuerung.memory.put(mem_key="company.chart_of_accounts",
                         category="accounting", title="Kontenrahmen",
                         content="SKR04")
    steuerung.ask(FRAGE, use_history=False)
    assert zaehler.aufrufe == 2, \
        "nach einer Aenderung am Unternehmenswissen muss neu gerechnet werden"


def test_mit_gespraechsverlauf_wird_nicht_gespeichert(controller):
    """Dieselbe Frage meint im naechsten Gespraech etwas anderes."""
    zaehler = Zaehler(controller.rag)
    controller.rag.answer = zaehler
    controller.ask("Was ist eine Rueckstellung?", use_history=True)
    controller.ask(FRAGE, use_history=True)
    controller.ask(FRAGE, use_history=True)
    assert zaehler.aufrufe == 3


# -- Verwalten -----------------------------------------------------------

def test_der_stand_laesst_sich_ablesen(gezaehlt):
    steuerung, _ = gezaehlt
    assert steuerung.antwortspeicher_stand()["eintraege"] == 0
    steuerung.ask(FRAGE, use_history=False)
    steuerung.ask(FRAGE, use_history=False)
    stand = steuerung.antwortspeicher_stand()
    assert stand["eintraege"] == 1
    assert stand["wiederverwendungen"] == 1


def test_der_speicher_laesst_sich_leeren(gezaehlt):
    steuerung, zaehler = gezaehlt
    steuerung.ask(FRAGE, use_history=False)
    assert steuerung.antwortspeicher_leeren() == 1
    steuerung.ask(FRAGE, use_history=False)
    assert zaehler.aufrufe == 2, "nach dem Leeren muss neu gerechnet werden"


def test_der_speicher_waechst_nicht_unbegrenzt(controller):
    speicher = Antwortspeicher(controller.company_db, grenze=3)
    for nummer in range(6):
        speicher.merken(f"schluessel{nummer}", f"Frage {nummer}",
                        {"text": "Antwort"})
    assert speicher.stand()["eintraege"] == 3
    assert speicher.holen("schluessel0") is None, \
        "der am laengsten unbenutzte Eintrag muss herausfallen"
    assert speicher.holen("schluessel5") is not None


def test_abgeschaltet_speichert_er_nichts(controller):
    speicher = Antwortspeicher(controller.company_db, aktiv=False)
    speicher.merken("schluessel", "Frage", {"text": "Antwort"})
    assert speicher.stand()["eintraege"] == 0
    assert speicher.holen("schluessel") is None


def test_ein_eintrag_aus_einer_aelteren_fassung_bricht_nichts(controller):
    """Kommt ein Feld hinzu, darf ein alter Eintrag hoechstens
    unvollstaendig sein - nicht toedlich."""
    from app.controller import _referenz_aus

    referenz = _referenz_aus({
        "number": 1, "origin": "knowledge", "reference": "§ 14 UStG",
        "title": "Rechnung", "excerpt": "...",
        "ein_feld_von_morgen": "unbekannt",
    })
    assert referenz.reference == "§ 14 UStG"


def test_der_gedaechtnisstand_merkt_auch_eine_loeschung(controller):
    """Ein Zaehler allein uebersaehe eine Aenderung, ein Zeitstempel
    allein eine Loeschung."""
    stand = Antwortspeicher.gedaechtnisstand
    controller.memory.put(mem_key="probe.eins", category="other",
                          title="Eins", content="A")
    vorher = stand(controller.memory)
    controller.memory.delete("probe.eins")
    assert stand(controller.memory) != vorher


def test_auch_aus_dem_speicher_entsteht_die_bestellte_datei(controller):
    """Die Rechenergebnisse muessen den Speicher ueberstehen.

    Sonst bekaeme dieselbe Bestellung beim zweiten Mal eine Datei ohne
    Tabelle - und niemand wuesste warum. Die gespeicherte Antwort haelt
    deshalb auch die berechneten Werte fest, nicht nur den Text.
    """
    aufgabe = (
        "Stichtag: 30.09.2026\n"
        "Fuhrpark: Firmenwagen am 15.03.2026 fuer 53.550 EUR "
        "(inkl. 19% MwSt.) angeschafft, Nutzungsdauer 5 Jahre.\n\n"
        "Erstelle dazu bitte eine Excel-Arbeitsmappe.")

    erste = controller.ask(aufgabe, use_history=False)
    assert erste.datei is not None, erste.datei_fehler
    assert erste.answer.rechnungen, "hier muss gerechnet worden sein"

    zweite = controller.ask(aufgabe, use_history=False)
    assert "Aus dem Antwortspeicher" in zweite.answer.text
    assert zweite.datei is not None, zweite.datei_fehler
    assert len(zweite.answer.rechnungen) == len(erste.answer.rechnungen)

    import re
    import zipfile

    with zipfile.ZipFile(zweite.datei.pfad) as archiv:
        roh = archiv.read("xl/worksheets/sheet1.xml").decode("utf-8")
    zahlen = set(re.findall(r"<v>([^<]+)</v>", roh))
    from decimal import Decimal
    assert any(Decimal(z) == Decimal("39750") for z in zahlen), (
        f"der Buchwert fehlt in der Arbeitsmappe: {sorted(zahlen)}")


def test_ein_anderes_modell_macht_den_speicher_ungueltig(controller):
    """Der Anbietername allein genuegt nicht.

    Er lautet beim mitgelieferten Dienst immer "local-llama-cpp", auch
    wenn jemand eine andere Modelldatei in den Ordner legt. Der Speicher
    antwortete sonst weiter mit den Antworten des alten Modells.
    """
    vorher = controller._modellkennung()

    class AndereDatei:
        name = "local-llama-cpp"

        @staticmethod
        def describe():
            return {"anbieter": "local-llama-cpp", "modell": "mistral-7b",
                    "pfad": "models/ein-anderes-modell.gguf"}

    controller.llm.primary = AndereDatei()
    assert controller._modellkennung() != vorher
    assert "ein-anderes-modell" in controller._modellkennung()


def test_ein_anbieter_ohne_auskunft_bricht_nichts(controller):
    class Schweigsam:
        name = "kein-modell"

        @staticmethod
        def describe():
            raise RuntimeError("sagt nichts")

    controller.llm.primary = Schweigsam()
    assert controller._modellkennung() == "kein-modell"
