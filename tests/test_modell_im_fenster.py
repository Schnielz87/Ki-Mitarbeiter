"""Der Weg zum Sprachmodell muss dort sein, wo der Benutzer sitzt.

Anlass ist eine Rueckmeldung aus dem Betrieb. Im Fenster stand:

    Es konnte keine KI-Antwort erzeugt werden.
    Auf diesem Rechner ist kein Sprachmodell eingerichtet.
    Einrichten mit: PORTABLE_BUCHHALTER_KONSOLE.exe modell empfehlen

Sachlich richtig - das Modell liegt bewusst nicht im Paket und wird einmalig
geladen. Als Bedienung unbrauchbar: wer die Anwendung per Doppelklick
oeffnet, hat keine Konsole offen und liest das als "geht nicht", nicht als
"fehlt noch". Genau so kam die Rueckmeldung dann auch an.

Zwei Dinge werden hier festgehalten:

* Die Meldung nennt den Weg, der zur Bedienung passt.
* Dieser Weg fuehrt wirklich zum Ziel - die Registerkarte laedt das Modell,
  bindet es ein und weist nach, dass es antwortet.
"""

from __future__ import annotations

import sys

import pytest

import tk_double
from pkc.llm.base import ChatMessage, LlmResponse
from pkc.llm.providers import RetrievalOnlyProvider
from pkc.llm.manager import LlmManager
from test_controller import make_controller


def _ohne_modell(paths):
    """Eine Anwendung im Zustand, den der Benutzer beim ersten Start hat.

    ``make_controller`` setzt einen Skriptanbieter ein - der meldet sich als
    bereit. Hier geht es aber genau um den anderen Fall: es ist kein Modell
    da, und die Anwendung laeuft im Notbetrieb.
    """
    controller = make_controller(paths)
    # Auch die Konfiguration muss den Fall hergeben: modell_neu_laden baut
    # den Anbieter aus ihr neu auf. Bliebe dort "echo" stehen, pruefte der
    # Test danach den Testanbieter statt den Notbetrieb.
    controller.config.set("llm.provider", "local")
    controller.llm = LlmManager(RetrievalOnlyProvider("kein Modell vorhanden"))
    controller.rag.llm = controller.llm
    return controller

FRAGE = [ChatMessage("system", "Kontext:\n[1] Fundstelle"),
         ChatMessage("user", "Wie ist das bei der Umsatzsteuer?")]


# -- Die Meldung ---------------------------------------------------------

def test_notbetrieb_nennt_ohne_zutun_den_konsolenweg():
    """Wer wirklich in der Konsole sitzt, bekommt weiter den Befehl."""
    text = RetrievalOnlyProvider("kein Modell").generate(FRAGE).text
    assert "PORTABLE_BUCHHALTER_KONSOLE.exe modell empfehlen" in text


def test_notbetrieb_kann_auf_das_fenster_verweisen():
    text = RetrievalOnlyProvider("kein Modell",
                                 weg=RetrievalOnlyProvider.WEG_FENSTER).generate(FRAGE).text
    assert "Registerkarte **Sprachmodell**" in text
    assert "KONSOLE.exe" not in text, (
        "im Fenster darf kein Befehl fuer ein anderes Programm stehen")
    assert "einmaliger" in text, "es muss klar sein, dass etwas fehlt - nicht kaputt ist"


def test_die_meldung_sagt_weiter_was_los_ist():
    """Der Weg ersetzt die Aussage nicht, er ergaenzt sie."""
    text = RetrievalOnlyProvider("kein Modell",
                                 weg=RetrievalOnlyProvider.WEG_FENSTER).generate(FRAGE).text
    assert "kein Sprachmodell eingerichtet" in text
    assert "Fundstellen" in text, "die gefundenen Belege muessen erwaehnt bleiben"


# -- Die Anwendung -------------------------------------------------------

@pytest.fixture
def anwendung(portable_root):
    controller = _ohne_modell(portable_root)
    controller.bootstrap(build_embeddings=False)
    try:
        yield controller
    finally:
        controller.shutdown()


def test_controller_reicht_den_weg_bis_in_die_antwort(anwendung):
    anwendung.einrichtungsweg(RetrievalOnlyProvider.WEG_FENSTER)
    assert isinstance(anwendung.llm.primary, RetrievalOnlyProvider), (
        "ohne Modell muss der Notbetrieb der eingerichtete Anbieter sein")
    assert "Registerkarte" in anwendung.llm.primary.generate(FRAGE).text


def test_weg_ueberlebt_den_neuaufbau_der_modellanbindung(anwendung):
    """Nach einem Modellbezug wird neu aufgebaut - der Weg darf nicht zurueckfallen."""
    anwendung.einrichtungsweg(RetrievalOnlyProvider.WEG_FENSTER)
    anwendung.modell_neu_laden()
    assert "Registerkarte" in anwendung.llm.primary.generate(FRAGE).text


def test_auch_der_rueckfall_mitten_in_einer_anfrage_nennt_den_weg(anwendung):
    """Faellt ein Anbieter aus, entsteht der Notbetrieb erst waehrend der Anfrage."""
    from pkc.llm.base import LlmError

    class Kaputt:
        name = "kaputt"
        model = "keines"

        def available(self):
            return True, ""

        def generate(self, *a, **k):
            raise LlmError("Anbieter weg")

    anwendung.einrichtungsweg(RetrievalOnlyProvider.WEG_FENSTER)
    anwendung.llm.primary = Kaputt()
    antwort = anwendung.llm.generate(FRAGE)

    assert isinstance(antwort, LlmResponse) and not antwort.is_generated
    assert "Registerkarte" in antwort.text, (
        "sonst haengt es vom Zufall ab, welchen Weg der Benutzer liest")
    assert "KONSOLE.exe" not in antwort.text


# -- Die Registerkarte ---------------------------------------------------

@pytest.fixture
def fenster(portable_root):
    dialoge = tk_double.install()
    for modul in [m for m in sys.modules if m.startswith("ui.")]:
        del sys.modules[modul]
    from ui import tk_app

    controller = _ohne_modell(portable_root)
    bericht = controller.bootstrap()
    window = tk_app.MainWindow(controller, bericht)
    try:
        yield window, controller, dialoge
    finally:
        controller.shutdown()


def test_es_gibt_eine_registerkarte_sprachmodell(fenster):
    window, _, _ = fenster
    assert hasattr(window, "modell_button"), "die Registerkarte fehlt"
    assert window.modell_button.options["text"] == "Sprachmodell einrichten"


def test_das_fenster_meldet_der_anwendung_seinen_weg(fenster):
    """Sonst nuetzt die Registerkarte nichts - niemand findet sie."""
    _, controller, _ = fenster
    text = controller.llm.primary.generate(FRAGE).text
    assert "Registerkarte **Sprachmodell**" in text
    assert "KONSOLE.exe" not in text


def test_die_lage_wird_ohne_modell_ehrlich_angezeigt(fenster):
    window, _, _ = fenster
    assert window.modell_lage_label.options["text"] == "Noch nicht eingerichtet"
    assert "Modelldatei" in window.modell_detail_label.options["text"]
    assert "Hinterlegte Bezugsquellen" in window.modell_log.buffer


def test_ohne_bestaetigung_wird_nichts_geladen(fenster, monkeypatch):
    """Es geht um mehrere Gigabyte - der Klick allein reicht nicht."""
    window, controller, dialoge = fenster

    def darf_nicht(*a, **k):
        raise AssertionError("Ohne Bestaetigung darf nichts geladen werden.")

    monkeypatch.setattr(controller, "modell_beziehen", darf_nicht)
    dialoge.answers = [False]
    window._modell_einrichten()

    arten = [m[0] for m in dialoge.messages]
    assert "frage" in arten, "es muss ausdruecklich gefragt werden"


def test_die_rueckfrage_nennt_groesse_lizenz_und_pruefstand(fenster, monkeypatch):
    window, controller, dialoge = fenster
    monkeypatch.setattr(controller, "modell_beziehen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("nein")))
    dialoge.answers = [False]
    window._modell_einrichten()

    frage = next(m[2] for m in dialoge.messages if m[0] == "frage")
    assert "GB" in frage and "Lizenz" in frage
    assert "Bezugsquelle" in frage, "der Pruefstand der Quelle gehoert dazu"


def test_einrichten_laedt_bindet_ein_und_weist_nach(fenster, monkeypatch):
    """Erst wenn das Modell geantwortet hat, gilt es als einsatzbereit."""
    window, controller, dialoge = fenster
    ablauf: list[str] = []

    def beziehen(kennung, *, bestaetigt=False, fortschritt=None, **k):
        assert bestaetigt, "es darf nur nach Bestaetigung geladen werden"
        ablauf.append(f"laden:{kennung}")
        if fortschritt:
            fortschritt(50, 100, 1.0)
            fortschritt(100, 100, 1.0)
        return {"ok": True, "meldung": "geladen", "quelle": {"name": "Testmodell"},
                "pfad": "x.gguf", "bytes": 10, "teile": 1}

    monkeypatch.setattr(controller, "modell_beziehen", beziehen)
    monkeypatch.setattr(controller, "modell_neu_laden",
                        lambda: ablauf.append("neu_laden"))
    monkeypatch.setattr(controller, "modell_probe", lambda *a, **k: (
        ablauf.append("probe") or {"ok": True, "dauer_s": 1.2, "token_je_sekunde": 9.0,
                                   "text": "UStG steht fuer Umsatzsteuergesetz."}))
    dialoge.answers = [True]
    window._modell_einrichten()

    assert [s.split(":")[0] for s in ablauf] == ["laden", "neu_laden", "probe"], (
        "ohne Neuaufbau und Probe waere 'einsatzbereit' nur eine Behauptung")
    assert window.modell_progress.options["value"] == 100
    assert "einsatzbereit" in window.modell_log.buffer
    assert "Umsatzsteuergesetz" in window.modell_log.buffer
    assert any(m[0] == "info" and "einsatzbereit" in m[2] for m in dialoge.messages)


def test_geladen_aber_stumm_wird_nicht_als_erfolg_gemeldet(fenster, monkeypatch):
    """Eine Datei auf der Platte ist noch kein antwortendes Modell."""
    window, controller, dialoge = fenster
    monkeypatch.setattr(controller, "modell_beziehen", lambda *a, **k: {
        "ok": True, "meldung": "geladen", "quelle": {"name": "Testmodell"},
        "pfad": "x.gguf", "bytes": 10, "teile": 1})
    monkeypatch.setattr(controller, "modell_neu_laden", lambda: None)
    monkeypatch.setattr(controller, "modell_probe", lambda *a, **k: {
        "ok": False, "grund": "Der Modelldienst ist nicht hochgekommen."})
    dialoge.answers = [True]
    window._modell_einrichten()

    assert not any(m[0] == "info" for m in dialoge.messages), (
        "ein stummes Modell darf nicht als Erfolg gemeldet werden"
    )
    warnung = next(m for m in dialoge.messages if m[0] == "warnung")
    assert "nicht hochgekommen" in warnung[2]


def test_fehlgeschlagener_bezug_wird_als_fehler_gemeldet(fenster, monkeypatch):
    window, controller, dialoge = fenster
    monkeypatch.setattr(controller, "modell_beziehen", lambda *a, **k: {
        "ok": False, "meldung": "Der Platz reicht nicht.", "quelle": {"name": "x"},
        "pfad": "", "bytes": 0, "teile": 0})
    dialoge.answers = [True]
    window._modell_einrichten()

    assert any(m[0] == "fehler" and "Platz" in m[2] for m in dialoge.messages)
    assert window.modell_progress.options["value"] == 0


def test_probeschaltflaeche_fragt_das_modell(fenster, monkeypatch):
    window, controller, _ = fenster
    monkeypatch.setattr(controller, "modell_probe", lambda *a, **k: {
        "ok": True, "anbieter": "test", "modell": "m", "dauer_s": 0.5,
        "token_je_sekunde": 12.0, "text": "Antwort."})
    window._modell_probe()
    assert "hat geantwortet" in window.modell_log.buffer
