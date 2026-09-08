"""Der Fensterrahmen: linke Navigation, Kopfzeile, Inhaltsflaeche.

Was sich damit aendert und was nicht:

* **Aendert sich:** die Karteireiter oben weichen einer dauerhaften
  Navigation links. Die aktive Ansicht ist hervorgehoben, die Leiste laesst
  sich einklappen, und welche Bereiche erscheinen, entscheidet das Profil.
* **Aendert sich nicht:** was in den Bereichen steht. Die Schale nimmt eine
  Flaeche entgegen und zeigt sie an - sie weiss nichts ueber Unterhaltung,
  Belege oder Einstellungen und hat keinerlei Fachlogik.

Diese Trennung ist Absicht. Der Umbau der Oberflaeche darf die
Geschaeftslogik nicht anfassen, und was die Schale nicht kennt, kann sie
auch nicht kaputtmachen.

**Warum einfache tk-Bausteine und keine ttk-Widgets in der Seitenleiste:**
ttk faerbt sich je nach System unterschiedlich, und unter Windows laesst
sich ein dunkler Hintergrund dort nicht zuverlaessig durchsetzen. Die
Seitenleiste soll auf jedem Rechner gleich aussehen, also wird sie aus
``tk.Frame`` und ``tk.Button`` gebaut, wo die Farbe verbindlich ist.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from typing import Callable

from pkc.logging_setup import get_logger

log = get_logger(__name__)

# -- Farben ------------------------------------------------------------
# Aus dem PORTIVA-Classic-Logo abgeleitet, nicht frei gewaehlt: das dunkle
# Marineblau des Schriftzugs traegt die Seitenleiste, das helle Blau der
# drei Punkte hebt die aktive Ansicht hervor.
NAVY = "#17202e"
NAVY_HELL = "#1f2b3d"
AKTIV = "#1e6fd9"
AKTIV_TEXT = "#ffffff"
TEXT = "#c6d4e4"
TEXT_LEISE = "#7f93aa"
GRUND = "#f5f7fa"
KARTE = "#ffffff"
RAND = "#dfe5ec"
TRENNER = "#2b3a4f"
TITEL = "#14243c"

#: Breite der offenen Seitenleiste. Nicht frei gewaehlt: der laengste
#: Eintrag ist "Einstellungen & Status" und braucht im aktiven (fetten)
#: Zustand gemessene 241 Bildpunkte. Mit 250 wurde er abgeschnitten.
#:
#: 290 statt der knapp ausreichenden 272, weil die Messung unter Linux mit
#: einer Ersatzschrift entstand. Unter Windows gibt es Segoe UI wirklich,
#: und eine andere Schrift misst anders. Ein Wert, der nur auf dem
#: Entwicklungsrechner passt, ist kein Wert - er ist ein Zufall.
BREITE_OFFEN = 290
BREITE_ZU = 56


@dataclass
class Bereich:
    """Ein Hauptbereich der Anwendung."""

    kennung: str
    titel: str
    untertitel: str = ""
    #: Kurzform fuer die Navigation. Die Leiste hat eine feste Breite;
    #: "Plugins & Erweiterungen" passt dort nicht und wurde zu "Plugins &
    #: Erweiterunge" abgeschnitten. In den Vorlagen steht in der Leiste
    #: ohnehin die Kurzform und die lange Fassung als Ueberschrift.
    #: Leer heisst: die Leiste zeigt den vollen Titel.
    kurz: str = ""
    #: Ein Zeichen als Sinnbild. Bewusst Text und keine Bilddatei: eine
    #: fehlende Bilddatei waere ein leerer Knopf, ein Zeichen ist immer da.
    zeichen: str = "•"
    rahmen: object = None
    knopf: object = None
    kopf: object = field(default=None, repr=False)


class Navigationsschale:
    """Fensterrahmen mit dauerhafter Navigation links.

    Verwendung::

        schale = Navigationsschale(root, brand, "Buchhalter")
        flaeche = schale.bereich_anlegen("unterhaltung", "Unterhaltung",
                                         "Natuerlich fragen.", "\\u25cf")
        ...  # Inhalte in flaeche bauen
        schale.fertig()          # erste Ansicht zeigen
    """

    def __init__(self, root, brand, profil: str = "",
                 sichtbare: list[str] | None = None):
        self.root = root
        self.brand = brand
        self.profil = profil
        #: Welche Bereiche das Profil zulaesst. None heisst: alle.
        self.sichtbare = list(sichtbare) if sichtbare else None
        self.bereiche: dict[str, Bereich] = {}
        self.reihenfolge: list[str] = []
        self.aktiv: str = ""
        self.eingeklappt = False
        self._beim_wechsel: list[Callable[[str], None]] = []
        self._aufbauen()

    # -- Aufbau --------------------------------------------------------
    def _aufbauen(self) -> None:
        self.rahmen = tk.Frame(self.root, bg=GRUND)
        self.rahmen.pack(fill="both", expand=True)

        self.seitenleiste = tk.Frame(self.rahmen, bg=NAVY, width=BREITE_OFFEN)
        self.seitenleiste.pack(side="left", fill="y")
        try:
            # Ohne das schrumpft der Rahmen auf die Breite seines Inhalts.
            self.seitenleiste.pack_propagate(False)
        except Exception:               # pragma: no cover - Testdoppel
            pass

        self._marke_aufbauen()

        self.navigation = tk.Frame(self.seitenleiste, bg=NAVY)
        self.navigation.pack(fill="both", expand=True, padx=8, pady=(4, 4))

        self._fusszeile_aufbauen()

        # Rechts: Kopfzeile und darunter die gestapelten Ansichten.
        self.inhalt = tk.Frame(self.rahmen, bg=GRUND)
        self.inhalt.pack(side="left", fill="both", expand=True)
        self._kopfzeile_aufbauen()

        self.buehne = tk.Frame(self.inhalt, bg=GRUND)
        self.buehne.pack(fill="both", expand=True, padx=20, pady=(0, 12))

    def _marke_aufbauen(self) -> None:
        kopf = tk.Frame(self.seitenleiste, bg=NAVY)
        kopf.pack(fill="x", padx=14, pady=(16, 10))
        self.markenrahmen = kopf

        self._logo = _logo_laden(self.brand, kopf, hoehe=42)
        if self._logo is not None:
            self.markenbild = tk.Label(kopf, image=self._logo, bg=NAVY,
                                       borderwidth=0)
            self.markenbild.image = self._logo
            self.markenbild.pack(anchor="w")
        else:
            # Kein Bild? Dann der Schriftzug. Nie ein leerer Kopf.
            self.markenbild = tk.Label(kopf, text=self.brand.name, bg=NAVY,
                                       fg="#ffffff",
                                       font=("Segoe UI", 17, "bold"))
            self.markenbild.pack(anchor="w")
            tk.Label(kopf, text=self.brand.claim, bg=NAVY, fg=TEXT_LEISE,
                     font=("Segoe UI", 8)).pack(anchor="w")

        self.einklapp_knopf = tk.Button(
            self.seitenleiste, text="‹  Leiste einklappen", bg=NAVY,
            fg=TEXT_LEISE, activebackground=NAVY_HELL, activeforeground="#ffffff",
            relief="flat", borderwidth=0, highlightthickness=1,
            highlightbackground=NAVY, highlightcolor=AKTIV,
            anchor="w", cursor="hand2",
            font=("Segoe UI", 8), command=self.leiste_umschalten)
        self.einklapp_knopf.pack(fill="x", padx=14, pady=(0, 6))

    def _fusszeile_aufbauen(self) -> None:
        fuss = tk.Frame(self.seitenleiste, bg=NAVY)
        fuss.pack(side="bottom", fill="x", padx=14, pady=(6, 16))
        tk.Frame(fuss, bg=TRENNER, height=1).pack(fill="x", pady=(0, 10))
        self.profil_label = tk.Label(
            fuss, text=f"Profil: {self.profil}" if self.profil else self.brand.name,
            bg=NAVY, fg="#ffffff", font=("Segoe UI", 9, "bold"), anchor="w")
        self.profil_label.pack(fill="x")
        self.lage_label = tk.Label(fuss, text="", bg=NAVY, fg=TEXT_LEISE,
                                   font=("Segoe UI", 8), anchor="w")
        self.lage_label.pack(fill="x")

    def _kopfzeile_aufbauen(self) -> None:
        kopf = tk.Frame(self.inhalt, bg=GRUND)
        kopf.pack(fill="x", padx=20, pady=(18, 10))
        links = tk.Frame(kopf, bg=GRUND)
        links.pack(side="left", anchor="w")
        self.titel_label = tk.Label(links, text="", bg=GRUND, fg=TITEL,
                                    font=("Segoe UI", 20, "bold"), anchor="w")
        self.titel_label.pack(anchor="w")
        self.untertitel_label = tk.Label(links, text="", bg=GRUND, fg="#5b6b80",
                                         font=("Segoe UI", 9), anchor="w")
        self.untertitel_label.pack(anchor="w")

        self.chips = tk.Frame(kopf, bg=GRUND)
        self.chips.pack(side="right", anchor="e")

    # -- Bereiche ------------------------------------------------------
    def bereich_anlegen(self, kennung: str, titel: str, untertitel: str = "",
                        zeichen: str = "●", kurz: str = ""):
        """Legt einen Hauptbereich an und gibt seine Inhaltsflaeche zurueck.

        Ist der Bereich fuer dieses Profil nicht vorgesehen, wird er
        trotzdem gebaut, aber nicht in die Navigation aufgenommen. So bleibt
        der Code der Ansicht unveraendert, egal welches Profil laeuft.
        """
        flaeche = tk.Frame(self.buehne, bg=GRUND)
        bereich = Bereich(kennung=kennung, titel=titel, untertitel=untertitel,
                          zeichen=zeichen, rahmen=flaeche, kurz=kurz)

        if self.sichtbare is None or kennung in self.sichtbare:
            bereich.knopf = self._navigationsknopf(bereich)
            self.reihenfolge.append(kennung)
        self.bereiche[kennung] = bereich
        return flaeche

    def _navigationsknopf(self, bereich: Bereich):
        knopf = tk.Button(
            self.navigation,
            text=f"  {bereich.zeichen}   {bereich.kurz or bereich.titel}",
            command=lambda k=bereich.kennung: self.zeigen(k),
            bg=NAVY, fg=TEXT, activebackground=NAVY_HELL,
            activeforeground="#ffffff", relief="flat", borderwidth=0,
            # ``highlightthickness`` ist nicht dasselbe wie
            # ``borderwidth``. Tk zeichnet damit einen Fokusrahmen, unter
            # X11 in einem hellen Grau - im Bild sah jeder Eintrag der
            # Seitenleiste aus wie ein umrandeter Kasten. In der Vorlage
            # hat nur der aktive Eintrag eine Flaeche.
            #
            # Der Rahmen wird deshalb nicht abgeschaltet, sondern
            # unsichtbar gemacht: in Leistenfarbe, solange der Knopf
            # keinen Fokus hat, und blau, sobald er ihn bekommt. Ihn
            # ganz abzuschalten (``highlightthickness=0``) waere der
            # bequemere Weg gewesen und haette die Leiste fuer die
            # Tastatur unbrauchbar gemacht - man saehe nicht mehr, wo man
            # ist. Wer keine Maus benutzt, ist kein Sonderfall.
            highlightthickness=1, highlightbackground=NAVY,
            highlightcolor=AKTIV,
            anchor="w", padx=12, pady=10, cursor="hand2",
            font=("Segoe UI", 10),
        )
        knopf.pack(fill="x", pady=1)
        return knopf

    def zeigen(self, kennung: str) -> bool:
        """Wechselt die Ansicht. Unbekannte Kennung aendert nichts."""
        bereich = self.bereiche.get(kennung)
        if bereich is None:
            log.debug("Unbekannter Bereich angefordert: %s", kennung)
            return False
        if self.aktiv == kennung:
            return True

        alt = self.bereiche.get(self.aktiv)
        if alt is not None and alt.rahmen is not None:
            try:
                alt.rahmen.pack_forget()
            except Exception:           # pragma: no cover - defensiv
                log.debug("Alte Ansicht liess sich nicht ausblenden",
                          exc_info=True)
        self.aktiv = kennung
        try:
            bereich.rahmen.pack(fill="both", expand=True)
        except Exception:               # pragma: no cover - defensiv
            log.debug("Neue Ansicht liess sich nicht einblenden", exc_info=True)

        self.titel_label.configure(text=bereich.titel)
        self.untertitel_label.configure(text=bereich.untertitel)
        self._hervorhebung_setzen()
        for rueckruf in list(self._beim_wechsel):
            try:
                rueckruf(kennung)
            except Exception:           # pragma: no cover - defensiv
                log.debug("Rueckruf beim Ansichtswechsel fehlgeschlagen",
                          exc_info=True)
        return True

    def _hervorhebung_setzen(self) -> None:
        """Die aktive Ansicht muss eindeutig zu erkennen sein."""
        for kennung in self.reihenfolge:
            bereich = self.bereiche[kennung]
            if bereich.knopf is None:
                continue
            ist_aktiv = kennung == self.aktiv
            bereich.knopf.configure(
                bg=AKTIV if ist_aktiv else NAVY,
                fg=AKTIV_TEXT if ist_aktiv else TEXT,
                activebackground=AKTIV if ist_aktiv else NAVY_HELL,
                font=("Segoe UI", 10, "bold") if ist_aktiv else ("Segoe UI", 10),
            )

    def beim_wechsel(self, rueckruf: Callable[[str], None]) -> None:
        """Meldet einen Rueckruf an, der bei jedem Ansichtswechsel laeuft.

        Gebraucht, damit eine Ansicht ihre Daten erst dann nachlaedt, wenn
        sie wirklich sichtbar wird - und nicht alle zehn beim Start.
        """
        self._beim_wechsel.append(rueckruf)

    def fertig(self, start: str = "") -> None:
        """Zeigt die erste Ansicht. Ohne Angabe die erste angelegte."""
        if not self.reihenfolge:
            return
        self.zeigen(start if start in self.bereiche else self.reihenfolge[0])

    # -- Leiste ein- und ausklappen ------------------------------------
    def leiste_umschalten(self) -> None:
        self.eingeklappt = not self.eingeklappt
        breite = BREITE_ZU if self.eingeklappt else BREITE_OFFEN
        try:
            self.seitenleiste.configure(width=breite)
        except Exception:               # pragma: no cover - Testdoppel
            pass
        for kennung in self.reihenfolge:
            bereich = self.bereiche[kennung]
            if bereich.knopf is None:
                continue
            # Eingeklappt steht nur das Sinnbild da - mittig und ohne
            # den fuehrenden Abstand. Mit Abstand und linksbuendig
            # brauchte der Knopf mehr Breite, als die schmale Leiste hat.
            bereich.knopf.configure(
                text=bereich.zeichen if self.eingeklappt
                else f"  {bereich.zeichen}   {bereich.kurz or bereich.titel}",
                anchor="center" if self.eingeklappt else "w",
                padx=2 if self.eingeklappt else 12)
        self.einklapp_knopf.configure(
            text="›" if self.eingeklappt else "‹  Leiste einklappen",
            anchor="center" if self.eingeklappt else "w")
        # Auch der Rand muss mit: eingeklappt bleiben von 56 Bildpunkten
        # nach zweimal 14 Abstand nur 28 uebrig, und der Knopf braucht mit
        # seinem Fokusrahmen 32. Er wurde beschnitten.
        try:
            self.einklapp_knopf.pack_configure(
                padx=4 if self.eingeklappt else 14)
        except Exception:               # pragma: no cover - Testdoppel
            pass
        # Marke und Fusszeile im eingeklappten Zustand ausblenden - sonst
        # ragen sie ueber die schmale Leiste hinaus.
        for widget in (getattr(self, "markenbild", None),
                       getattr(self, "profil_label", None),
                       getattr(self, "lage_label", None)):
            if widget is None:
                continue
            try:
                widget.pack_forget() if self.eingeklappt else widget.pack(
                    anchor="w", fill="x")
            except Exception:           # pragma: no cover - defensiv
                pass

    # -- Kopfzeile -----------------------------------------------------
    def lage_setzen(self, profiltext: str = "", lagetext: str = "") -> None:
        if profiltext:
            self.profil_label.configure(text=profiltext)
        self.lage_label.configure(text=lagetext)


# -- Helfer ------------------------------------------------------------

def _logo_laden(brand, eltern, hoehe: int = 42):
    """Laedt die dunkle Logovariante fuer die Seitenleiste.

    Gibt None zurueck, wenn kein Bild verfuegbar ist. Der Aufrufer zeigt
    dann den Schriftzug - ein leerer Kopf waere schlimmer als ein Bild
    weniger.
    """
    pfad = brand.variante("dark") or brand.logo_pfad
    if pfad is None:
        return None
    try:
        from PIL import Image, ImageTk

        bild = Image.open(pfad).convert("RGBA")
        breite = max(1, round(bild.width * hoehe / bild.height))
        return ImageTk.PhotoImage(bild.resize((breite, hoehe), Image.LANCZOS),
                                  master=eltern)
    except Exception:
        log.debug("Pillow nicht verfuegbar - Logo wird ganzzahlig verkleinert",
                  exc_info=True)
    try:
        bild = tk.PhotoImage(file=str(pfad), master=eltern)
        teiler = max(1, round(bild.height() / hoehe))
        return bild.subsample(teiler, teiler) if teiler > 1 else bild
    except Exception:                   # pragma: no cover - defensiv
        log.debug("Logo konnte nicht geladen werden", exc_info=True)
        return None


class Chip:
    """Eine kleine Statusanzeige in der Kopfzeile.

    Warum als eigene Klasse: es gibt drei davon (Wissensstand, Betriebsart,
    Internet), sie sehen gleich aus und aendern sich zur Laufzeit. Ohne
    eigene Klasse stuenden Farben und Randabstaende dreimal im Code.
    """

    FARBEN = {
        "neutral": ("#eef2f7", "#42556e"),
        "gut": ("#e6f4ec", "#1c7a45"),
        "warnung": ("#fdf3e3", "#9a6512"),
        "fehler": ("#fdecec", "#a32626"),
    }

    def __init__(self, eltern, text: str = "", art: str = "neutral"):
        grund, schrift = self.FARBEN.get(art, self.FARBEN["neutral"])
        self.label = tk.Label(eltern, text=text, bg=grund, fg=schrift,
                              font=("Segoe UI", 9, "bold"), padx=12, pady=5)
        self.label.pack(side="left", padx=(8, 0))

    def setzen(self, text: str, art: str = "neutral") -> None:
        grund, schrift = self.FARBEN.get(art, self.FARBEN["neutral"])
        self.label.configure(text=text, bg=grund, fg=schrift)


class Kartenwahl:
    """Eine Auswahl von Gruppen als Karten - statt Karteireitern.

    In den Vorlagen des Auftraggebers stehen die Einstellungsgruppen als
    Karten untereinander: Titel, darunter eine Zeile, was in der Gruppe
    steckt. Die gewaehlte Karte ist hervorgehoben, ihr Inhalt steht
    rechts daneben.

    Die Schnittstelle ist bewusst dieselbe wie bei ``ttk.Notebook``::

        wahl = Kartenwahl(eltern)
        flaeche = tk.Frame(wahl.buehne)
        wahl.add(flaeche, text="Allgemein", untertitel="Sprache, Profil")

    Damit bleibt der Code, der die Inhalte baut, unveraendert - genau
    darum geht es bei einem Umbau der Oberflaeche.
    """

    #: Breite der Kartenspalte.
    BREITE = 260

    def __init__(self, eltern, breite: int = BREITE):
        self.breite = int(breite)
        self.rahmen = tk.Frame(eltern, bg=GRUND)
        self.rahmen.columnconfigure(1, weight=1)
        self.rahmen.rowconfigure(0, weight=1)

        self.spalte = tk.Frame(self.rahmen, bg=GRUND, width=breite)
        self.spalte.grid(row=0, column=0, sticky="nsw")
        try:
            self.spalte.grid_propagate(False)
            self.spalte.pack_propagate(False)
        except Exception:               # pragma: no cover - Testdoppel
            pass

        #: Hierhinein gehoeren die Inhaltsflaechen.
        self.buehne = tk.Frame(self.rahmen, bg=GRUND)
        self.buehne.grid(row=0, column=1, sticky="nsew", padx=(14, 0))

        self.karten: list = []
        self.flaechen: list = []
        self.aktiv = -1

    # -- wie ttk.Notebook ----------------------------------------------
    def add(self, flaeche, text: str = "", untertitel: str = "", **_egal):
        """Nimmt eine Flaeche auf und legt ihre Karte an."""
        nummer = len(self.flaechen)
        self.flaechen.append(flaeche)
        karte = tk.Frame(self.spalte, bg=KARTE, highlightbackground=RAND,
                         highlightthickness=1, cursor="hand2")
        karte.pack(fill="x", pady=(0, 8))
        innen = tk.Frame(karte, bg=KARTE)
        innen.pack(fill="x", padx=14, pady=11)
        # ``wraplength`` an beiden Beschriftungen: die Karte hat eine
        # feste Breite, und ohne Umbruch wird abgeschnitten statt
        # umgebrochen - aus "Protokollierung" wurde "Protokollieru".
        umbruch = max(self.breite - 40, 120)
        titel = tk.Label(innen, text=text, bg=KARTE, fg=TITEL, anchor="w",
                         justify="left", wraplength=umbruch,
                         font=("Segoe UI", 10, "bold"))
        titel.pack(fill="x")
        unter = None
        if untertitel:
            unter = tk.Label(innen, text=untertitel, bg=KARTE, fg="#5b6b80",
                             anchor="w", justify="left", wraplength=umbruch,
                             font=("Segoe UI", 8))
            unter.pack(fill="x")
        # Die ganze Karte ist das Klickziel, nicht nur der Titel. Wer auf
        # den Untertitel klickt, meint dieselbe Gruppe.
        for teil in (karte, innen, titel, unter):
            if teil is None:
                continue
            try:
                teil.bind("<Button-1>", lambda _e, n=nummer: self.waehlen(n))
            except Exception:           # pragma: no cover - Testdoppel
                pass
        self.karten.append((karte, innen, titel, unter))
        if nummer == 0:
            self.waehlen(0)
        return flaeche

    def waehlen(self, nummer: int) -> None:
        """Zeigt die Gruppe mit dieser Nummer."""
        if not (0 <= nummer < len(self.flaechen)) or nummer == self.aktiv:
            return
        for flaeche in self.flaechen:
            try:
                flaeche.pack_forget()
            except Exception:           # pragma: no cover - Testdoppel
                pass
        self.aktiv = nummer
        try:
            self.flaechen[nummer].pack(fill="both", expand=True)
        except Exception:               # pragma: no cover - Testdoppel
            pass
        self._hervorheben()

    def _hervorheben(self) -> None:
        for stelle, (karte, innen, titel, unter) in enumerate(self.karten):
            ist_aktiv = stelle == self.aktiv
            grund = AKTIV if ist_aktiv else KARTE
            schrift = AKTIV_TEXT if ist_aktiv else TITEL
            leise = "#d7e6fb" if ist_aktiv else "#5b6b80"
            for teil, farbe in ((karte, grund), (innen, grund)):
                try:
                    teil.configure(bg=farbe)
                except Exception:       # pragma: no cover - Testdoppel
                    pass
            try:
                titel.configure(bg=grund, fg=schrift)
                if unter is not None:
                    unter.configure(bg=grund, fg=leise)
                karte.configure(highlightbackground=AKTIV if ist_aktiv else RAND)
            except Exception:           # pragma: no cover - Testdoppel
                pass

    # -- Auskunft fuer Tests -------------------------------------------
    @property
    def anzahl(self) -> int:
        return len(self.flaechen)
