"""Das Protokoll zwischen Anwendung und Plugin-Vorgang (E5.108).

Ein Plugin laeuft in einem **eigenen Vorgang**. Beide Seiten reden ueber
Standardeingabe und Standardausgabe, je Nachricht eine Zeile JSON. Das ist
absichtlich schlicht: es braucht keine Netzverbindung, keinen Port und keine
zusaetzliche Bibliothek, und es funktioniert auch in der gepackten EXE.

Wer spricht wann?

* Die Anwendung ruft im Plugin etwas auf: ``anmelden``, ``werkzeug``,
  ``format``.
* Das Plugin fragt bei der Anwendung nach, wenn es etwas braucht, das
  Rechte verlangt: ``anfrage``. Die Antwort kommt als ``antwort``.

Der zweite Punkt ist der eigentliche Gewinn: das Plugin hat selbst **keinen**
Zugriff auf Datenbank, Tresor oder Unternehmensdaten. Es kann nur fragen -
und die Anwendung entscheidet anhand der erteilten Berechtigungen.
"""

from __future__ import annotations

import base64
import json
from typing import Any

#: Groessengrenze je Nachricht. Ein Plugin soll dem Hauptvorgang nicht
#: beliebig viel Speicher aufdraengen koennen.
HOECHSTLAENGE = 32 * 1024 * 1024

#: Arten von Nachrichten der Anwendung an das Plugin.
AUFTRAEGE = ("anmelden", "werkzeug", "format", "ende")

#: Arten von Nachrichten des Plugins an die Anwendung.
ANTWORTEN = ("ergebnis", "fehler", "anfrage", "bereit", "protokoll")


class ProtokollFehler(RuntimeError):
    """Die Gegenstelle hat etwas geschickt, das nicht zum Protokoll passt."""


def schreiben(strom, nachricht: dict) -> None:
    """Schreibt eine Nachricht als eine Zeile."""
    roh = json.dumps(nachricht, ensure_ascii=False, default=str)
    if len(roh) > HOECHSTLAENGE:
        raise ProtokollFehler(
            f"Die Nachricht ist zu gross ({len(roh)} Zeichen, erlaubt "
            f"{HOECHSTLAENGE})."
        )
    strom.write(roh + "\n")
    strom.flush()


def lesen(strom) -> dict | None:
    """Liest eine Nachricht. ``None`` heisst: die Gegenstelle ist weg."""
    zeile = strom.readline()
    if not zeile:
        return None
    zeile = zeile.strip()
    if not zeile:
        return {}
    if len(zeile) > HOECHSTLAENGE:
        raise ProtokollFehler("Die Gegenstelle hat eine zu grosse Nachricht geschickt.")
    try:
        nachricht = json.loads(zeile)
    except json.JSONDecodeError as fehler:
        raise ProtokollFehler(f"Unlesbare Nachricht: {zeile[:120]}") from fehler
    if not isinstance(nachricht, dict):
        raise ProtokollFehler("Eine Nachricht muss eine Zuordnung sein.")
    return nachricht


# -- Umwandlung von Werten ----------------------------------------------

def bytes_hinein(daten: bytes) -> str:
    """Bytes wandern als Text ueber die Leitung."""
    return base64.b64encode(daten).decode("ascii")


def bytes_heraus(text: str) -> bytes:
    try:
        return base64.b64decode(text.encode("ascii"), validate=True)
    except Exception as fehler:                  # pragma: no cover - defensiv
        raise ProtokollFehler("Unbrauchbare Binaerdaten empfangen.") from fehler


def dokument_hinein(dokument) -> dict:
    """Ein Dokument (Erweiterung E4) als schlichte Zuordnung."""
    return {
        "titel": dokument.titel,
        "angaben": dict(dokument.angaben),
        "bloecke": [
            {"art": b.art, "text": b.text, "ebene": b.ebene,
             "punkte": list(b.punkte), "zeilen": [list(z) for z in b.zeilen]}
            for b in dokument.bloecke
        ],
    }


def dokument_heraus(daten: dict):
    """Baut das Dokument im Plugin-Vorgang wieder auf."""
    from ..artefakte.modell import Block, Dokument

    dokument = Dokument(titel=str(daten.get("titel", "")),
                        angaben=dict(daten.get("angaben", {})))
    for eintrag in daten.get("bloecke", []):
        dokument.bloecke.append(Block(
            art=str(eintrag.get("art", "absatz")),
            text=str(eintrag.get("text", "")),
            ebene=int(eintrag.get("ebene", 1)),
            punkte=[str(p) for p in eintrag.get("punkte", [])],
            zeilen=[[str(z) for z in zeile] for zeile in eintrag.get("zeilen", [])],
        ))
    return dokument


def einfach(wert: Any) -> Any:
    """Nur einfache Werte gehen ueber die Leitung.

    Beliebige Objekte koennten im anderen Vorgang gar nicht entstehen - und
    ein Plugin soll auch keine Objekte der Anwendung in die Hand bekommen.
    """
    if wert is None or isinstance(wert, (bool, int, float, str)):
        return wert
    if isinstance(wert, (list, tuple)):
        return [einfach(w) for w in wert]
    if isinstance(wert, dict):
        return {str(k): einfach(v) for k, v in wert.items()}
    if hasattr(wert, "as_dict"):
        return einfach(wert.as_dict())
    return str(wert)
