"""Fachliche Widersprueche, die ohne Rechnung erkennbar sind.

**Der gemeldete Fehler.** Das Modell schrieb: *"Rueckstellung der
Lieferantenrechnungen: 8.500 EUR netto muessen in den ARAP umgebucht
werden."* Eine Rueckstellung ist eine ungewisse Verbindlichkeit und
steht auf der **Passivseite**. Ein aktiver Rechnungsabgrenzungsposten
ist ein **Aktivposten**. Die beiden haben nichts miteinander zu tun.

Solche Saetze sind nicht falsch gerechnet - sie sind falsch gedacht.
Kein Rechenwerk der Welt faengt das ab; dafuer braucht es Regeln.

**Der Massstab fuer eine Regel hier.** Sie muss ohne Kenntnis des
Einzelfalls entscheidbar sein. "Eine Rueckstellung ist kein ARAP" gilt
immer. "Diese Rueckstellung ist zu hoch" gilt nur mit Kenntnis des
Sachverhalts - so etwas steht hier nicht drin.

Jede Regel nennt ihre Grundlage. Erfunden wird nichts: wo kein
Paragraf danebensteht, steht auch keiner da.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


def umlauttolerant(muster: str) -> str:
    """Macht ein Muster unabhaengig von der Umlautschreibung.

    Die Anwendung schreibt Umlaute durchgaengig als "ue", "ae", "oe" -
    der Anwender tippt sie als "ü", "ä", "ö". Beides muss dasselbe
    Muster treffen.

    Das war der erste Fehler dieses Moduls: Die Regel gegen
    "Rueckstellung im ARAP" stand da, und der Satz, fuer den sie gebaut
    war, ging glatt durch. Ein Muster, das nur eine Schreibweise kennt,
    ist eine halbe Regel.
    """
    for laut, ersatz in (("ü", "(?:ü|ue|u)"), ("ä", "(?:ä|ae|a)"),
                         ("ö", "(?:ö|oe|o)")):
        muster = muster.replace(laut, ersatz)
    return muster


@dataclass(frozen=True)
class Regelbefund:
    regel: str
    text: str


@dataclass(frozen=True)
class Regel:
    """Eine Regel greift, wenn *beide* Muster in einem Satz stehen."""

    name: str
    eines: re.Pattern
    und: re.Pattern
    text: str
    #: Ausnahmen: steht eines dieser Muster im Satz, greift die Regel
    #: nicht. Damit bleibt ein Satz erlaubt, der den Unterschied
    #: ausdruecklich *erklaert*.
    ausser: re.Pattern | None = None


REGELN: list[Regel] = [
    Regel(
        name="rueckstellung_ist_kein_arap",
        eines=re.compile(umlauttolerant(r"rückstellung\w*"), re.IGNORECASE),
        und=re.compile(r"\bARAP\b|aktive[rn]?\s+rechnungsabgrenzung\w*",
                       re.IGNORECASE),
        text=(
            "Die Antwort bringt eine Rueckstellung mit dem aktiven "
            "Rechnungsabgrenzungsposten (ARAP) zusammen. Das passt nicht: "
            "Eine Rueckstellung ist eine ungewisse Verbindlichkeit und steht "
            "auf der Passivseite (§ 249 HGB). Ein ARAP ist ein Aktivposten "
            "fuer eine Ausgabe vor dem Abschlussstichtag, die Aufwand fuer "
            "eine bestimmte Zeit danach ist (§ 250 Abs. 1 HGB). Bitte "
            "besonders sorgfaeltig pruefen."
        ),
        # Ein Satz, der den Unterschied gerade erklaert, ist kein Fehler.
        ausser=re.compile(
            r"nicht\s+(?:in\s+den\s+|mit\s+dem\s+)?ARAP|kein\s+ARAP|"
            r"unterschied|abzugrenzen\s+von|verwechsel\w*|"
            r"im\s+Gegensatz\s+zu", re.IGNORECASE),
    ),
    Regel(
        name="rueckstellung_ist_passiv",
        eines=re.compile(umlauttolerant(r"rückstellung\w*"), re.IGNORECASE),
        und=re.compile(r"aktivposten|auf\s+der\s+aktivseite|"
                       r"aktiviert\s+werden", re.IGNORECASE),
        text=(
            "Die Antwort bezeichnet eine Rueckstellung als Aktivposten. "
            "Rueckstellungen stehen auf der Passivseite (§ 249 HGB). Bitte "
            "besonders sorgfaeltig pruefen."
        ),
        ausser=re.compile(r"kein\s+aktivposten|nicht\s+aktiviert", re.IGNORECASE),
    ),
    Regel(
        name="prap_ist_passiv",
        eines=re.compile(r"\bPRAP\b|passive[rn]?\s+rechnungsabgrenzung\w*",
                         re.IGNORECASE),
        und=re.compile(r"aktivposten|auf\s+der\s+aktivseite", re.IGNORECASE),
        text=(
            "Die Antwort bezeichnet einen passiven Rechnungsabgrenzungsposten "
            "als Aktivposten. Der PRAP steht auf der Passivseite "
            "(§ 250 Abs. 2 HGB). Bitte besonders sorgfaeltig pruefen."
        ),
        ausser=re.compile(r"kein\s+aktivposten", re.IGNORECASE),
    ),
]


def pruefe_regeln(text: str) -> list[Regelbefund]:
    """Sucht nach fachlichen Widerspruechen - satzweise.

    Satzweise, weil es um den Zusammenhang geht. Stehen "Rueckstellung"
    und "ARAP" in zwei verschiedenen Absaetzen einer langen Antwort,
    sagt das nichts; im selben Satz sagt es viel.
    """
    befunde: list[Regelbefund] = []
    getroffen: set[str] = set()

    for satz in re.split(r"(?<=[.;!?])\s+|\n", text or ""):
        for regel in REGELN:
            if regel.name in getroffen:
                continue
            if not (regel.eines.search(satz) and regel.und.search(satz)):
                continue
            if regel.ausser is not None and regel.ausser.search(satz):
                continue
            getroffen.add(regel.name)
            befunde.append(Regelbefund(regel=regel.name, text=regel.text))
    return befunde
