"""Quellen der Antwort - als Karten, einklappbar, mit Recherche-Details.

Warum es das gibt: bisher standen die Fundstellen als Fliesstext in einem
Textfeld. Was fehlte, war die Trennung zwischen dem, was den Anwender
angeht, und dem, was nur die Technik angeht.

Auftrag Abschnitt 18 und 19:

* **Quellen** gehoeren getrennt neben die Antwort: Nummer, Titel,
  Quellenart, Herausgeber, Datum, Fundstelle, Primaer- oder
  Sekundaerstatus, Oeffnen, Details.
* **Recherche-Details** - Bewertungen, Dokument-IDs, interne Kennungen -
  gehoeren **nicht** in die normale Ansicht. Sie stehen in einem eigenen,
  standardmaessig geschlossenen Bereich.

Das ist keine Kosmetik. Eine Bewertungszahl neben einer Gesetzesangabe
sieht aus, als gehoere sie zur fachlichen Aussage. Sie tut es nicht.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pkc.logging_setup import get_logger

log = get_logger(__name__)

GRUND = "#f5f7fa"
KARTE = "#ffffff"
RAND = "#dfe5ec"
TITEL = "#14243c"
LEISE = "#5b6b80"
NUMMER_GRUND = "#e8f0fb"
NUMMER_TEXT = "#1e6fd9"

#: Ab dieser Stufe gilt eine Quelle als Sekundaerquelle. Dieselbe Grenze
#: wie in der Antwortpruefung - sie darf nicht auseinanderlaufen.
SEKUNDAER_AB = 5


class Quellenpanel:
    """Das rechte Panel: Quellen als Karten, Details getrennt.

    Verwendung::

        panel = Quellenpanel(eltern, oeffnen=controller.datei_oeffnen)
        panel.setzen(antwort.used_references, antwort.references)
    """

    def __init__(self, eltern, oeffnen=None, breite: int = 320):
        self.oeffnen = oeffnen
        self.eingeklappt = False
        self.details_offen = False
        self._details_text = ""
        self._karten: list = []

        self.rahmen = tk.Frame(eltern, bg=GRUND, width=breite)
        self.rahmen.pack(side="right", fill="y")
        try:
            self.rahmen.pack_propagate(False)
        except Exception:               # pragma: no cover - Testdoppel
            pass

        kopf = tk.Frame(self.rahmen, bg=GRUND)
        kopf.pack(fill="x", padx=12, pady=(4, 6))
        self.titel = tk.Label(kopf, text="Quellen der Antwort", bg=GRUND,
                              fg=TITEL, font=("Segoe UI", 11, "bold"))
        self.titel.pack(side="left")
        self.klapp_knopf = tk.Button(
            kopf, text="ausblenden", command=self.umschalten, bg=GRUND,
            fg=NUMMER_TEXT, relief="flat", borderwidth=0, cursor="hand2",
            highlightthickness=1, highlightbackground=GRUND,
            highlightcolor=NUMMER_TEXT, font=("Segoe UI", 8))
        self.klapp_knopf.pack(side="right")

        # ``wraplength`` ist hier Pflicht, kein Feinschliff: der Satz
        # "Zu dieser Frage wurde keine Fundstelle herangezogen." ist
        # laenger als die Spalte breit ist und wurde ohne Umbruch am Rand
        # abgeschnitten - man las "... herangezoge".
        self.untertitel = tk.Label(self.rahmen, text="nach Relevanz", bg=GRUND,
                                   fg=LEISE, font=("Segoe UI", 8), anchor="w",
                                   justify="left", wraplength=max(breite - 30, 120))
        self.untertitel.pack(fill="x", padx=12)

        self.koerper = tk.Frame(self.rahmen, bg=GRUND)
        self.koerper.pack(fill="both", expand=True, padx=12, pady=(6, 0))

        # Recherche-Details ganz unten, geschlossen.
        fuss = tk.Frame(self.rahmen, bg=GRUND)
        fuss.pack(fill="x", side="bottom", padx=12, pady=(4, 10))
        self.details_knopf = tk.Button(
            fuss, text="Recherche-Details anzeigen", command=self.details_umschalten,
            bg=GRUND, fg=NUMMER_TEXT, relief="flat", borderwidth=0,
            highlightthickness=1, highlightbackground=GRUND,
            highlightcolor=NUMMER_TEXT,
            anchor="w", cursor="hand2", font=("Segoe UI", 9))
        self.details_knopf.pack(fill="x")
        self.details_feld = tk.Text(fuss, height=8, wrap="none",
                                    font=("Consolas", 8), bg="#eef2f7",
                                    borderwidth=0)
        self.details_feld.configure(state="disabled")

    # -- Inhalt --------------------------------------------------------
    def setzen(self, quellen, alle=None) -> None:
        """Zeigt die Quellen der letzten Antwort.

        ``quellen`` sind die tatsaechlich verwendeten, ``alle`` die
        gefundenen. Angezeigt werden die verwendeten; die Recherche-Details
        nennen beide Zahlen, denn der Unterschied ist eine Auskunft:
        gefunden ist nicht benutzt.
        """
        for karte in self._karten:
            try:
                karte.destroy()
            except Exception:           # pragma: no cover - defensiv
                pass
        self._karten = []

        quellen = list(quellen or [])
        alle = list(alle if alle is not None else quellen)

        if not quellen:
            self.untertitel.configure(
                text="Zu dieser Frage wurde keine Fundstelle herangezogen.")
        else:
            self.untertitel.configure(
                text=f"{len(quellen)} Fundstellen · nach Relevanz")
            for quelle in quellen:
                self._karten.append(self._karte(quelle))

        self._details_text = self._details_bauen(quellen, alle)
        self._details_schreiben()

    def _karte(self, quelle):
        karte = tk.Frame(self.koerper, bg=KARTE, highlightbackground=RAND,
                         highlightthickness=1)
        karte.pack(fill="x", pady=(0, 8))
        innen = tk.Frame(karte, bg=KARTE)
        innen.pack(fill="x", padx=10, pady=9)

        kopf = tk.Frame(innen, bg=KARTE)
        kopf.pack(fill="x")
        tk.Label(kopf, text=str(getattr(quelle, "number", "?")), bg=NUMMER_GRUND,
                 fg=NUMMER_TEXT, font=("Segoe UI", 9, "bold"), width=3,
                 padx=4, pady=2).pack(side="left")
        titel = (getattr(quelle, "title", "") or getattr(quelle, "reference", "")
                 or "ohne Titel")
        tk.Label(kopf, text=titel, bg=KARTE, fg=TITEL, anchor="w",
                 justify="left", wraplength=230,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(8, 0))

        for zeile in self._zeilen(quelle):
            tk.Label(innen, text=zeile, bg=KARTE, fg=LEISE, anchor="w",
                     justify="left", wraplength=270,
                     font=("Segoe UI", 8)).pack(fill="x", pady=(3, 0))

        url = getattr(quelle, "url", "")
        if url and self.oeffnen is not None:
            tk.Button(innen, text="Oeffnen", command=lambda u=url: self.oeffnen(u),
                      bg=KARTE, fg=NUMMER_TEXT, relief="flat", borderwidth=0,
                      highlightthickness=1, highlightbackground=KARTE,
                      highlightcolor=NUMMER_TEXT,
                      anchor="w", cursor="hand2",
                      font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(6, 0))
        return karte

    @staticmethod
    def _zeilen(quelle) -> list[str]:
        """Die Angaben unter dem Titel - nur die, die es wirklich gibt.

        Leere Felder werden weggelassen statt als "unbekannt" angezeigt.
        Ein Feld, das bei jeder Quelle "unbekannt" sagt, ist Laerm.
        """
        zeilen = []
        art = getattr(quelle, "priority_label", "")
        stufe = int(getattr(quelle, "priority", SEKUNDAER_AB) or SEKUNDAER_AB)
        rang = "Primaerquelle" if stufe < SEKUNDAER_AB else "Sekundaerquelle"
        zeilen.append(f"{rang}{(' · ' + art) if art else ''}")

        herkunft = getattr(quelle, "reference", "")
        if herkunft and herkunft != getattr(quelle, "title", ""):
            zeilen.append(herkunft)

        stand = (getattr(quelle, "valid_from", None)
                 or getattr(quelle, "fetched_at", None))
        if stand:
            zeilen.append(f"Stand: {str(stand)[:10]}")

        auszug = (getattr(quelle, "excerpt", "") or "").strip()
        if auszug:
            zeilen.append(auszug[:220] + ("..." if len(auszug) > 220 else ""))
        return zeilen

    # -- Recherche-Details ---------------------------------------------
    @staticmethod
    def _details_bauen(quellen, alle) -> str:
        """Die technischen Angaben - getrennt von der Antwort.

        Hier duerfen Bewertungen und Kennungen stehen. In der Antwort
        duerfen sie es nicht (Erweiterung E6 §18).
        """
        zeilen = [
            f"gefunden: {len(alle)}   verwendet: {len(quellen)}",
            "",
            f"{'Nr':>3}  {'Bewertung':>9}  {'Stufe':>5}  Kennung / Herkunft",
            "-" * 64,
        ]
        for quelle in alle:
            zeilen.append(
                f"{getattr(quelle, 'number', 0):>3}  "
                f"{float(getattr(quelle, 'score', 0.0)):>9.3f}  "
                f"{int(getattr(quelle, 'priority', 0) or 0):>5}  "
                f"{getattr(quelle, 'ref_id', '') or getattr(quelle, 'origin', '')}"
            )
        return "\n".join(zeilen)

    def _details_schreiben(self) -> None:
        self.details_feld.configure(state="normal")
        self.details_feld.delete("1.0", "end")
        self.details_feld.insert("1.0", self._details_text)
        self.details_feld.configure(state="disabled")

    def details_umschalten(self) -> None:
        self.details_offen = not self.details_offen
        if self.details_offen:
            self.details_feld.pack(fill="x", pady=(6, 0))
            self.details_knopf.configure(text="Recherche-Details ausblenden")
        else:
            self.details_feld.pack_forget()
            self.details_knopf.configure(text="Recherche-Details anzeigen")

    # -- Ein- und ausklappen -------------------------------------------
    def umschalten(self) -> None:
        """Blendet das Panel aus - die Antwort bekommt dann die ganze Breite."""
        self.eingeklappt = not self.eingeklappt
        if self.eingeklappt:
            self.koerper.pack_forget()
            self.untertitel.pack_forget()
            self.klapp_knopf.configure(text="einblenden")
            try:
                self.rahmen.configure(width=150)
            except Exception:           # pragma: no cover - Testdoppel
                pass
        else:
            self.untertitel.pack(fill="x", padx=12)
            self.koerper.pack(fill="both", expand=True, padx=12, pady=(6, 0))
            self.klapp_knopf.configure(text="ausblenden")
            try:
                self.rahmen.configure(width=320)
            except Exception:           # pragma: no cover - Testdoppel
                pass

    # -- Auskunft fuer Tests und Protokoll ------------------------------
    @property
    def anzahl(self) -> int:
        return len(self._karten)

    @property
    def detailtext(self) -> str:
        return self._details_text
