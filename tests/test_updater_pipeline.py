"""Update-Pipeline gegen einen echten (lokalen) HTTP-Server.

Damit wird die vollstaendige Kette geprueft: Abruf -> Original -> Extraktion
-> Normalisierung -> Metadaten -> Chunking -> Index -> Bericht -> Ruecknahme.
"""

from __future__ import annotations

import io
import json
import zipfile

import pytest

from pkc.db import Database
from pkc.db.schema import KNOWLEDGE_MIGRATIONS
from pkc.knowledge.store import KnowledgeStore
from pkc.retrieval.embeddings import HashingEmbedder
from pkc.retrieval.search import HybridSearcher
from pkc.updater.http_client import HttpClient
from pkc.updater.pipeline import UpdatePipeline
from pkc.updater.registry import SourceRegistry

USTG_XML = """<?xml version="1.0" encoding="UTF-8"?>
<dokumente>
  <norm>
    <metadaten><jurabk>UStG</jurabk><titel>Umsatzsteuergesetz</titel></metadaten>
    <textdaten><text><Content><P>Rahmen des Umsatzsteuergesetzes mit einleitendem Text.</P></Content></text></textdaten>
  </norm>
  <norm>
    <metadaten><enbez>&#167; 14</enbez><titel>Ausstellung von Rechnungen</titel><amtabk>UStG</amtabk></metadaten>
    <textdaten><text><Content><P>(1) Rechnung ist jedes Dokument, mit dem ueber eine Lieferung
    oder sonstige Leistung abgerechnet wird. Die Echtheit der Herkunft der Rechnung, die
    Unversehrtheit ihres Inhalts und ihre Lesbarkeit muessen gewaehrleistet werden.</P></Content></text></textdaten>
  </norm>
  <norm>
    <metadaten><enbez>&#167; 15</enbez><titel>Vorsteuerabzug</titel><amtabk>UStG</amtabk></metadaten>
    <textdaten><text><Content><P>(1) Der Unternehmer kann die gesetzlich geschuldete Steuer fuer
    Lieferungen und sonstige Leistungen, die von einem anderen Unternehmer fuer sein Unternehmen
    ausgefuehrt worden sind, als Vorsteuer abziehen. Die Ausuebung des Vorsteuerabzugs setzt voraus,
    dass der Unternehmer eine nach den Paragraphen 14 und 14a ausgestellte Rechnung besitzt.</P></Content></text></textdaten>
  </norm>
</dokumente>
"""

BMF_HTML = b"""<html><head><title>GoBD - Grundsaetze ordnungsmaessiger Buchfuehrung</title></head>
<body><h1>GoBD</h1><p>Die Grundsaetze zur ordnungsmaessigen Fuehrung und Aufbewahrung von
Buechern, Aufzeichnungen und Unterlagen in elektronischer Form sowie zum Datenzugriff regeln
die Aufbewahrungspflichten. Aufzubewahren sind Buecher, Aufzeichnungen, Belege und
Arbeitsanweisungen ueber zehn Jahre.</p></body></html>"""


def _zip_bytes(name: str, payload: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, payload)
    return buffer.getvalue()


@pytest.fixture
def setup(portable_root, http_server):
    law_url = http_server.add("/ustg/xml.zip", _zip_bytes("ustg.xml", USTG_XML),
                              "application/zip", '"law-v1"')
    bmf_url = http_server.add("/bmf/gobd.html", BMF_HTML, "text/html; charset=utf-8", '"bmf-v1"')
    registry_data = {
        "sources": [
            {
                "source_id": "T01_GESETZ", "name": "Testgesetzquelle", "publisher": "Test",
                "priority": 1, "kind": "law", "base_url": http_server.base,
                "licence": "amtlich", "documents": [
                    {"doc_uid": "T_USTG", "url": law_url, "title": "Umsatzsteuergesetz",
                     "citation": "UStG", "format": "xml_zip", "kind": "law"}
                ],
            },
            {
                "source_id": "T02_VERWALTUNG", "name": "Testverwaltungsquelle", "publisher": "Test",
                "priority": 2, "kind": "admin", "base_url": http_server.base,
                "documents": [
                    {"doc_uid": "T_GOBD", "url": bmf_url, "title": "GoBD",
                     "citation": "GoBD", "format": "html", "kind": "admin"}
                ],
            },
            {
                "source_id": "T03_KAPUTT", "name": "Nicht erreichbare Quelle", "publisher": "Test",
                "priority": 5, "kind": "secondary", "base_url": http_server.base,
                "documents": [
                    {"doc_uid": "T_FEHLT", "url": f"{http_server.base}/gibt-es-nicht.html",
                     "title": "Fehlende Seite", "format": "html", "kind": "secondary"}
                ],
            },
        ]
    }
    registry_path = portable_root.get("config") / "test_registry.json"
    registry_path.write_text(json.dumps(registry_data), encoding="utf-8")

    db = Database(portable_root.knowledge_db, KNOWLEDGE_MIGRATIONS)
    store = KnowledgeStore(db)
    searcher = HybridSearcher(db, HashingEmbedder(256))
    pipeline = UpdatePipeline(
        portable_root, store, SourceRegistry.load(registry_path), searcher,
        HttpClient(min_delay=0.0, respect_robots=False),
    )
    return pipeline, store, searcher, portable_root, http_server


def test_first_run_downloads_normalises_and_indexes(setup):
    pipeline, store, searcher, paths, _ = setup
    report = pipeline.run(trigger="test")

    assert report.status == "partial", "eine Quelle ist absichtlich kaputt"
    assert report.updated == 2 and report.failed == 1

    # Originale, Normalisate und Metadaten liegen tatsaechlich auf der Platte
    assert (paths.get("resources_raw") / "T01_GESETZ" / "T_USTG.zip").is_file()
    normalized = paths.get("resources_normalized") / "T01_GESETZ" / "T_USTG.txt"
    assert normalized.is_file() and "Vorsteuer" in normalized.read_text(encoding="utf-8")
    meta_file = paths.get("resources_metadata") / "T01_GESETZ" / "T_USTG.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta["sha256"] and meta["priority"] == 1 and meta["citation"] == "UStG"

    # Bericht existiert als Datei
    report_dir = paths.get("updates") / report.run_id
    assert (report_dir / "bericht.json").is_file()
    assert (report_dir / "bericht.md").is_file()
    assert "fehlgeschlagen" in (report_dir / "bericht.md").read_text(encoding="utf-8")

    stats = store.stats()
    assert stats["documents"] == 2 and stats["chunks"] >= 3
    assert stats["knowledge_date"]


def test_second_run_is_incremental_via_etag(setup):
    pipeline, store, _, _, http_server = setup
    pipeline.run(trigger="test")
    before = store.stats()["chunks"]

    second = pipeline.run(trigger="test")
    assert second.unchanged == 2, "unveraenderte Dokumente duerfen nicht neu geladen werden"
    assert second.updated == 0
    assert store.stats()["chunks"] == before


def test_changed_document_is_reindexed(setup):
    pipeline, store, _, _, http_server = setup
    pipeline.run(trigger="test")
    http_server.add(
        "/bmf/gobd.html",
        BMF_HTML.replace(b"zehn Jahre", b"acht Jahre nach neuer Fassung"),
        "text/html; charset=utf-8", '"bmf-v2"',
    )
    report = pipeline.run(trigger="test")
    assert report.updated == 1 and report.unchanged == 1
    text = store.db.scalar(
        "SELECT c.text FROM chunks c JOIN documents d ON d.id=c.doc_id "
        "WHERE d.doc_uid='T_GOBD' AND c.text LIKE '%acht Jahre%'"
    )
    assert text and "acht Jahre" in text


def test_search_finds_indexed_law(setup):
    pipeline, store, searcher, _, _ = setup
    pipeline.run(trigger="test")
    searcher.index_embeddings()

    hits = searcher.search("Welche Voraussetzungen gelten fuer den Vorsteuerabzug?", top_k=5)
    assert hits, "die indexierte Norm muss gefunden werden"
    top = hits[0]
    assert "15" in top.citation and top.source_id == "T01_GESETZ"
    assert top.priority == 1
    assert "Vorsteuer" in top.text


def test_offline_run_changes_nothing(setup):
    pipeline, store, _, _, _ = setup
    report = pipeline.run(trigger="test", online=False)
    assert report.status == "no_network"
    assert report.checked == 0
    assert store.stats()["documents"] == 0
    assert "Kein Internetzugang" in report.messages[0]


def test_dry_run_writes_nothing(setup):
    pipeline, store, _, paths, _ = setup
    report = pipeline.run(trigger="test", dry_run=True)
    assert report.updated == 2
    assert store.stats()["documents"] == 0
    assert not any((paths.get("resources_raw")).rglob("*.zip"))


def test_rollback_restores_previous_state(setup):
    pipeline, store, _, _, http_server = setup
    pipeline.run(trigger="test")
    first_chunks = store.stats()["chunks"]

    http_server.add("/bmf/gobd.html", BMF_HTML.replace(b"zehn Jahre", b"voellig anderer Inhalt hier"),
                    "text/html; charset=utf-8", '"bmf-v9"')
    second = pipeline.run(trigger="test")
    assert second.updated == 1

    ok, message = pipeline.rollback(second.run_id)
    assert ok, message
    assert store.stats()["chunks"] == first_chunks
    assert store.db.scalar(
        "SELECT COUNT(*) FROM chunks WHERE text LIKE '%voellig anderer Inhalt%'"
    ) == 0


@pytest.mark.parametrize("register", [
    {"sources": [{"source_id": "../../ausbruch", "name": "x", "priority": 1}]},
    {"sources": [{"source_id": "a/b", "name": "x", "priority": 1}]},
    {"sources": [{"source_id": "Q01", "name": "x", "priority": 1, "documents": [
        {"doc_uid": "../../ausbruch", "url": "http://x/y", "title": "t"}]}]},
])
def test_registry_rejects_path_escaping_identifiers(portable_root, register):
    """Kennungen werden zu Dateinamen - sie duerfen nicht aus dem Bereich fuehren.

    Ein Quellenregister ist eine gewoehnliche Textdatei und kann weitergegeben
    werden. Ohne diese Pruefung koennte es Dateien ausserhalb von
    resources/raw anlegen.
    """
    from pkc.updater.registry import RegistryError

    pfad = portable_root.get("config") / "boes.json"
    pfad.write_text(json.dumps(register), encoding="utf-8")
    with pytest.raises(RegistryError) as fehler:
        SourceRegistry.load(pfad)
    assert "Unzulaessige" in str(fehler.value)


def test_shipped_registry_is_valid():
    """Das ausgelieferte Quellenregister muss die Pruefung bestehen."""
    from pathlib import Path as _Path

    pfad = _Path(__file__).resolve().parents[1] / "config" / "source_registry.json"
    registry = SourceRegistry.load(pfad)
    assert len(registry) >= 12 and registry.document_count() >= 30


def test_pruefstand_der_quellen_geht_beim_speichern_nicht_verloren(tmp_path):
    """Warum ``verified`` wahr ist, muss ein Speichern ueberleben.

    Der Pruefstand wird von tools/quellen_pruefen.py eingetragen. Wuerde ihn
    das Register beim Zurueckschreiben stillschweigend wegwerfen, stuende
    spaeter "geprueft" da, ohne dass noch jemand nachsehen koennte, wo.
    """
    from pathlib import Path as _Path

    quelle = _Path(__file__).resolve().parents[1] / "config" / "source_registry.json"
    daten = json.loads(quelle.read_text(encoding="utf-8"))
    daten["sources"][0]["pruefung"] = {
        "geprueft_am": "2026-09-06", "dokumente": 17, "erreichbar": 17,
        "beleg": "https://example.invalid/lauf/1",
    }
    pfad = tmp_path / "source_registry.json"
    pfad.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")

    registry = SourceRegistry.load(pfad)
    assert registry.sources[0].pruefung["beleg"] == "https://example.invalid/lauf/1"

    ziel = tmp_path / "erneut.json"
    registry.save(ziel)
    danach = json.loads(ziel.read_text(encoding="utf-8"))
    assert danach["sources"][0]["pruefung"]["beleg"] == "https://example.invalid/lauf/1"
    assert danach["sources"][0]["pruefung"]["erreichbar"] == 17


def test_binary_content_is_not_indexed(setup):
    """Binaerdaten duerfen nicht als vermeintliches Fachwissen im Index landen."""
    pipeline, store, _, _, http_server = setup
    http_server.add("/bmf/gobd.html", bytes(range(256)) * 40,
                    "text/html; charset=utf-8", '"binaer"')
    report = pipeline.run(trigger="test")
    ergebnis = next(r for r in report.results if r.doc_uid == "T_GOBD")
    assert ergebnis.status == "failed"
    assert "kein lesbarer Text" in ergebnis.detail
    assert store.db.scalar(
        "SELECT COUNT(*) FROM documents WHERE doc_uid='T_GOBD'"
    ) == 0, "das Dokument darf gar nicht erst angelegt werden"


def test_schedule_due_logic(setup):
    pipeline, _, _, _, _ = setup
    due, reason = pipeline.due("manual")
    assert due is False and "manuell" in reason
    due, reason = pipeline.due("weekly")
    assert due is True and "noch nie" in reason
    pipeline.run(trigger="test")
    due, reason = pipeline.due("weekly")
    assert due is False and "naechstes in" in reason


# ======================================================================
# Fehlerbehandlung beim Wissensupdate
#
# Anlass: Beim ersten echten Update auf dem Windows-Rechner schlugen 8 von
# 31 Dokumenten fehl. Vier verschiedene Ursachen, davon zwei in unserem
# Code: kein eigener Zertifikatskontext und kein zweiter Versuch.
# ======================================================================

def test_voruebergehender_fehler_wird_wiederholt(monkeypatch):
    """503 heisst 'gerade nicht', nicht 'nie' - also erneut versuchen."""
    from pkc.updater.http_client import HttpClient, FetchResult

    monkeypatch.setattr("pkc.updater.http_client.WARTEZEITEN", (0.0, 0.0))
    client = HttpClient(min_delay=0.0, respect_robots=False)

    versuche = []

    def antwort(request, url, host):
        versuche.append(url)
        if len(versuche) < 3:
            return FetchResult(url, 503, False, error="HTTP 503",
                               wiederholbar=True)
        return FetchResult(url, 200, True, content=b"endlich da")

    monkeypatch.setattr(client, "_einmal_abrufen", antwort)
    ergebnis = client.fetch("https://beispiel.invalid/seite")

    assert ergebnis.ok and ergebnis.content == b"endlich da"
    assert len(versuche) == 3, "es muss bis zu dreimal versucht werden"


def test_dauerhafter_fehler_wird_nicht_wiederholt(monkeypatch):
    """Ein 404 wird durch Warten nicht besser - das waere nur Zeitverlust."""
    from pkc.updater.http_client import HttpClient, FetchResult

    client = HttpClient(min_delay=0.0, respect_robots=False)
    versuche = []

    def antwort(request, url, host):
        versuche.append(url)
        return FetchResult(url, 404, False, error="HTTP 404", wiederholbar=False)

    monkeypatch.setattr(client, "_einmal_abrufen", antwort)
    ergebnis = client.fetch("https://beispiel.invalid/weg")

    assert not ergebnis.ok
    assert len(versuche) == 1, "ein 404 darf nicht wiederholt werden"


def test_fehlermeldungen_sagen_was_zu_tun_ist():
    """Eine Fehlermeldung, die nur 'HTTP 404' sagt, hilft niemandem."""
    from pkc.updater.http_client import _verstaendlich

    assert "Quellenregister" in _verstaendlich(404, "HTTP 404: Not Found")
    assert "voruebergehend" in _verstaendlich(503, "HTTP 503: Backend fetch failed")
    assert "automatisierte Abrufe" in _verstaendlich(403, "HTTP 403: Forbidden")
    zertifikat = _verstaendlich(0, "URLError: [SSL: CERTIFICATE_VERIFY_FAILED] ...")
    assert "nie ungeprueft" in zertifikat, \
        "es muss klar sein, dass nicht etwa ungeprueft geladen wird"


def test_zertifikatspruefung_ist_eingeschaltet():
    """Nie ohne Pruefung laden - auch nicht, um einen Fehler loszuwerden."""
    import ssl
    from pkc.updater.http_client import HttpClient, _ssl_kontext

    kontext = _ssl_kontext()
    assert kontext.verify_mode == ssl.CERT_REQUIRED
    assert kontext.check_hostname is True

    client = HttpClient()
    assert client._ssl.verify_mode == ssl.CERT_REQUIRED
    assert client._ssl.check_hostname is True


def test_echter_server_antwortet_erst_mit_503(http_server, monkeypatch):
    """Gegen einen echten lokalen Server, nicht nur gegen ein Doppel."""
    from pkc.updater.http_client import HttpClient

    monkeypatch.setattr("pkc.updater.http_client.WARTEZEITEN", (0.0, 0.0))
    url = http_server.add("/wackelig", b"<html><body>Inhalt</body></html>")
    client = HttpClient(min_delay=0.0, respect_robots=False)

    ergebnis = client.fetch(url)
    assert ergebnis.ok and b"Inhalt" in ergebnis.content

    fehlt = client.fetch(f"{http_server.base}/gibtesnicht")
    assert not fehlt.ok and fehlt.status == 404
    assert not fehlt.wiederholbar
    assert "Quellenregister" in fehlt.error
