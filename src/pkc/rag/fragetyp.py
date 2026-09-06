"""Erkennt, um welche Art Frage es sich handelt.

Hintergrund: Bisher loeste jede Nachricht eine Fachrecherche aus. Auf
"Kannst Du mir helfen?" antwortete der Buchhalter mit acht Fundstellen aus
dem Umsatzsteuerrecht. Das ist nicht nur unbrauchbar, es ist auch
irrefuehrend - es sieht aus, als haette die Frage etwas mit diesen Quellen
zu tun.

Die Einstufung entscheidet zweierlei:

* ob ueberhaupt recherchiert wird
* wie ausfuehrlich geantwortet werden soll

Sie arbeitet mit Regeln, nicht mit einem Modell. Das ist Absicht: die
Einstufung muss auch dann funktionieren, wenn kein Sprachmodell vorhanden
ist, und sie muss nachvollziehbar bleiben.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Fragetyp(str, Enum):
    """Vier Arten, wie im Auftrag (Abschnitt 9) beschrieben."""

    SMALLTALK = "SMALLTALK"
    EINFACH = "EINFACH"
    FACHLICH = "FACHLICH"
    KOMPLEX = "KOMPLEX"

    @property
    def braucht_recherche(self) -> bool:
        """Nur bei Smalltalk wird nicht recherchiert."""
        return self is not Fragetyp.SMALLTALK

    @property
    def volle_struktur(self) -> bool:
        """Nur ein komplexer Fall bekommt das vollstaendige Fachschema."""
        return self is Fragetyp.KOMPLEX


#: Reine Konversation - Begruessung, Dank, Fragen nach den Faehigkeiten.
_SMALLTALK = re.compile(
    r"^\s*("
    r"hallo|hi|hey|guten\s+(morgen|tag|abend)|moin|servus|gruess\s+gott"
    r"|danke(\s+schoen)?|vielen\s+dank|passt|alles\s+klar|ok(ay)?"
    r"|tschuess|auf\s+wiedersehen|bis\s+(spaeter|morgen)"
    r"|wer\s+bist\s+du|was\s+kannst\s+du|was\s+machst\s+du"
    r"|kannst\s+du\s+(mir\s+)?(dabei\s+)?helfen"
    r"|wie\s+funktionierst\s+du|wie\s+gehts"
    r")\b[\s\.\!\?]*$",
    re.IGNORECASE,
)

#: Fragen nach den eigenen Faehigkeiten - auch laenger formuliert.
_FAEHIGKEIT = re.compile(
    r"\b(kannst\s+du\s+mir|koennen\s+sie\s+mir|hilfst\s+du\s+mir"
    r"|wobei\s+kannst\s+du|womit\s+kannst\s+du|was\s+kannst\s+du\s+alles)\b",
    re.IGNORECASE,
)

#: Wortstaemme, die auf einen fachlichen Sachverhalt hindeuten.
#
# Bewusst OHNE Wortgrenzen: das Deutsche setzt zusammen. "Eingangsrechnungen"
# enthaelt "rechnung", "Umsatzsteuervoranmeldung" enthaelt "steuer",
# "Buchungsbeleg" enthaelt "beleg". Mit \b davor wuerde nichts davon greifen -
# genau daran ist die erste Fassung gescheitert.
_FACHLICH = re.compile(
    r"(rechnung|vorsteuer|umsatzsteuer|mwst|buchen|buchung|buchhalt"
    r"|konto|konten|kontier|skr\d*|beleg|abschreibung|bilanz|abschluss"
    r"|steuer|finanzamt|reverse\s*charge|innergemeinschaft"
    r"|kleinunternehmer|gobd|aufbewahr|frist|paragraf|paragraph|§"
    r"|lieferant|debitor|kreditor|zahlung|mahnung|skonto"
    r"|vermoegen|rueckstellung|abgrenzung|erloes|aufwand"
    r"|xrechnung|zugferd|datev|kasse|inventur|anlagegut"
    # Diese kurz und mehrdeutig - daher mit Wortgrenze:
    r"|\b(ust|afa|gewinn|verlust|kunde|kunden)\b)",
    re.IGNORECASE,
)

#: Hinweise auf einen konkreten, zu wuerdigenden Einzelfall.
_SACHVERHALT = re.compile(
    r"\b(wir\s+haben|ich\s+habe|unser\s+|uns\s+|erhalten|bekommen|gekauft"
    r"|geleast|verkauft|bezahlt|gestellt|ausgestellt|liegt\s+vor"
    r"|wie\s+buche\s+ich|wie\s+buchen\s+wir|wie\s+ist\s+das\s+zu"
    r"|was\s+ist\s+zu\s+tun|wie\s+gehe\s+ich\s+vor)\b",
    re.IGNORECASE,
)


@dataclass
class Einstufung:
    typ: Fragetyp
    grund: str

    @property
    def braucht_recherche(self) -> bool:
        return self.typ.braucht_recherche

    def as_dict(self) -> dict:
        return {"typ": self.typ.value, "grund": self.grund,
                "recherche": self.braucht_recherche}


def einstufen(frage: str, hat_verlauf: bool = False) -> Einstufung:
    """Stuft eine Nachricht ein.

    ``hat_verlauf`` sagt, ob es vorangehende Nachrichten gibt. Eine kurze
    Antwort wie "Ja" ist ohne Verlauf Smalltalk, mitten in einem fachlichen
    Gespraech aber die Antwort auf eine Rueckfrage - und dann darf sie nicht
    als Geplauder behandelt werden.
    """
    text = (frage or "").strip()
    if not text:
        return Einstufung(Fragetyp.SMALLTALK, "leere Eingabe")

    woerter = len(text.split())

    # Kurze Bestaetigungen im laufenden Gespraech gehoeren zum Sachverhalt.
    if hat_verlauf and woerter <= 4 and not _FACHLICH.search(text):
        return Einstufung(
            Fragetyp.FACHLICH,
            "kurze Antwort im laufenden Gespraech - bezieht sich auf die Rueckfrage",
        )

    fachlich = bool(_FACHLICH.search(text))
    sachverhalt = bool(_SACHVERHALT.search(text))

    if _SMALLTALK.match(text):
        return Einstufung(Fragetyp.SMALLTALK, "Begruessung oder Verabschiedung")

    # "Kannst Du mir bei meiner Buchhaltung helfen?" ist eine Frage nach den
    # Faehigkeiten, keine Buchhaltungsfrage - obwohl "buchhalt" darin steht.
    # Erst wenn ein konkreter Sachverhalt geschildert wird, ist es fachlich.
    if _FAEHIGKEIT.search(text) and not sachverhalt:
        return Einstufung(Fragetyp.SMALLTALK, "Frage nach den Faehigkeiten")

    if not fachlich and not sachverhalt:
        return Einstufung(Fragetyp.EINFACH, "kein fachlicher Anhaltspunkt erkennbar")

    # Ein geschilderter Einzelfall mit einigem Umfang ist ein komplexer Fall.
    if fachlich and sachverhalt and woerter >= 12:
        return Einstufung(Fragetyp.KOMPLEX, "geschilderter Einzelfall mit Fachbezug")
    if fachlich and text.count("?") >= 2:
        return Einstufung(Fragetyp.KOMPLEX, "mehrere fachliche Fragen auf einmal")

    return Einstufung(Fragetyp.FACHLICH, "fachlicher Begriff erkannt")
