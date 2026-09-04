"""Fachliche Testfaelle (Masterprompt 47).

**Was geprueft wird:** dass die lokale Recherche zu jedem der geforderten
Sachverhalte das fachlich passende Material findet - also das richtige
Fachmodul, die richtigen Stichworte und, soweit im Bestand vorhanden, die
richtige Norm.

**Was NICHT geprueft wird:** die Qualitaet der ausformulierten Antwort. Dafuer
braucht es ein Sprachmodell; in der Entwicklungsumgebung stand keines zur
Verfuegung. Dieser Schritt ist in docs/ABNAHME.md als manueller Abnahmepunkt
beschrieben und dort mit denselben Faellen hinterlegt.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pytest

from test_controller import make_controller

TESTCASES = json.loads(
    (Path(__file__).resolve().parents[1] / "src" / "profiles" / "buchhalter" /
     "testcases.json").read_text(encoding="utf-8")
)
FAELLE = TESTCASES["faelle"]


def normalise(text: str) -> str:
    """Vergleich ohne Umlaut-, Schreibweisen- und Umbruchunterschiede."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    for a, b in (("ae", "a"), ("oe", "o"), ("ue", "u"), ("ss", "s")):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text)


def norm_matcher(norm: str) -> re.Pattern[str]:
    """Baut ein Suchmuster fuer eine Norm wie "§ 6 EStG".

    Es muss auch dann passen, wenn im Text Absatz- und Satzangaben stehen
    ("§ 6 Abs. 2 EStG") oder mehrere Paragraphen zusammengefasst sind
    ("§§ 6, 7 EStG"). Massgeblich ist: die Paragraphennummer und das Gesetz
    stehen im selben Zitat.
    """
    match = re.match(r"§+\s*(?P<nummer>\d+[a-z]?)\s*(?P<gesetz>[A-Za-zÄÖÜäöü]+)", norm.strip())
    if not match:
        return re.compile(re.escape(normalise(norm)))
    nummer = re.escape(match.group("nummer"))
    gesetz = re.escape(normalise(match.group("gesetz")))
    return re.compile(rf"§[§\s]*[\d,\sa-z]*\b{nummer}\b[^§]{{0,60}}?{gesetz}")


@pytest.fixture(scope="module")
def recherche(tmp_path_factory):
    """Eine einmal aufgebaute Wissensbasis fuer alle Faelle."""
    from pkc.paths import Paths

    root = tmp_path_factory.mktemp("fachfaelle")
    paths = Paths(root)
    paths.ensure_runtime_dirs()
    paths.write_marker()
    controller = make_controller(paths)
    controller.bootstrap()
    yield controller
    controller.shutdown()


def test_all_required_cases_are_present():
    """Alle in Masterprompt 47 geforderten Faelle sind hinterlegt."""
    namen = normalise(" ".join(f["name"] for f in FAELLE))
    for gefordert in [
        "normale eingangsrechnung", "fehlerhafte rechnung",
        "innergemeinschaftlicher erwerb", "innergemeinschaftliche lieferung",
        "reverse charge", "kleinunternehmer", "vorsteuer", "e-rechnung",
        "anlagegut", "abschreibung", "skonto", "gutschrift", "forderungsausfall",
        "rechnungsabgrenzung", "ruckstellung", "vertragsstrafe", "anzahlung",
    ]:
        assert normalise(gefordert) in namen, f"Testfall fehlt: {gefordert}"
    assert len(FAELLE) >= 18


@pytest.mark.parametrize("fall", FAELLE, ids=[f["id"] for f in FAELLE])
def test_local_research_finds_relevant_material(recherche, fall):
    hits = recherche.searcher.search(fall["frage"], top_k=8)
    assert hits, f"{fall['id']}: die lokale Recherche fand nichts"

    gefunden = normalise(" ".join(f"{h.title} {h.heading} {h.text}" for h in hits))
    fehlend = [
        wort for wort in fall["erwartete_stichworte"]
        if normalise(wort) not in gefunden
    ]
    assert not fehlend, (
        f"{fall['id']} ({fall['name']}): erwartete Stichworte nicht im gefundenen "
        f"Material: {fehlend}"
    )


@pytest.mark.parametrize(
    "fall", [f for f in FAELLE if f["erwartete_normen"]],
    ids=[f["id"] for f in FAELLE if f["erwartete_normen"]],
)
def test_expected_norms_appear_in_material(recherche, fall):
    """Mindestens eine der erwarteten Normen muss im Material vorkommen.

    Geprueft wird das gesamte Fundstellenmaterial, wie es auch dem Modell und
    dem Nutzer geliefert wird: Fundstellenangabe, Ueberschrift und Text.
    """
    hits = recherche.searcher.search(fall["frage"], top_k=10)
    gefunden = normalise(
        " ".join(f"{h.reference} {h.citation} {h.heading} {h.text}" for h in hits)
    )
    treffer = [n for n in fall["erwartete_normen"] if norm_matcher(n).search(gefunden)]
    assert treffer, (
        f"{fall['id']} ({fall['name']}): keine der erwarteten Normen "
        f"{fall['erwartete_normen']} im gefundenen Material"
    )


@pytest.mark.parametrize("fall", FAELLE[:6], ids=[f["id"] for f in FAELLE[:6]])
def test_answers_carry_sources_and_knowledge_date(recherche, fall):
    """Jede Antwort enthaelt Quellen, Wissensstand und Freigabehinweis."""
    outcome = recherche.ask(fall["frage"])
    text = outcome.answer.text
    assert "QUELLEN" in text
    assert "WISSENSSTAND" in text
    assert outcome.answer.references
    # Freigabehinweis nur, wenn ein Modell geantwortet hat
    if outcome.answer.model_answered:
        assert "FREIGABEBEDARF" in text
