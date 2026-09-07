"""Die Netzpruefung darf nicht "kein Internet" melden, wenn Internet da ist.

Aus dem Betrieb gemeldet: die Anwendung verweigerte den Modellbezug mit
"Zurzeit besteht keine Internetverbindung" - waehrend der Benutzer im selben
Moment im Browser surfte.

Die Ursache waren zwei Entscheidungen, die einzeln vertretbar aussahen:

* Geprueft wurden **nur zwei amtliche Seiten**, darunter
  gesetze-im-internet.de - genau die Adresse, die schon im Bauablauf nicht
  antwortete. Antworteten beide nicht, galt das Netz als tot.
* Gefragt wurde mit **HEAD**. Manche Server beantworten das gar nicht.

Und daraus folgte die dritte, schlimmste: der Bezug eines Modells wurde
anhand dieser Auskunft verweigert, ohne die Bezugsquelle selbst je gefragt
zu haben.
"""

from __future__ import annotations

import json

import pytest

from pkc.config import DEFAULTS
from test_controller import make_controller


# -- Der Abruf -----------------------------------------------------------

def test_probe_versucht_auch_get(http_server, monkeypatch):
    """Ein Server, der HEAD nicht beantwortet, ist trotzdem erreichbar."""
    import http.server

    from pkc import netstate

    verfahren: list[str] = []
    echtes_urlopen = netstate.urllib.request.urlopen

    def nur_get(request, *a, **k):
        verfahren.append(request.get_method())
        if request.get_method() == "HEAD":
            raise OSError("dieser Server mag kein HEAD")
        return echtes_urlopen(request, *a, **k)

    monkeypatch.setattr(netstate.urllib.request, "urlopen", nur_get)
    http_server.add("/", b"da", "text/plain")

    assert netstate.probe(http_server.base + "/", 5.0) is True
    assert verfahren == ["HEAD", "GET"], (
        "nach einem erfolglosen HEAD muss GET folgen")


def test_probe_wertet_fehlercode_als_erreichbar(http_server):
    """Ein 404 beweist, dass die Verbindung steht - darum geht es hier."""
    from pkc.netstate import probe

    assert probe(http_server.base + "/gibt-es-nicht", 5.0) is True


def test_probe_meldet_echte_unerreichbarkeit(monkeypatch):
    from pkc import netstate

    monkeypatch.setattr(netstate.urllib.request, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("kein Netz")))
    assert netstate.probe("https://beispiel.invalid/", 1.0) is False


# -- Die geprueften Adressen ---------------------------------------------

def test_mehr_als_eine_adresse_wird_geprueft():
    """Eine einzelne stillstehende Seite darf nicht ueber das Netz entscheiden."""
    hosts = DEFAULTS["network"]["probe_hosts"]
    assert len(hosts) >= 3, f"nur {len(hosts)} Adresse(n) - zu wenig"


def test_die_bezugsquelle_der_modelle_wird_mitgeprueft():
    """Sie ist die Adresse, auf die es beim Einrichten ankommt."""
    hosts = DEFAULTS["network"]["probe_hosts"]
    assert any("huggingface.co" in h for h in hosts)
    assert hosts[0].startswith("https://huggingface.co"), (
        "sie gehoert nach vorn - der erste Erfolg genuegt")


def test_es_werden_keine_fremden_dienste_gefragt():
    """Eine Buchhaltungsanwendung kontaktiert keinen Dritten zum Zeitvertreib.

    Ein Aufruf bei einem grossen Anbieter waere fuer die Netzpruefung
    zuverlaessiger - und wuerde bedeuten, dass die Anwendung ungefragt
    Verbindung zu jemandem aufnimmt, der mit der Aufgabe nichts zu tun hat.
    """
    hosts = DEFAULTS["network"]["probe_hosts"]
    erlaubt = ("huggingface.co", "bundesfinanzministerium.de",
               "gesetze-im-internet.de")
    for host in hosts:
        assert any(teil in host for teil in erlaubt), (
            f"{host} gehoert nicht zu den Adressen, die die Anwendung ohnehin braucht")


def test_die_zeitgrenze_ist_nicht_zu_knapp():
    """Vier Sekunden melden auf einer langsamen Leitung "kein Netz"."""
    assert DEFAULTS["network"]["probe_timeout_seconds"] >= 8


# -- Der Modellbezug -----------------------------------------------------

KATALOG = {
    "stand": "2026-01-01",
    "modelle": [{
        "id": "probe-klein", "profil": "probe", "name": "Probemodell",
        "lizenz": "Apache-2.0", "herkunft": "Test",
        "url": "https://beispiel.invalid/probe.gguf", "datei": "probe.gguf",
        "groesse_gb": 0.4, "min_ram_gb": 2, "produktiv": False,
        "pruefung": {"erreichbar": True, "geprueft_am": "2026-09-06"},
    }],
}


@pytest.fixture
def anwendung(portable_root):
    (portable_root.get("config")).mkdir(parents=True, exist_ok=True)
    (portable_root.get("config") / "model_catalog.json").write_text(
        json.dumps(KATALOG), encoding="utf-8")
    controller = make_controller(portable_root)
    controller.bootstrap(build_embeddings=False)
    try:
        yield controller
    finally:
        controller.shutdown()


def test_bezug_fragt_die_quelle_selbst(anwendung, monkeypatch):
    """Der Kern des Fehlers: geladen wurde nicht, weil eine FREMDE Seite schwieg.

    Die allgemeine Netzpruefung sagt "kein Netz", die Bezugsquelle antwortet
    aber. Dann muss geladen werden - alles andere ist eine Verweigerung mit
    falscher Begruendung.
    """
    from pkc.netstate import Mode

    anwendung.set_mode(Mode.HYBRID)
    anwendung.network.force(False, "Test: allgemeine Pruefung findet nichts")

    gefragt: list[str] = []
    monkeypatch.setattr("pkc.netstate.probe",
                        lambda adresse, zeit: gefragt.append(adresse) or True)
    geladen: list[str] = []
    monkeypatch.setattr("pkc.llm.bezug.laden", lambda *a, **k: geladen.append(a[0]) or
                        __import__("pkc.llm.bezug", fromlist=["Ladeergebnis"])
                        .Ladeergebnis(True, anwendung.paths.get("models") / "probe.gguf",
                                      meldung="geladen"))

    ergebnis = anwendung.modell_beziehen("probe-klein", bestaetigt=True)
    assert ergebnis["ok"], ergebnis["meldung"]
    assert gefragt == ["https://beispiel.invalid/probe.gguf"], (
        "geprueft werden muss die Adresse, von der geladen wird")


def test_ohne_jede_verbindung_wird_weiter_abgelehnt(anwendung, monkeypatch):
    """Die Sperre bleibt - sie stuetzt sich nur auf die richtige Auskunft."""
    from pkc.netstate import Mode

    anwendung.set_mode(Mode.HYBRID)
    anwendung.network.force(False, "Test: kein Netz")
    monkeypatch.setattr("pkc.netstate.probe", lambda adresse, zeit: False)
    monkeypatch.setattr("pkc.llm.bezug.laden", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("ohne Verbindung darf nichts geladen werden")))

    with pytest.raises(ValueError) as fehler:
        anwendung.modell_beziehen("probe-klein", bestaetigt=True)
    assert "keine Internetverbindung" in str(fehler.value)


def test_offline_bleibt_offline(anwendung, monkeypatch):
    """Die Betriebsart OFFLINE ist eine Entscheidung, keine Vermutung."""
    from pkc.netstate import Mode

    anwendung.set_mode(Mode.OFFLINE)
    monkeypatch.setattr("pkc.netstate.probe", lambda adresse, zeit: True)
    monkeypatch.setattr("pkc.llm.bezug.laden", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("im Modus OFFLINE darf nichts geladen werden")))

    with pytest.raises(ValueError) as fehler:
        anwendung.modell_beziehen("probe-klein", bestaetigt=True)
    assert "OFFLINE" in str(fehler.value)
