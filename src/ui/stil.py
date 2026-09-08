"""Ein Aussehen fuer die ganze Anwendung - an einer Stelle festgelegt.

Warum es das gibt: Tkinter sieht ohne Zutun aus wie Windows 95. Graue
erhabene Knoepfe, graue Flaechen, Tabellen mit Rillen. Die Vorlagen des
Auftraggebers zeigen etwas anderes: helle Flaeche, weisse Karten, flache
Knoepfe, ein Blau als einzige Betonung.

Das laesst sich in Tkinter erreichen, aber nur ueber ``ttk`` und nur mit
einem Grundthema, das Farben ueberhaupt durchlaesst. ``clam`` tut das;
die Themen ``vista`` und ``xpnative`` unter Windows nicht - sie zeichnen
mit Systembildern und ignorieren jede Farbangabe. Deshalb wird hier
ausdruecklich auf ``clam`` gewechselt.

**Warum an einer Stelle:** Weil 41 Knoepfe, fuenf Tabellen und fuenf
Auswahlfelder sonst 51 Stellen waeren, an denen sich das Aussehen
auseinanderentwickelt. Wer hier eine Farbe aendert, aendert sie ueberall.

Was hier nicht passieren darf: dass ein fehlendes Thema die Anwendung
aufhaelt. Jeder Schritt ist einzeln abgesichert; schlaegt einer fehl,
sieht es aus wie vorher - die Anwendung laeuft.
"""

from __future__ import annotations

from tkinter import ttk

from pkc.logging_setup import get_logger

log = get_logger(__name__)

# -- Farben ------------------------------------------------------------
#: Marineblau der Seitenleiste und der Ueberschriften.
NAVY = "#17202e"
#: Das Blau der Betonung - Knoepfe, Verweise, aktiver Bereich.
BLAU = "#1e6fd9"
#: Dunkleres Blau fuer den Mauszeiger darueber.
BLAU_DUNKEL = "#1857ab"
#: Sehr helles Blau als Fuellung hinter Betontem.
BLAU_HELL = "#e8f0fb"
#: Die Flaeche der Seite. Nicht weiss - sonst heben sich die Karten nicht ab.
GRUND = "#f5f7fa"
#: Die Flaeche der Karten.
KARTE = "#ffffff"
#: Rand der Karten und Trennlinien.
RAND = "#dfe5ec"
#: Ueberschriften und wichtiger Text.
TEXT = "#14243c"
#: Nebentext - Untertitel, Einheiten, Erlaeuterungen.
LEISE = "#5b6b80"
#: Gut, Warnung, Fehler - in dieser Reihenfolge.
GRUEN = "#1e7d4f"
GELB = "#9a6b00"
ROT = "#b3261e"

# -- Schriften ---------------------------------------------------------
SCHRIFT = "Segoe UI"
#: Ersatzschriften. Unter Linux gibt es Segoe UI nicht; Tk nimmt dann
#: stillschweigend etwas anderes. Damit das etwas Vernuenftiges ist, wird
#: die erste vorhandene aus dieser Liste gewaehlt.
ERSATZ = ("Segoe UI", "DejaVu Sans", "Liberation Sans", "Helvetica", "TkDefaultFont")


def schriftfamilie(root=None) -> str:
    """Die erste Schrift aus ERSATZ, die es auf diesem System gibt."""
    try:
        from tkinter import font as tkfont

        vorhanden = {name.lower() for name in tkfont.families(root)}
    except Exception:                   # pragma: no cover - Testdoppel
        return SCHRIFT
    for name in ERSATZ:
        if name.lower() in vorhanden:
            return name
    return SCHRIFT


def anwenden(root) -> str:
    """Legt das Aussehen fuer dieses Fenster fest.

    Gibt den verwendeten Themennamen zurueck - fuer das Protokoll und
    damit ein Test nachsehen kann, ob wirklich umgestellt wurde.
    Bei jedem Fehler bleibt es beim bisherigen Aussehen.
    """
    try:
        stil = ttk.Style(root)
    except Exception:                   # pragma: no cover - Testdoppel
        log.debug("ttk-Stil nicht verfuegbar", exc_info=True)
        return ""

    thema = _thema_setzen(stil)
    familie = schriftfamilie(root)
    _grundschriften(root, familie)
    _flaechen(stil, familie)
    _knoepfe(stil, familie)
    _eingaben(stil, familie)
    _tabellen(stil, familie)
    _sonstiges(stil, familie)
    log.info("Aussehen gesetzt (Thema %s, Schrift %s)", thema, familie)
    return thema


def _thema_setzen(stil) -> str:
    """Auf ein Thema wechseln, das Farben durchlaesst."""
    try:
        vorhanden = list(stil.theme_names())
    except Exception:                   # pragma: no cover - Testdoppel
        return ""
    for name in ("clam", "alt", "default"):
        if name in vorhanden:
            try:
                stil.theme_use(name)
                return name
            except Exception:           # pragma: no cover - defensiv
                continue
    return ""


def _grundschriften(root, familie: str) -> None:
    """Die Standardschriften von Tk selbst - sonst bleiben tk-Widgets alt."""
    try:
        from tkinter import font as tkfont

        for name, groesse, fett in (("TkDefaultFont", 10, False),
                                    ("TkTextFont", 10, False),
                                    ("TkMenuFont", 10, False),
                                    ("TkHeadingFont", 10, True),
                                    ("TkFixedFont", 9, False)):
            schrift = tkfont.nametofont(name, root=root)
            if name != "TkFixedFont":
                schrift.configure(family=familie)
            schrift.configure(size=groesse)
            if fett:
                schrift.configure(weight="bold")
    except Exception:                   # pragma: no cover - Testdoppel
        log.debug("Grundschriften nicht setzbar", exc_info=True)


def _flaechen(stil, familie: str) -> None:
    stil.configure("TFrame", background=GRUND)
    stil.configure("Karte.TFrame", background=KARTE, relief="flat")
    stil.configure("TLabel", background=GRUND, foreground=TEXT,
                   font=(familie, 10))
    stil.configure("Karte.TLabel", background=KARTE, foreground=TEXT)
    stil.configure("Titel.TLabel", background=GRUND, foreground=TEXT,
                   font=(familie, 16, "bold"))
    stil.configure("Untertitel.TLabel", background=GRUND, foreground=LEISE,
                   font=(familie, 9))
    stil.configure("Abschnitt.TLabel", background=KARTE, foreground=TEXT,
                   font=(familie, 11, "bold"))
    stil.configure("Leise.TLabel", background=GRUND, foreground=LEISE,
                   font=(familie, 9))
    stil.configure("TLabelframe", background=GRUND, foreground=TEXT,
                   bordercolor=RAND, relief="solid", borderwidth=1)
    stil.configure("TLabelframe.Label", background=GRUND, foreground=TEXT,
                   font=(familie, 10, "bold"))
    stil.configure("TPanedwindow", background=GRUND)


def _knoepfe(stil, familie: str) -> None:
    """Flach, hell, mit ruhigem Blau als Betonung.

    Drei Auspraegungen, mehr braucht es nicht: der gewoehnliche Knopf,
    der eine hervorgehobene Knopf je Ansicht (``Betont.TButton``) und der
    Knopf, der wie ein Verweis aussieht (``Verweis.TButton``).
    """
    stil.configure("TButton", background=KARTE, foreground=TEXT,
                   bordercolor=RAND, focuscolor=BLAU_HELL,
                   font=(familie, 9), relief="flat", borderwidth=1,
                   padding=(12, 6))
    stil.map("TButton",
             background=[("pressed", BLAU_HELL), ("active", BLAU_HELL),
                         ("disabled", GRUND)],
             foreground=[("disabled", "#9aa7b6"), ("active", BLAU)],
             bordercolor=[("active", BLAU)])

    stil.configure("Betont.TButton", background=BLAU, foreground="#ffffff",
                   bordercolor=BLAU, font=(familie, 9, "bold"),
                   relief="flat", borderwidth=1, padding=(14, 7))
    stil.map("Betont.TButton",
             background=[("pressed", BLAU_DUNKEL), ("active", BLAU_DUNKEL),
                         ("disabled", "#b9cbe4")],
             foreground=[("disabled", "#eef2f7")])

    stil.configure("Verweis.TButton", background=GRUND, foreground=BLAU,
                   bordercolor=GRUND, font=(familie, 9), relief="flat",
                   borderwidth=0, padding=(4, 2))
    stil.map("Verweis.TButton",
             background=[("active", GRUND), ("pressed", GRUND)],
             foreground=[("active", BLAU_DUNKEL), ("disabled", "#9aa7b6")])


def _eingaben(stil, familie: str) -> None:
    for name in ("TEntry", "TCombobox", "TSpinbox"):
        # ``selectforeground``/``selectbackground`` sind hier keine
        # Feinheit. Ein Auswahlfeld mit ``state="readonly"`` zeichnet
        # seinen Text als markiert - mit den Markierungsfarben des Themas.
        # Bei clam ist die Markierungsschrift weiss; auf dem weissen Feld
        # war der Betriebsmodus dadurch unsichtbar. Das Feld sah leer aus,
        # obwohl "OFFLINE" darinstand. Gefunden auf einem Bildschirmfoto,
        # nicht in einem Test - ein Test haette den Wert abgefragt und ihn
        # gefunden.
        stil.configure(name, fieldbackground=KARTE, background=KARTE,
                       foreground=TEXT, bordercolor=RAND, lightcolor=RAND,
                       darkcolor=RAND, insertcolor=TEXT, arrowcolor=LEISE,
                       selectbackground=BLAU_HELL, selectforeground=TEXT,
                       relief="flat", borderwidth=1, padding=(6, 5))
        stil.map(name,
                 bordercolor=[("focus", BLAU)],
                 lightcolor=[("focus", BLAU)],
                 darkcolor=[("focus", BLAU)],
                 fieldbackground=[("readonly", KARTE), ("disabled", GRUND)],
                 selectbackground=[("readonly", KARTE), ("!focus", KARTE)],
                 selectforeground=[("readonly", TEXT), ("!focus", TEXT)],
                 foreground=[("disabled", "#9aa7b6")])
    stil.configure("TCheckbutton", background=GRUND, foreground=TEXT,
                   font=(familie, 10), focuscolor=GRUND)
    stil.map("TCheckbutton",
             background=[("active", GRUND)],
             indicatorcolor=[("selected", BLAU), ("!selected", KARTE)])
    stil.configure("TRadiobutton", background=GRUND, foreground=TEXT,
                   font=(familie, 10), focuscolor=GRUND)
    stil.map("TRadiobutton", background=[("active", GRUND)],
             indicatorcolor=[("selected", BLAU), ("!selected", KARTE)])


def _tabellen(stil, familie: str) -> None:
    """Tabellen ohne Rillen: weisse Zeilen, eine helle Trennlinie.

    ``rowheight`` ist kein Schoenheitswert. Mit der Standardhoehe sitzt
    der Text in Zeilen mit Umlauten am Rand und wird oben beschnitten.
    """
    stil.configure("Treeview", background=KARTE, fieldbackground=KARTE,
                   foreground=TEXT, bordercolor=RAND, borderwidth=0,
                   relief="flat", rowheight=26, font=(familie, 9))
    stil.map("Treeview",
             background=[("selected", BLAU_HELL)],
             foreground=[("selected", TEXT)])
    stil.configure("Treeview.Heading", background=GRUND, foreground=LEISE,
                   font=(familie, 9, "bold"), relief="flat", borderwidth=0,
                   padding=(8, 6))
    stil.map("Treeview.Heading",
             background=[("active", BLAU_HELL)],
             foreground=[("active", TEXT)])


def _sonstiges(stil, familie: str) -> None:
    stil.configure("TNotebook", background=GRUND, bordercolor=RAND,
                   borderwidth=0, tabmargins=(0, 4, 0, 0))
    stil.configure("TNotebook.Tab", background=GRUND, foreground=LEISE,
                   font=(familie, 9), padding=(14, 7), borderwidth=0)
    stil.map("TNotebook.Tab",
             background=[("selected", KARTE)],
             foreground=[("selected", BLAU)])
    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        stil.configure(name, background=GRUND, troughcolor=GRUND,
                       bordercolor=GRUND, arrowcolor=LEISE,
                       relief="flat", borderwidth=0)
        stil.map(name, background=[("active", "#c8d2df")])
    stil.configure("TProgressbar", background=BLAU, troughcolor=RAND,
                   bordercolor=RAND, lightcolor=BLAU, darkcolor=BLAU,
                   borderwidth=0)
    stil.configure("TSeparator", background=RAND)
