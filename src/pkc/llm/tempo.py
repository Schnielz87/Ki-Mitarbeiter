"""Antworttempo: wieviel Arbeit eine Antwort kosten darf.

Warum es dieses Modul gibt: die Wartezeit auf eine Antwort entsteht an drei
Stellen, und nur eine davon ist das Modell selbst.

1. **Das Modell laden.** Mehrere Gigabyte von der Platte - einmalig, aber
   bei der ersten Frage schmerzhaft. Dagegen hilft, den Dienst vorher zu
   starten, nicht ihn kleiner zu machen.
2. **Den Prompt verarbeiten** (Vorlauf). Jedes Token des Kontextes muss
   durch das Modell, bevor das erste Wort der Antwort erscheint. Auf reiner
   CPU sind das je nach Modell 30 bis 150 Token je Sekunde. Ein Kontext von
   2700 Token bedeutet also 20 bis 90 Sekunden Warten, **bevor** ueberhaupt
   etwas zu sehen ist.
3. **Die Antwort erzeugen.** Hier zaehlt jedes Token einzeln. 1024 erlaubte
   Token bei 4 Token je Sekunde sind vier Minuten.

Gemessen an einem echten Aufbau lag der Kontext bei rund 2700 Token und die
erlaubte Antwortlaenge bei 1024. Beides zusammen ist der Grund, warum eine
Antwort Minuten dauerte - und beides ist eine Einstellung, keine
Naturkonstante.

Deshalb hier drei benannte Stufen statt fuenf einzelner Zahlen, die niemand
aufeinander abstimmen kann. Wer es genauer will, stellt die Einzelwerte
weiterhin von Hand ein; die Stufe ist nur eine abgestimmte Vorgabe.
"""

from __future__ import annotations

STUFEN = {
    "schnell": {
        "label": "Schnell",
        "max_output_tokens": 320,
        "kontext_tokens": 900,
        "unternehmen_tokens": 300,
        "top_k": 3,
        "verlauf": 2,
        "beschreibung": "Kurze, belegte Antwort. Am wenigsten Wartezeit.",
    },
    "ausgewogen": {
        "label": "Ausgewogen",
        "max_output_tokens": 600,
        "kontext_tokens": 1600,
        "unternehmen_tokens": 500,
        "top_k": 5,
        "verlauf": 4,
        "beschreibung": "Vollstaendige Fachantwort bei vertretbarer Wartezeit.",
    },
    "ausfuehrlich": {
        "label": "Ausfuehrlich",
        "max_output_tokens": 1024,
        "kontext_tokens": 3200,
        "unternehmen_tokens": 900,
        "top_k": 8,
        "verlauf": 6,
        "beschreibung": "Mehr Fundstellen, laengere Antwort - deutlich laenger.",
    },
}

#: Die Vorgabe. Nicht die ausfuehrlichste Stufe: eine Antwort, auf die
#: niemand wartet, nuetzt niemandem. Wer mehr Tiefe braucht, stellt um.
VORGABE = "ausgewogen"


#: Die Stufe dem Rechner ueberlassen. Das ist bei einer portablen Anwendung
#: nicht nur bequem, sondern richtig: derselbe Datentraeger laeuft heute an
#: einem Buerorechner ohne Grafikkarte und morgen an einer Arbeitsstation
#: mit. Eine fest eingetragene Stufe waere an einem der beiden falsch.
AUTOMATISCH = "automatisch"


def empfehlung(gpu: bool, modell_gb: float, kerne: int = 0) -> str:
    """Welche Stufe zu diesem Rechner und diesem Modell passt.

    Die Ueberlegung dahinter steht oben im Modul: die Wartezeit vor dem
    ersten Wort waechst mit der Zahl der Token im Kontext, und wie teuer ein
    Token ist, haengt am Modell und daran, ob eine Grafikkarte rechnet.

    * Rechnet eine Grafikkarte mit, ist ein Token billig - dann kann der
      Kontext gross sein.
    * Auf reiner Prozessorrechnung ist ein Token bei einem grossen Modell
      teuer. Dort bedeutet die mittlere Stufe Minuten statt Sekunden.
    * Sehr wenige Kerne sind derselbe Fall, auch bei kleinem Modell.

    Keine Zahl hier ist geraten: die Grenze von vier Gigabyte trennt die
    Modelle des Katalogs so, dass die beiden grossen (7B und 14B) auf der
    langsamen Seite liegen. Wer es anders will, stellt die Stufe von Hand
    ein - dann gilt die Wahl und nicht diese Empfehlung.
    """
    if gpu:
        return "ausgewogen"
    if float(modell_gb or 0.0) >= 4.0:
        return "schnell"
    if kerne and int(kerne) < 4:
        return "schnell"
    return "ausgewogen"


def stufe(name: str) -> dict:
    """Die Werte einer Stufe. Unbekanntes faellt auf die Vorgabe zurueck.

    ``automatisch`` ist hier bewusst unbekannt: die Aufloesung braucht die
    Angaben des Rechners, die dieses Modul nicht hat. Sie geschieht eine
    Ebene hoeher (``Controller.tempostufe``). Faellt sie aus, gilt die
    Vorgabe - eine mittlere Stufe ist nie falsch, nur nicht optimal.
    """
    return STUFEN.get(str(name or "").strip().lower(), STUFEN[VORGABE])


def namen() -> list[str]:
    return list(STUFEN)


def geschaetzte_wartezeit(werte: dict, kopf_tokens: int, vorlauf_tps: float,
                          ausgabe_tps: float) -> dict:
    """Wieviel Wartezeit eine Stufe auf diesem Rechner bedeutet.

    Keine Zusage - eine Rechnung aus zwei gemessenen Geschwindigkeiten. Sie
    macht sichtbar, was die Umstellung tatsaechlich bringt, statt es zu
    behaupten.
    """
    vorlauf = (kopf_tokens + werte["kontext_tokens"]) / max(vorlauf_tps, 0.1)
    ausgabe = werte["max_output_tokens"] / max(ausgabe_tps, 0.1)
    return {"vorlauf_s": round(vorlauf, 1), "ausgabe_s": round(ausgabe, 1),
            "gesamt_s": round(vorlauf + ausgabe, 1)}
