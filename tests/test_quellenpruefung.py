"""Die Pruefung des Quellenregisters (Werkzeug tools/quellen_pruefen.py).

Der Sinn des Werkzeugs ist eine ehrliche Aussage: erreicht **die Anwendung**
die hinterlegten Adressen? Deshalb wird hier zweierlei geprueft:

* dass es den HTTP-Zugriff der Anwendung benutzt und nicht einen eigenen,
* dass ein Ausfall als Ausfall im Ergebnis steht - mit Grund, nicht nur mit
  einer Zahl.

Ein echter Abruf findet hier nicht statt. Er gehoert in den Windows-
Bauablauf, wo es Internet gibt; hier wuerde er nur die Sperre der
Entwicklungsumgebung messen.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "tools"))

import quellen_pruefen                                   # noqa: E402
from pkc.updater.http_client import FetchResult          # noqa: E402

REGISTER = {
    "sources": [
        {"source_id": "Q01_TEST", "documents": [
            {"doc_uid": "GUT", "url": "https://example.invalid/gut.zip"},
            {"doc_uid": "SCHLECHT", "url": "https://example.invalid/weg.html"},
        ]},
        {"source_id": "Q02_TEST", "documents": [
            {"doc_uid": "ZWEITE", "url": "https://example.invalid/zwei.html"},
        ]},
    ]
}


class Erfundener:
    """Ein HTTP-Zugriff, der nicht ins Netz geht."""

    gerufen: list[str] = []

    def __init__(self, *_args, **kwargs):
        self.kwargs = kwargs
        Erfundener.gerufen = []

    def fetch(self, url: str) -> FetchResult:
        Erfundener.gerufen.append(url)
        if "weg" in url:
            return FetchResult(url, 0, False, error="URLError: Name nicht aufloesbar")
        return FetchResult(url, 200, True, content=b"x" * 12,
                           content_type="application/zip")


@pytest.fixture
def register(tmp_path):
    pfad = tmp_path / "source_registry.json"
    pfad.write_text(json.dumps(REGISTER), encoding="utf-8")
    return pfad


@pytest.fixture(autouse=True)
def ohne_netz(monkeypatch):
    monkeypatch.setattr(quellen_pruefen, "HttpClient", Erfundener)


def test_jede_adresse_wird_abgerufen(register):
    zeilen = quellen_pruefen.pruefen(register)
    assert [z["dokument"] for z in zeilen] == ["GUT", "SCHLECHT", "ZWEITE"]
    assert Erfundener.gerufen == [d["url"] for q in REGISTER["sources"]
                                  for d in q["documents"]]


def test_ausfall_steht_mit_grund_im_ergebnis(register):
    zeilen = quellen_pruefen.pruefen(register)
    gut, schlecht = zeilen[0], zeilen[1]

    assert gut["erreichbar"] and gut["status"] == 200 and gut["groesse_bytes"] == 12
    assert not schlecht["erreichbar"]
    assert "Name nicht aufloesbar" in schlecht["fehler"], (
        "eine Statuszahl allein sagt niemandem, warum die Quelle fehlt")


def test_bericht_zaehlt_und_benennt(register):
    text = quellen_pruefen.bericht(quellen_pruefen.pruefen(register))
    assert "ERREICHBAR: 2 von 3" in text
    assert "Q01_TEST/SCHLECHT" in text and "Name nicht aufloesbar" in text


def test_eine_quelle_allein_pruefbar(register):
    zeilen = quellen_pruefen.pruefen(register, nur="Q02_TEST")
    assert [z["dokument"] for z in zeilen] == ["ZWEITE"]


def test_rueckgabewert_und_datei(register, tmp_path, capsys):
    ziel = tmp_path / "ergebnis.json"
    code = quellen_pruefen.main(["--register", str(register), "--ziel", str(ziel)])
    capsys.readouterr()
    assert code == 1, "ein Ausfall darf nicht als Erfolg gemeldet werden"
    assert len(json.loads(ziel.read_text(encoding="utf-8"))) == 3

    nur_gute = tmp_path / "gut.json"
    nur_gute.write_text(json.dumps(
        {"sources": [{"source_id": "Q02_TEST",
                      "documents": REGISTER["sources"][1]["documents"]}]}),
        encoding="utf-8")
    assert quellen_pruefen.main(["--register", str(nur_gute)]) == 0
    capsys.readouterr()


def test_werkzeug_nutzt_den_zugriff_der_anwendung():
    """Ein fremdes Abrufwerkzeug wuerde etwas anderes messen als der Betrieb."""
    quelltext = (WURZEL / "tools" / "quellen_pruefen.py").read_text(encoding="utf-8")
    assert "from pkc.updater.http_client import HttpClient" in quelltext
    for fremd in ("Invoke-WebRequest", "requests.", "urllib.request.urlopen"):
        assert fremd not in quelltext, f"{fremd} umgeht den Zugriff der Anwendung"


def test_hoeflichkeit_bleibt_erhalten(register, monkeypatch):
    """Amtliche Server werden nicht im Sekundentakt angefasst."""
    gesehen = {}

    class Merkend(Erfundener):
        def __init__(self, *args, **kwargs):
            gesehen.update(kwargs)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(quellen_pruefen, "HttpClient", Merkend)
    quellen_pruefen.pruefen(register)
    assert gesehen.get("min_delay", 0) >= 1.0
