"""Plugin- und Erweiterungssystem (Erweiterung E5, Abschnitte 98 bis 123).

Der Schwerpunkt liegt nicht darauf, dass ein Plugin laeuft - sondern darauf,
dass es **nur** das kann, was ihm erlaubt wurde, und dass ein veraendertes
Paket auffliegt.

Ehrlich zur Reichweite: geprueft ist die vermittelte Schnittstelle, nicht
eine Trennung auf Betriebssystemebene. Ein Plugin ist Python-Code im selben
Prozess; das ist in PLUGIN_KONZEPT.md als offener Punkt vermerkt.
"""

from __future__ import annotations

import json
import zipfile

import pytest

from pkc.plugins import (
    BerechtigungFehlt, Manifest, PluginFehler, Pluginverwaltung, packen, pruefen,
    signaturdaten,
)

MANIFEST = {
    "id": "testplugin",
    "name": "Testplugin",
    "version": "1.0",
    "api": 1,
    "kategorie": "AUTOMATION",
    "einstieg": "plugin:anmelden",
    "beschreibung": "Nur fuer den Test",
    "berechtigungen": [],
}

CODE = '''
def anmelden(kontext):
    kontext.werkzeug_anmelden("gruss", "Sagt Hallo", lambda: "Hallo")
'''


def _paket_bauen(tmp_path, manifest=None, code=CODE, name="testplugin"):
    ordner = tmp_path / f"quelle_{name}"
    ordner.mkdir(exist_ok=True)
    daten = {**MANIFEST, **(manifest or {})}
    (ordner / "manifest.json").write_text(json.dumps(daten), encoding="utf-8")
    (ordner / f"{daten['einstieg'].split(':')[0]}.py").write_text(code, encoding="utf-8")
    return packen(ordner, tmp_path / name, daten)


@pytest.fixture
def verwaltung(portable_root):
    return Pluginverwaltung(portable_root)


# -- Manifest ------------------------------------------------------------

def test_manifest_verlangt_brauchbare_angaben():
    with pytest.raises(PluginFehler):
        Manifest.from_dict({**MANIFEST, "kategorie": "IRGENDWAS"})
    with pytest.raises(PluginFehler):
        Manifest.from_dict({**MANIFEST, "einstieg": "ohne_doppelpunkt"})
    with pytest.raises(PluginFehler):
        Manifest.from_dict({**MANIFEST, "berechtigungen": ["ALLES_DUERFEN"]})


def test_netzangabe_ohne_berechtigung_wird_abgelehnt():
    """Wer ins Netz will, muss das Recht auch verlangen - sonst ist es unklar."""
    with pytest.raises(PluginFehler) as fehler:
        Manifest.from_dict({**MANIFEST, "benoetigt_netz": True})
    assert "NETWORK_ACCESS" in str(fehler.value)


# -- Paketpruefung -------------------------------------------------------

def test_veraendertes_paket_wird_erkannt(tmp_path):
    paket = _paket_bauen(tmp_path)
    with zipfile.ZipFile(paket) as archiv:
        inhalt = {name: archiv.read(name) for name in archiv.namelist()}
    inhalt["plugin.py"] = b"def anmelden(kontext):\n    pass\n"
    with zipfile.ZipFile(paket, "w") as archiv:
        for name, daten in inhalt.items():
            archiv.writestr(name, daten)

    with pytest.raises(PluginFehler) as fehler:
        pruefen(paket)
    assert "veraendert" in str(fehler.value)


def test_zusaetzliche_datei_wird_abgelehnt(tmp_path):
    """Was nicht im Manifest steht, ist nicht mitsigniert - also nicht erlaubt."""
    paket = _paket_bauen(tmp_path)
    with zipfile.ZipFile(paket, "a") as archiv:
        archiv.writestr("heimlich.py", "print('hallo')")
    with pytest.raises(PluginFehler) as fehler:
        pruefen(paket)
    assert "nicht mitsigniert" in str(fehler.value)


def test_ausfuehrbare_dateien_kommen_nicht_ins_paket(tmp_path):
    paket = _paket_bauen(tmp_path)
    with zipfile.ZipFile(paket, "a") as archiv:
        archiv.writestr("werkzeug.exe", b"MZ")
    with pytest.raises(PluginFehler) as fehler:
        pruefen(paket)
    assert "werkzeug.exe" in str(fehler.value)


def test_pfad_aus_dem_ordner_heraus_wird_abgelehnt(tmp_path):
    paket = _paket_bauen(tmp_path)
    with zipfile.ZipFile(paket, "a") as archiv:
        archiv.writestr("../boeser.py", "print('x')")
    with pytest.raises(PluginFehler) as fehler:
        pruefen(paket)
    assert "Unzulaessiger Pfad" in str(fehler.value)


def test_unsigniertes_paket_wird_deutlich_benannt(tmp_path):
    pruefung = pruefen(_paket_bauen(tmp_path))
    assert not pruefung.vertrauenswuerdig
    assert any("nicht signiert" in hinweis for hinweis in pruefung.hinweise)


def test_gueltige_signatur_wird_erkannt(tmp_path):
    pytest.importorskip("cryptography")
    from pkc.licensing.issue import generate_keypair, load_private_key

    privat, oeffentlich = generate_keypair(tmp_path / "privat.pem", tmp_path / "oeff.pem")
    ohne = _paket_bauen(tmp_path, name="vorlauf")
    with zipfile.ZipFile(ohne) as archiv:
        manifest = Manifest.from_dict(json.loads(archiv.read("manifest.json")))
    signatur = load_private_key(privat).sign(signaturdaten(manifest))

    ordner = tmp_path / "quelle_vorlauf"
    signiert = packen(ordner, tmp_path / "signiert", manifest.as_dict(), signatur)
    pruefung = pruefen(signiert, oeffentlich.read_bytes())
    assert pruefung.signiert and pruefung.signatur_gueltig and pruefung.vertrauenswuerdig


def test_falsche_signatur_wird_abgelehnt(tmp_path):
    pytest.importorskip("cryptography")
    from pkc.licensing.issue import generate_keypair, load_private_key

    privat, _ = generate_keypair(tmp_path / "p1.pem", tmp_path / "o1.pem")
    _, fremd = generate_keypair(tmp_path / "p2.pem", tmp_path / "o2.pem")
    ohne = _paket_bauen(tmp_path, name="vorlauf2")
    with zipfile.ZipFile(ohne) as archiv:
        manifest = Manifest.from_dict(json.loads(archiv.read("manifest.json")))
    signatur = load_private_key(privat).sign(signaturdaten(manifest))
    signiert = packen(tmp_path / "quelle_vorlauf2", tmp_path / "s2",
                      manifest.as_dict(), signatur)

    with pytest.raises(PluginFehler) as fehler:
        pruefen(signiert, fremd.read_bytes())
    assert "Signatur" in str(fehler.value)


# -- Installation --------------------------------------------------------

def test_ohne_bestaetigung_wird_nichts_installiert(tmp_path, verwaltung):
    paket = _paket_bauen(tmp_path, {"berechtigungen": ["COMPANY_MEMORY_READ"]})
    with pytest.raises(PluginFehler) as fehler:
        verwaltung.installieren(paket)
    assert "COMPANY_MEMORY_READ" in str(fehler.value)
    assert verwaltung.liste() == []


def test_es_koennen_nur_verlangte_rechte_erteilt_werden(tmp_path, verwaltung):
    paket = _paket_bauen(tmp_path)
    with pytest.raises(PluginFehler):
        verwaltung.installieren(paket, bestaetigt=True, rechte=["NETWORK_ACCESS"])


def test_falsche_schnittstellenfassung_wird_abgelehnt(tmp_path, verwaltung):
    paket = _paket_bauen(tmp_path, {"api": 99})
    with pytest.raises(PluginFehler) as fehler:
        verwaltung.pruefen(paket)
    assert "99" in str(fehler.value)


def test_installieren_aktivieren_laden(tmp_path, verwaltung):
    paket = _paket_bauen(tmp_path)
    stand = verwaltung.installieren(paket, bestaetigt=True)
    assert stand.aktiv is False, "installiert ist noch nicht aktiv"

    verwaltung.aktivieren("testplugin")
    geladen = verwaltung.laden()
    assert [s.manifest.id for s in geladen] == ["testplugin"]
    werkzeuge = verwaltung.werkzeuge()
    assert [w.name for w in werkzeuge] == ["gruss"]
    assert werkzeuge[0].funktion() == "Hallo"


def test_plugincode_liegt_im_programmordner_daten_beim_kunden(tmp_path, verwaltung,
                                                              portable_root):
    verwaltung.installieren(_paket_bauen(tmp_path), bestaetigt=True)
    verwaltung.aktivieren("testplugin")
    verwaltung.laden()
    kontext = verwaltung.geladen["testplugin"]
    assert "plugins" in verwaltung.plugin_ordner("testplugin").parts
    assert "workspace" in kontext.datenordner.parts, \
        "Plugindaten gehoeren in den Kundenbereich (Abschnitt 61)"


def test_entfernen_laesst_die_daten_stehen(tmp_path, verwaltung):
    verwaltung.installieren(_paket_bauen(tmp_path), bestaetigt=True)
    daten = verwaltung.datenordner("testplugin")
    daten.mkdir(parents=True, exist_ok=True)
    (daten / "merkzettel.txt").write_text("wichtig", encoding="utf-8")

    verwaltung.entfernen("testplugin")
    assert verwaltung.stand("testplugin") is None
    assert (daten / "merkzettel.txt").is_file(), "Kundendaten bleiben erhalten"


def test_fehlerhaftes_plugin_haelt_den_start_nicht_auf(tmp_path, verwaltung):
    kaputt = "def anmelden(kontext):\n    raise RuntimeError('geht nicht')\n"
    verwaltung.installieren(_paket_bauen(tmp_path, code=kaputt), bestaetigt=True)
    verwaltung.aktivieren("testplugin")
    staende = verwaltung.laden()
    assert staende[0].fehler and "geht nicht" in staende[0].fehler
    assert verwaltung.stand("testplugin").aktiv is False, \
        "ein fehlerhaftes Plugin schaltet sich selbst ab"


# -- Berechtigungen im Betrieb ------------------------------------------

class _GedaechtnisDoppel:
    def __init__(self):
        self.geschrieben = []

    def get(self, key):
        return f"Wert zu {key}"

    def list(self, limit=100):
        return []

    def set(self, key, titel, inhalt, source="", category=""):
        self.geschrieben.append((key, inhalt, source))


def _kontext(tmp_path, rechte, netz=False):
    from pkc.plugins.kontext import Pluginkontext

    manifest = Manifest.from_dict({**MANIFEST, "berechtigungen": list(rechte)})
    ordner = tmp_path / "plugindaten"
    ordner.mkdir(exist_ok=True)
    return Pluginkontext(manifest=manifest, berechtigungen=frozenset(rechte),
                         datenordner=ordner, _memory=_GedaechtnisDoppel(),
                         _netz_erlaubt=netz)


def test_ohne_recht_kein_zugriff_auf_das_gedaechtnis(tmp_path):
    kontext = _kontext(tmp_path, [])
    with pytest.raises(BerechtigungFehlt) as fehler:
        kontext.gedaechtnis_lesen("company.name")
    assert "COMPANY_MEMORY_READ" in str(fehler.value)


def test_lesen_erlaubt_heisst_nicht_schreiben_erlaubt(tmp_path):
    kontext = _kontext(tmp_path, ["COMPANY_MEMORY_READ"])
    assert kontext.gedaechtnis_lesen("company.name") == "Wert zu company.name"
    with pytest.raises(BerechtigungFehlt):
        kontext.gedaechtnis_schreiben("company.name", "Name", "Fremde GmbH")


def test_netzzugriff_scheitert_im_offlinebetrieb(tmp_path):
    """Die Berechtigung allein genuegt nicht - der Modus entscheidet mit."""
    kontext = _kontext(tmp_path, ["NETWORK_ACCESS"], netz=False)
    with pytest.raises(BerechtigungFehlt) as fehler:
        kontext.netz_abrufen("https://example.org/")
    assert "ohne Netzzugriff" in str(fehler.value)


def test_plugin_schreibt_nur_in_seinen_eigenen_ordner(tmp_path):
    kontext = _kontext(tmp_path, ["FILE_WRITE"])
    ziel = kontext.datei_schreiben("bericht.txt", "Inhalt")
    assert ziel.parent == kontext.datenordner
    with pytest.raises(BerechtigungFehlt):
        kontext.datei_schreiben("../../heimlich.txt", "Inhalt")


# -- Zusammenspiel mit der Dateiausgabe (E4 und E5) ---------------------

def test_beispielplugin_ergaenzt_ein_ausgabeformat(tmp_path, verwaltung, portable_root):
    """Der Fall aus E5.123: neues Plugin, neue Faehigkeit, ohne neuen Programmstand."""
    from pathlib import Path

    from pkc.artefakte import Artefaktwerk, abmelden, formate

    quelle = Path(__file__).resolve().parents[1] / "examples" / "plugin_html"
    paket = packen(quelle, tmp_path / "html_export",
                   json.loads((quelle / "manifest.json").read_text(encoding="utf-8")))
    try:
        verwaltung.installieren(paket, bestaetigt=True)
        verwaltung.aktivieren("html_export")
        verwaltung.laden()

        assert "html" in {s.kuerzel for s in formate()}
        werk = Artefaktwerk(portable_root)
        artefakt = werk.erzeugen("## Ergebnis\nAlles geprueft.", "html", name="Bericht")
        text = artefakt.pfad.read_text(encoding="utf-8")
        assert "<h3>Ergebnis</h3>" in text and "Alles geprueft." in text
    finally:
        abmelden("html")


def test_installation_bleibt_unter_der_uebergebenen_wurzel(tmp_path, verwaltung,
                                                           portable_root):
    """Nichts wird ausserhalb des Datentraegers abgelegt.

    Anlass: in einer Zwischenfassung lag der Pluginordner beim Programmcode.
    Bei getrennter Datenablage - und in den Tests - wurde dadurch in das
    Quellverzeichnis geschrieben. Genau das darf nicht passieren
    (Masterprompt 20: keine unkontrollierte Ablage ausserhalb).
    """
    verwaltung.installieren(_paket_bauen(tmp_path), bestaetigt=True)
    ordner = verwaltung.plugin_ordner("testplugin")
    assert ordner.is_relative_to(portable_root.root), \
        f"Plugin landete ausserhalb der Wurzel: {ordner}"


def test_ein_dateiformat_zaehlt_als_faehigkeit(tmp_path, verwaltung, portable_root):
    """Ein Plugin muss kein Werkzeug anmelden, um etwas beizutragen.

    Anlass: die Systempruefung meldete "0 zusaetzliche Faehigkeiten", obwohl
    das Plugin gerade ein Ausgabeformat ergaenzt hatte. Gezaehlt wurden nur
    Werkzeuge.
    """
    import json as _json
    from pathlib import Path

    from pkc.artefakte import abmelden

    quelle = Path(__file__).resolve().parents[1] / "examples" / "plugin_html"
    paket = packen(quelle, tmp_path / "html_export",
                   _json.loads((quelle / "manifest.json").read_text(encoding="utf-8")))
    try:
        verwaltung.installieren(paket, bestaetigt=True)
        verwaltung.aktivieren("html_export")
        verwaltung.laden()
        assert verwaltung.beitraege() == ["Dateiformat html"]
    finally:
        abmelden("html")
