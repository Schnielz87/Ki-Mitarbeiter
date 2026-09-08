"""Grafische Oberflaeche (Tkinter).

Bewusst eine *duenne* Ansicht auf den ``AppController``: keine Fachlogik,
keine Datenbankzugriffe, kein Netzcode.  Alles, was hier passiert, ist an
anderer Stelle kopflos getestet.

Warum Tkinter: es gehoert zur Standardbibliothek, braucht keine
Zusatzinstallation, funktioniert ohne Internet und laesst sich zuverlaessig in
eine Windows-EXE packen.
"""

from __future__ import annotations

import queue
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Callable

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk

from app.controller import AppController, AskOutcome, StartupReport
from pkc.branding import load_brand, profilname
from pkc.logging_setup import get_logger
from pkc.netstate import Mode
from ui.antwort import teilen
# Die Farben kommen aus einer Stelle. Sie hier noch einmal als Zahl
# hinzuschreiben hiesse, sie beim naechsten Umbau an einer davon zu
# vergessen (OBERFLAECHEN_STANDARD.md Abschnitt 2).
from ui.stil import (BLAU, BLAU_HELL, GRUND as FLAECHE, KARTE, LEISE, NAVY,
                     RAND, TEXT)
from ui.markdown import zerlegen
from pkc.audit import ApprovalState
from pkc.memory.schema_keys import CATEGORIES

PAD = 8

#: Breite der Quellenspalte in der Unterhaltung. Fest, nicht anteilig:
#: eine Quellenkarte braucht eine bestimmte Breite, sonst bricht der Titel
#: nach jedem Wort um. Wird das Fenster breiter, waechst die Unterhaltung.
QUELLEN_BREITE = 330

#: Mindestbreite der Knopfspalte neben dem Eingabefeld. Ohne sie schneidet
#: Tk die laengste Beschriftung ab, sobald es eng wird.
KNOPFSPALTE = 150

#: Breite der Statusspalte in den Einstellungen. Ebenfalls fest: die
#: Ampelwerte stehen rechtsbuendig, und eine schrumpfende Spalte schiebt
#: sie aus dem Bild.
STATUS_BREITE = 430

#: Ab dieser Fensterbreite passt die Quellenspalte neben die Unterhaltung.
#: Darunter wird sie ausgeblendet - eine Unterhaltung, die nur noch 130
#: Bildpunkte breit ist, ist keine Unterhaltung mehr. Ueber "einblenden"
#: laesst sie sich jederzeit zurueckholen.
SCHWELLE_QUELLEN = 1150

#: Ab dieser Breite bleibt die Navigation ausgeschrieben. Darunter klappt
#: sie auf die Sinnbilder zusammen und gibt 234 Bildpunkte frei.
SCHWELLE_LEISTE = 1000

#: Der Tastenhinweis unter dem Eingabefeld - lang und kurz. Die lange
#: Fassung passt auf ein schmales Fenster nicht und wurde dort mitten im
#: Wort abgeschnitten. Ein halber Hinweis hilft niemandem.
HINWEIS_LANG = ("Eingabe sendet  ·  Umschalt+Eingabe neue Zeile  ·  "
                "Strg+N neue Unterhaltung  ·  Esc bricht ab")
HINWEIS_KURZ = "Eingabe sendet  ·  Umschalt+Eingabe neue Zeile"

FONT_BASE = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)
FONT_TITLE = ("Segoe UI", 14, "bold")

#: Stelle im Chat, ab der die gerade laufende Antwort steht (Abschnitt 21).
MARKE_STROM = "laufende_antwort"

# Die Ausweichzweige beim Branding und beim Update-Status schreiben ins
# Protokoll. Ohne dieses Protokoll waere dort ein NameError entstanden -
# ausgerechnet an den Stellen, die einen Fehler abfangen sollen.
log = get_logger(__name__)


class Abgebrochen(Exception):
    """Der Benutzer hat die Erzeugung abgebrochen - kein Fehler."""


class BackgroundTask:
    """Fuehrt langlaufende Arbeit ausserhalb des Oberflaechen-Threads aus."""

    def __init__(self, widget: tk.Misc):
        self.widget = widget
        self.results: queue.Queue = queue.Queue()
        #: Wird gesetzt, wenn der Benutzer abbricht (Abschnitt 22).
        self.abgebrochen = False

    def abbrechen(self) -> None:
        """Bricht das Warten ab.

        Der Arbeitsfaden selbst laeuft zu Ende - ihn mitten in einer
        Modellberechnung abzuschiessen waere weder sauber moeglich noch
        ratsam. Sein Ergebnis wird aber verworfen, und die Oberflaeche ist
        sofort wieder bedienbar. Das ist der ehrliche Umfang dessen, was
        hier zugesichert werden kann.
        """
        self.abgebrochen = True

    def run(
        self,
        work: Callable[[], Any],
        done: Callable[[Any, Exception | None], None],
        on_tick: Callable[[], None] | None = None,
    ) -> None:
        """Startet die Arbeit. ``on_tick`` laeuft bei jedem Wartedurchlauf.

        Es gibt bewusst nur **eine** Warteschleife: eine zweite wuerde die
        Oberflaeche unnoetig belasten und schwerer nachvollziehbar machen.
        """
        def worker() -> None:
            try:
                self.results.put((work(), None))
            except Exception as exc:  # jede Ausnahme erreicht die Oberflaeche
                self.results.put((None, exc))

        threading.Thread(target=worker, daemon=True).start()
        self._poll(done, on_tick)

    def _poll(
        self,
        done: Callable[[Any, Exception | None], None],
        on_tick: Callable[[], None] | None = None,
    ) -> None:
        if self.abgebrochen:
            done(None, Abgebrochen("Die Erzeugung wurde abgebrochen."))
            return
        if on_tick is not None:
            on_tick()
        try:
            result, error = self.results.get_nowait()
        except queue.Empty:
            self.widget.after(80, lambda: self._poll(done, on_tick))
            return
        if on_tick is not None:
            on_tick()
        done(result, error)


def _logo_bild(brand, hoehe: int = 84):
    """Laedt das Logo als Tk-Bild - oder None, wenn es fehlt.

    Tkinter kann von Haus aus nur GIF und PNG. Reicht das nicht, oder fehlt
    die Datei, wird None geliefert; der Aufrufer zeigt dann den Schriftzug.
    Ein fehlendes Logo darf nie ein Startproblem sein.
    """
    pfad = brand.logo_pfad
    if pfad is None:
        return None
    try:
        bild = tk.PhotoImage(file=str(pfad))
    except Exception as exc:            # unlesbar, unbekanntes Format
        log.warning("Logo nicht darstellbar (%s): %s", pfad.name, exc)
        return None
    # Nur ganzzahlig verkleinern - Tk kann nichts anderes, und Strecken
    # wuerde die Proportionen verletzen.
    if bild.height() > hoehe:
        faktor = max(1, round(bild.height() / hoehe))
        try:
            bild = bild.subsample(faktor, faktor)
        except Exception:               # pragma: no cover - defensiv
            pass
    return bild


def _taskleisten_kennung(brand) -> None:
    """Eigene Anwendungskennung fuer Windows.

    Ohne sie gruppiert Windows das Fenster unter der Kennung des
    Python-Interpreters und zeigt in der Taskleiste dessen Symbol statt
    unseres - selbst wenn das Fenstersymbol richtig gesetzt ist. Der Aufruf
    existiert nur unter Windows und schadet anderswo nicht, weil er dort
    schlicht fehlschlaegt und abgefangen wird.
    """
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"{brand.name}.KI-Mitarbeiter")
    except Exception:                   # kein Windows oder nicht verfuegbar
        pass


def _fenstericon(fenster, brand) -> list[str]:
    """Setzt Fenster- und Taskleistensymbol, soweit das System es zulaesst.

    Gibt zurueck, welche Wege tatsaechlich funktioniert haben - fuer das
    Protokoll und damit ein Test nachsehen kann. Nie eine Ausnahme: ein
    fehlendes Symbol darf den Start nicht verhindern.

    **Warum alle Wege und nicht der erste, der klappt:** Die vorherige
    Fassung rief ``iconbitmap(default=...)`` auf und kehrte bei Erfolg
    sofort zurueck. ``default`` setzt aber das Symbol fuer Fenster, die
    danach entstehen - das bereits erzeugte Fenster behaelt seines. In
    der Titelleiste stand deshalb weiterhin die Feder, das Standardbild
    von Tk. Der Aufruf hatte keinen Fehler gemeldet; er hatte nur etwas
    anderes getan, als gemeint war.

    Deshalb jetzt: erst das Symbol fuer *dieses* Fenster, dann das fuer
    kuenftige, und zusaetzlich ``iconphoto``. Die Wege stoeren sich nicht
    gegenseitig, und welcher auf welchem System greift, muss man nicht
    raten.
    """
    _taskleisten_kennung(brand)
    geschafft: list[str] = []

    ico = brand.icon_pfad
    if ico is not None:
        # Ohne "default": das Symbol dieses Fensters.
        try:
            fenster.iconbitmap(str(ico))
            geschafft.append("iconbitmap")
        except Exception as exc:        # unter Linux kennt Tk kein .ico
            log.debug("iconbitmap nicht moeglich (%s)", exc)
        # Mit "default": das Symbol aller spaeteren Fenster (Dialoge).
        try:
            fenster.iconbitmap(default=str(ico))
            geschafft.append("iconbitmap-default")
        except Exception as exc:
            log.debug("iconbitmap default nicht moeglich (%s)", exc)

    png = brand.variante("icon")
    if png is not None:
        try:
            bild = tk.PhotoImage(file=str(png), master=fenster)
            fenster.iconphoto(True, bild)
            # Referenz halten, sonst raeumt der Sammler das Bild weg und
            # das Symbol verschwindet wieder.
            fenster._portiva_icon = bild
            geschafft.append("iconphoto")
        except Exception as exc:        # pragma: no cover - defensiv
            log.debug("iconphoto nicht moeglich (%s)", exc)

    if geschafft:
        log.info("Fenstersymbol gesetzt (%s)", ", ".join(geschafft))
    else:
        log.warning("Fenstersymbol konnte nicht gesetzt werden - in der "
                    "Titelleiste steht das Standardbild von Tk.")
    return geschafft


class _BrandKopf:
    """Logo links, darunter Marke und Claim - oder nur der Schriftzug."""

    def __init__(self, eltern, brand, profil: str = "", gross: bool = True):
        rahmen = ttk.Frame(eltern)
        self.frame = rahmen
        bild = _logo_bild(brand, hoehe=72 if gross else 40)
        if bild is not None:
            label = ttk.Label(rahmen, image=bild)
            label.image = bild          # Referenz halten
            label.pack(side="left", padx=(0, PAD))
        schrift = ttk.Frame(rahmen)
        schrift.pack(side="left", anchor="w")
        ttk.Label(schrift, text=brand.titel(profil),
                  font=FONT_TITLE if gross else ("Segoe UI", 12, "bold")).pack(anchor="w")
        if gross:
            ttk.Label(schrift, text=brand.claim, foreground="#555555").pack(anchor="w")


class StartupWindow:

    """Fenster der Systempruefung (Masterprompt 38)."""

    def __init__(self, controller: AppController):
        self.controller = controller
        self.report: StartupReport | None = None
        self.proceed = False

        self.brand = load_brand(controller.paths, controller.config)
        self.profil = profilname(controller.profile)

        self.root = tk.Tk()
        self.root.title(f"{self.brand.titel(self.profil)} - Systempruefung")
        self.root.geometry("820x600")
        self.root.minsize(640, 460)
        _fenstericon(self.root, self.brand)

        # Marke, Claim und Profil - das Logo, soweit vorhanden.
        kopf = _BrandKopf(self.root, self.brand, self.profil, gross=True)
        kopf.frame.pack(anchor="w", padx=PAD * 2, pady=(PAD * 2, PAD // 2))
        if self.profil:
            ttk.Label(self.root, text=f"Profil: {self.profil}",
                      font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=PAD * 2)
        ttk.Label(
            self.root,
            text="Die Anwendung prueft ihren eigenen Zustand. Bitte einen Moment warten.",
        ).pack(anchor="w", padx=PAD * 2, pady=(PAD // 2, PAD))

        self.text = scrolledtext.ScrolledText(
            self.root, font=FONT_MONO, wrap="word", height=18, state="disabled"
        )
        self.text.pack(fill="both", expand=True, padx=PAD * 2, pady=PAD)

        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=PAD * 2)
        self.progress.start(12)

        buttons = ttk.Frame(self.root)
        buttons.pack(fill="x", padx=PAD * 2, pady=PAD * 2)
        self.start_button = ttk.Button(
            buttons,
            text=f"{(self.profil or self.brand.name).upper()} STARTEN",
            command=self._start, state="disabled",
        )
        self.start_button.pack(side="right")
        ttk.Button(buttons, text="Beenden", command=self.root.destroy).pack(
            side="right", padx=(0, PAD)
        )

    def _write(self, text: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.configure(state="disabled")

    def _start(self) -> None:
        self.proceed = True
        self.root.destroy()

    def run(self) -> tuple[bool, StartupReport | None]:
        task = BackgroundTask(self.root)

        def done(result: Any, error: Exception | None) -> None:
            self.progress.stop()
            self.progress.pack_forget()
            if error is not None:
                self._write(
                    "Die Systempruefung ist fehlgeschlagen.\n\n"
                    f"{type(error).__name__}: {error}\n\n"
                    + "".join(traceback.format_exception(error))
                )
                return
            self.report = result
            self._write(result.as_text())
            self.start_button.configure(state="normal" if result.usable else "disabled")
            if result.usable:
                self.start_button.focus_set()

        self.root.after(120, lambda: task.run(self.controller.bootstrap, done))
        self.root.mainloop()
        return self.proceed, self.report


class MainWindow:
    """Hauptfenster mit Chat, Quellen, Unternehmenswissen und Verwaltung."""

    def __init__(self, controller: AppController, report: StartupReport | None = None):
        self.controller = controller
        self.report = report
        self.busy = False
        self.pending_candidates: list = []
        self._letzte_quellen: list = []

        # Fehlt das Sprachmodell, nennt die Antwort den Weg dorthin. Aus dem
        # Fenster heraus ist das die Registerkarte - nicht ein Befehl fuer
        # ein Konsolenprogramm, das hier niemand offen hat.
        from pkc.llm.providers import RetrievalOnlyProvider
        controller.einrichtungsweg(RetrievalOnlyProvider.WEG_FENSTER)

        self.root = tk.Tk()
        # Das Aussehen zuerst: ttk zeichnet einen Knopf mit dem Stil, der
        # zum Zeitpunkt seiner Erzeugung gilt. Wer spaeter umstellt, hat
        # halb alte und halb neue Knoepfe im selben Fenster.
        self._aussehen_setzen()
        self.brand = load_brand(controller.paths, controller.config)
        self.profil = profilname(controller.profile)
        # PORTIVA ist fest, der Profilname kommt aus dem aktiven Profil -
        # nach einem Profilwechsel heisst das Fenster automatisch anders.
        self.root.title(self.brand.titel(self.profil))
        _fenstericon(self.root, self.brand)
        self.root.geometry("1280x820")
        self.root.minsize(880, 600)
        #: Zuletzt gesetzter Zustand der Breitenanpassung. Ohne dieses
        #: Merken liefe bei jedem Mausziehen am Fensterrand der ganze
        #: Umbau erneut - hundertmal in der Sekunde.
        self._breitenlage: tuple[bool, bool] | None = None
        self._leiste_auto_zu = False
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Abschnitt 23: die Unterhaltung soll sich wie ein Gespraech lesen.
        # Wer spricht, steht als Name darueber - nicht als "Sie"/"Buchhalter",
        # sondern mit der Marke und dem aktiven Profil.
        self._sprecher_ich = "BENUTZER"
        self._sprecher_ki = self.brand.titel(self.profil)

        # Reihenfolge beachten: erst die Schale, dann die Kopfzeile. Die
        # Statusanzeigen sitzen in der Kopfzeile der Schale, nicht mehr in
        # einer eigenen Leiste ueber den Karteireitern.
        self._build_body()
        self._build_header()
        self._build_statusbar()
        self.schale.fertig("unterhaltung")

        controller.network.on_change(self._on_network_change)
        controller.start_network_monitor()
        self.controller.ensure_conversation()
        self._refresh_status()
        self._refresh_conversations()
        self._refresh_memory()
        self._append_chat(
            "System",
            "Der portable Buchhalter ist bereit.\n\n"
            "Er arbeitet mit lokalem Fachwissen und dem Unternehmensgedaechtnis auf "
            "diesem Datentraeger. Alle Antworten sind fachliche Zuarbeit und beduerfen "
            "der Pruefung durch einen verantwortlichen Menschen.",
        )

    # -- Aufbau --------------------------------------------------------
    #: Farbpaare fuer die Statuschips: Hintergrund, Schrift.
    CHIPFARBEN = {
        "neutral": ("#eef2f7", "#42556e"),
        "gut": ("#e6f4ec", "#1c7a45"),
        "warnung": ("#fdf3e3", "#9a6512"),
    }

    def _chip(self, eltern, art: str = "neutral", fett: bool = True):
        """Eine kleine Statusanzeige in der Kopfzeile.

        Bewusst ein einfaches ``tk.Label`` statt eines ttk-Widgets: nur dort
        laesst sich die Hintergrundfarbe auf jedem System verbindlich
        setzen, und ein Chip ohne Farbe ist kein Chip.
        """
        grund, schrift = self.CHIPFARBEN[art]
        label = tk.Label(eltern, text="", bg=grund, fg=schrift, padx=12, pady=5,
                         font=("Segoe UI", 9, "bold" if fett else "normal"))
        label.pack(side="left", padx=(8, 0))
        return label

    @staticmethod
    def _chip_faerben(label, art: str) -> None:
        grund, schrift = MainWindow.CHIPFARBEN[art]
        label.configure(bg=grund, fg=schrift)

    def _build_header(self) -> None:
        """Statusanzeigen oben rechts, Betriebsmodus daneben.

        Die Marke steht jetzt in der Seitenleiste, nicht mehr hier - deshalb
        traegt die Kopfzeile nur noch Zustand: Wissensstand, Betriebsmodus,
        Internet. Auftrag Abschnitt 31: schnell erreichbar, aber die
        Oberflaeche nicht beherrschend.
        """
        chips = self.schale.chips

        self.knowledge_label = self._chip(chips, "neutral", fett=False)
        self.internet_label = self._chip(chips, "neutral")
        # Der Betriebsmodus stand hier zweimal: als Chip und gleich
        # daneben als Auswahlfeld mit demselben Wort. Zwei Anzeigen
        # derselben Sache sind nicht doppelt so deutlich, sie sind
        # doppelt so breit - und im Kopf wurde es so eng, dass aus
        # "OFFLINE" ein "OFFL" wurde. Der Chip entfaellt; das
        # Auswahlfeld zeigt den Modus und laesst ihn zugleich aendern.

        # Moduswahl: eine Entscheidung des Benutzers. Sie gehoert nicht in
        # ein Untermenue, sondern in Reichweite.
        self.mode_var = tk.StringVar(value=self.controller.mode.value)
        self.mode_box = ttk.Combobox(
            chips, textvariable=self.mode_var, state="readonly", width=9,
            values=[m.value for m in Mode],
        )
        self.mode_box.pack(side="left", padx=(10, 0))
        self.mode_box.bind("<<ComboboxSelected>>", self._on_mode_changed)

    #: Die Schritte, die ein Wissensupdate durchlaeuft. Reihenfolge und
    #: Benennung stammen aus der Pipeline selbst, nicht aus dem Entwurf -
    #: sonst zeigte die Oberflaeche Schritte an, die es nicht gibt.
    PIPELINE_SCHRITTE = ("Pruefen", "Staging", "Validieren", "Indexieren",
                         "Aktivieren")

    def _pipeline_setzen(self, erreicht: int, fehler: bool = False) -> None:
        """Faerbt die Schritte bis zum erreichten ein.

        ``erreicht`` ist die Zahl der abgeschlossenen Schritte. Bei einem
        Fehler wird der letzte rot - so ist zu sehen, wo es hakte, statt
        nur dass es hakte.
        """
        for nummer, schritt in enumerate(self.PIPELINE_SCHRITTE):
            label = self._pipeline_schritte.get(schritt)
            if label is None:
                continue
            if nummer < erreicht:
                zeichen, farbe = "\u25cf", "#1c7a45"
            elif nummer == erreicht and fehler:
                zeichen, farbe = "\u25cf", "#a32626"
            else:
                zeichen, farbe = "\u25cb", "#9aa8b8"
            label.configure(text=f"  {zeichen}  {schritt}  ", fg=farbe)

    def _refresh_wissen_kacheln(self, faellig) -> None:
        werte = {
            "Wissensstand": (self.controller.knowledge.knowledge_date() or "unbekannt")[:10],
            "Quellen": f"{len(self.controller.knowledge.sources())} erfasst",
            "Letzte Pruefung": (faellig.letzte_pruefung or "noch nie")[:16],
            "Naechste Pruefung": (faellig.naechste_pruefung or "kein Plan")[:16],
        }
        for titel, wert in werte.items():
            label = self._wissen_kachel_widgets.get(titel)
            if label is not None:
                label.configure(text=str(wert))

    def _refresh_update_lage(self) -> None:
        """Zeigt Wissensstand, Faelligkeit und naechste Pruefung."""
        if not hasattr(self, "update_lage_label"):
            return
        try:
            faellig = self.controller.update_faelligkeit()
        except Exception as exc:        # pragma: no cover - defensiv
            log.debug("Faelligkeit nicht ermittelbar (%s)", exc)
            return
        self.update_lage_label.configure(text=f"Update-Status: {faellig.lage.value}")
        self.update_detail_label.configure(text=faellig.text)
        plan = self.controller.config.get("updates.schedule", "weekly")
        teile = [f"Automatik: {plan}"]
        if faellig.intervall_tage:
            teile.append(f"Intervall: alle {faellig.intervall_tage} Tage")
        if faellig.letzte_pruefung:
            teile.append(f"Letzte Aktualisierung: {faellig.letzte_pruefung}")
        if faellig.naechste_pruefung:
            teile.append(f"Naechste Pruefung: {faellig.naechste_pruefung}")
        self.update_plan_label.configure(text="  ·  ".join(teile))
        try:
            self._refresh_wissen_kacheln(faellig)
        except Exception:               # pragma: no cover - defensiv
            log.debug("Wissenskacheln nicht aktualisierbar", exc_info=True)

    def _on_mode_changed(self, event=None) -> str:
        """Moduswechsel durch den Benutzer - mit Ansage, was jetzt gilt."""
        gewaehlt = Mode.parse(self.mode_var.get(), self.controller.mode)
        if gewaehlt is self.controller.mode:
            return "break"
        lage = self.controller.set_mode(gewaehlt, grund="Oberflaeche")
        messagebox.showinfo("Betriebsmodus", lage.modus.beschreibung, parent=self.root)
        self._append_chat("System", lage.modus.beschreibung, "system")
        self._refresh_status()
        return "break"

    def _aussehen_setzen(self) -> None:
        """Legt Farben, Schriften und Knopfformen fest (ui/stil.py).

        Faellt es aus, sieht die Anwendung aus wie vorher - sie laeuft.
        Ein Aussehen ist nie ein Grund, den Start zu verhindern.
        """
        self.thema = ""
        try:
            from ui import stil

            self.thema = stil.anwenden(self.root)
            self.root.configure(bg=stil.GRUND)
        except Exception:               # pragma: no cover - defensiv
            log.debug("Aussehen liess sich nicht setzen", exc_info=True)

    def _build_body(self) -> None:
        """Baut die Schale und haengt die Ansichten hinein.

        Die Ansichten selbst sind unveraendert: sie bekommen nur eine
        andere Flaeche als Elternteil. Genau darin liegt der Sinn dieses
        Schrittes - der Rahmen wechselt, der Inhalt nicht.
        """
        from ui.schale import Navigationsschale

        self.schale = Navigationsschale(
            self.root, self.brand, self.profil,
            sichtbare=self._sichtbare_bereiche())
        # Reihenfolge wie im Zielentwurf. Sie bestimmt die Navigation.
        self._build_chat_tab()
        self._build_memory_tab()
        self._build_documents_tab()
        self._build_results_tab()
        self._build_update_tab()
        self._build_templates_tab()
        self._build_tasks_tab()
        self._build_plugins_tab()
        self._build_services_tab()
        # Die Einstellungen zuerst: sie legen die Gruppe an, in die der
        # Modellbereich einzieht.
        self._build_settings_tab()
        self._build_model_tab()

    def _sichtbare_bereiche(self) -> list[str] | None:
        """Welche Bereiche dieses Profil zeigt.

        Auftrag Abschnitt 9: die Navigation muss profilspezifisch
        konfigurierbar bleiben - ein spaeteres Mitarbeiterprofil soll
        Bereiche ausblenden oder ergaenzen koennen, ohne dass der Kern neu
        gebaut werden muss. Steht nichts im Profil, werden alle gezeigt.
        """
        try:
            roh = self.controller.profile.raw.get("navigation")
        except Exception:               # pragma: no cover - defensiv
            return None
        if not isinstance(roh, list) or not roh:
            return None
        return [str(k) for k in roh]

    # -- Registerkarte: Unterhaltung -----------------------------------
    def _build_chat_tab(self) -> None:
        frame = self.schale.bereich_anlegen(
            "unterhaltung", "Unterhaltung",
            "Natuerlich fragen, Quellen nur bei Bedarf einblenden.", "\u25c9")

        # Raster statt Schiebeteiler. Der Schiebeteiler verteilte die
        # Breite nach Gewichten und hat dabei die Knopfspalte so weit
        # zusammengedrueckt, dass aus "Senden" ein "Send" wurde und rechts
        # eine graue Luecke stehenblieb. Im Raster bekommt die Quellen-
        # spalte eine feste Breite und die Unterhaltung den Rest - das
        # kann nicht kippen.
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0, minsize=QUELLEN_BREITE)
        frame.rowconfigure(0, weight=1)

        left = ttk.Frame(frame)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, PAD))
        left.rowconfigure(1, weight=1)          # die Unterhaltung waechst
        left.columnconfigure(0, weight=1)

        # Werkzeugleiste ueber der Unterhaltung. "Neue Unterhaltung" und
        # "Antwort speichern" standen vorher unten neben dem Tastenhinweis
        # und wurden dort abgeschnitten - im Bild stand "Neue Unt". Oben
        # haben sie Platz, und der Hinweis unten bleibt ein Hinweis statt
        # einer Knopfleiste.
        werkzeuge = ttk.Frame(left)
        werkzeuge.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.chat = scrolledtext.ScrolledText(
            left, wrap="word", font=FONT_BASE, state="disabled",
            relief="flat", borderwidth=0, background=KARTE,
            padx=16, pady=12, highlightthickness=1,
            highlightbackground=RAND, highlightcolor=RAND)
        self.chat.grid(row=1, column=0, sticky="nsew")
        self.chat.tag_configure("wer", font=("Segoe UI", 10, "bold"))
        # Abschnitt 23: Frage und Antwort sollen sich auf einen Blick
        # unterscheiden lassen.
        self.chat.tag_configure("sprecher_ich", font=("Segoe UI", 9, "bold"),
                                foreground=LEISE, spacing1=14)
        # Die eigene Frage bekommt eine eigene Flaeche - wie in den
        # Vorlagen. Tk kennt keine runden Ecken; was es kann, ist eine
        # Hintergrundfarbe mit Innenabstand ueber ``lmargin`` und
        # ``spacing``. Das genuegt, um Frage und Antwort auf einen Blick
        # zu trennen, worum es hier geht.
        self.chat.tag_configure("frage", background=BLAU_HELL,
                                foreground=TEXT, lmargin1=14, lmargin2=14,
                                rmargin=14, spacing1=8, spacing3=8,
                                borderwidth=0)
        self.chat.tag_configure("sprecher_ki", font=("Segoe UI", 10, "bold"),
                                foreground="#1f4e79", spacing1=10)
        # Quellen, Wissensstand und Hinweise stehen unter der Antwort -
        # lesbar, aber ruhiger als die Antwort selbst.
        self.chat.tag_configure("anhang", font=("Segoe UI", 9), foreground="#555555",
                                lmargin1=12, lmargin2=12, spacing1=2)
        self.chat.tag_configure("anhang_kopf", font=("Segoe UI", 9, "bold"),
                                foreground="#444444", lmargin1=12, lmargin2=12,
                                spacing1=6)
        self.chat.tag_configure("system", foreground="#555555")
        self.chat.tag_configure("hinweis", foreground="#8a4b00")
        # Stile fuer die Markdown-Darstellung (Abschnitt 7). Ohne sie
        # stuenden **, # und - roh im Fenster.
        self.chat.tag_configure("ueberschrift1", font=("Segoe UI", 12, "bold"),
                                foreground="#1f4e79", spacing1=8, spacing3=3)
        self.chat.tag_configure("ueberschrift2", font=("Segoe UI", 11, "bold"),
                                spacing1=6, spacing3=2)
        self.chat.tag_configure("fett", font=("Segoe UI", 10, "bold"))
        self.chat.tag_configure("kursiv", font=("Segoe UI", 10, "italic"))
        self.chat.tag_configure("code", font=FONT_MONO, foreground="#33691e")
        self.chat.tag_configure("aufzaehlung", foreground="#1f4e79")
        self.chat.tag_configure("tabelle", font=FONT_MONO)

        # -- Eingabe: dauerhaft unten, Aktionen direkt daneben ----------
        entry_frame = ttk.Frame(left)
        entry_frame.grid(row=2, column=0, sticky="ew", pady=(PAD, 0))
        entry_frame.columnconfigure(0, weight=1)
        self.entry = tk.Text(entry_frame, height=3, font=FONT_BASE, wrap="word",
                             relief="flat", borderwidth=0, background=KARTE,
                             padx=12, pady=8, highlightthickness=1,
                             highlightbackground=RAND,
                             highlightcolor=BLAU)
        self.entry.grid(row=0, column=0, sticky="nsew")

        # Auftrag Abschnitt 33: Eingabe sendet, Umschalt+Eingabe bricht die
        # Zeile um. Bisher war es umgekehrt herum geloest (Strg+Eingabe) -
        # das kennt aus anderen Anwendungen niemand.
        #
        # Die Reihenfolge der beiden Bindungen ist wichtig: Tk wertet die
        # genauere zuerst. Ohne "break" wuerde ausserdem zusaetzlich zum
        # Senden noch ein Zeilenumbruch eingefuegt.
        self.entry.bind("<Shift-Return>", lambda _e: None)
        self.entry.bind("<Return>", self._auf_eingabetaste)
        self.entry.bind("<Control-Return>", lambda _e: self._send())

        # Die Knopfspalte bekommt eine Mindestbreite. Ohne sie schneidet
        # Tk die Beschriftung ab, sobald der Platz knapp wird - und ein
        # Knopf mit der Aufschrift "Send" ist ein Fehler, kein Layout.
        buttons = ttk.Frame(entry_frame)
        buttons.grid(row=0, column=1, sticky="nsew", padx=(PAD, 0))
        entry_frame.columnconfigure(1, weight=0, minsize=KNOPFSPALTE)
        buttons.columnconfigure(0, weight=1)
        self.send_button = ttk.Button(buttons, text="Senden", command=self._send,
                                      style="Betont.TButton")
        self.send_button.grid(row=0, column=0, sticky="ew")
        # Abschnitt 22: waehrend einer laengeren Antwort abbrechen koennen.
        self.stop_button = ttk.Button(buttons, text="Stoppen",
                                      command=self._abbrechen, state="disabled")
        self.stop_button.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Button(buttons, text="Datei anhaengen",
                   command=self._add_document).grid(row=2, column=0, sticky="ew",
                                                    pady=(4, 0))

        # Ablageflaeche fuer Drag & Drop. Sie ist zugleich ein Klickziel -
        # kommt die Ablage auf diesem System nicht zustande, bleibt der
        # Bereich also benutzbar statt tot zu sein.
        self.drop_hinweis = tk.Label(
            entry_frame, text="Datei hierher ziehen oder \u201eDatei anhaengen\u201c",
            bg="#eef2f7", fg=LEISE, font=("Segoe UI", 8), pady=6,
            cursor="hand2")
        self.drop_hinweis.grid(row=2, column=0, columnspan=2, sticky="ew",
                               pady=(6, 0))
        self.drop_hinweis.bind("<Button-1>", lambda _e: self._add_document())
        self._ablage_einrichten()

        hinweise = ttk.Frame(left)
        hinweise.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        self.tastenhinweis = ttk.Label(
            hinweise, text=HINWEIS_LANG, foreground=LEISE,
            font=("Segoe UI", 8))
        self.tastenhinweis.pack(side="left")

        # Erweiterung E4: das Ergebnis soll als Datei herausgehen koennen -
        # ohne installiertes Office und ohne Internet.
        self.datei_format = tk.StringVar(value="pdf")
        ttk.Combobox(werkzeuge, textvariable=self.datei_format, state="readonly",
                     width=6,
                     values=[eintrag["format"] for eintrag
                             in self.controller.artefakt_formate()]).pack(side="right")
        ttk.Button(werkzeuge, text="Antwort speichern",
                   command=self._antwort_speichern).pack(side="right", padx=(0, 6))
        ttk.Button(werkzeuge, text="Neue Unterhaltung",
                   command=self._new_conversation).pack(side="right", padx=(0, 6))

        # -- Rechts: Quellen als Karten, darunter der Verlauf -----------
        # Auch hier ein Raster: die Quellen nehmen die Hoehe, der Verlauf
        # steht darunter mit fester Hoehe. Vorher lag der Verlauf mit
        # "side=bottom" ueber der Quellenspalte - im Bild sah es aus, als
        # haenge eine Liste mitten im Fenster.
        right = ttk.Frame(frame, width=QUELLEN_BREITE)
        right.grid(row=0, column=1, sticky="nsew")
        self._quellenspalte = right
        self._quellenspalte_ist_da = True
        right.grid_propagate(False)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        from ui.quellenpanel import Quellenpanel

        quellenflaeche = ttk.Frame(right)
        quellenflaeche.grid(row=0, column=0, sticky="nsew")
        self.quellenpanel = Quellenpanel(quellenflaeche,
                                         oeffnen=self._quelle_oeffnen,
                                         breite=QUELLEN_BREITE)

        verlauf = ttk.Frame(right)
        verlauf.grid(row=1, column=0, sticky="ew", pady=(PAD, 0))
        verlauf.columnconfigure(0, weight=1)
        ttk.Label(verlauf, text="Unterhaltungen",
                  font=("Segoe UI", 10, "bold")).grid(row=0, column=0,
                                                      sticky="w")
        self.conversation_list = tk.Listbox(
            verlauf, height=6, font=("Segoe UI", 9), relief="flat",
            borderwidth=0, background=KARTE, highlightthickness=1,
            highlightbackground=RAND, activestyle="none")
        self.conversation_list.grid(row=1, column=0, sticky="ew", pady=2)
        self.conversation_list.bind("<Double-Button-1>", self._open_conversation)
        ttk.Button(verlauf, text="Unterhaltung exportieren",
                   command=self._export_conversation).grid(row=2, column=0,
                                                           sticky="ew")

        # Tastenkuerzel am Fenster, nicht am Eingabefeld: sie sollen auch
        # dann wirken, wenn der Mauszeiger woanders steht.
        # Auf schmalen Fenstern raeumt die Oberflaeche selbst auf. Ohne
        # das war die Unterhaltung bei 900 Bildpunkten Breite nur noch ein
        # Streifen von 130 - die Seitenleiste, die Quellenspalte und die
        # Knopfspalte hatten den Platz unter sich aufgeteilt.
        self.root.bind("<Configure>", self._auf_groessenaenderung)

        self.root.bind("<Control-n>", lambda _e: self._new_conversation())
        self.root.bind("<Control-N>", lambda _e: self._new_conversation())
        self.root.bind("<Escape>", self._auf_escape)

    def _auf_groessenaenderung(self, ereignis=None) -> None:
        """Passt die Aufteilung an die Fensterbreite an.

        Zwei Stellschrauben, in dieser Reihenfolge: unter
        ``SCHWELLE_QUELLEN`` verschwindet die Quellenspalte, unter
        ``SCHWELLE_LEISTE`` klappt zusaetzlich die Navigation zusammen.
        Wird das Fenster wieder breiter, kommt beides zurueck - aber die
        Navigation nur, wenn *diese* Automatik sie zugeklappt hat und
        nicht der Benutzer selbst. Sonst wuerde die Anwendung eine
        Entscheidung des Benutzers ueberschreiben.
        """
        if ereignis is not None and getattr(ereignis, "widget", None) not in (
                self.root, None):
            return                      # Meldungen von Kindfenstern ignorieren
        try:
            breite = int(self.root.winfo_width())
        except Exception:               # pragma: no cover - Testdoppel
            return
        if breite <= 1:                 # noch nicht gezeichnet
            return
        quellen_zeigen = breite >= SCHWELLE_QUELLEN
        leiste_zu = breite < SCHWELLE_LEISTE
        if self._breitenlage == (quellen_zeigen, leiste_zu):
            return
        self._breitenlage = (quellen_zeigen, leiste_zu)
        self._quellenspalte_zeigen(quellen_zeigen)
        self._leiste_anpassen(leiste_zu)
        # Auf schmalen Fenstern muss ein Chip weichen, sonst quetscht die
        # Kopfzeile das Auswahlfeld fuer den Betriebsmodus auf wenige
        # Bildpunkte zusammen. Der Wissensstand ist der am ehesten
        # entbehrliche der drei - er steht auch in der Statuszeile unten
        # und unter "Wissen & Quellen".
        hinweis = getattr(self, "tastenhinweis", None)
        if hinweis is not None:
            try:
                hinweis.configure(text=HINWEIS_KURZ if leiste_zu else HINWEIS_LANG)
            except Exception:           # pragma: no cover - Testdoppel
                pass
        marke = getattr(self, "knowledge_label", None)
        if marke is not None:
            try:
                if leiste_zu:
                    marke.pack_forget()
                else:
                    marke.pack(side="left", padx=(8, 0), before=self.internet_label)
            except Exception:           # pragma: no cover - Testdoppel
                pass

    def _quellenspalte_zeigen(self, zeigen: bool) -> None:
        spalte = getattr(self, "_quellenspalte", None)
        if spalte is None or zeigen == self._quellenspalte_ist_da:
            return
        try:
            if zeigen:
                spalte.grid()
            else:
                spalte.grid_remove()    # merkt sich die Rasterangaben
        except Exception:               # pragma: no cover - Testdoppel
            return
        self._quellenspalte_ist_da = zeigen

    def _leiste_anpassen(self, zuklappen: bool) -> None:
        schale = getattr(self, "schale", None)
        if schale is None:
            return
        try:
            if zuklappen and not schale.eingeklappt:
                schale.leiste_umschalten()
                self._leiste_auto_zu = True
            elif not zuklappen and schale.eingeklappt and self._leiste_auto_zu:
                schale.leiste_umschalten()
                self._leiste_auto_zu = False
        except Exception:               # pragma: no cover - defensiv
            log.debug("Leiste liess sich nicht anpassen", exc_info=True)

    def _auf_eingabetaste(self, ereignis=None) -> str:
        """Eingabe sendet - ausser bei gedrueckter Umschalttaste.

        Tk meldet den Zustand der Sondertasten im Feld ``state``; Bit 0
        steht fuer Umschalt. Die Abfrage ist bewusst defensiv: meldet ein
        System nichts, wird gesendet - das ist der haeufigere Wunsch.
        """
        zustand = int(getattr(ereignis, "state", 0) or 0)
        if zustand & 0x0001:            # Umschalt gedrueckt: Zeilenumbruch
            return ""
        self._send()
        return "break"

    def _auf_escape(self, _ereignis=None) -> str:
        """Escape bricht eine laufende Erzeugung ab (Abschnitt 33).

        Laeuft nichts, tut die Taste nichts - sie darf keine Unterhaltung
        schliessen und nichts verwerfen.
        """
        if getattr(self, "_laufende_aufgabe", None) is not None:
            self._abbrechen()
        return "break"

    def _quelle_oeffnen(self, ziel: str) -> None:
        """Oeffnet eine Quelle - lokale Datei bevorzugt (Abschnitt 41)."""
        if not ziel:
            return
        if str(ziel).lower().startswith(("http://", "https://")):
            if not self.controller.lage.online_moeglich:
                messagebox.showinfo(
                    "Quelle oeffnen",
                    "Diese Quelle liegt im Internet. Im aktuellen "
                    "Betriebsmodus wird nicht online zugegriffen.",
                    parent=self.root)
                return
            import webbrowser

            webbrowser.open(str(ziel))
            return
        if not self.controller.datei_oeffnen(ziel):
            messagebox.showwarning("Quelle oeffnen",
                                   f"Liess sich nicht oeffnen:\n{ziel}",
                                   parent=self.root)

    def _ablage_einrichten(self) -> None:
        """Richtet Drag & Drop ein, soweit das System es hergibt.

        Tkinter kann das nicht von sich aus. Unter Windows laesst es sich
        ueber die Systemschnittstelle nachruesten (``DragAcceptFiles`` und
        die Nachricht WM_DROPFILES). Bewusst **keine** zusaetzliche
        Bibliothek: das Paket soll von einem Datentraeger laufen, und jede
        weitere Binaerdatei darin ist eine weitere Fehlerquelle.

        Gelingt es nicht, bleibt es beim Klicken. Der Bereich sagt dann
        auch nur noch das - eine Aufforderung zum Ziehen, die nicht
        funktioniert, waere schlimmer als keine.
        """
        self.ablage_moeglich = False
        try:
            from ui.dateiablage import einrichten

            self.ablage_moeglich = einrichten(self.root, self._datei_abgelegt)
        except Exception:               # pragma: no cover - defensiv
            log.debug("Drag & Drop nicht verfuegbar", exc_info=True)
        if not self.ablage_moeglich:
            self.drop_hinweis.configure(
                text="Datei anhaengen (Ziehen ist auf diesem System nicht "
                     "verfuegbar)")

    def _datei_abgelegt(self, pfade) -> None:
        """Nimmt per Ziehen abgelegte Dateien auf."""
        for pfad in list(pfade)[:20]:
            self._dokument_aufnehmen(Path(pfad))

    # -- Registerkarte: Unternehmenswissen -----------------------------
    def _build_memory_tab(self) -> None:
        frame = self.schale.bereich_anlegen(
            "unternehmenswissen", "Unternehmenswissen",
            "Dauerhafte Unternehmensinformationen verwalten, pruefen und "
            "versionieren.", "\u25a4", kurz="Unternehmenswissen")

        top = ttk.Frame(frame)
        top.pack(fill="x", pady=(0, PAD))
        ttk.Label(top, text="Suche:").pack(side="left")
        self.memory_query = ttk.Entry(top, width=40)
        self.memory_query.pack(side="left", padx=PAD)
        self.memory_query.bind("<Return>", lambda e: self._refresh_memory())
        ttk.Button(top, text="Suchen", command=self._refresh_memory).pack(side="left")
        ttk.Button(top, text="Alles anzeigen", command=self._show_all_memory).pack(
            side="left", padx=PAD
        )
        self.onboarding_label = ttk.Label(top, text="")
        self.onboarding_label.pack(side="right")

        # Kategorien als Kacheln mit Anzahl. Eine flache Liste mit dreissig
        # Eintraegen sagt nicht, was das Unternehmen ueberhaupt hinterlegt
        # hat - und ob irgendwo etwas fehlt.
        self.memory_kacheln = tk.Frame(frame, bg=FLAECHE)
        self.memory_kacheln.pack(fill="x", pady=(0, PAD))
        self._memory_kachel_widgets: dict[str, tuple] = {}

        columns = ("schluessel", "kategorie", "titel", "inhalt", "version")
        self.memory_tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
        for column, heading, width in (
            ("schluessel", "Schluessel", 220), ("kategorie", "Kategorie", 150),
            # "V" mit 40 Bildpunkten sah aus wie eine abgeschnittene
            # Ueberschrift und war eine. Eine Spalte, deren Name erklaert
            # werden muss, ist keine gute Spalte.
            ("titel", "Titel", 180), ("inhalt", "Inhalt", 420),
            ("version", "Fassung", 80),
        ):
            self.memory_tree.heading(column, text=heading)
            self.memory_tree.column(column, width=width, anchor="w")
        self.memory_tree.pack(fill="both", expand=True)

        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=PAD)
        ttk.Button(actions, text="Neu / Aendern", command=self._edit_memory).pack(side="left")
        ttk.Button(actions, text="Verlauf", command=self._memory_history).pack(
            side="left", padx=PAD
        )
        ttk.Button(actions, text="Archivieren", command=self._archive_memory).pack(side="left")
        ttk.Button(actions, text="Onboarding fortsetzen", command=self._onboarding).pack(
            side="left", padx=PAD
        )
        ttk.Button(actions, text="Profil exportieren", command=self._export_profile).pack(
            side="right"
        )

    # -- Registerkarte: Belege -----------------------------------------
    def _build_documents_tab(self) -> None:
        frame = self.schale.bereich_anlegen(
            "belege", "Belege & Dokumente",
            "Hochladen, analysieren, klassifizieren und mit Fachwissen "
            "verknuepfen.", "\u25a5")
        leiste = ttk.Frame(frame)
        leiste.pack(fill="x", pady=(0, PAD))
        ttk.Button(leiste, text="Datei auswaehlen",
                   command=self._add_document).pack(side="left")
        for text, befehl in (("Oeffnen", self._beleg_oeffnen),
                             ("Erneut analysieren", self._beleg_erneut),
                             ("In Unterhaltung uebernehmen", self._beleg_uebernehmen),
                             ("Aktualisieren", self._refresh_documents)):
            ttk.Button(leiste, text=text, command=befehl).pack(side="left", padx=(PAD, 0))
        self.documents_hint = ttk.Label(leiste, text="", foreground=LEISE)
        self.documents_hint.pack(side="right")

        ttk.Label(frame, foreground=LEISE, font=("Segoe UI", 8),
                  text="Automatische Erkennung \u2192 fachliche Analyse "
                       "\u2192 Ergebnis \u2192 Quellen").pack(anchor="w",
                                                                pady=(0, 4))

        columns = ("titel", "art", "hinzugefuegt", "status", "ergebnis", "pfad")
        self.document_tree = ttk.Treeview(frame, columns=columns, show="headings")
        for column, heading, width in (
            ("titel", "Dokument", 300), ("art", "Typ", 90),
            ("hinzugefuegt", "Hinzugefuegt", 160), ("status", "Status", 120),
            ("ergebnis", "Ergebnis", 200),
            ("pfad", "Ablage auf dem Datentraeger", 360),
        ):
            self.document_tree.heading(column, text=heading)
            self.document_tree.column(column, width=width, anchor="w")
        self.document_tree.pack(fill="both", expand=True)
        self.document_tree.bind("<Double-Button-1>", lambda _e: self._beleg_oeffnen())
        self._refresh_documents()

    # -- Bereich: Arbeitsergebnisse ------------------------------------
    def _build_results_tab(self) -> None:
        """Von PORTIVA erzeugte Dateien zentral finden, oeffnen, exportieren.

        Der Dienst dahinter gab es laengst (``Artefaktwerk``); erreichbar
        war er nur ueber den Knopf "Antwort speichern" im Chat und ueber
        die Konsole. Hier ist er, wo man ihn sucht.
        """
        frame = self.schale.bereich_anlegen(
            "arbeitsergebnisse", "Arbeitsergebnisse",
            "Von PORTIVA erzeugte Dateien zentral finden, oeffnen und "
            "exportieren.", "\u25ad")

        leiste = ttk.Frame(frame)
        leiste.pack(fill="x", pady=(0, PAD))
        ttk.Button(leiste, text="Aktualisieren",
                   command=self._refresh_results).pack(side="left")
        for text, befehl in (("Oeffnen", self._result_oeffnen),
                             ("Exportieren", self._result_exportieren),
                             ("Umbenennen", self._result_umbenennen),
                             ("Loeschen", self._result_loeschen)):
            ttk.Button(leiste, text=text, command=befehl).pack(side="left", padx=(PAD, 0))
        self.results_hint = ttk.Label(
            leiste, text="Zeile auswaehlen, dann eine Aktion",
            foreground=LEISE)
        self.results_hint.pack(side="right")

        spalten = ("name", "format", "zeitpunkt", "fassung", "groesse", "zustand")
        self.results_tree = ttk.Treeview(frame, columns=spalten, show="headings")
        for spalte, kopf, breite in (
            ("name", "Datei", 320), ("format", "Format", 90),
            ("zeitpunkt", "Erzeugt", 160), ("fassung", "Fassung", 80),
            ("groesse", "Groesse", 100), ("zustand", "Zustand", 140),
        ):
            self.results_tree.heading(spalte, text=kopf)
            self.results_tree.column(spalte, width=breite, anchor="w")
        self.results_tree.pack(fill="both", expand=True)
        self.results_tree.bind("<Double-Button-1>",
                               lambda _e: self._result_oeffnen())
        self._refresh_results()

    def _refresh_results(self) -> None:
        if not hasattr(self, "results_tree"):
            return
        self.results_tree.delete(*self.results_tree.get_children())
        eintraege = self.controller.artefakt_liste(limit=200)
        for eintrag in eintraege:
            groesse = eintrag.get("bytes") or eintrag.get("groesse") or 0
            self.results_tree.insert("", "end", values=(
                eintrag.get("name") or eintrag.get("pfad", ""),
                (eintrag.get("format") or "").upper(),
                (eintrag.get("erzeugt_am") or eintrag.get("zeitpunkt", ""))[:16],
                eintrag.get("fassung", ""),
                f"{int(groesse) / 1024:.0f} KB" if groesse else "",
                "vorhanden" if eintrag.get("vorhanden", True)
                else "nicht mehr vorhanden",
            ))
        self.results_hint.configure(
            text=f"{len(eintraege)} Arbeitsergebnisse"
            if eintraege else "Noch keine Dateien erzeugt")

    def _gewaehltes_ergebnis(self) -> str:
        """Der Dateiname der markierten Zeile - oder eine Meldung.

        Kein stilles Nichtstun: wer auf "Oeffnen" drueckt, ohne etwas
        gewaehlt zu haben, bekommt gesagt, was fehlt.
        """
        auswahl = self.results_tree.selection()
        if not auswahl:
            messagebox.showinfo(
                "Arbeitsergebnisse",
                "Bitte zuerst eine Zeile in der Liste auswaehlen.",
                parent=self.root)
            return ""
        return str(self.results_tree.item(auswahl[0])["values"][0])

    def _result_oeffnen(self) -> None:
        name = self._gewaehltes_ergebnis()
        if not name:
            return
        if not self.controller.datei_oeffnen(self.controller.artefakt_pfad(name)):
            messagebox.showwarning(
                "Oeffnen",
                f"{name} liess sich nicht oeffnen.\n\n"
                "Entweder gibt es die Datei nicht mehr, oder auf diesem "
                "Rechner ist kein Programm fuer dieses Format eingerichtet.",
                parent=self.root)

    def _result_exportieren(self) -> None:
        name = self._gewaehltes_ergebnis()
        if not name:
            return
        ziel = filedialog.asksaveasfilename(
            title="Arbeitsergebnis exportieren", initialfile=name, parent=self.root)
        if not ziel:
            return
        try:
            pfad = self.controller.artefakt_exportieren(name, ziel)
        except Exception as fehler:
            messagebox.showerror("Export", str(fehler), parent=self.root)
            return
        messagebox.showinfo(
            "Export",
            f"Kopiert nach:\n{pfad}\n\nDas Original bleibt auf dem "
            "Datentraeger - der Nachweis mit Pruefsumme bleibt damit gueltig.",
            parent=self.root)

    def _result_umbenennen(self) -> None:
        name = self._gewaehltes_ergebnis()
        if not name:
            return
        neu = simpledialog.askstring(
            "Umbenennen", "Neuer Name (die Endung bleibt erhalten):",
            initialvalue=Path(name).stem, parent=self.root)
        if not neu:
            return
        try:
            pfad = self.controller.artefakt_umbenennen(name, neu)
        except Exception as fehler:
            messagebox.showerror("Umbenennen", str(fehler), parent=self.root)
            return
        self._refresh_results()
        messagebox.showinfo("Umbenennen", f"Heisst jetzt: {pfad.name}",
                            parent=self.root)

    def _result_loeschen(self) -> None:
        name = self._gewaehltes_ergebnis()
        if not name:
            return
        if not messagebox.askyesno(
            "Loeschen",
            f"{name} endgueltig loeschen?\n\n"
            "Der Eintrag im Verzeichnis bleibt als Nachweis erhalten - die "
            "Datei selbst ist danach weg.",
            parent=self.root,
        ):
            return
        if self.controller.artefakt_loeschen(name):
            self._refresh_results()
        else:
            messagebox.showwarning("Loeschen", f"{name} war nicht mehr da.",
                                   parent=self.root)

    # -- Registerkarte: Wissensupdate ----------------------------------
    def _build_update_tab(self) -> None:
        frame = self.schale.bereich_anlegen(
            "wissen_quellen", "Wissen & Quellen",
            "Lokalen Wissensstand, Quellen und Synchronisierung transparent "
            "verwalten.", "\u25eb")

        # Kennzahlen zuerst - vier Zahlen sagen mehr als vier Absaetze.
        self.wissen_kacheln = tk.Frame(frame, bg=FLAECHE)
        self.wissen_kacheln.pack(fill="x", pady=(0, PAD))
        self._wissen_kachel_widgets: dict[str, object] = {}
        for spalte, titel in enumerate(
                ("Wissensstand", "Quellen", "Letzte Pruefung", "Naechste Pruefung")):
            kachel = tk.Frame(self.wissen_kacheln, bg=KARTE,
                              highlightbackground=RAND, highlightthickness=1)
            kachel.grid(row=0, column=spalte, sticky="ew", padx=(0, 10))
            innen = tk.Frame(kachel, bg=KARTE)
            innen.pack(fill="x", padx=16, pady=12)
            tk.Label(innen, text=titel, bg=KARTE, fg=TEXT, anchor="w",
                     font=("Segoe UI", 10, "bold")).pack(anchor="w")
            wert = tk.Label(innen, text="\u2014", bg=KARTE, fg=LEISE,
                            anchor="w", font=("Segoe UI", 9))
            wert.pack(anchor="w")
            self._wissen_kachel_widgets[titel] = wert
        for spalte in range(4):
            try:
                self.wissen_kacheln.columnconfigure(spalte, weight=1)
            except Exception:           # pragma: no cover - Testdoppel
                pass

        # Die Schritte des Updates sichtbar machen. Es gab sie laengst -
        # sie liefen nur unsichtbar ab, und ein Vorgang, den niemand sieht,
        # wirkt wie ein Stillstand.
        self.pipeline_rahmen = ttk.LabelFrame(frame, text="Update-Pipeline")
        self.pipeline_rahmen.pack(fill="x", pady=(0, PAD))
        self._pipeline_schritte: dict[str, object] = {}
        schrittzeile = tk.Frame(self.pipeline_rahmen, bg=FLAECHE)
        schrittzeile.pack(fill="x", padx=10, pady=8)
        for schritt in self.PIPELINE_SCHRITTE:
            label = tk.Label(schrittzeile, text=f"  \u25cb  {schritt}  ",
                             bg=FLAECHE, fg=LEISE, font=("Segoe UI", 9))
            label.pack(side="left")
            self._pipeline_schritte[schritt] = label

        info = ttk.Label(
            frame,
            text=(
                "Ein Update laedt amtliche Quellen, speichert die Originale lokal und "
                "macht sie danach auch OHNE Internet nutzbar.\n"
                "Ohne Internetverbindung wird nichts abgerufen - der lokale Wissensstand "
                "bleibt unveraendert nutzbar."
            ),
            justify="left",
        )
        info.pack(anchor="w", pady=(0, PAD))

        # Fälligkeit sichtbar machen - sonst weiss niemand, wie alt der
        # Wissensstand ist und wann als naechstes geprueft wird.
        stand = ttk.LabelFrame(frame, text="Stand der Aktualisierung")
        stand.pack(fill="x", pady=(0, PAD))
        self.update_lage_label = ttk.Label(stand, text="", font=("Segoe UI", 10, "bold"))
        self.update_lage_label.pack(anchor="w", padx=PAD, pady=(PAD // 2, 0))
        self.update_detail_label = ttk.Label(stand, text="", wraplength=900,
                                             justify="left")
        self.update_detail_label.pack(anchor="w", padx=PAD, pady=(0, PAD // 2))
        self.update_plan_label = ttk.Label(stand, text="", foreground="#555555")
        self.update_plan_label.pack(anchor="w", padx=PAD, pady=(0, PAD // 2))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        self.update_button = ttk.Button(
            buttons, text="Wissen jetzt aktualisieren", command=lambda: self._run_update(False)
        )
        self.update_button.pack(side="left")
        ttk.Button(buttons, text="Trockenlauf (nichts schreiben)",
                   command=lambda: self._run_update(True)).pack(side="left", padx=PAD)
        ttk.Button(buttons, text="Letzten Lauf zuruecknehmen",
                   command=self._rollback_update).pack(side="left")
        ttk.Button(buttons, text="Sicherung erstellen", command=self._backup).pack(side="right")

        self.update_progress = ttk.Progressbar(frame, mode="determinate")
        self.update_progress.pack(fill="x", pady=PAD)

        self.update_log = scrolledtext.ScrolledText(
            frame, wrap="word", font=FONT_MONO, height=20, state="disabled"
        )
        self.update_log.pack(fill="both", expand=True)
        self._write_update_log(self._update_overview())

    def _update_overview(self) -> str:
        lines = ["Quellenregister", ""]
        if self.controller.registry is None:
            lines.append(f"  nicht ladbar: {self.controller.registry_error}")
        else:
            for source in self.controller.registry:
                state = "aktiv" if source.enabled else "deaktiviert"
                lines.append(
                    f"  {source.source_id:26s} Prioritaet {source.priority} · "
                    f"{len(source.documents):2d} Dokument(e) · {state}"
                )
                lines.append(f"      {source.name}")
        due, reason = self.controller.update_due()
        lines += ["", f"Zeitplan: {self.controller.config.get('updates.schedule')} - {reason}", ""]
        runs = self.controller.update_runs(5)
        if runs:
            lines.append("Letzte Laeufe:")
            for run in runs:
                lines.append(
                    f"  {run['started_at'][:19]} {run['status']:10s} "
                    f"aktualisiert {run['updated']} · fehlgeschlagen {run['failed']}"
                )
        return "\n".join(lines)

    # -- Registerkarte: Sprachmodell -----------------------------------
    def _build_model_tab(self) -> None:
        """Der Weg zum Sprachmodell - im Fenster, nicht in der Konsole.

        Das Modell liegt bewusst nicht im Auslieferungspaket: es ist mehrere
        Gigabyte gross, und seine Lizenz waehlt der Betreiber selbst. Es
        fehlt also beim ersten Start, und die Anwendung sagt das auch. Nur
        stand als Abhilfe bisher ein Befehl fuer ein **anderes** Programm da.
        Wer die Anwendung per Doppelklick oeffnet, hat keine Konsole offen -
        und liest die Meldung als "geht nicht", nicht als "fehlt noch".
        """
        # Kein eigener Hauptbereich mehr, sondern die Gruppe "KI & Modelle"
        # unter "Einstellungen & Status" - so sieht es der Zielentwurf vor,
        # und so sind es genau zehn Bereiche in der Navigation.
        frame = self.gruppe_modelle

        ttk.Label(
            frame,
            text=(
                "Ohne Sprachmodell recherchiert der Buchhalter in seinen Quellen und "
                "zeigt die Fundstellen - er formuliert aber keine Fachantwort.\n"
                "Das Modell wird einmalig geladen. Danach steht es dauerhaft auf "
                "diesem Datentraeger und wird auch ohne Internet verwendet."
            ),
            justify="left",
        ).pack(anchor="w", pady=(0, PAD))

        lage = ttk.LabelFrame(frame, text="Lage auf diesem Rechner")
        lage.pack(fill="x", pady=(0, PAD))
        self.modell_lage_label = ttk.Label(lage, text="", font=("Segoe UI", 10, "bold"))
        self.modell_lage_label.pack(anchor="w", padx=PAD, pady=(PAD // 2, 0))
        self.modell_detail_label = ttk.Label(lage, text="", wraplength=900,
                                             justify="left")
        self.modell_detail_label.pack(anchor="w", padx=PAD, pady=(0, PAD // 2))

        auswahl = ttk.Frame(frame)
        auswahl.pack(fill="x", pady=(0, PAD))
        ttk.Label(auswahl, text="Auswahl:").pack(side="left")
        self.modell_wahl = tk.StringVar()
        self.modell_auswahl = ttk.Combobox(auswahl, textvariable=self.modell_wahl,
                                           state="readonly", width=70)
        self.modell_auswahl.pack(side="left", padx=PAD)

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        self.modell_button = ttk.Button(
            buttons, text="Sprachmodell einrichten", command=self._modell_einrichten
        )
        self.modell_button.pack(side="left")
        # Wer das Modell schon hat, soll es nicht ein zweites Mal ziehen -
        # fuer einen weiteren Stick, fuer ein Buero mit gesperrtem Download.
        self.modell_uebernehmen_button = ttk.Button(
            buttons, text="Vorhandene Modelldatei uebernehmen",
            command=self._modell_uebernehmen)
        self.modell_uebernehmen_button.pack(side="left", padx=PAD)
        ttk.Button(buttons, text="Lage neu pruefen",
                   command=self._refresh_modell).pack(side="left")
        ttk.Button(buttons, text="Modell ausprobieren",
                   command=self._modell_probe).pack(side="left", padx=PAD)
        # Die Wartezeit gehoert ins Fenster, nicht in eine Konsole. Wer die
        # Anwendung per Doppelklick oeffnet, hat keine offen - und soll fuer
        # eine Auskunft ueber sein eigenes Programm keine oeffnen muessen.
        ttk.Button(buttons, text="Wartezeit messen",
                   command=self._modell_messen).pack(side="left")

        self.modell_progress = ttk.Progressbar(frame, mode="determinate")
        self.modell_progress.pack(fill="x", pady=PAD)

        self.modell_log = scrolledtext.ScrolledText(
            frame, wrap="word", font=FONT_MONO, height=18, state="disabled"
        )
        self.modell_log.pack(fill="both", expand=True)
        self._refresh_modell()

    def _write_modell_log(self, text: str) -> None:
        self.modell_log.configure(state="normal")
        self.modell_log.delete("1.0", "end")
        self.modell_log.insert("1.0", text)
        self.modell_log.configure(state="disabled")

    def _refresh_modell(self, protokoll: bool = True) -> None:
        """Zeigt, was da ist und was fehlt - ohne Dateipfade in der Antwort.

        ``protokoll=False`` laesst den Textbereich in Ruhe. Nach einem Bezug
        steht dort das Ergebnis - also gerade das, was der Benutzer lesen
        soll. Es durch die Katalogliste zu ersetzen hiesse, ihm die Antwort
        vor der Nase wegzunehmen.
        """
        try:
            lage = self.controller.modell_lage()
        except Exception as fehler:                # pragma: no cover - defensiv
            self.modell_lage_label.configure(text="Lage nicht feststellbar")
            self.modell_detail_label.configure(text=str(fehler))
            return
        self._modell_lage = lage

        if lage["bereit"]:
            self.modell_lage_label.configure(text="Einsatzbereit")
            self.modell_detail_label.configure(
                text=f"Anbieter: {lage['anbieter'].get('anbieter', '?')} · "
                     f"Modell: {lage['anbieter'].get('modell', '?')}")
            self.modell_button.configure(text="Anderes Modell einrichten")
        else:
            self.modell_lage_label.configure(text="Noch nicht eingerichtet")
            self.modell_detail_label.configure(
                text="Es fehlt: " + ", ".join(lage["fehlt"]) if lage["fehlt"]
                     else lage["hinweis"])
            self.modell_button.configure(text="Sprachmodell einrichten")

        # Die Liste zeigt zu jedem Modell, ob es auf DIESEN Rechner passt.
        # Ein Modell, das nicht in den Arbeitsspeicher passt, laeuft mit
        # Bruchteilen eines Tokens je Sekunde - das muss vorher dastehen.
        from pkc.hardware import modelleignung

        eintraege, empfohlen, installiert = [], "", ""
        gefunden = {m["name"] for m in lage["modelle"]}
        for quelle in lage["katalog"]:
            eignung = modelleignung(quelle["min_ram_gb"],
                                    lage["hardware"]["arbeitsspeicher_gb"],
                                    quelle["groesse_gb"])
            marke = {"gut": "", "knapp": " · KNAPP",
                     "zu_gross": " · ZU GROSS FUER DIESEN RECHNER"}.get(
                         eignung["stufe"], "")
            zusatz = " · NUR ZUM AUSPROBIEREN" if not quelle["produktiv"] else ""
            teile = (f" · {len(quelle['teile'])} Teildateien"
                     if quelle.get("geteilt") else "")
            eintraege.append(
                f"{quelle['profil']:9s} {quelle['name']}  ({quelle['groesse_gb']} GB, "
                f"ab {quelle['min_ram_gb']} GB RAM{teile}{zusatz}{marke})")
            if lage["empfehlung"] and quelle["id"] == lage["empfehlung"]["id"]:
                empfohlen = eintraege[-1]
            # Was tatsaechlich auf der Platte liegt, hat Vorrang vor der
            # Empfehlung: sonst zeigt die Liste "standard", waehrend das
            # 14B-Modell laeuft - und widerspricht damit der Zeile darueber.
            if any(name in gefunden for name in
                   ([quelle["datei"]] if quelle.get("datei") else [])):
                installiert = eintraege[-1]

        self.modell_auswahl.configure(values=eintraege)
        # Eine ausdrueckliche Wahl des Benutzers wird nie ueberschrieben.
        if self.modell_wahl.get() not in eintraege:
            self.modell_wahl.set(installiert or empfohlen or
                                 (eintraege[0] if eintraege else ""))

        hardware = lage["hardware"]
        zeilen = [
            "Erkannte Hardware",
            f"  Arbeitsspeicher : {hardware['arbeitsspeicher_gb'] or 'unbekannt'} GB",
            f"  Prozessorkerne  : {hardware['kerne'] or 'unbekannt'}",
            f"  Grafikkarte     : {hardware['grafik'] or 'keine erkannt'}",
            f"  Freier Platz    : {hardware['freier_platz_gb'] or '?'} GB",
            "",
            f"Empfohlen: {lage['empfohlenes_profil_text']}",
            "",
            "Hinterlegte Bezugsquellen",
        ]
        for quelle in lage["katalog"]:
            zeilen.append(f"  {quelle['id']}  {quelle['name']}")
            zeilen.append(f"      Lizenz      : {quelle['lizenz']}")
            zeilen.append(f"      Bezugsquelle: {quelle['pruefstand']}")
            if quelle["hinweis"]:
                zeilen.append(f"      {quelle['hinweis']}")
        if lage["katalogfehler"]:
            zeilen += ["", lage["katalogfehler"]]
        if protokoll:
            self._write_modell_log("\n".join(zeilen))

    def _gewaehlte_quelle(self) -> dict | None:
        wahl = self.modell_wahl.get().strip()
        if not wahl:
            return None
        profil = wahl.split()[0]
        for quelle in getattr(self, "_modell_lage", {}).get("katalog", []):
            if quelle["profil"] == profil:
                return quelle
        return None

    def _modell_einrichten(self) -> None:
        """Laedt das gewaehlte Modell - nach ausdruecklicher Bestaetigung."""
        if self.busy:
            return
        quelle = self._gewaehlte_quelle()
        if quelle is None:
            messagebox.showinfo("Sprachmodell", "Bitte zuerst ein Modell auswaehlen.",
                                parent=self.root)
            return

        # Was hier bestaetigt wird, muss vorher dastehen: Groesse, Lizenz und
        # ob die Bezugsquelle ueberhaupt geprueft ist (Abschnitt 42).
        text = [
            f"{quelle['name']}",
            "",
            f"Groesse       : etwa {quelle['groesse_gb']} GB",
            f"Lizenz        : {quelle['lizenz']}",
            f"Herkunft      : {quelle['herkunft']}",
            f"Bezugsquelle  : {quelle['pruefstand']}",
        ]
        if quelle.get("geteilt"):
            text.append(f"Teildateien   : {len(quelle['teile'])} - alle gehoeren zusammen")
        from pkc.hardware import modelleignung

        eignung = modelleignung(
            quelle["min_ram_gb"],
            getattr(self, "_modell_lage", {}).get("hardware", {}).get(
                "arbeitsspeicher_gb"),
            quelle["groesse_gb"])
        text += ["", eignung["text"]]
        if eignung["stufe"] == "zu_gross":
            text += ["", "Empfehlung: ein kleineres Modell waehlen. Trotzdem "
                         "laden?"]
        if not quelle["produktiv"]:
            text += ["", "ACHTUNG: Dieses Modell ist nur zum Ausprobieren. "
                         "Fuer Fachfragen ist es NICHT geeignet."]
        if not quelle["geprueft"]:
            text += ["", "Die Adresse dieser Bezugsquelle wurde in diesem "
                         "Programmstand nicht abgerufen. Die Datei wird beim "
                         "Laden nicht gegen eine hinterlegte Pruefsumme geprueft."]
        text += ["", "Jetzt laden? Das kann je nach Verbindung einige Minuten dauern."]

        if not messagebox.askyesno("Sprachmodell einrichten", "\n".join(text),
                                   parent=self.root):
            return

        self._set_busy(True, "Das Sprachmodell wird geladen ...")
        self.modell_progress.configure(value=0, maximum=100)
        meldungen: queue.Queue = queue.Queue()

        def fortschritt(geladen: int, gesamt: int, tempo: float) -> None:
            meldungen.put(int(geladen * 100 / gesamt) if gesamt else 0)

        def abholen() -> None:
            wert = None
            try:
                while True:
                    wert = meldungen.get_nowait()
            except queue.Empty:
                pass
            if wert is not None:
                self.modell_progress.configure(value=wert)

        def work() -> dict:
            ergebnis = self.controller.modell_beziehen(
                quelle["id"], bestaetigt=True, fortschritt=fortschritt)
            if not ergebnis["ok"]:
                return ergebnis
            # Erst wenn das Modell wirklich antwortet, ist es eingerichtet.
            self.controller.modell_neu_laden()
            ergebnis["probe"] = self.controller.modell_probe()
            return ergebnis

        # Bezug und Uebernahme enden gleich - siehe _modell_fertig.
        BackgroundTask(self.root).run(work, self._modell_fertig, on_tick=abholen)

    def _modell_uebernehmen(self) -> None:
        """Nimmt eine schon vorhandene GGUF-Datei auf den Datentraeger.

        Das Modell muss nicht auf jedem Rechner neu geladen werden. Es
        gehoert auf den Datentraeger - und von dort laesst es sich
        weitergeben.
        """
        if self.busy:
            return
        pfad = filedialog.askopenfilename(
            title="Modelldatei auswaehlen",
            filetypes=[("GGUF-Modelldateien", "*.gguf"), ("Alle Dateien", "*.*")],
        )
        if not pfad:
            return

        quelle = Path(pfad)
        try:
            groesse_gb = quelle.stat().st_size / 1024 ** 3
        except OSError as fehler:                  # pragma: no cover - defensiv
            messagebox.showerror("Sprachmodell", str(fehler), parent=self.root)
            return

        if not messagebox.askyesno(
            "Modelldatei uebernehmen",
            f"{quelle.name}\n\n"
            f"Groesse: etwa {groesse_gb:.2f} GB\n"
            f"Herkunft: {quelle.parent}\n\n"
            "Die Datei wird auf diesen Datentraeger kopiert - nicht nur "
            "verknuepft. Nur so laeuft der Datentraeger auch an einem "
            "Rechner, der die Herkunft nicht erreicht.\n\n"
            "Jetzt uebernehmen?",
            parent=self.root,
        ):
            return

        self._set_busy(True, "Die Modelldatei wird uebernommen ...")
        self.modell_progress.configure(value=0, maximum=100)
        meldungen: queue.Queue = queue.Queue()

        def fortschritt(kopiert: int, gesamt: int, tempo: float) -> None:
            meldungen.put(int(kopiert * 100 / gesamt) if gesamt else 0)

        def abholen() -> None:
            wert = None
            try:
                while True:
                    wert = meldungen.get_nowait()
            except queue.Empty:
                pass
            if wert is not None:
                self.modell_progress.configure(value=wert)

        def work() -> dict:
            ergebnis = self.controller.modell_uebernehmen(quelle, fortschritt=fortschritt)
            if not ergebnis["ok"]:
                return ergebnis
            self.controller.modell_neu_laden()
            ergebnis["probe"] = self.controller.modell_probe()
            return ergebnis

        BackgroundTask(self.root).run(work, self._modell_fertig, on_tick=abholen)

    def _modell_fertig(self, ergebnis: dict | None, error: Exception | None) -> None:
        """Gemeinsamer Abschluss fuer Bezug und Uebernahme.

        Beide Wege enden gleich: geladen ist nicht eingerichtet. Erst wenn
        das Modell geantwortet hat, steht "einsatzbereit" da.
        """
        self._set_busy(False)
        geglueckt = error is None and bool(ergebnis and ergebnis.get("ok"))
        self.modell_progress.configure(value=100 if geglueckt else 0)
        if error is not None:
            self._write_modell_log(f"Das Modell konnte nicht eingerichtet werden:\n{error}")
            messagebox.showerror("Sprachmodell", str(error), parent=self.root)
            self._refresh_modell(protokoll=False)
            return
        if not ergebnis["ok"]:
            self._write_modell_log(ergebnis["meldung"])
            messagebox.showerror("Sprachmodell", ergebnis["meldung"], parent=self.root)
            self._refresh_modell(protokoll=False)
            return

        probe = ergebnis.get("probe", {})
        zeilen = [ergebnis["meldung"], ""]
        if probe.get("ok"):
            zeilen += [
                "Das Sprachmodell ist einsatzbereit.",
                # Ausdruecklich als Probefrage benannt. "Antwortzeit: 4.0 s"
                # unmittelbar nach einem Modellbezug wurde als Dauer des
                # Herunterladens gelesen - verstaendlich, denn davon war
                # gerade die Rede. Es ist die Zeit der kurzen Probefrage.
                f"  Probefrage  : {probe['dauer_s']} s bis zur Antwort",
                f"  Tempo       : {probe['token_je_sekunde']} Token je Sekunde",
                *self._tempo_zeilen(probe["token_je_sekunde"]),
                "", "Probeantwort:", "  " + probe.get("text", ""),
            ]
        else:
            zeilen += ["Das Modell liegt vor, hat aber nicht geantwortet:",
                       "  " + str(probe.get("grund", "ohne Angabe"))]
        self._write_modell_log("\n".join(zeilen))
        self._refresh_modell(protokoll=False)
        self._refresh_status()
        if probe.get("ok"):
            messagebox.showinfo(
                "Sprachmodell",
                "Das Sprachmodell ist einsatzbereit.\n\n"
                "Zur Kontrolle wurde ihm eine kurze Probefrage gestellt. "
                f"Darauf hat es nach {probe['dauer_s']} Sekunden geantwortet.\n\n"
                "Diese Zahl sagt nichts darueber, wie lange das "
                "Herunterladen gedauert hat, und auch noch nichts ueber "
                "richtige Fachfragen: die sind laenger und brauchen "
                "deutlich mehr Zeit. Was Sie im Alltag erwartet, misst der "
                "Knopf \u201eWartezeit messen\u201c.\n\n"
                "Ab der naechsten Frage formuliert der Buchhalter wieder "
                "Fachantworten.",
                parent=self.root)
        else:
            messagebox.showwarning(
                "Sprachmodell",
                "Das Modell liegt vor, hat aber nicht geantwortet:\n\n"
                + str(probe.get("grund", "ohne Angabe")), parent=self.root)

    def _tempo_zeilen(self, token_je_sekunde: float) -> list[str]:
        """Ordnet die gemessene Geschwindigkeit ein - und nennt den Hebel.

        "0,3 Token je Sekunde" ist keine Auskunft. Der Benutzer will wissen,
        ob das normal ist und was daran zu aendern waere. Beides steht hier -
        ohne etwas zu versprechen, was auf reiner CPU nicht geht.
        """
        from pkc.hardware import modelleignung, tempoeinschaetzung

        einschaetzung = tempoeinschaetzung(token_je_sekunde)
        zeilen = [f"  Einordnung  : {einschaetzung['stufe']} - {einschaetzung['text']}"]
        if einschaetzung["stufe"] in ("langsam", "sehr langsam"):
            quelle = self._gewaehlte_quelle() or {}
            hardware = getattr(self, "_modell_lage", {}).get("hardware", {})
            eignung = modelleignung(quelle.get("min_ram_gb", 0),
                                    hardware.get("arbeitsspeicher_gb"),
                                    quelle.get("groesse_gb", 0.0))
            zeilen += ["", "  Was hilft:"]
            if eignung["stufe"] in ("knapp", "zu_gross"):
                zeilen.append("    - ein kleineres Modell waehlen (Auswahl oben). "
                              "Das ist hier der groesste Hebel.")
            zeilen += [
                "    - der mitgelieferte Modelldienst rechnet nur auf der CPU. "
                "Mit einer",
                "      Grafikkarte waere es ein Vielfaches - dafuer braucht es "
                "eine",
                "      GPU-Fassung von llama.cpp in runtime\\llama und "
                "Einstellungen und",
                "      Status -> Grafikschichten groesser 0.",
            ]
            if hardware.get("grafik"):
                zeilen.append(f"      Erkannt wurde: {hardware['grafik']}")
        return zeilen

    @staticmethod
    def _dauer_text(sekunden: float) -> str:
        """Sekunden so schreiben, wie eine Stoppuhr sie anzeigt.

        "500.0 s" muss der Benutzer selbst umrechnen, um es mit seiner
        Stoppuhr zu vergleichen. "8 Min 20 Sek" nicht.
        """
        sekunden = float(sekunden or 0.0)
        if sekunden < 60:
            return f"{sekunden:.1f} Sekunden"
        minuten, rest = divmod(int(round(sekunden)), 60)
        return f"{minuten} Min {rest} Sek ({sekunden:.0f} Sekunden)"

    def _modell_messen(self) -> None:
        """Misst die Wartezeit an zwei echten Fachfragen.

        Dauert ein bis zwei Minuten und sagt mehr als "Modell ausprobieren":
        dort geht eine kurze Frage an das Modell, hier zwei richtige - mit
        Recherche, Fundstellen und allem, was eine echte Antwort kostet.
        """
        if self.busy:
            return
        if not messagebox.askyesno(
            "Wartezeit messen",
            "Es werden zwei echte Fachfragen gestellt und die Zeiten "
            "gemessen.\n\n"
            "Das dauert ein bis zwei Minuten. Vorher wartet die Messung ab, "
            "bis das Sprachmodell geladen ist - genau wie Sie es im Alltag "
            "erleben.\n\nJetzt messen?",
            parent=self.root,
        ):
            return

        self._set_busy(True, "Die Wartezeit wird gemessen ...")

        def done(ergebnis: dict | None, error: Exception | None) -> None:
            self._set_busy(False)
            if error is not None:
                messagebox.showerror("Wartezeit messen", str(error), parent=self.root)
                return
            zeilen = ["Wartezeit - gemessen auf diesem Rechner", ""]
            for nummer, gestellt in enumerate(ergebnis["fragen"], start=1):
                zeilen.append(f"  Frage {nummer}: {gestellt}")
            zeilen.append(f"  Tempostufe: {ergebnis['tempo']}")
            dienst = ergebnis.get("dienst", {})
            if dienst.get("fassung"):
                auf = "Grafikkarte" if dienst.get("gpu_schichten") else "Prozessor"
                zeilen.append(f"  Modelldienst: {dienst['fassung']} "
                              f"(rechnet auf: {auf})")
            aufteilung = dienst.get("zeitaufteilung") or {}
            if aufteilung:
                # Das Protokoll des Modelldienstes sagt, wohin die Zeit
                # geht. Beide Anteile verlangen verschiedene Massnahmen -
                # ohne die Aufteilung raet man.
                verarbeiten = aufteilung.get("verarbeiten") or {}
                schreiben = aufteilung.get("schreiben") or {}
                if verarbeiten:
                    zeilen.append(
                        f"  Frage verarbeiten: {verarbeiten['sekunden']} s "
                        f"fuer {verarbeiten['tokens']} Textbausteine")
                if schreiben:
                    zeilen.append(
                        f"  Antwort schreiben: {schreiben['sekunden']} s "
                        f"fuer {schreiben['tokens']} Textbausteine")
            if ergebnis.get("bereit_nach_s"):
                zeilen.append(f"  Warten auf die Bereitschaft: "
                              f"{ergebnis['bereit_nach_s']} s "
                              "(beim Start laeuft das nebenher)")
            zeilen += ["", f"  {'Durchgang':11}{'1. Wort':>10}{'gesamt':>10}   Bemerkung"]
            for lauf in ergebnis["laeufe"]:
                if not lauf.get("ok"):
                    zeilen.append(f"  {lauf['nummer']:<11}{'-':>10}{'-':>10}   "
                                  + str(lauf.get("grund", "")))
                    continue
                bemerkung = ("erste Frage, Anwendung bereit" if lauf["nummer"] == 1
                             else "andere Frage, im laufenden Betrieb")
                zeilen.append(f"  {lauf['nummer']:<11}{lauf['erstes_wort_s']:>9.1f}s"
                              f"{lauf['gesamt_s']:>9.1f}s   {bemerkung}")

            if ergebnis["ok"]:
                zeilen += [
                    "",
                    "Massgeblich ist die Zeit bis zum ersten Wort: danach laeuft",
                    "die Antwort sichtbar weiter, man liest mit statt zu warten.",
                    "",
                    f"Im laufenden Betrieb: {ergebnis['im_betrieb_erstes_wort_s']} s "
                    "bis zum ersten Wort.",
                ]
            # Die Stoppuhrzeit gehoert dazu - auch wenn nichts geantwortet
            # hat. Wer acht Minuten gewartet hat und darueber zwei Zeilen
            # mit je zwei Minuten liest, haelt die Anzeige sonst fuer
            # falsch. Sie ist es nicht; sie war nur unvollstaendig.
            if ergebnis.get("messdauer_s"):
                zeilen += [
                    "",
                    f"Gesamte Messdauer (Stoppuhr): "
                    f"{self._dauer_text(ergebnis['messdauer_s'])}.",
                    "Darin enthalten: das Warten auf die Bereitschaft, beide",
                    "Fragen samt Recherche und das vollstaendige Schreiben",
                    "beider Antworten. Die Zeilen oben nennen die Teilzeiten.",
                ]
            wieder = ergebnis.get("prompt_wiederverwendung") or {}
            if wieder:
                zeilen += [
                    "",
                    "Prompt-Anfang wiederverwendet: "
                    + ("ja" if wieder["greift"] else "NEIN"),
                    f"  erster Durchgang : {wieder['tokens_erster_lauf']} "
                    "Textbausteine verarbeitet",
                    f"  zweiter Durchgang: {wieder['tokens_spaeterer_lauf']} "
                    f"Textbausteine verarbeitet ({wieder['rueckgang_prozent']} % "
                    "weniger)",
                ]
            else:
                zeilen += ["", "Es hat kein Sprachmodell geantwortet."]
            self._write_modell_log("\n".join(zeilen))
            (messagebox.showinfo if ergebnis["ok"] else messagebox.showwarning)(
                "Wartezeit messen",
                (f"Im laufenden Betrieb: "
                 f"{ergebnis['im_betrieb_erstes_wort_s']} s bis zum ersten Wort.\n\n"
                 f"Die ganze Messung hat "
                 f"{self._dauer_text(ergebnis.get('messdauer_s', 0))} gedauert - "
                 "sie umfasst zwei vollstaendige Fragen samt Recherche.\n\n"
                 "Die Einzelheiten stehen unten im Textbereich - Sie koennen "
                 "sie mit der Maus markieren und kopieren.")
                if ergebnis["ok"] else "Es hat kein Sprachmodell geantwortet.",
                parent=self.root)

        BackgroundTask(self.root).run(self.controller.modell_messen, done)

    def _modell_probe(self) -> None:
        """Stellt dem Modell eine Frage - der Nachweis, nicht die Behauptung."""
        if self.busy:
            return
        self._set_busy(True, "Das Sprachmodell wird gefragt ...")

        def done(probe: dict | None, error: Exception | None) -> None:
            self._set_busy(False)
            if error is not None:
                messagebox.showerror("Sprachmodell", str(error), parent=self.root)
                return
            if probe.get("ok"):
                self._write_modell_log(
                    "Das Sprachmodell hat geantwortet.\n"
                    f"  Anbieter    : {probe.get('anbieter', '?')}\n"
                    f"  Modell      : {probe.get('modell', '?')}\n"
                    f"  Antwortzeit : {probe['dauer_s']} s\n"
                    f"  Tempo       : {probe['token_je_sekunde']} Token je Sekunde\n"
                    + "\n".join(self._tempo_zeilen(probe["token_je_sekunde"]))
                    + "\n\nProbeantwort:\n  " + probe.get("text", ""))
            else:
                self._write_modell_log(
                    "Es hat kein Sprachmodell geantwortet.\n  "
                    + str(probe.get("grund", "ohne Angabe")))

        BackgroundTask(self.root).run(self.controller.modell_probe, done)

    # -- Bereiche in Vorbereitung ---------------------------------------
    def _build_pending_tab(self, kennung: str, titel: str, untertitel: str,
                           zeichen: str, zweck: list[str], heute: str,
                           weg=None, kurz: str = "") -> None:
        """Ein Bereich, den es noch nicht gibt - ehrlich gekennzeichnet.

        Auftrag Abschnitt 34 laesst genau zwei Moeglichkeiten: eine Aktion
        funktioniert, oder sie ist eindeutig als nicht verfuegbar
        gekennzeichnet. Hier gilt die zweite. Es gibt deshalb **keinen**
        Knopf, der nichts tut - sondern eine Erklaerung, was der Bereich
        koennen wird, und den Weg, der heute stattdessen zum Ziel fuehrt.

        Den Bereich ganz wegzulassen waere die schlechtere Loesung: der
        Zielentwurf nennt zehn Bereiche, und wer nur acht sieht, sucht die
        beiden anderen.
        """
        frame = self.schale.bereich_anlegen(kennung, titel, untertitel, zeichen,
                                            kurz=kurz)

        karte = tk.Frame(frame, bg=KARTE, highlightbackground=RAND,
                         highlightthickness=1)
        karte.pack(fill="x", pady=(0, PAD))
        innen = tk.Frame(karte, bg=KARTE)
        innen.pack(fill="x", padx=20, pady=18)

        tk.Label(innen, text="Dieser Bereich ist noch nicht verfuegbar.",
                 bg=KARTE, fg="#9a6512", anchor="w",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(innen, bg=KARTE, fg=LEISE, anchor="w", justify="left",
                 wraplength=760, font=("Segoe UI", 9),
                 text="Er ist geplant und beauftragt, aber noch nicht gebaut. "
                      "Damit hier nichts steht, was nicht funktioniert, gibt "
                      "es vorerst keine Schaltflaechen.").pack(anchor="w",
                                                               pady=(6, 0))

        tk.Label(innen, text="Was der Bereich koennen wird:", bg=KARTE,
                 fg=TEXT, anchor="w",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(16, 4))
        for punkt in zweck:
            tk.Label(innen, text=f"   \u2022  {punkt}", bg=KARTE,
                     fg="#42556e", anchor="w", justify="left", wraplength=740,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=1)

        tk.Label(innen, text="Was heute schon geht:", bg=KARTE,
                 fg=TEXT, anchor="w",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(16, 4))
        tk.Label(innen, text=heute, bg=KARTE, fg="#42556e", anchor="w",
                 justify="left", wraplength=740,
                 font=("Segoe UI", 9)).pack(anchor="w")

        if weg is not None:
            kennung_ziel, beschriftung = weg
            ttk.Button(innen, text=beschriftung,
                       command=lambda k=kennung_ziel: self.schale.zeigen(k)
                       ).pack(anchor="w", pady=(14, 0))

    def _build_templates_tab(self) -> None:
        self._build_pending_tab(
            "vorlagen", "Vorlagen",
            "Wiederverwendbare Word-, Excel-, PowerPoint- und Fachvorlagen.",
            "\u25a7",
            ["Vorlagen durchsuchen und nach Kategorien ordnen",
             "Eine Vorlage mit Unternehmens- und Profildaten fuellen lassen",
             "Vorschau vor dem Erzeugen",
             "Eigene Unternehmensvorlagen aufnehmen"],
            "PORTIVA erzeugt Dateien bereits in neun Formaten - aus einer "
            "Antwort heraus ueber \u201eAntwort speichern\u201c in der "
            "Unterhaltung. Was fehlt, ist die Verwaltung wiederverwendbarer "
            "Vorlagen.",
            weg=("arbeitsergebnisse", "Zu den Arbeitsergebnissen"))

    def _build_tasks_tab(self) -> None:
        self._build_pending_tab(
            "aufgaben", "Aufgaben & Automationen",
            "Geplante Pruefungen, wiederkehrende Arbeiten und Freigaben im "
            "Blick behalten.", "\u25f7",
            ["Aufgaben fuer heute, geplant und wiederkehrend",
             "Zeitpunkt, Ausloeser, Profil und Aktion festlegen",
             "Aktivieren, pausieren, sofort ausfuehren",
             "Letzte und naechste Ausfuehrung mit Ergebnis"],
            "Die Wissensaktualisierung hat bereits einen Zeitplan mit "
            "Faelligkeit und Intervall - zu finden unter "
            "\u201eWissen & Quellen\u201c. Ein allgemeiner Aufgabenplaner "
            "fehlt noch.",
            weg=("wissen_quellen", "Zu Wissen & Quellen"), kurz="Aufgaben")

    # -- Bereich: Plugins ----------------------------------------------
    def _build_plugins_tab(self) -> None:
        """Faehigkeiten installieren, Berechtigungen pruefen, sicher verwalten.

        Die Pluginverwaltung gab es vollstaendig - nur ueber die Konsole.
        Wer die Anwendung per Doppelklick oeffnet, hat keine offen.
        """
        frame = self.schale.bereich_anlegen(
            "plugins", "Plugins & Erweiterungen",
            "Faehigkeiten installieren, Berechtigungen pruefen und sicher "
            "verwalten.", "\u25c8", kurz="Plugins")

        leiste = ttk.Frame(frame)
        leiste.pack(fill="x", pady=(0, PAD))
        ttk.Button(leiste, text="Aus Datei installieren",
                   command=self._plugin_installieren).pack(side="left")
        for text, befehl in (("Aktivieren", lambda: self._plugin_schalten(True)),
                             ("Deaktivieren", lambda: self._plugin_schalten(False)),
                             ("Berechtigungen", self._plugin_rechte),
                             ("Deinstallieren", self._plugin_entfernen),
                             ("Aktualisieren", self._refresh_plugins)):
            ttk.Button(leiste, text=text, command=befehl).pack(side="left", padx=(PAD, 0))
        self.plugins_hint = ttk.Label(leiste, text="", foreground=LEISE)
        self.plugins_hint.pack(side="right")

        spalten = ("id", "name", "version", "kategorie", "zustand", "signatur")
        self.plugins_tree = ttk.Treeview(frame, columns=spalten, show="headings")
        for spalte, kopf, breite in (
            ("id", "Kennung", 160), ("name", "Name", 240),
            ("version", "Version", 90), ("kategorie", "Kategorie", 140),
            ("zustand", "Zustand", 120), ("signatur", "Signatur", 160),
        ):
            self.plugins_tree.heading(spalte, text=kopf)
            self.plugins_tree.column(spalte, width=breite, anchor="w")
        self.plugins_tree.pack(fill="both", expand=True)

        self.plugins_log = scrolledtext.ScrolledText(frame, height=7, wrap="word",
                                                     font=FONT_MONO)
        self.plugins_log.pack(fill="x", pady=(PAD, 0))
        self.plugins_log.configure(state="disabled")
        self._refresh_plugins()

    def _refresh_plugins(self) -> None:
        if not hasattr(self, "plugins_tree"):
            return
        self.plugins_tree.delete(*self.plugins_tree.get_children())
        eintraege = self.controller.plugin_liste()
        for eintrag in eintraege:
            if eintrag.get("fehler"):
                zustand = "fehlerhaft"
            else:
                zustand = "aktiv" if eintrag.get("aktiv") else "installiert"
            if not eintrag.get("signiert"):
                signatur = "nicht signiert"
            elif eintrag.get("signatur_gueltig"):
                signatur = "gueltig"
            else:
                signatur = "UNGUELTIG"
            self.plugins_tree.insert("", "end", values=(
                eintrag.get("id", ""), eintrag.get("name", ""),
                eintrag.get("version", ""), eintrag.get("kategorie", ""),
                zustand, signatur,
            ))
        self.plugins_hint.configure(
            text=f"{len(eintraege)} installiert" if eintraege
            else "Noch keine Plugins installiert")

    def _gewaehltes_plugin(self) -> str:
        auswahl = self.plugins_tree.selection()
        if not auswahl:
            messagebox.showinfo("Plugins", "Bitte zuerst ein Plugin auswaehlen.",
                                parent=self.root)
            return ""
        return str(self.plugins_tree.item(auswahl[0])["values"][0])

    def _plugin_schreiben(self, text: str) -> None:
        self.plugins_log.configure(state="normal")
        self.plugins_log.delete("1.0", "end")
        self.plugins_log.insert("1.0", text)
        self.plugins_log.configure(state="disabled")

    def _plugin_installieren(self) -> None:
        """Erst pruefen, dann fragen, dann installieren.

        Ein Plugin laeuft mit den Rechten der Anwendung. Es ohne Rueckfrage
        zu installieren waere derselbe Fehler wie ein Modellbezug ohne
        Bestaetigung - nur mit groesserer Wirkung.
        """
        pfad = filedialog.askopenfilename(
            title="Pluginpaket auswaehlen",
            filetypes=[("PORTIVA-Plugin", "*.kimplug"), ("Alle Dateien", "*.*")],
            parent=self.root)
        if not pfad:
            return
        try:
            bericht = self.controller.plugins.pruefen(Path(pfad))
        except Exception as fehler:
            messagebox.showerror("Plugin pruefen", str(fehler), parent=self.root)
            return

        angaben = bericht.as_dict() if hasattr(bericht, "as_dict") else dict(bericht)
        rechte = self.controller.plugins.rechtebeschreibung(
            angaben.get("berechtigungen") or angaben.get("verlangt") or [])
        text = "\n".join([
            f"Name        : {angaben.get('name', '?')}",
            f"Version     : {angaben.get('version', '?')}",
            f"Kategorie   : {angaben.get('kategorie', '?')}",
            f"Herausgeber : {angaben.get('autor', '?')}",
            f"Signatur    : {'vorhanden' if angaben.get('signiert') else 'keine'}",
            "", "Verlangte Berechtigungen:",
            *(f"  - {r}" for r in (rechte or ["(keine)"])),
        ])
        self._plugin_schreiben(text)

        if not messagebox.askyesno(
            "Plugin installieren",
            text + "\n\nEin Plugin laeuft mit den Rechten der Anwendung.\n"
            "Installieren Sie es nur, wenn Sie der Herkunft trauen.\n\n"
            "Jetzt installieren?",
            parent=self.root,
        ):
            return
        try:
            self.controller.plugins.installieren(Path(pfad), bestaetigt=True)
        except Exception as fehler:
            messagebox.showerror("Installation", str(fehler), parent=self.root)
            return
        self._refresh_plugins()
        messagebox.showinfo(
            "Installation",
            "Installiert. Aktivieren Sie das Plugin, damit seine Faehigkeit "
            "beim naechsten Start bereitsteht.", parent=self.root)

    def _plugin_schalten(self, aktiv: bool) -> None:
        kennung = self._gewaehltes_plugin()
        if not kennung:
            return
        try:
            self.controller.plugin_schalten(kennung, aktiv)
        except Exception as fehler:
            messagebox.showerror("Plugins", str(fehler), parent=self.root)
            return
        self._refresh_plugins()
        self._plugin_schreiben(
            f"{kennung} ist jetzt {'aktiv' if aktiv else 'deaktiviert'}.\n"
            "Die Aenderung wirkt beim naechsten Programmstart vollstaendig.")

    def _plugin_rechte(self) -> None:
        kennung = self._gewaehltes_plugin()
        if not kennung:
            return
        eintrag = next((p for p in self.controller.plugin_liste()
                        if p.get("id") == kennung), {})
        zeilen = [f"Berechtigungen von {eintrag.get('name', kennung)}", ""]
        zeilen += [f"  - {r}" for r in (eintrag.get("rechte_text") or ["(keine)"])]
        erteilt = eintrag.get("berechtigungen") or []
        zeilen += ["", "Tatsaechlich erteilt:",
                   *(f"  - {r}" for r in (erteilt or ["(keine)"]))]
        self._plugin_schreiben("\n".join(zeilen))

    def _plugin_entfernen(self) -> None:
        kennung = self._gewaehltes_plugin()
        if not kennung:
            return
        if not messagebox.askyesno(
            "Deinstallieren",
            f"{kennung} entfernen?\n\nDie Faehigkeit steht danach nicht mehr "
            "zur Verfuegung. Bereits erzeugte Dateien bleiben erhalten.",
            parent=self.root,
        ):
            return
        try:
            self.controller.plugins.entfernen(kennung)
        except Exception as fehler:
            messagebox.showerror("Deinstallieren", str(fehler), parent=self.root)
            return
        self._refresh_plugins()

    # -- Bereich: Verbundene Dienste -----------------------------------
    def _build_services_tab(self) -> None:
        frame = self.schale.bereich_anlegen(
            "dienste", "Verbundene Dienste",
            "Externe Konten und Unternehmenssysteme sicher verbinden.",
            "\u26ad")

        leiste = ttk.Frame(frame)
        leiste.pack(fill="x", pady=(0, PAD))
        for text, befehl in (("Verbindung testen", self._dienst_testen),
                             ("Trennen", self._dienst_trennen),
                             ("Aktualisieren", self._refresh_services)):
            ttk.Button(leiste, text=text, command=befehl).pack(side="left", padx=(0, PAD))
        self.services_hint = ttk.Label(leiste, text="", foreground=LEISE)
        self.services_hint.pack(side="right")

        spalten = ("id", "name", "system", "modus", "zustand")
        self.services_tree = ttk.Treeview(frame, columns=spalten, show="headings")
        for spalte, kopf, breite in (
            # "DATEV Rechnungswesen / Unternehmen online" ist der laengste
            # Systemname und wurde bei 180 abgeschnitten. Die Kennung
            # daneben braucht dafuer weniger.
            ("id", "Kennung", 120), ("name", "Dienst", 230),
            ("system", "System", 300), ("modus", "Betrieb", 110),
            ("zustand", "Zustand", 150),
        ):
            self.services_tree.heading(spalte, text=kopf)
            self.services_tree.column(spalte, width=breite, anchor="w")
        self.services_tree.pack(fill="both", expand=True)

        self.services_log = scrolledtext.ScrolledText(frame, height=7, wrap="word",
                                                      font=FONT_MONO)
        self.services_log.pack(fill="x", pady=(PAD, 0))
        self.services_log.configure(state="disabled")
        self._refresh_services()

    def _refresh_services(self) -> None:
        if not hasattr(self, "services_tree"):
            return
        self.services_tree.delete(*self.services_tree.get_children())
        eintraege = self.controller.dienste()
        for eintrag in eintraege:
            self.services_tree.insert("", "end", values=(
                eintrag.get("id", ""), eintrag.get("name", ""),
                eintrag.get("system", ""), eintrag.get("modus", ""),
                "verbunden" if eintrag.get("verbunden") else "nicht verbunden",
            ))
        verbunden = sum(1 for e in eintraege if e.get("verbunden"))
        self.services_hint.configure(
            text=f"{verbunden} von {len(eintraege)} verbunden")
        self._dienst_schreiben(
            "Zugangsdaten liegen ausschliesslich verschluesselt im Tresor auf "
            "diesem Datentraeger. Sie werden nirgends im Klartext angezeigt "
            "oder abgelegt.")

    def _dienst_schreiben(self, text: str) -> None:
        self.services_log.configure(state="normal")
        self.services_log.delete("1.0", "end")
        self.services_log.insert("1.0", text)
        self.services_log.configure(state="disabled")

    def _gewaehlter_dienst(self) -> str:
        auswahl = self.services_tree.selection()
        if not auswahl:
            messagebox.showinfo("Verbundene Dienste",
                                "Bitte zuerst einen Dienst auswaehlen.",
                                parent=self.root)
            return ""
        return str(self.services_tree.item(auswahl[0])["values"][0])

    def _dienst_testen(self) -> None:
        kennung = self._gewaehlter_dienst()
        if not kennung:
            return
        ergebnis = self.controller.dienst_testen(kennung)
        self._dienst_schreiben(f"{kennung}: {ergebnis['meldung']}")
        (messagebox.showinfo if ergebnis["ok"] else messagebox.showwarning)(
            "Verbindung testen", ergebnis["meldung"], parent=self.root)

    def _dienst_trennen(self) -> None:
        kennung = self._gewaehlter_dienst()
        if not kennung:
            return
        if not messagebox.askyesno(
            "Trennen",
            f"Die Zugangsdaten fuer {kennung} aus dem Tresor entfernen?\n\n"
            "Bereits uebernommene Daten im Unternehmensgedaechtnis bleiben "
            "erhalten - deren Loeschung ist eine eigene Entscheidung.",
            parent=self.root,
        ):
            return
        entfernt = self.controller.dienst_trennen(kennung)
        self._refresh_services()
        self._dienst_schreiben(
            f"{kennung}: Zugangsdaten entfernt." if entfernt
            else f"{kennung}: Es waren keine Zugangsdaten hinterlegt.")

    # -- Registerkarte: Einstellungen ----------------------------------
    def _build_settings_tab(self) -> None:
        frame = self.schale.bereich_anlegen(
            "einstellungen", "Einstellungen & Status",
            "Betriebsmodus, Modelle, Speicher, Sicherheit und Systemstatus.",
            "\u2699")

        # Gruppen statt einer langen Spalte (Auftrag Abschnitt 30). Das
        # Sprachmodell zieht hier ein - es ist kein eigener Hauptbereich,
        # sondern eine Einstellung. Damit sind es genau die zehn Bereiche
        # des Zielentwurfs.
        # Raster: die Einstellungen wachsen, die Statusspalte hat eine
        # feste Breite. Mit "pack(side=right, expand=True)" bekam die
        # Statusspalte nur den Rest - und der reichte nicht: "Lokales
        # Modell" und "nicht eingerichtet" lagen uebereinander, von
        # "Sicherung erstellen" blieb ein "S".
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0, minsize=STATUS_BREITE)
        frame.rowconfigure(0, weight=1)

        # Karten statt Karteireiter - wie in den Vorlagen. Die
        # Schnittstelle ist dieselbe wie beim Notebook (``add`` mit
        # ``text``), deshalb bleibt der Code, der die Inhalte baut,
        # unveraendert. Genau darum geht es bei einem Umbau der
        # Oberflaeche: der Rahmen wechselt, der Inhalt nicht.
        from ui.schale import Kartenwahl

        self.einstellungsgruppen = Kartenwahl(frame)
        self.einstellungsgruppen.rahmen.grid(row=0, column=0, sticky="nsew")

        left = ttk.Frame(self.einstellungsgruppen.buehne)
        self.einstellungsgruppen.add(
            left, text="Allgemein",
            untertitel="Wissensupdate, Speichern, Protokollierung")

        self.gruppe_modelle = ttk.Frame(self.einstellungsgruppen.buehne)
        self.einstellungsgruppen.add(
            self.gruppe_modelle, text="KI & Modelle",
            untertitel="Sprachmodell, Antworttempo, Rechenleistung")

        ttk.Label(left, text="Einstellungen", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.setting_vars: dict[str, tk.Variable] = {}

        def add_choice(label: str, key: str, values: list[str]) -> None:
            row = ttk.Frame(left)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=32).pack(side="left")
            var = tk.StringVar(value=str(self.controller.config.get(key)))
            ttk.Combobox(row, textvariable=var, values=values, state="readonly",
                         width=24).pack(side="left")
            self.setting_vars[key] = var

        def add_check(label: str, key: str) -> None:
            var = tk.BooleanVar(value=bool(self.controller.config.get(key)))
            ttk.Checkbutton(left, text=label, variable=var).pack(anchor="w", pady=2)
            self.setting_vars[key] = var

        add_choice("Zeitplan Wissensupdate", "updates.schedule",
                   ["manual", "weekly", "monthly", "custom"])
        add_choice("Fundstellen je Antwort", "retrieval.top_k", ["4", "6", "8", "12", "16"])
        add_check("Dauerhafte Unternehmensinformationen erkennen", "memory.auto_capture")
        add_check("Vor dem Speichern nachfragen", "memory.confirm_before_store")
        add_check("Online-Sprachmodell erlauben (optional)", "network.allow_online_llm")
        add_check("Protokollierung aktiv", "security.audit_enabled")

        # Geschwindigkeit des Sprachmodells. Der mitgelieferte Modelldienst
        # rechnet auf der CPU; wer eine GPU-Fassung von llama.cpp in
        # runtime\llama legt, kann hier Schichten auf die Grafikkarte
        # verlagern. 0 heisst: alles auf der CPU.
        from pkc.llm import tempo as _tempo

        ttk.Label(left, text="Sprachmodell - Geschwindigkeit",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(PAD, 2))
        # Der wirksamste Regler zuerst: er bestimmt Antwortlaenge,
        # Kontextgroesse, Zahl der Fundstellen und Verlaufstiefe in einem
        # abgestimmten Satz. Diese vier Werte gegeneinander von Hand
        # einzustellen gelingt niemandem.
        add_choice("Antworttempo", "llm.tempo",
                   [_tempo.AUTOMATISCH, *_tempo.namen()])
        # Was "automatisch" auf DIESEM Rechner gerade bedeutet, muss
        # dastehen. Eine Einstellung, deren Wirkung man nicht sehen kann,
        # ist keine Einstellung, sondern ein Versprechen.
        gewaehlt = self.controller.tempostufe()
        ttk.Label(left, wraplength=430, justify="left", foreground="#555555",
                  text=("automatisch: richtet sich nach diesem Rechner und dem "
                        f"eingerichteten Modell - hier gerade \"{gewaehlt}\".")
                  ).pack(anchor="w", pady=(0, 2))
        ttk.Label(left, wraplength=430, justify="left", foreground="#555555",
                  text=" · ".join(f"{n}: {_tempo.stufe(n)['beschreibung']}"
                                  for n in _tempo.namen())
                  ).pack(anchor="w", pady=(0, 4))
        add_choice("Grafikschichten (0 = nur CPU)", "llm.gpu_layers",
                   ["0", "10", "20", "35", "99"])
        add_choice("Rechenkerne (0 = automatisch)", "llm.threads",
                   ["0", "2", "4", "6", "8", "12", "16"])
        add_choice("Kontextgroesse", "llm.context_tokens",
                   ["2048", "4096", "8192", "16384"])
        ttk.Label(left, wraplength=430, justify="left", foreground="#555555",
                  text=("Grafikschichten wirken nur mit einer GPU-Fassung von "
                        "llama.cpp in runtime\\llama. Die mitgelieferte "
                        "Fassung rechnet auf der CPU - dort bringt der Wert "
                        "nichts. Eine kleinere Kontextgroesse spart "
                        "Arbeitsspeicher und beschleunigt knappe "
                        "Rechner.")).pack(anchor="w", pady=(0, PAD))

        ttk.Button(left, text="Einstellungen speichern", command=self._save_settings).pack(
            anchor="w", pady=PAD
        )

        # -- Systemstatus als Ampelliste --------------------------------
        right = tk.Frame(frame, bg=KARTE, highlightbackground=RAND,
                         highlightthickness=1, width=STATUS_BREITE)
        right.grid(row=0, column=1, sticky="nsew", padx=(PAD * 2, 0))
        # Die Kinder dieser Flaeche werden mit ``pack`` gesetzt - dann
        # zaehlt ``pack_propagate``, nicht ``grid_propagate``. Ohne das
        # zieht das breite Textfeld im Inneren die ganze Spalte auf und
        # die Einstellungen daneben werden eng.
        right.pack_propagate(False)
        right.grid_propagate(False)
        innen = tk.Frame(right, bg=KARTE)
        innen.pack(fill="both", expand=True, padx=18, pady=16)
        tk.Label(innen, text="Systemstatus", bg=KARTE, fg=TEXT,
                 font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(innen, text="Aktueller PORTIVA-Zustand", bg=KARTE,
                 fg=LEISE, font=("Segoe UI", 8), anchor="w").pack(fill="x")

        self.statusliste = tk.Frame(innen, bg=KARTE)
        self.statusliste.pack(fill="x", pady=(12, 0))
        self._statuszeilen: dict[str, tuple] = {}

        # Drei Knoepfe nebeneinander passen in diese Spalte nicht. Sie
        # standen vorher in einer Zeile und wurden am Rand abgeschnitten -
        # der dritte war nur noch ein "S". Untereinander haben sie Platz
        # und ihre volle Beschriftung.
        knoepfe = tk.Frame(innen, bg=KARTE)
        knoepfe.pack(fill="x", pady=(14, 0))
        ttk.Button(knoepfe, text="Status aktualisieren",
                   command=self._refresh_status).pack(fill="x")
        ttk.Button(knoepfe, text="Sicherung erstellen",
                   command=self._backup).pack(fill="x", pady=(6, 0))
        ttk.Button(knoepfe, text="Sicherung wiederherstellen",
                   command=self._wiederherstellen).pack(fill="x", pady=(6, 0))

        # Der vollstaendige Zustand als Text bleibt erhalten - er ist das,
        # was bei einer Stoerung kopiert und weitergegeben wird. Nur steht
        # er jetzt darunter statt an erster Stelle.
        ttk.Label(innen, text="Vollstaendiger Zustand zum Kopieren:",
                  foreground=LEISE).pack(anchor="w", pady=(14, 2))
        self.status_text = scrolledtext.ScrolledText(
            innen, wrap="word", font=FONT_MONO, height=12, state="disabled")
        self.status_text.pack(fill="both", expand=True)

    #: Wie ein Statuswert eingefaerbt wird. Alles, was nicht hier steht,
    #: gilt als neutral - lieber keine Farbe als eine falsche.
    STATUSFARBEN = {
        "gut": ("#e6f4ec", "#1c7a45"),
        "warnung": ("#fdf3e3", "#9a6512"),
        "fehler": ("#fdecec", "#a32626"),
        "neutral": ("#eef2f7", "#42556e"),
    }

    def _statuszeile(self, name: str, wert: str, art: str) -> None:
        """Eine Zeile der Ampelliste - beim ersten Mal anlegen, danach nur
        noch aendern. Sonst waechst die Liste bei jeder Aktualisierung."""
        grund, schrift = self.STATUSFARBEN.get(art, self.STATUSFARBEN["neutral"])
        if name in self._statuszeilen:
            _, wertlabel = self._statuszeilen[name]
            wertlabel.configure(text=wert, bg=grund, fg=schrift)
            return
        # Eine haarfeine Linie zwischen den Zeilen - wie in den Vorlagen.
        # Ohne sie schwimmen Name und Wert in der Flaeche und es ist auf
        # den ersten Blick nicht klar, welcher Wert zu welcher Zeile
        # gehoert. Die erste Zeile bekommt keine.
        if self._statuszeilen:
            tk.Frame(self.statusliste, bg="#eef2f7", height=1).pack(
                fill="x", pady=(4, 0))
        zeile = tk.Frame(self.statusliste, bg=KARTE)
        zeile.pack(fill="x", pady=5)
        # Der Wert zuerst und rechts, der Name danach mit dem Rest der
        # Breite. Umgekehrt nahm der Name so viel Platz, wie er wollte,
        # und schob den Wert aus der Spalte heraus.
        wertlabel = tk.Label(zeile, text=wert, bg=grund, fg=schrift,
                             font=("Segoe UI", 9, "bold"), padx=10, pady=3)
        wertlabel.pack(side="right")
        namelabel = tk.Label(zeile, text=name, bg=KARTE, fg=TEXT,
                             anchor="w", justify="left",
                             font=("Segoe UI", 9, "bold"))
        namelabel.pack(side="left", fill="x", expand=True)
        self._statuszeilen[name] = (namelabel, wertlabel)

    def _refresh_statusliste(self, status: dict) -> None:
        """Fuellt die Ampelliste aus dem Zustandsbericht.

        Die Bewertung ist bewusst zurueckhaltend: nur was eindeutig gut
        oder eindeutig fehlerhaft ist, bekommt Farbe. Eine gruene Ampel,
        die nichts bedeutet, ist schlimmer als gar keine.
        """
        if not hasattr(self, "statusliste"):
            return
        modell = status.get("lokales_modell") or {}
        modell_ok = bool(modell.get("verfuegbar") if isinstance(modell, dict)
                         else modell)
        wissen = status.get("wissensstand")
        plugins = status.get("plugins") or {}
        lizenz = str(status.get("lizenz", {}).get("status", "")
                     if isinstance(status.get("lizenz"), dict)
                     else status.get("lizenz", ""))

        self._statuszeile("PORTIVA Core", "OK", "gut")
        self._statuszeile(
            "Lokales Modell",
            "verfuegbar" if modell_ok else "nicht eingerichtet",
            "gut" if modell_ok else "warnung")
        self._statuszeile("Wissensindex", str(wissen)[:10] if wissen else "unbekannt",
                          "gut" if wissen else "warnung")
        self._statuszeile("Unternehmensgedaechtnis",
                          f"{status.get('gedaechtnis_eintraege', 0)} Eintraege",
                          "neutral")
        self._statuszeile("Arbeitsergebnisse",
                          f"{len(self.controller.artefakt_liste(limit=999))} Dateien",
                          "neutral")
        anzahl_plugins = plugins.get("aktiv", 0) if isinstance(plugins, dict) \
            else len(plugins or [])
        self._statuszeile("Plugins", f"{anzahl_plugins} aktiv", "neutral")
        self._statuszeile("Lizenz", lizenz or "keine Angabe",
                          "gut" if lizenz.lower() in ("gueltig", "valid", "ok")
                          else "neutral")

    def _build_statusbar(self) -> None:
        self.statusbar = ttk.Label(self.root, text="", relief="sunken", anchor="w")
        self.statusbar.pack(fill="x", side="bottom")

    # -- Chat ----------------------------------------------------------
    def _sprecherstil(self, who: str) -> str:
        if who == self._sprecher_ki:
            return "sprecher_ki"
        if who == self._sprecher_ich:
            return "sprecher_ich"
        return "wer"

    def _append_chat(self, who: str, text: str, tag: str = "") -> None:
        """Fuegt einen Beitrag ein - Markdown wird dabei ausgewertet.

        Ohne das stuenden ``**`` und ``#`` roh im Fenster (Abschnitt 7). Bei
        einem ausdruecklich gesetzten Stil (etwa Systemhinweise) bleibt der
        Text unveraendert; dort gibt es kein Markdown.
        """
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n{who}\n", self._sprecherstil(who))
        if tag:
            self.chat.insert("end", f"{text}\n", tag)
        elif who == self._sprecher_ich:
            # Die eigene Frage auf eigener Flaeche - wie in den Vorlagen.
            # Sie bekommt kein Markdown: was der Benutzer geschrieben hat,
            # wird gezeigt wie er es geschrieben hat.
            self.chat.insert("end", f"{text}\n", "frage")
        else:
            self._text_einfuegen(text)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _text_einfuegen(self, text: str) -> None:
        """Antwort oben, Anhang darunter - beides an der Einfuegestelle.

        Abschnitt 23: Quellen, Wissensstand, Freigabebedarf und Hinweise
        gehoeren unter die Antwort und duerfen sie nicht optisch erschlagen.
        Der Text selbst bleibt unveraendert - nur die Darstellung trennt.
        """
        teile = teilen(text)
        for stueck in zerlegen(teile.antwort):
            self.chat.insert("end", stueck.text,
                             stueck.stil if stueck.stil != "normal" else ())
        if teile.hat_anhang:
            self.chat.insert("end", "\n")
            for stueck in zerlegen(teile.anhang):
                stil = "anhang_kopf" if stueck.stil in (
                    "fett", "ueberschrift1", "ueberschrift2") else "anhang"
                self.chat.insert("end", stueck.text, stil)
        self.chat.insert("end", "\n")

    # -- Schrittweise Ausgabe (Abschnitt 21) ---------------------------
    def _strom_zuruecksetzen(self) -> None:
        """Verwirft, was bisher schrittweise angezeigt wurde - samt Namenszeile.

        Die Marke steht **vor** dem Namen. So bleibt nach einem Abbruch keine
        leere Sprechblase stehen, und ein zweiter Anbieter faengt sauber von
        vorn an.
        """
        if not getattr(self, "_strom_laeuft", False):
            return
        self.chat.configure(state="normal")
        self.chat.delete(MARKE_STROM, "end")
        self.chat.configure(state="disabled")
        self._strom_laeuft = False
        self._strom_leer = True

    def _strom_ausgeben(self) -> None:
        """Holt fertige Textstuecke aus dem Arbeitsfaden in das Fenster.

        Laeuft im Oberflaechen-Thread (ueber die Warteschleife der
        Hintergrundaufgabe) - Tkinter darf nur von dort bedient werden. Eine
        leere Zeichenkette bedeutet: der Anbieter hat abgebrochen, das bisher
        Gezeigte gilt nicht mehr.
        """
        puffer = getattr(self, "_strom_puffer", None)
        if puffer is None:
            return
        while True:
            try:
                stueck = puffer.get_nowait()
            except queue.Empty:
                return
            if stueck == "":
                self._strom_zuruecksetzen()
                continue
            if not getattr(self, "_strom_laeuft", False):
                # Erst beim ersten echten Textstueck erscheint der Name -
                # sonst stuende eine leere Sprechblase da, falls das Modell
                # gar nicht antwortet. Die Marke wird davor gesetzt: dann
                # laesst sich der ganze Beitrag wieder entfernen.
                self.chat.configure(state="normal")
                self.chat.mark_set(MARKE_STROM, "end-1c")
                self.chat.mark_gravity(MARKE_STROM, "left")
                self.chat.insert("end", f"\n{self._sprecher_ki}\n", "sprecher_ki")
                self.chat.configure(state="disabled")
                self._strom_laeuft = True
            self.chat.configure(state="normal")
            self.chat.insert("end", stueck)
            self.chat.configure(state="disabled")
            self.chat.see("end")
            self._strom_leer = False

    def _send(self) -> str:
        if self.busy:
            return "break"
        question = self.entry.get("1.0", "end").strip()
        if not question:
            return "break"
        self.entry.delete("1.0", "end")
        self._append_chat(self._sprecher_ich, question)
        self._frage_begonnen = time.monotonic()
        self._set_busy(True, "Der Buchhalter recherchiert lokal ...")

        # Abschnitt 21: Textstuecke kommen aus dem Arbeitsfaden, angezeigt
        # werden sie ausschliesslich im Oberflaechen-Thread.
        self._strom_puffer = queue.Queue()
        self._strom_laeuft = False
        self._strom_leer = True

        def work() -> AskOutcome:
            return self.controller.ask(question, on_token=self._strom_puffer.put)

        def done(outcome: AskOutcome | None, error: Exception | None) -> None:
            self._set_busy(False)
            self.stop_button.configure(state="disabled")
            self._laufende_aufgabe = None
            if isinstance(error, Abgebrochen):
                # Ein halber Absatz ohne Quellen und ohne Hinweise ist keine
                # Antwort. Er wird entfernt, statt stehenzubleiben.
                self._strom_zuruecksetzen()
                self._append_chat(
                    "System",
                    "Abgebrochen. Die Frage wurde gespeichert, es wurde nur keine "
                    "Antwort erzeugt.", "system")
                return
            if error is not None:
                self._strom_zuruecksetzen()
                self._append_chat("Fehler", f"{type(error).__name__}: {error}", "hinweis")
                return
            assert outcome is not None
            self._antwort_anzeigen(outcome.answer.text)
            self._datei_melden(outcome)
            self._show_sources(outcome)
            self._refresh_conversations()
            self._ask_about_candidates(outcome)

        self._laufende_aufgabe = BackgroundTask(self.root)
        self.stop_button.configure(state="normal")
        def takt() -> None:
            self._strom_ausgeben()
            self._wartestand_anzeigen()

        self._laufende_aufgabe.run(work, done, on_tick=takt)
        return "break"

    def _datei_melden(self, outcome) -> None:
        """Sagt in der Unterhaltung, dass eine Datei entstanden ist.

        Eine Datei, die stillschweigend im Ordner landet, ist fuer den
        Anwender keine erzeugte Datei - er weiss nichts von ihr. Deshalb
        steht es in der Unterhaltung, mit Namen und Ablageort, und die
        Liste der Arbeitsergebnisse wird gleich mit aufgefrischt.
        """
        datei = getattr(outcome, "datei", None)
        fehler = getattr(outcome, "datei_fehler", "")
        if datei is None and not fehler:
            return
        if fehler:
            self._append_chat(
                "System",
                "Die verlangte Datei konnte nicht erzeugt werden: "
                f"{fehler}", "hinweis")
            return
        self._append_chat(
            "System",
            f"Datei erzeugt: {datei.name} ({datei.format.upper()}, "
            f"{datei.groesse} Bytes)\n"
            f"Zu finden unter \u201eArbeitsergebnisse\u201c - dort laesst "
            "sie sich oeffnen, exportieren und umbenennen.",
            "system")
        try:
            self._refresh_results()
        except Exception:               # pragma: no cover - defensiv
            log.debug("Arbeitsergebnisse nicht auffrischbar", exc_info=True)

    def _wartestand_anzeigen(self) -> None:
        """Sagt waehrend des Wartens, worauf gewartet wird - und wie lange.

        Gemeldet wurde: viereinhalb Minuten bis zur ersten Antwort, und in
        der ganzen Zeit stand unveraendert "recherchiert lokal" da. Wer das
        sieht, haelt die Anwendung fuer haengend - zumal der groesste Teil
        dieser Zeit gar keine Recherche war, sondern das einmalige Laden des
        Modells.

        Die Zeit selbst wird dadurch nicht kuerzer. Aber eine Wartezeit, von
        der man weiss, wofuer sie ist und wie lange sie schon laeuft, ist
        etwas anderes als ein stehendes Fenster.
        """
        begonnen = getattr(self, "_frage_begonnen", None)
        if begonnen is None or not self.busy:
            return
        if getattr(self, "_strom_laeuft", False):
            stand = "Die Antwort wird geschrieben"
        elif not self.controller.modell_bereit():
            stand = "Das Sprachmodell wird geladen (einmalig nach dem Start)"
        else:
            stand = "Der Buchhalter recherchiert und denkt nach"
        self.statusbar.configure(
            text=f"{stand} - seit {self._dauer_text(time.monotonic() - begonnen)}")

    def _antwort_anzeigen(self, text: str) -> None:
        """Zeigt die fertige Antwort - notfalls anstelle des Stroms.

        Waehrend der Erzeugung steht der rohe Modelltext im Fenster. Am Ende
        tritt der gepruefte Text an seine Stelle: mit Quellenteil, Wissensstand
        und den Hinweisen der Anwendung, und in der lesbaren Darstellung. Was
        angezeigt bleibt, ist damit genau das, was auch gespeichert wurde.
        """
        self._strom_zuruecksetzen()
        self._append_chat(self._sprecher_ki, text)

    def _antwort_speichern(self) -> None:
        """Schreibt die letzte Antwort als Datei (Erweiterung E4)."""
        try:
            artefakt = self.controller.antwort_speichern(self.datei_format.get())
        except Exception as fehler:
            messagebox.showerror("Speichern", str(fehler), parent=self.root)
            return
        self._append_chat(
            "System",
            f"Gespeichert als {artefakt.format.upper()}:\n{artefakt.pfad}", "system")
        messagebox.showinfo("Gespeichert", f"{artefakt.pfad}", parent=self.root)

    def _abbrechen(self) -> None:
        """Bricht eine laufende Erzeugung ab (Abschnitt 22)."""
        if getattr(self, "_laufende_aufgabe", None) is not None:
            self._laufende_aufgabe.abbrechen()
            self.stop_button.configure(state="disabled")

    def _show_sources(self, outcome: AskOutcome) -> None:
        """Quellen ins rechte Panel - Technisches nur in die Details.

        Auftrag Abschnitt 18 und 19: die Quelle gehoert neben die Antwort,
        die Bewertungszahl nicht. Eine Zahl neben einer Gesetzesangabe
        sieht aus, als gehoere sie zur fachlichen Aussage.
        """
        #: Die zuletzt angezeigten Quellen - fuer die Recherche-Details und
        #: damit ein Test nachsehen kann, was wirklich herangezogen wurde.
        self._letzte_quellen = list(outcome.answer.references or [])
        self.quellenpanel.setzen(
            outcome.answer.used_references or outcome.answer.references,
            outcome.answer.references)

    def _ask_about_candidates(self, outcome: AskOutcome) -> None:
        for candidate in outcome.capture_candidates:
            keep = messagebox.askyesno(
                "Dauerhaft merken?",
                f"{candidate.question()}\n\n"
                f"Schluessel: {candidate.mem_key}\n"
                f"Erkennung: {candidate.rationale}\n\n"
                "Ja speichert die Angabe dauerhaft auf diesem Datentraeger.",
                parent=self.root,
            )
            if keep:
                self.controller.remember(candidate)
                self._append_chat(
                    "System", f"Dauerhaft gespeichert: {candidate.content}", "system"
                )
                self._refresh_memory()

    def _new_conversation(self) -> None:
        self.controller.new_conversation()
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self._append_chat("System", "Neue Unterhaltung begonnen.", "system")
        self._refresh_conversations()

    def _refresh_conversations(self) -> None:
        self.conversation_list.delete(0, "end")
        self._conversations = self.controller.conversations(limit=50)
        for item in self._conversations:
            marker = "* " if item["uid"] == self.controller.conversation_uid else "  "
            self.conversation_list.insert("end", f"{marker}{item['title'][:52]}")

    def _open_conversation(self, event=None) -> None:
        selection = self.conversation_list.curselection()
        if not selection:
            return
        item = self._conversations[selection[0]]
        self.controller.open_conversation(item["uid"])
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        for message in self.controller.messages(item["uid"]):
            who = {"user": self._sprecher_ich,
                   "assistant": self._sprecher_ki}.get(message["role"], "System")
            self._append_chat(who, message["content"])
        self._refresh_conversations()

    def _export_conversation(self) -> None:
        try:
            path = self.controller.export_conversation()
        except Exception as exc:
            messagebox.showerror("Export", str(exc), parent=self.root)
            return
        messagebox.showinfo("Export", f"Gespeichert:\n{path}", parent=self.root)

    # -- Belege --------------------------------------------------------
    def _add_document(self) -> None:
        filename = filedialog.askopenfilename(
            title="Beleg auswaehlen",
            filetypes=[("Alle unterstuetzten", "*.pdf *.txt *.md *.html *.htm *.xml *.csv"),
                       ("Alle Dateien", "*.*")],
            parent=self.root,
        )
        if not filename:
            return
        self._dokument_aufnehmen(Path(filename))

    def _dokument_aufnehmen(self, pfad: Path) -> None:
        """Nimmt eine Datei auf - egal ob ausgewaehlt oder hergezogen.

        Ein gemeinsamer Weg fuer beides. Zwei Wege haetten frueher oder
        spaeter zwei verschiedene Verhalten - und dann klappt es beim
        Auswaehlen und beim Ziehen nicht.
        """
        try:
            result = self.controller.add_document(pfad)
        except Exception as exc:
            messagebox.showerror("Beleg", str(exc), parent=self.root)
            return
        if result["status"] == "nicht_lesbar":
            messagebox.showwarning(
                "Beleg gespeichert, aber nicht lesbar",
                f"Die Datei wurde abgelegt, ihr Text konnte aber nicht ausgewertet werden.\n\n"
                f"{result.get('fehler', '')}",
                parent=self.root,
            )
        else:
            self._append_chat(
                "System",
                f"Beleg aufgenommen: {result['titel']} ({result['abschnitte']} Abschnitte).",
                "system",
            )
        self._refresh_documents()

    def _refresh_documents(self) -> None:
        for row in self.document_tree.get_children():
            self.document_tree.delete(row)
        eintraege = self.controller.documents()
        for item in eintraege:
            # Die Ergebnisspalte sagt, was die Analyse ergeben hat - und
            # sagt es auch dann, wenn sie nichts ergeben hat. Ein
            # Gedankenstrich laesst offen, ob nichts gefunden wurde oder
            # ob gar nichts passiert ist.
            abschnitte = int(item.get("abschnitte") or 0)
            if item["status"] == "nicht_lesbar":
                ergebnis = "Text nicht auswertbar"
            elif abschnitte:
                ergebnis = f"{abschnitte} Abschnitte erkannt"
            else:
                ergebnis = "aufgenommen, kein auswertbarer Text"
            self.document_tree.insert(
                "", "end",
                values=(item["title"], item["kind"] or "-", item["added_at"][:19],
                        item["status"], ergebnis, item["path"]),
            )
        if hasattr(self, "documents_hint"):
            self.documents_hint.configure(
                text=f"{len(eintraege)} Dokumente" if eintraege
                else "Noch keine Dokumente aufgenommen")

    def _gewaehlter_beleg(self) -> dict:
        """Der markierte Beleg - oder eine Meldung, was fehlt."""
        auswahl = self.document_tree.selection()
        if not auswahl:
            messagebox.showinfo("Belege", "Bitte zuerst ein Dokument auswaehlen.",
                                parent=self.root)
            return {}
        werte = self.document_tree.item(auswahl[0])["values"]
        titel = str(werte[0])
        return next((d for d in self.controller.documents()
                     if d["title"] == titel), {})

    def _beleg_oeffnen(self) -> None:
        beleg = self._gewaehlter_beleg()
        if not beleg:
            return
        if not self.controller.datei_oeffnen(beleg["path"]):
            messagebox.showwarning(
                "Oeffnen", f"{beleg['title']} liess sich nicht oeffnen.",
                parent=self.root)

    def _beleg_erneut(self) -> None:
        """Analysiert einen Beleg noch einmal.

        Sinnvoll, nachdem sich das Unternehmenswissen oder der
        Wissensstand geaendert hat: dieselbe Datei kann dann zu einem
        anderen Ergebnis fuehren.
        """
        beleg = self._gewaehlter_beleg()
        if not beleg:
            return
        pfad = Path(beleg["path"])
        if not pfad.is_file():
            messagebox.showwarning(
                "Erneut analysieren",
                f"Die abgelegte Datei ist nicht mehr da:\n{pfad}",
                parent=self.root)
            return
        self._dokument_aufnehmen(pfad)

    def _beleg_uebernehmen(self) -> None:
        """Uebergibt den Beleg an die laufende Unterhaltung.

        Es wird nichts automatisch gefragt - der Beleg wird genannt und die
        Frage vorbereitet. Was gefragt wird, entscheidet der Benutzer.
        """
        beleg = self._gewaehlter_beleg()
        if not beleg:
            return
        self.schale.zeigen("unterhaltung")
        self._append_chat(
            "System",
            f"Dokument uebernommen: {beleg['title']} "
            f"({beleg.get('kind') or 'ohne Typangabe'}). "
            "Es steht der naechsten Frage als Zusammenhang zur Verfuegung.",
            "system")
        self.entry.delete("1.0", "end")
        self.entry.insert("1.0", f"Zum Dokument \u201e{beleg['title']}\u201c: ")
        try:
            self.entry.focus_set()
        except Exception:               # pragma: no cover - defensiv
            pass

    # -- Unternehmenswissen --------------------------------------------
    #: Die Kacheln des Unternehmenswissens. Beschriftung und Reihenfolge
    #: folgen dem Zielentwurf; die Kategorien kommen aus dem Schema, damit
    #: sich beides nicht auseinanderentwickelt.
    WISSENSKACHELN = (
        ("Unternehmensprofil", ("profile", "organization")),
        ("Buchhaltung", ("accounting", "tax")),
        ("Prozesse & Regeln", ("process", "rule")),
        ("Personen & Rollen", ("people",)),
        ("Kunden & Lieferanten", ("case", "erp")),
        ("Vorlagen & Entscheidungen", ("approval", "preference")),
    )

    def _refresh_memory_kacheln(self) -> None:
        """Zaehlt die Eintraege je Kategorie und zeigt sie als Kacheln.

        Ein Klick filtert die Liste darunter. Eine Kachel, die nur eine
        Zahl anzeigt und sonst nichts tut, waere ein toter Knopf.
        """
        if not hasattr(self, "memory_kacheln"):
            return
        eintraege = self.controller.memory.list(limit=2000)
        anzahl: dict[str, int] = {}
        for eintrag in eintraege:
            anzahl[eintrag.category] = anzahl.get(eintrag.category, 0) + 1

        for spalte, (titel, kategorien) in enumerate(self.WISSENSKACHELN):
            summe = sum(anzahl.get(k, 0) for k in kategorien)
            if titel in self._memory_kachel_widgets:
                _, zahl_label = self._memory_kachel_widgets[titel]
                zahl_label.configure(text=f"{summe} Eintraege")
                continue
            kachel = tk.Frame(self.memory_kacheln, bg=KARTE,
                              highlightbackground=RAND, highlightthickness=1,
                              cursor="hand2")
            kachel.grid(row=spalte // 3, column=spalte % 3, sticky="ew",
                        padx=(0, 10), pady=(0, 10))
            innen = tk.Frame(kachel, bg=KARTE)
            innen.pack(fill="x", padx=16, pady=12)
            kopf = tk.Label(innen, text=titel, bg=KARTE, fg=TEXT,
                            anchor="w", font=("Segoe UI", 10, "bold"))
            kopf.pack(anchor="w")
            zahl = tk.Label(innen, text=f"{summe} Eintraege", bg=KARTE,
                            fg=LEISE, anchor="w", font=("Segoe UI", 9))
            zahl.pack(anchor="w")
            for widget in (kachel, innen, kopf, zahl):
                widget.bind("<Button-1>",
                            lambda _e, k=kategorien: self._memory_filtern(k))
            self._memory_kachel_widgets[titel] = (kachel, zahl)
        for spalte in range(3):
            try:
                self.memory_kacheln.columnconfigure(spalte, weight=1)
            except Exception:           # pragma: no cover - Testdoppel
                pass

    def _memory_filtern(self, kategorien) -> None:
        """Zeigt nur die Eintraege der angeklickten Kachel."""
        self.memory_filter = tuple(kategorien)
        self._refresh_memory()

    def _refresh_memory(self) -> None:
        query = self.memory_query.get().strip() if hasattr(self, "memory_query") else ""
        entries = self.controller.memory.search(query, limit=200) if query \
            else self.controller.memory.list(limit=500)
        # Filter einer angeklickten Kachel. Eine Suche hebt ihn auf - wer
        # tippt, will suchen und nicht im Filter gefangen bleiben.
        filter_kategorien = getattr(self, "memory_filter", ())
        if filter_kategorien and not query:
            entries = [e for e in entries if e.category in filter_kategorien]
        for row in self.memory_tree.get_children():
            self.memory_tree.delete(row)
        for entry in entries:
            self.memory_tree.insert(
                "", "end",
                values=(entry.mem_key, CATEGORIES.get(entry.category, entry.category),
                        entry.title, entry.content[:160], entry.version),
            )
        self._refresh_memory_kacheln()
        done, total = self.controller.onboarding_progress()
        self.onboarding_label.configure(text=f"Onboarding: {done} von {total} beantwortet")

    def _show_all_memory(self) -> None:
        self.memory_filter = ()
        self.memory_query.delete(0, "end")
        self._refresh_memory()

    def _selected_memory_key(self) -> str:
        selection = self.memory_tree.selection()
        if not selection:
            return ""
        return str(self.memory_tree.item(selection[0])["values"][0])

    def _edit_memory(self) -> None:
        key = self._selected_memory_key()
        entry = self.controller.memory.get(key) if key else None
        MemoryEditor(self.root, self.controller, entry, self._refresh_memory)

    def _memory_history(self) -> None:
        key = self._selected_memory_key()
        if not key:
            messagebox.showinfo("Verlauf", "Bitte zuerst einen Eintrag auswaehlen.",
                                parent=self.root)
            return
        history = self.controller.memory.history(key)
        lines = [f"Verlauf von {key}", ""]
        for item in history:
            lines.append(f"Version {item['version']} · {item['change_type']} · {item['changed_at']}")
            lines.append(f"   {item['snapshot']['content']}")
            if item.get("reason"):
                lines.append(f"   Grund: {item['reason']}")
            lines.append("")
        TextWindow(self.root, f"Verlauf {key}", "\n".join(lines))

    def _archive_memory(self) -> None:
        key = self._selected_memory_key()
        if not key:
            return
        if messagebox.askyesno(
            "Archivieren",
            f"Eintrag '{key}' archivieren?\n\n"
            "Der Eintrag bleibt im Verlauf nachvollziehbar erhalten und kann "
            "wiederhergestellt werden.",
            parent=self.root,
        ):
            self.controller.forget(key, reason="ueber die Oberflaeche archiviert")
            self._refresh_memory()

    def _onboarding(self) -> None:
        OnboardingWindow(self.root, self.controller, self._refresh_memory)

    def _export_profile(self) -> None:
        path = self.controller.export_company_profile()
        messagebox.showinfo(
            "Unternehmensprofil",
            f"Exportiert nach:\n{path}\nund {path.with_suffix('.md').name}",
            parent=self.root,
        )

    # -- Update --------------------------------------------------------
    def _write_update_log(self, text: str) -> None:
        self.update_log.configure(state="normal")
        self.update_log.delete("1.0", "end")
        self.update_log.insert("1.0", text)
        self.update_log.configure(state="disabled")

    def _run_update(self, dry_run: bool) -> None:
        if self.busy:
            return
        if not self.controller.network.status.online:
            if not messagebox.askyesno(
                "Kein Internet",
                "Es ist derzeit keine Internetverbindung erkennbar.\n\n"
                "Trotzdem versuchen? Ohne Verbindung wird nichts abgerufen; der lokale "
                "Wissensstand bleibt unveraendert nutzbar.",
                parent=self.root,
            ):
                return
        self._set_busy(True, "Wissensupdate laeuft ...")
        self.update_progress.configure(value=0, maximum=100)
        self._pipeline_setzen(0)

        # Der Fortschritt kommt aus dem Arbeitsthread. Tkinter darf nur aus
        # dem Oberflaechen-Thread bedient werden, deshalb geht der Wert ueber
        # eine Warteschlange und wird von einem Zeitgeber abgeholt.
        fortschritt: queue.Queue = queue.Queue()

        def progress(title: str, index: int, total: int) -> None:
            fortschritt.put(int(index * 100 / max(total, 1)))

        def abholen() -> None:
            wert = None
            try:
                while True:
                    wert = fortschritt.get_nowait()
            except queue.Empty:
                pass
            if wert is not None:
                self.update_progress.configure(value=wert)
                # Der Fortschritt der Quellenpruefung ist der erste
                # Schritt. Was danach kommt, meldet erst das Ergebnis -
                # eine Anzeige, die weiterlaeuft, ohne dass etwas
                # weiterlaeuft, waere eine Behauptung.
                self._pipeline_setzen(1 if wert < 100 else 2)

        def work():
            return self.controller.run_update(
                trigger="gui", dry_run=dry_run, progress=progress
            )

        def done(report, error) -> None:
            self._set_busy(False)
            self.update_progress.configure(value=100 if error is None else 0)
            if error is not None:
                self._pipeline_setzen(1, fehler=True)
                self._write_update_log(f"Update fehlgeschlagen:\n{error}")
                return
            # Alle Schritte durch - oder beim Validieren gescheitert. Was
            # der Bericht sagt, sagt auch die Anzeige.
            geglueckt = str(report.status).lower() in ("ok", "erfolg", "success")
            self._pipeline_setzen(
                len(self.PIPELINE_SCHRITTE) if geglueckt else 2,
                fehler=not geglueckt)
            self._write_update_log(report.as_markdown() + "\n\n" + self._update_overview())
            self._refresh_status()
            messagebox.showinfo(
                "Wissensupdate",
                f"Ergebnis: {report.status.upper()}\n\n"
                f"geprueft {report.checked} · aktualisiert {report.updated} · "
                f"unveraendert {report.unchanged} · fehlgeschlagen {report.failed}",
                parent=self.root,
            )

        BackgroundTask(self.root).run(work, done, on_tick=abholen)

    def _rollback_update(self) -> None:
        runs = self.controller.update_runs(1)
        if not runs or not runs[0].get("report_path"):
            messagebox.showinfo("Ruecknahme", "Es gibt keinen zuruecknehmbaren Lauf.",
                                parent=self.root)
            return
        run_id = Path(runs[0]["report_path"]).parent.name
        if not messagebox.askyesno(
            "Ruecknahme",
            f"Wissensupdate {run_id} zuruecknehmen?\n\n"
            "Das Unternehmensgedaechtnis bleibt davon unberuehrt.",
            parent=self.root,
        ):
            return
        ok, message = self.controller.rollback_update(run_id)
        (messagebox.showinfo if ok else messagebox.showerror)(
            "Ruecknahme", message, parent=self.root
        )
        self._refresh_status()

    def _backup(self) -> None:
        info = self.controller.backup("manuell")
        TextWindow(
            self.root, "Sicherung",
            "Sicherung erstellt in:\n"
            f"{info['verzeichnis']}\n\nDateien mit Pruefsummen:\n"
            + "\n".join(f"  {n}: {c}" for n, c in info["pruefsummen"].items()),
        )

    def _wiederherstellen(self) -> None:
        """Spielt eine Sicherung zurueck - in vier Schritten, jeder mit Grund.

        Wiederherstellen ueberschreibt den aktuellen Stand. Es ist die
        einschneidendste Handlung der Anwendung und wird entsprechend
        behandelt: auswaehlen, Pruefstand zeigen, ausdruecklich bestaetigen,
        und der bisherige Stand wird vorher gesichert.
        """
        sicherungen = self.controller.sicherungen()
        if not sicherungen:
            messagebox.showinfo(
                "Wiederherstellen",
                "Es gibt noch keine Sicherung.\n\n"
                "Legen Sie zuerst eine an - dann laesst sich dieser Stand "
                "spaeter zurueckholen.", parent=self.root)
            return

        uebersicht = "\n".join(
            f"  {e['name']}   {'in Ordnung' if e['vollstaendig'] else 'BESCHAEDIGT'}"
            f"   ({e['befund']})" for e in sicherungen[:15])
        name = simpledialog.askstring(
            "Wiederherstellen",
            "Verfuegbare Sicherungen:\n\n" + uebersicht
            + "\n\nWelche soll eingespielt werden? (Name eintragen)",
            initialvalue=sicherungen[0]["name"], parent=self.root)
        if not name:
            return

        eintrag = next((e for e in sicherungen if e["name"] == name.strip()), None)
        if eintrag is None:
            messagebox.showerror("Wiederherstellen",
                                 f"Diese Sicherung gibt es nicht: {name}",
                                 parent=self.root)
            return
        if not eintrag["vollstaendig"]:
            messagebox.showerror(
                "Wiederherstellen",
                f"Die Sicherung {name} ist nicht unversehrt:\n\n"
                f"{eintrag['befund']}\n\n"
                "Sie wird nicht eingespielt. Eine beschaedigte Sicherung "
                "macht aus einem heilen Stand einen kaputten.",
                parent=self.root)
            return

        if not messagebox.askyesno(
            "Wiederherstellen",
            f"Sicherung {name} vom {eintrag['erstellt_am'][:16]} einspielen?\n\n"
            "Der aktuelle Stand von Unternehmensgedaechtnis, Fachwissen und "
            "Einstellungen wird dabei UEBERSCHRIEBEN.\n\n"
            "Der bisherige Stand wird vorher automatisch gesichert - wer "
            "sich vertut, kommt zurueck.\n\nJetzt einspielen?",
            parent=self.root,
        ):
            return

        try:
            ergebnis = self.controller.wiederherstellen(name.strip(), bestaetigt=True)
        except Exception as fehler:
            messagebox.showerror("Wiederherstellen", str(fehler), parent=self.root)
            return
        self._refresh_status()
        TextWindow(self.root, "Wiederherstellen", ergebnis["meldung"])

    # -- Status --------------------------------------------------------
    def _refresh_status(self) -> None:
        import json

        status = self.controller.status()
        self._refresh_statusliste(status)
        self.status_text.configure(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", json.dumps(status, indent=2, ensure_ascii=False))
        self.status_text.configure(state="disabled")

        self._refresh_update_lage()
        lage = self.controller.lage
        # Internetstatus getrennt anzeigen: "OFFLINE gewaehlt, Internet
        # verfuegbar" ist ein gueltiger und wichtiger Zustand.
        self.internet_label.configure(text=f"Internet: {lage.internet_text}")
        self._chip_faerben(self.internet_label,
                           "gut" if lage.internet else "warnung")
        if self.mode_var.get() != lage.modus.value:
            self.mode_var.set(lage.modus.value)
        knowledge_date = status["wissensstand"]
        self.knowledge_label.configure(
            text=f"Wissensstand: {knowledge_date[:10] if knowledge_date else 'unbekannt'}"
        )
        # Dieselbe Auskunft noch einmal unten in der Seitenleiste - dort
        # steht sie dauerhaft im Blick, auch wenn oben gerade ein langer
        # Ansichtstitel steht.
        if hasattr(self, "schale"):
            self.schale.lage_setzen(
                f"Profil: {self.profil}" if self.profil else self.brand.name,
                f"{lage.modus.value} \u00b7 Internet {lage.internet_text}")
        self.statusbar.configure(
            text=f"{self.controller.status_line()} · Datentraeger: {self.controller.paths.root}"
        )

    def _on_network_change(self, status) -> None:
        """Wird aus dem Netz-Ueberwachungsthread aufgerufen.

        Die eigentliche Anzeige laeuft ueber ``after`` im Oberflaechen-Thread.
        """

        def apply() -> None:
            self._refresh_status()
            if status.online:
                self._append_chat(
                    "System",
                    "Internetverbindung verfuegbar. Online-Funktionen koennen genutzt werden.",
                    "system",
                )
            else:
                knowledge_date = self.controller.knowledge.knowledge_date()
                self._append_chat(
                    "System",
                    "Internetverbindung verloren. Der portable Buchhalter arbeitet mit dem "
                    f"lokalen Wissensstand vom {(knowledge_date or 'unbekannt')[:10]} weiter.",
                    "system",
                )

        self.root.after(0, apply)

    def _save_settings(self) -> None:
        changes: dict[str, Any] = {}
        # Zahlen muessen als Zahlen in der Konfiguration landen. Als Text
        # wuerden sie beim naechsten Start stillschweigend auf die Vorgabe
        # zurueckfallen - die Einstellung waere dann wirkungslos, ohne dass
        # es jemandem auffiele.
        zahlen = {"retrieval.top_k", "llm.gpu_layers", "llm.threads",
                  "llm.context_tokens", "llm.max_output_tokens"}
        for key, variable in self.setting_vars.items():
            value = variable.get()
            if key in zahlen:
                value = int(value)
            changes[key] = value
        vorher = {s: self.controller.config.get(s) for s in
                  ("llm.gpu_layers", "llm.threads", "llm.context_tokens")}
        path = self.controller.save_settings(changes)
        # Antworttempo und Fundstellenzahl sofort uebernehmen: sie werden
        # beim Aufbau der Recherche festgelegt und blieben sonst bis zum
        # naechsten Programmstart wirkungslos.
        self.controller.tempo_anwenden()

        # Die Werte des Modelldienstes werden beim Start des Dienstes
        # uebergeben. Ohne Neuaufbau blieben sie bis zum naechsten
        # Programmstart wirkungslos - und der Benutzer haette den Eindruck,
        # die Einstellung tue nichts.
        nachher = {s: self.controller.config.get(s) for s in vorher}
        hinweis = ""
        if nachher != vorher:
            self.controller.modell_neu_laden()
            hinweis = ("\n\nDie Werte fuer das Sprachmodell wurden sofort "
                       "uebernommen; der Modelldienst startet bei der "
                       "naechsten Frage neu.")
            if hasattr(self, "modell_lage_label"):
                self._refresh_modell()
        messagebox.showinfo("Einstellungen", f"Gespeichert in:\n{path}{hinweis}",
                            parent=self.root)

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.send_button.configure(state=state)
        self.update_button.configure(state=state)
        self.statusbar.configure(
            text=message if busy
            else f"{self.controller.status_line()} · Datentraeger: {self.controller.paths.root}"
        )
        self.root.configure(cursor="watch" if busy else "")

    def _on_close(self) -> None:
        try:
            self.controller.shutdown()
        finally:
            self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


class TextWindow:
    """Einfaches Fenster fuer laengere Textausgaben."""

    def __init__(self, parent: tk.Misc, title: str, text: str):
        window = tk.Toplevel(parent)
        window.title(title)
        window.geometry("760x520")
        area = scrolledtext.ScrolledText(window, wrap="word", font=FONT_MONO)
        area.pack(fill="both", expand=True, padx=PAD, pady=PAD)
        area.insert("1.0", text)
        area.configure(state="disabled")
        ttk.Button(window, text="Schliessen", command=window.destroy).pack(pady=(0, PAD))


class MemoryEditor:
    """Anlegen und Aendern eines Eintrags im Unternehmensgedaechtnis."""

    def __init__(self, parent: tk.Misc, controller: AppController, entry, on_saved):
        self.controller = controller
        self.on_saved = on_saved
        self.window = tk.Toplevel(parent)
        self.window.title("Unternehmenswissen bearbeiten")
        self.window.geometry("620x420")
        self.window.transient(parent)

        form = ttk.Frame(self.window)
        form.pack(fill="both", expand=True, padx=PAD * 2, pady=PAD * 2)

        ttk.Label(form, text="Schluessel").grid(row=0, column=0, sticky="w")
        self.key = ttk.Entry(form, width=48)
        self.key.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(form, text="Titel").grid(row=1, column=0, sticky="w")
        self.title = ttk.Entry(form, width=48)
        self.title.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(form, text="Kategorie").grid(row=2, column=0, sticky="w")
        self.category = ttk.Combobox(form, values=sorted(CATEGORIES), state="readonly", width=46)
        self.category.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(form, text="Inhalt").grid(row=3, column=0, sticky="nw")
        self.content = tk.Text(form, height=10, wrap="word")
        self.content.grid(row=3, column=1, sticky="nsew", pady=2)

        form.columnconfigure(1, weight=1)
        form.rowconfigure(3, weight=1)

        if entry is not None:
            self.key.insert(0, entry.mem_key)
            self.title.insert(0, entry.title)
            self.category.set(entry.category)
            self.content.insert("1.0", entry.content)
        else:
            self.category.set("other")

        buttons = ttk.Frame(self.window)
        buttons.pack(fill="x", padx=PAD * 2, pady=(0, PAD * 2))
        ttk.Button(buttons, text="Speichern", command=self._save).pack(side="right")
        ttk.Button(buttons, text="Abbrechen", command=self.window.destroy).pack(
            side="right", padx=PAD
        )

    def _save(self) -> None:
        key = self.key.get().strip()
        content = self.content.get("1.0", "end").strip()
        if not key or not content:
            messagebox.showwarning("Eingabe", "Schluessel und Inhalt sind erforderlich.",
                                   parent=self.window)
            return
        self.controller.remember_manual(
            key, self.title.get().strip() or key, content,
            self.category.get() or "other", source="Oberflaeche",
        )
        self.on_saved()
        self.window.destroy()


class OnboardingWindow:
    """Gefuehrte Erfassung der Unternehmensdaten (Masterprompt 39)."""

    def __init__(self, parent: tk.Misc, controller: AppController, on_saved):
        self.controller = controller
        self.on_saved = on_saved
        self.window = tk.Toplevel(parent)
        self.window.title("Unternehmens-Onboarding")
        self.window.geometry("760x620")
        self.window.transient(parent)

        ttk.Label(
            self.window,
            text=("Diese Angaben werden dauerhaft auf dem Datentraeger gespeichert und "
                  "stehen danach auf jedem Rechner zur Verfuegung.\n"
                  "Felder duerfen leer bleiben und spaeter ergaenzt werden."),
            justify="left",
        ).pack(anchor="w", padx=PAD * 2, pady=PAD)

        canvas = tk.Canvas(self.window, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(PAD * 2, 0))
        scrollbar.pack(side="right", fill="y")

        self.fields: dict[str, ttk.Entry] = {}
        for row, question in enumerate(controller.onboarding_questions()):
            ttk.Label(inner, text=question["titel"], width=32).grid(
                row=row, column=0, sticky="w", pady=3
            )
            entry = ttk.Entry(inner, width=60)
            entry.insert(0, question["wert"])
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            self.fields[question["key"]] = entry

        buttons = ttk.Frame(self.window)
        buttons.pack(fill="x", side="bottom", padx=PAD * 2, pady=PAD)
        ttk.Button(buttons, text="Speichern", command=self._save).pack(side="right")
        ttk.Button(buttons, text="Schliessen", command=self.window.destroy).pack(
            side="right", padx=PAD
        )

    def _save(self) -> None:
        saved = 0
        for key, entry in self.fields.items():
            value = entry.get().strip()
            if value:
                self.controller.answer_onboarding(key, value)
                saved += 1
        self.controller.export_company_profile()
        self.on_saved()
        messagebox.showinfo("Onboarding", f"{saved} Angaben gespeichert.", parent=self.window)
        self.window.destroy()


def run(startbild: bool = True) -> int:
    """Startet Begruessungsbild, Systempruefung und Hauptfenster.

    Die Reihenfolge ist nicht beliebig: der Controller wird **vor** dem
    Begruessungsbild aufgebaut. Er faehrt dabei den Modelldienst im
    Hintergrund hoch, und genau diese Zeit ueberbrueckt das Bild. Stuende
    es davor, waeren die drei Sekunden verlorene Zeit statt gewonnener.
    """
    controller = AppController(console_logging=False)
    if startbild:
        try:
            from ui.startbild import Startbild

            Startbild(load_brand(controller.paths, controller.config),
                      profilname(controller.profile)).zeigen()
        except Exception:               # pragma: no cover - defensiv
            # Ein Begruessungsbild, das den Start verhindert, waere die
            # schlechteste aller Loesungen.
            log.debug("Begruessungsbild uebersprungen", exc_info=True)
    proceed, report = StartupWindow(controller).run()
    if not proceed:
        controller.shutdown()
        return 0
    MainWindow(controller, report).run()
    return 0
