"""Vorlagen: verwalten, fuellen, erzeugen.

Der Bereich „Vorlagen" war bisher ein Schild an einer leeren Tuer. Hier
steht, was hinter der Tuer passiert - und vor allem, was passiert, wenn
etwas fehlt.

Der Kernsatz, um den die meisten Tests kreisen: **ein Platzhalter ohne
Wert bleibt stehen.** Er wird nicht durch Leere ersetzt. Ein Brief mit
„Sehr geehrte Damen und Herren der {{firma.name}}," faellt auf; einer, in
dem der Name stillschweigend fehlt, geht raus.
"""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest

from pkc.artefakte import Artefaktwerk
from pkc.vorlagen import (
    VorlagenFehler, Vorlagenspeicher, Vorlagenwerk, finden, fuellen,
    kopfzeilen_lesen, sammeln, uebernehmen,
)

RUMPF = (
    "# Brief an {{firma.name}}\n\n"
    "{{ort}}, den {{datum}}\n\n"
    "Sehr geehrte Damen und Herren,\n\n"
    "{{anliegen}}\n"
)


@pytest.fixture
def speicher(portable_root):
    return Vorlagenspeicher(portable_root)


@pytest.fixture
def werk(portable_root, speicher):
    return Vorlagenwerk(speicher, Artefaktwerk(portable_root,
                                               profil="Buchhalter"))


class Gedaechtnis:
    """Ein Doppel des Unternehmensgedaechtnisses - nur was hier zaehlt."""

    def __init__(self, eintraege):
        self._eintraege = eintraege

    def list(self, status="active"):
        return [e for e in self._eintraege if e.status == status]


class Eintrag:
    def __init__(self, mem_key, content, status="active"):
        self.mem_key = mem_key
        self.content = content
        self.status = status


# -- Platzhalter ---------------------------------------------------------

def test_platzhalter_werden_gefunden():
    assert finden("a {{firma.name}} b {{ datum }} c {{firma.name}}") == \
        ["firma.name", "datum"]


def test_was_fehlt_bleibt_stehen():
    """Der wichtigste Test dieser Datei."""
    fuellung = fuellen(RUMPF, {"firma": {"name": "TechMove GmbH"}})
    assert "TechMove GmbH" in fuellung.text
    assert "{{anliegen}}" in fuellung.text, \
        "ein Platzhalter ohne Wert darf nicht verschwinden"
    assert "anliegen" in fuellung.offen
    assert not fuellung.vollstaendig


def test_ein_leerer_wert_gilt_nicht_als_wert():
    """Sonst waere die Stelle leer statt sichtbar offen."""
    fuellung = fuellen("Hallo {{name}}", {"name": "   "})
    assert "{{name}}" in fuellung.text
    assert fuellung.offen == ["name"]


def test_verschachtelt_und_flach_beantworten_denselben_platzhalter():
    verschachtelt = fuellen("{{firma.name}}", {"firma": {"name": "A"}})
    flach = fuellen("{{firma.name}}", {"firma.name": "A"})
    assert verschachtelt.text == flach.text == "A"


def test_eine_struktur_ist_kein_wert():
    """{{firma}} auf ein ganzes Verzeichnis zu setzen ergaebe Unsinn."""
    fuellung = fuellen("{{firma}}", {"firma": {"name": "A"}})
    assert fuellung.text == "{{firma}}"
    assert fuellung.offen == ["firma"]


def test_die_vorschau_hebt_offene_stellen_hervor():
    fuellung = fuellen("Hallo {{name}}", {})
    assert "{{name}}" not in fuellung.vorschau()
    assert "name" in fuellung.vorschau()


def test_der_bericht_nennt_jeden_offenen_platzhalter_einmal():
    fuellung = fuellen("{{a}} {{b}} {{a}}", {})
    bericht = fuellung.bericht()
    assert bericht.count("a") >= 1 and "b" in bericht
    assert bericht.count("a,") <= 1


def test_ohne_offene_stellen_gibt_es_keinen_bericht():
    assert fuellen("Hallo {{name}}", {"name": "Welt"}).bericht() == ""


# -- Speicher ------------------------------------------------------------

def test_eine_vorlage_wird_aufgenommen_und_wiedergefunden(speicher):
    vorlage = speicher.aufnehmen("Brief an den Mandanten", RUMPF,
                                 kategorie="Korrespondenz")
    wieder = speicher.holen(vorlage.kennung)
    assert wieder is not None
    assert wieder.name == "Brief an den Mandanten"
    assert wieder.rumpf == RUMPF
    assert "firma.name" in wieder.platzhalter


def test_der_rumpf_liegt_als_lesbare_datei_daneben(speicher, portable_root):
    """Portabel heisst: die Daten sind auch ohne das Programm etwas wert."""
    vorlage = speicher.aufnehmen("Brief", RUMPF)
    datei = portable_root.get("vorlagen") / f"{vorlage.kennung}.md"
    assert datei.is_file()
    assert datei.read_text(encoding="utf-8") == RUMPF


def test_eine_leere_vorlage_wird_abgelehnt(speicher):
    with pytest.raises(VorlagenFehler):
        speicher.aufnehmen("Leer", "   ")


def test_zwei_vorlagen_mit_gleichem_namen_bekommen_eigene_kennungen(speicher):
    erste = speicher.aufnehmen("Brief", RUMPF)
    zweite = speicher.aufnehmen("Brief", RUMPF + "\nZusatz")
    assert erste.kennung != zweite.kennung
    assert speicher.holen(erste.kennung).rumpf == RUMPF
    assert len(speicher.liste()) == 2


def test_vorlagen_liegen_im_kundenbereich(portable_root, speicher):
    """Abschnitt 61: eine Vorlage von Kunde A gehoert nicht zu Kunde B."""
    speicher.aufnehmen("Brief", RUMPF)
    ordner = portable_root.get("vorlagen")
    assert "workspace" in ordner.parts, \
        "Vorlagen gehoeren in den Kundenbereich, nicht in den Programmordner"


def test_suche_und_kategorien(speicher):
    speicher.aufnehmen("Mandantenbrief", RUMPF, kategorie="Korrespondenz")
    speicher.aufnehmen("Monatsabschluss", RUMPF, kategorie="Abschluss")
    assert speicher.kategorien() == ["Abschluss", "Korrespondenz"]
    assert [v.name for v in speicher.liste(kategorie="Abschluss")] == \
        ["Monatsabschluss"]
    assert [v.name for v in speicher.liste(suche="mandant")] == \
        ["Mandantenbrief"]


def test_eine_eigene_vorlage_laesst_sich_entfernen(speicher, portable_root):
    vorlage = speicher.aufnehmen("Brief", RUMPF)
    assert speicher.entfernen(vorlage.kennung) is True
    assert speicher.holen(vorlage.kennung) is None
    assert not (portable_root.get("vorlagen") / f"{vorlage.kennung}.md").exists()


def test_eine_mitgelieferte_vorlage_laesst_sich_nicht_entfernen(speicher):
    """Ein Knopf, dessen Wirkung nicht haelt, ist schlimmer als keiner."""
    vorlage = speicher.aufnehmen("Brief", RUMPF, herkunft="mitgeliefert")
    with pytest.raises(VorlagenFehler) as fehler:
        speicher.entfernen(vorlage.kennung)
    assert "mitgeliefert" in str(fehler.value)
    assert speicher.holen(vorlage.kennung) is not None


def test_eine_kennung_kann_nicht_aus_dem_ordner_ausbrechen(speicher,
                                                           portable_root):
    """Das Verzeichnis ist eine Datei - jemand kann sie geaendert haben."""
    with pytest.raises(VorlagenFehler):
        speicher._rumpf_datei("../../config/settings")


def test_ein_beschaedigtes_verzeichnis_macht_den_bereich_nicht_unbenutzbar(
        speicher, portable_root):
    speicher.aufnehmen("Brief", RUMPF)
    (portable_root.get("vorlagen") / "verzeichnis.json").write_text(
        "{kaputt", encoding="utf-8")
    assert speicher.liste() == []
    assert speicher.aufnehmen("Neu", RUMPF) is not None


# -- Aufnehmen aus einer Datei -------------------------------------------

def test_eine_textdatei_wird_zur_vorlage(speicher, tmp_path):
    datei = tmp_path / "eigener_brief.md"
    datei.write_text(
        "---\nname: Eigener Brief\nkategorie: Korrespondenz\n"
        "format: pdf\n---\n" + RUMPF, encoding="utf-8")
    vorlage = speicher.aus_datei(datei)
    assert vorlage.name == "Eigener Brief"
    assert vorlage.kategorie == "Korrespondenz"
    assert vorlage.format == "pdf"
    assert vorlage.rumpf.startswith("# Brief an")
    assert vorlage.herkunft == "eigen"


def test_eine_worddatei_wird_mit_begruendung_abgelehnt(speicher, tmp_path):
    """Lieber ein klarer Satz als ein Ergebnis ohne Formatierung."""
    datei = tmp_path / "vorlage.docx"
    datei.write_bytes(b"PK\x03\x04egal")
    with pytest.raises(VorlagenFehler) as fehler:
        speicher.aus_datei(datei)
    text = str(fehler.value)
    assert ".docx" in text or "docx" in text
    assert "Textdatei" in text, "der Satz muss sagen, was stattdessen geht"


def test_kopfzeilen_ohne_kopf_geben_den_text_unveraendert_zurueck():
    kopf, rumpf = kopfzeilen_lesen("# Ohne Kopf\n")
    assert kopf == {} and rumpf == "# Ohne Kopf\n"


# -- Werte ---------------------------------------------------------------

def test_werte_kommen_aus_dem_gedaechtnis():
    gedaechtnis = Gedaechtnis([Eintrag("company.name", "TechMove GmbH")])
    werte = sammeln(gedaechtnis)
    assert werte["company.name"] == "TechMove GmbH"
    assert werte["firma.name"] == "TechMove GmbH", \
        "der deutsche Platzhalter muss genauso gehen"


def test_archivierte_eintraege_fuellen_nichts():
    gedaechtnis = Gedaechtnis([
        Eintrag("company.name", "Alte GmbH", status="archived")])
    assert "firma.name" not in sammeln(gedaechtnis)


def test_die_eingabe_des_menschen_hat_vorrang():
    gedaechtnis = Gedaechtnis([Eintrag("company.name", "Aus dem Gedaechtnis")])
    werte = sammeln(gedaechtnis, {"firma.name": "Von Hand"})
    assert werte["firma.name"] == "Von Hand"


def test_das_datum_kommt_von_selbst():
    werte = sammeln(heute=date(2026, 9, 9))
    assert werte["datum"] == "09.09.2026"
    assert werte["jahr"] == "2026"
    assert werte["monat"] == "September"


# -- Vorschau und Erzeugen -----------------------------------------------

def test_die_vorschau_erzeugt_noch_keine_datei(werk, speicher, portable_root):
    vorlage = speicher.aufnehmen("Brief", RUMPF)
    vorher = list(portable_root.get("artefakte").glob("*"))
    vorschau = werk.vorschau(vorlage.kennung, {"anliegen": "Bitte pruefen."})
    assert "Bitte pruefen." in vorschau.text
    assert list(portable_root.get("artefakte").glob("*")) == vorher, \
        "die Vorschau darf nichts schreiben"


def test_die_vorschau_nennt_die_offenen_stellen(werk, speicher):
    vorlage = speicher.aufnehmen("Brief", RUMPF)
    vorschau = werk.vorschau(vorlage.kennung)
    assert set(vorschau.offen) == {"firma.name", "ort", "anliegen"}
    assert not vorschau.vollstaendig
    assert "Platzhalter" in vorschau.hinweis


def test_aus_einer_vorlage_wird_eine_datei(werk, speicher):
    vorlage = speicher.aufnehmen("Brief", RUMPF, format="md")
    ergebnis = werk.erzeugen(
        vorlage.kennung,
        zusatz={"firma.name": "TechMove GmbH", "ort": "Hamburg",
                "anliegen": "Bitte pruefen."})
    text = ergebnis.artefakt.pfad.read_text(encoding="utf-8")
    assert "TechMove GmbH" in text and "Bitte pruefen." in text
    assert ergebnis.vollstaendig
    assert ergebnis.artefakt.pruefsumme, "auch hier gilt die Nachweiskette"


def test_die_erzeugte_datei_traegt_den_freigabehinweis(werk, speicher):
    """Sie sieht aus wie ein fertiges Dokument. Sie ist keins."""
    from pkc.vorlagen import FREIGABEHINWEIS

    vorlage = speicher.aufnehmen("Brief", RUMPF, format="md")
    ergebnis = werk.erzeugen(vorlage.kennung)
    text = ergebnis.artefakt.pfad.read_text(encoding="utf-8")
    assert FREIGABEHINWEIS.split(".")[0] in text


def test_offene_stellen_verhindern_das_erzeugen_nicht_und_stehen_drin(
        werk, speicher):
    vorlage = speicher.aufnehmen("Brief", RUMPF, format="md")
    ergebnis = werk.erzeugen(vorlage.kennung, zusatz={"ort": "Hamburg"})
    text = ergebnis.artefakt.pfad.read_text(encoding="utf-8")
    assert "{{anliegen}}" in text, \
        "die offene Stelle muss in der Datei sichtbar sein"
    assert "anliegen" in ergebnis.offen
    assert "anliegen" in ergebnis.artefakt.metadaten.get(
        "offene_platzhalter", "")


def test_eine_unbekannte_vorlage_wird_klar_gemeldet(werk):
    with pytest.raises(VorlagenFehler) as fehler:
        werk.erzeugen("gibtesnicht")
    assert "gibt es nicht" in str(fehler.value)


def test_eine_vorlage_ohne_rumpfdatei_wird_klar_gemeldet(werk, speicher,
                                                         portable_root):
    vorlage = speicher.aufnehmen("Brief", RUMPF)
    (portable_root.get("vorlagen") / f"{vorlage.kennung}.md").unlink()
    with pytest.raises(VorlagenFehler) as fehler:
        werk.erzeugen(vorlage.kennung)
    assert "Inhalt" in str(fehler.value)


def test_das_format_der_vorlage_wird_genommen(werk, speicher):
    vorlage = speicher.aufnehmen("Liste", "# {{jahr}}\n", format="csv")
    ergebnis = werk.erzeugen(vorlage.kennung)
    assert ergebnis.artefakt.pfad.suffix == ".csv"


def test_das_format_laesst_sich_uebersteuern(werk, speicher):
    vorlage = speicher.aufnehmen("Liste", "# {{jahr}}\n", format="csv")
    ergebnis = werk.erzeugen(vorlage.kennung, format="md")
    assert ergebnis.artefakt.pfad.suffix == ".md"


# -- Mitgelieferte Vorlagen ----------------------------------------------

class Ersatzwurzel:
    """Wurzel mit einem eigenen Assets-Ordner.

    ``assets`` gehoert zum Programm und zeigt deshalb auf den echten
    Programmordner. Ein Test, der eine mitgelieferte Vorlage aendert,
    wuerde also die ausgelieferte Datei im Projekt aendern. Diese Huelle
    lenkt nur ``assets`` um; alles andere bleibt die Testwurzel.
    """

    def __init__(self, paths, assets: Path):
        self._paths = paths
        self._assets = assets

    def get(self, name: str) -> Path:
        if name == "assets":
            return self._assets
        return self._paths.get(name)

    def __getattr__(self, name):
        return getattr(self._paths, name)


def _mitgeliefert_bereitstellen(portable_root, tmp_path) -> tuple[Path, object]:
    """Die echten mitgelieferten Vorlagen in eine Testkopie legen."""
    quelle = Path(__file__).resolve().parents[1] / "assets" / "vorlagen"
    assets = tmp_path / "programm_assets"
    ziel = assets / "vorlagen"
    ziel.mkdir(parents=True, exist_ok=True)
    for datei in quelle.glob("*.md"):
        shutil.copy2(datei, ziel / datei.name)
    return ziel, Ersatzwurzel(portable_root, assets)


def test_die_mitgelieferten_vorlagen_kommen_an(portable_root, speicher,
                                               tmp_path):
    _, wurzel = _mitgeliefert_bereitstellen(portable_root, tmp_path)
    bericht = uebernehmen(speicher, wurzel)
    assert bericht.neu >= 5
    namen = [v.name for v in speicher.liste()]
    assert "Mandantenbrief" in namen
    assert all(v.herkunft == "mitgeliefert" for v in speicher.liste())


def test_jede_mitgelieferte_vorlage_hat_platzhalter_und_beschreibung(
        portable_root, speicher, tmp_path):
    _, wurzel = _mitgeliefert_bereitstellen(portable_root, tmp_path)
    uebernehmen(speicher, wurzel)
    for vorlage in speicher.liste():
        assert vorlage.platzhalter, f"{vorlage.name} hat keine Platzhalter"
        assert vorlage.beschreibung, f"{vorlage.name} hat keine Beschreibung"
        assert vorlage.kategorie != "Allgemein" or vorlage.name == "Aktennotiz"


def test_die_uebernahme_laeuft_zweimal_ohne_dubletten(portable_root, speicher,
                                                      tmp_path):
    _, wurzel = _mitgeliefert_bereitstellen(portable_root, tmp_path)
    uebernehmen(speicher, wurzel)
    anzahl = len(speicher.liste())
    zweiter = uebernehmen(speicher, wurzel)
    assert len(speicher.liste()) == anzahl
    assert zweiter.neu == 0 and zweiter.aktualisiert == 0


def test_eine_eigene_aenderung_wird_nicht_ueberschrieben(portable_root,
                                                         speicher, tmp_path):
    """Aus Sicht des Anwenders waere das ein Datenverlust."""
    ordner, wurzel = _mitgeliefert_bereitstellen(portable_root, tmp_path)
    uebernehmen(speicher, wurzel)
    speicher.aufnehmen("Mandantenbrief", "Mein eigener Text {{firma.name}}",
                       herkunft="mitgeliefert", kennung="mandantenbrief")

    datei = ordner / "mandantenbrief.md"
    datei.write_text(datei.read_text(encoding="utf-8") + "\nNeue Zeile\n",
                     encoding="utf-8")
    bericht = uebernehmen(speicher, wurzel)

    assert speicher.holen("mandantenbrief").rumpf.startswith("Mein eigener")
    assert "Mandantenbrief" in bericht.geschont


def test_eine_neue_mitgelieferte_fassung_kommt_an(portable_root, speicher,
                                                  tmp_path):
    """Gegenprobe: ohne eigene Aenderung wird sehr wohl aktualisiert."""
    ordner, wurzel = _mitgeliefert_bereitstellen(portable_root, tmp_path)
    uebernehmen(speicher, wurzel)
    datei = ordner / "mandantenbrief.md"
    datei.write_text(datei.read_text(encoding="utf-8") + "\nNeue Zeile\n",
                     encoding="utf-8")
    bericht = uebernehmen(speicher, wurzel)
    assert bericht.aktualisiert == 1
    assert "Neue Zeile" in speicher.holen("mandantenbrief").rumpf


def test_aus_einer_mitgelieferten_vorlage_entsteht_eine_datei(
        portable_root, speicher, werk, tmp_path):
    _, wurzel = _mitgeliefert_bereitstellen(portable_root, tmp_path)
    uebernehmen(speicher, wurzel)
    ergebnis = werk.erzeugen(
        "mandantenbrief", format="md",
        zusatz={"firma.name": "X", "mandant.name": "TechMove GmbH",
                "betreff": "Jahresabschluss"})
    text = ergebnis.artefakt.pfad.read_text(encoding="utf-8")
    assert "TechMove GmbH" in text and "Jahresabschluss" in text
