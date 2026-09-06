"""RAG-Orchestrierung: Frage -> Recherche -> Kontext -> Modell -> Antwort.

Was diese Schicht zusaetzlich leistet:

* Sie stellt sicher, dass jede Antwort einen **nachvollziehbaren
  Quellenteil** und den **Wissensstand** bekommt - auch wenn das Modell das
  vergisst.
* Sie erkennt **erfundene Fundstellennummern** und entfernt sie samt Hinweis.
* Sie kennzeichnet, wenn **keine** lokale Fundstelle vorlag.
* Sie haengt den **Freigabehinweis** an, wo das Profil ihn verlangt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

from ..llm.base import ChatMessage, LlmResponse
from ..llm.manager import LlmManager
from ..logging_setup import get_logger
from ..memory.store import MemoryEntry, MemoryStore
from ..profile import EmployeeProfile
from ..retrieval.search import Hit, HybridSearcher
from .context import ContextBuilder, ContextBundle, SourceReference, cited_numbers
from .fragetyp import Einstufung, Fragetyp, einstufen

log = get_logger(__name__)

#: Kennzeichen im Kontext: es wurde bewusst nicht recherchiert.
KEINE_RECHERCHE = "Recherche: nicht durchgefuehrt, dies ist Konversation"


@dataclass
class AnswerResult:
    text: str
    references: list[SourceReference] = field(default_factory=list)
    used_references: list[SourceReference] = field(default_factory=list)
    context: ContextBundle | None = None
    llm: LlmResponse | None = None
    mode: str = "OFFLINE"
    knowledge_date: str | None = None
    warnings: list[str] = field(default_factory=list)
    elapsed: float = 0.0
    #: Wie die Frage eingestuft wurde - steuert Recherche und Antworttiefe.
    einstufung: Einstufung | None = None

    @property
    def fragetyp(self) -> Fragetyp:
        return self.einstufung.typ if self.einstufung else Fragetyp.FACHLICH

    @property
    def model_answered(self) -> bool:
        return bool(self.llm and self.llm.is_generated)


class RagEngine:
    """Verbindet Recherche, Gedaechtnis, Profil und Sprachmodell."""

    def __init__(
        self,
        profile: EmployeeProfile,
        searcher: HybridSearcher,
        memory: MemoryStore,
        llm: LlmManager,
        builder: ContextBuilder | None = None,
        top_k: int = 8,
        lexical_candidates: int = 40,
        vector_candidates: int = 40,
    ):
        self.profile = profile
        self.searcher = searcher
        self.memory = memory
        self.llm = llm
        self.builder = builder or ContextBuilder()
        self.top_k = int(top_k)
        self.lexical_candidates = int(lexical_candidates)
        self.vector_candidates = int(vector_candidates)

    # -- Kontext -------------------------------------------------------
    def retrieve(self, question: str, as_of: str | None = None) -> tuple[list[Hit], list[MemoryEntry]]:
        hits = self.searcher.search(
            question, top_k=self.top_k,
            lexical_candidates=self.lexical_candidates,
            vector_candidates=self.vector_candidates,
            as_of=as_of,
        )
        # Unternehmenswissen: gezielte Treffer plus die Stammdaten
        targeted = self.memory.search(question, limit=6)
        base = self.memory.all_active_for_prompt(max_entries=25)
        seen: set[str] = set()
        entries: list[MemoryEntry] = []
        for entry in list(targeted) + list(base):
            if entry.mem_key in seen:
                continue
            seen.add(entry.mem_key)
            entries.append(entry)
        return hits, entries

    def build_messages(
        self,
        question: str,
        bundle: ContextBundle,
        history: Sequence[ChatMessage] = (),
        mode: str = "OFFLINE",
        knowledge_date: str | None = None,
        einstufung: Einstufung | None = None,
    ) -> list[ChatMessage]:
        header = [
            self.profile.system_prompt,
            "",
            "---",
            "",
            "## LAUFZEITLAGE",
            "",
            f"* Betriebsart: **{mode}**",
            f"* Lokaler Wissensstand: **{knowledge_date or 'unbekannt'}**",
            "* Es wurde ausschliesslich lokal recherchiert."
            if mode == "OFFLINE"
            else "* Lokale Recherche; Online-Funktionen stehen zusaetzlich zur Verfuegung.",
        ]
        # Ausdruecklich vermerken, ob ueberhaupt gesucht wurde. Sonst muesste
        # der Anbieter raten - und wuerde bei Konversation faelschlich
        # behaupten, es sei nichts gefunden worden.
        if einstufung is not None and not einstufung.braucht_recherche:
            header.append(f"* {KEINE_RECHERCHE} ({einstufung.grund})")
        if self.profile.limits:
            header += ["", "## GRENZEN DIESER ROLLE", ""]
            header += [f"* {limit}" for limit in self.profile.limits]

        # Antworttiefe an die Art der Frage anpassen. Eine Begruessung mit dem
        # vollstaendigen Fachschema zu beantworten waere ebenso falsch wie ein
        # verwickelter Sachverhalt in zwei Saetzen.
        header += ["", "## ANTWORTTIEFE FUER DIESE NACHRICHT", ""]
        header += _tiefenanweisung(einstufung.typ if einstufung else Fragetyp.FACHLICH,
                                   self.profile)
        messages = [ChatMessage("system", "\n".join(header))]
        messages.append(ChatMessage("system", bundle.as_system_block()))
        messages.extend(history)
        messages.append(ChatMessage("user", question))
        return messages

    # -- Hauptweg ------------------------------------------------------
    def answer(
        self,
        question: str,
        history: Sequence[ChatMessage] = (),
        mode: str = "OFFLINE",
        knowledge_date: str | None = None,
        as_of: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        prefer_online: bool = False,
    ) -> AnswerResult:
        # Erst einstufen, dann entscheiden, ob ueberhaupt recherchiert wird.
        # Auf "Kannst Du mir helfen?" gehoeren keine acht Fundstellen aus dem
        # Umsatzsteuerrecht - das sieht aus, als haette die Frage damit zu tun.
        einstufung = einstufen(question, hat_verlauf=bool(history))

        if einstufung.braucht_recherche:
            hits, entries = self.retrieve(question, as_of=as_of)
        else:
            hits, entries = [], self.memory.list(limit=40) if self.memory else []
        bundle = self.builder.build(hits, entries)
        messages = self.build_messages(question, bundle, history, mode,
                                       knowledge_date, einstufung)

        response = self.llm.generate(
            messages, max_tokens=max_tokens, temperature=temperature,
            prefer_online=prefer_online,
        )

        text = response.text
        warnings: list[str] = []
        valid = {ref.number for ref in bundle.references}
        cited = cited_numbers(text)
        invented = sorted(cited - valid)
        if invented:
            warnings.append(
                "Das Modell hat Fundstellennummern genannt, die es nicht gab "
                f"({', '.join(f'[{n}]' for n in invented)}). Sie wurden entfernt."
            )
            text = _strip_numbers(text, invented)
            cited = cited_numbers(text)

        used = [ref for ref in bundle.references if ref.number in cited]
        if response.is_generated and bundle.references and not used:
            warnings.append(
                "Die Antwort nennt keine der gefundenen Fundstellen. Bitte besonders "
                "sorgfaeltig pruefen."
            )
        # Abschnitt 17: Nur Sekundaerquellen tragen keine belastbare
        # steuerliche Bewertung. Das muss dastehen - sonst sieht eine
        # Antwort aus Fachmodulen genauso belegt aus wie eine aus dem
        # Gesetzestext.
        if (einstufung.typ in (Fragetyp.FACHLICH, Fragetyp.KOMPLEX)
                and bundle.references
                and all(ref.priority >= 5 for ref in bundle.references)):
            warnings.append(
                "Fuer diese Aussage liegen im lokalen Wissensbestand nur "
                "Sekundaerquellen vor (Fachmodule, keine Primaerquellen). Fuer eine "
                "belastbare steuerliche Bewertung ist die Primaerquelle zu pruefen - "
                "Gesetzestext, Verwaltungsanweisung oder Rechtsprechung."
            )

        if not bundle.has_knowledge and einstufung.braucht_recherche:
            # Nur wenn ueberhaupt gesucht wurde. Bei Smalltalk waere der
            # Hinweis irrefuehrend: es fehlt nichts, es wurde bewusst nicht
            # recherchiert.
            warnings.append(
                "Zu dieser Frage lag lokal keine Fachfundstelle vor. Die Antwort stuetzt "
                "sich nicht auf eine lokale Quelle."
            )

        text = self._append_footer(
            text, bundle, used, mode, knowledge_date, response, warnings, einstufung
        )
        return AnswerResult(
            text=text, references=bundle.references, used_references=used,
            context=bundle, llm=response, mode=mode, knowledge_date=knowledge_date,
            warnings=warnings, elapsed=response.elapsed, einstufung=einstufung,
        )

    # -- Nachbereitung -------------------------------------------------
    def _append_footer(
        self, text: str, bundle: ContextBundle, used: Sequence[SourceReference],
        mode: str, knowledge_date: str | None, response: LlmResponse,
        warnings: Sequence[str], einstufung: Einstufung | None = None,
    ) -> str:
        parts = [text.rstrip()]

        # Bei Smalltalk wurde bewusst nicht recherchiert - dann gehoert auch
        # kein Quellenabschnitt darunter.
        if einstufung is not None and not einstufung.braucht_recherche:
            shown = []
        else:
            shown = list(used) or list(bundle.references)

        if shown and not _has_section(text, "QUELLEN"):
            # Nur die Bezeichnung, nie der Auszug. Die vollstaendigen
            # Fundstellen stehen im eigenen Quellenbereich der Oberflaeche
            # bzw. unter "Recherche-Details". Frueher wurden sie ohne Modell
            # mit vollem Text angehaengt - das las sich wie eine Antwort, war
            # aber keine.
            lines = [ref.as_line() for ref in shown]
            parts.append("**QUELLEN**\n" + "\n".join(lines))
        elif not shown and (einstufung is None or einstufung.braucht_recherche):
            parts.append(
                "**QUELLEN**\nKeine lokale Fundstelle verwendet. Diese Antwort ist nicht "
                "durch eine lokale Quelle belegt."
            )

        if not _has_section(text, "WISSENSSTAND"):
            parts.append(
                "**WISSENSSTAND**\n"
                f"Lokaler Wissensstand: {knowledge_date or 'unbekannt'} · "
                f"Betriebsart: {mode} · "
                f"Antwort erzeugt durch: {response.provider}"
                f"{'' if response.is_generated else ' (kein Sprachmodell verfuegbar)'}"
            )

        if response.is_generated and not _has_section(text, "FREIGABEBEDARF"):
            parts.append(
                "**FREIGABEBEDARF**\n"
                "Fachliche Zuarbeit ohne Gewaehr. Buchungen, Meldungen und Zahlungen "
                "beduerfen der Pruefung und Freigabe durch einen verantwortlichen "
                "Menschen."
            )

        if warnings:
            parts.append("**HINWEISE DER ANWENDUNG**\n" + "\n".join(f"* {w}" for w in warnings))
        return "\n\n".join(parts)


def _has_section(text: str, name: str) -> bool:
    """Erkennt eine Abschnittsueberschrift - nicht ein zufaelliges Vorkommen des Wortes.

    "in den vorhandenen Quellen" ist keine Ueberschrift "QUELLEN"; ohne diese
    Unterscheidung wuerde der Quellenteil faelschlich weggelassen.
    """
    pattern = rf"^[ \t]*(?:\*\*|##+[ \t]*|__)?{re.escape(name)}\b"
    return re.search(pattern, text or "", re.MULTILINE | re.IGNORECASE) is not None


def _strip_numbers(text: str, numbers: Sequence[int]) -> str:
    for number in numbers:
        text = re.sub(rf"\s*\[{number}\]", "", text)
    return text


def _tiefenanweisung(typ: Fragetyp, profile) -> list[str]:
    """Sagt dem Modell, wie ausfuehrlich zu antworten ist.

    Der Auftrag (Abschnitt 9) verlangt ausdruecklich, nicht jede Nachricht
    mit derselben starren langen Vorlage zu beantworten.
    """
    if typ is Fragetyp.SMALLTALK:
        return [
            "Dies ist **keine** Fachfrage, sondern Konversation.",
            "",
            "* Antworte kurz, natuerlich und freundlich, in zwei bis fuenf Saetzen.",
            "* Verwende **kein** Fachschema und keine Abschnittsueberschriften.",
            "* Nenne **keine** Quellen - es wurde bewusst nicht recherchiert.",
            "* Wird nach deinen Faehigkeiten gefragt, nenne konkrete Beispiele "
            "aus deinem Fachgebiet und weise darauf hin, dass du bei fehlenden "
            "Angaben nachfragst.",
        ]
    if typ is Fragetyp.EINFACH:
        return [
            "Eine einfache Frage.",
            "",
            "* Antworte knapp und direkt, ohne Fachschema.",
            "* Nenne eine Fundstelle nur, wenn sie die Antwort wirklich traegt.",
        ]
    if typ is Fragetyp.FACHLICH:
        return [
            "Eine fachliche Frage ohne geschilderten Einzelfall.",
            "",
            "* Antworte zusammenhaengend und verstaendlich, in Absaetzen.",
            "* Belege tragende Aussagen mit [1], [2] usw.",
            "* Verwende nur die Abschnitte, die wirklich etwas beitragen - "
            "nicht das vollstaendige Schema.",
            "* Nenne offene Punkte nur, wenn es wirklich welche gibt.",
        ]
    abschnitte = ", ".join(getattr(profile, "answer_sections", []) or [])
    return [
        "**Fehlen entscheidende Angaben, frage gezielt nach, statt zu raten.**",
        "Stelle dann hoechstens drei nummerierte Fragen und beantworte den Rest,",
        "soweit er ohne diese Angaben beantwortbar ist. Beispiel:",
        "",
        "> Fuer die umsatzsteuerliche Beurteilung brauche ich noch zwei Angaben:",
        "> 1. In welchem Land sitzt der Lieferant?",
        "> 2. Wann wurde die Leistung ausgefuehrt?",
        "",
        "Ein geschilderter Einzelfall - hier ist die vollstaendige fachliche "
        "Wuerdigung angebracht.",
        "",
        f"* Verwende das Fachschema: {abschnitte}",
        "* Lass Abschnitte weg, zu denen du nichts Belastbares sagen kannst.",
        "* Belege tragende Aussagen mit [1], [2] usw.",
        "* Fehlen entscheidende Angaben, frage gezielt nach, statt zu raten.",
    ]
