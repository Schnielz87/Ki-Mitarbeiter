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
import traceback
from pathlib import Path
from typing import Any, Callable

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from app.controller import AppController, AskOutcome, StartupReport
from pkc.branding import load_brand, profilname
from pkc.netstate import Mode
from ui.antwort import teilen
from ui.markdown import zerlegen
from pkc.audit import ApprovalState
from pkc.memory.schema_keys import CATEGORIES

PAD = 8
FONT_BASE = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)
FONT_TITLE = ("Segoe UI", 14, "bold")

#: Stelle im Chat, ab der die gerade laufende Antwort steht (Abschnitt 21).
MARKE_STROM = "laufende_antwort"


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


def _fenstericon(fenster, brand) -> None:
    """Setzt Fenster- und Taskleistensymbol, soweit das System es zulaesst."""
    _taskleisten_kennung(brand)
    ico = brand.icon_pfad
    if ico is not None:
        try:
            fenster.iconbitmap(default=str(ico))
            return
        except Exception as exc:        # unter Linux kennt Tk kein .ico
            log.debug("iconbitmap nicht moeglich (%s)", exc)
    png = brand.variante("icon")
    if png is None:
        return
    try:
        bild = tk.PhotoImage(file=str(png))
        fenster.iconphoto(True, bild)
        # Referenz halten, sonst raeumt der Sammler das Bild weg und das
        # Symbol verschwindet wieder.
        fenster._portiva_icon = bild
    except Exception as exc:            # pragma: no cover - defensiv
        log.debug("iconphoto nicht moeglich (%s)", exc)


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

        self.root = tk.Tk()
        self.brand = load_brand(controller.paths, controller.config)
        self.profil = profilname(controller.profile)
        # PORTIVA ist fest, der Profilname kommt aus dem aktiven Profil -
        # nach einem Profilwechsel heisst das Fenster automatisch anders.
        self.root.title(self.brand.titel(self.profil))
        _fenstericon(self.root, self.brand)
        self.root.geometry("1180x760")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Abschnitt 23: die Unterhaltung soll sich wie ein Gespraech lesen.
        # Wer spricht, steht als Name darueber - nicht als "Sie"/"Buchhalter",
        # sondern mit der Marke und dem aktiven Profil.
        self._sprecher_ich = "BENUTZER"
        self._sprecher_ki = self.brand.titel(self.profil)

        self._build_header()
        self._build_body()
        self._build_statusbar()

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
    def _build_header(self) -> None:
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=PAD, pady=(PAD, 0))
        _BrandKopf(header, self.brand, self.profil, gross=False).frame.pack(side="left")

        # Moduswahl: gut sichtbar, jederzeit erreichbar. Der aktuelle Modus
        # ist eine Entscheidung des Benutzers - er gehoert nicht in ein
        # Untermenue, sondern nach vorn.
        self.mode_var = tk.StringVar(value=self.controller.mode.value)
        self.mode_box = ttk.Combobox(
            header, textvariable=self.mode_var, state="readonly", width=10,
            values=[m.value for m in Mode],
        )
        self.mode_box.pack(side="right")
        self.mode_box.bind("<<ComboboxSelected>>", self._on_mode_changed)
        ttk.Label(header, text="Betriebsmodus:").pack(side="right", padx=(PAD * 2, 4))

        self.internet_label = ttk.Label(header, text="", font=("Segoe UI", 9))
        self.internet_label.pack(side="right", padx=(0, PAD * 2))
        self.mode_label = ttk.Label(header, text="", font=("Segoe UI", 10, "bold"))
        self.mode_label.pack(side="right", padx=(0, PAD))
        self.knowledge_label = ttk.Label(header, text="")
        self.knowledge_label.pack(side="right", padx=(0, PAD * 2))

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

    def _build_body(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=PAD, pady=PAD)
        self._build_chat_tab()
        self._build_memory_tab()
        self._build_documents_tab()
        self._build_update_tab()
        self._build_settings_tab()

    # -- Registerkarte: Unterhaltung -----------------------------------
    def _build_chat_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Unterhaltung")

        panes = ttk.PanedWindow(frame, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes)
        panes.add(left, weight=3)

        self.chat = scrolledtext.ScrolledText(left, wrap="word", font=FONT_BASE, state="disabled")
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_configure("wer", font=("Segoe UI", 10, "bold"))
        # Abschnitt 23: Frage und Antwort sollen sich auf einen Blick
        # unterscheiden lassen.
        self.chat.tag_configure("sprecher_ich", font=("Segoe UI", 9, "bold"),
                                foreground="#666666", spacing1=10)
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

        entry_frame = ttk.Frame(left)
        entry_frame.pack(fill="x", pady=(PAD, 0))
        self.entry = tk.Text(entry_frame, height=4, font=FONT_BASE, wrap="word")
        self.entry.pack(side="left", fill="both", expand=True)
        self.entry.bind("<Control-Return>", lambda event: self._send())

        buttons = ttk.Frame(entry_frame)
        buttons.pack(side="right", fill="y", padx=(PAD, 0))
        self.send_button = ttk.Button(buttons, text="Absenden", command=self._send)
        self.send_button.pack(fill="x")
        # Abschnitt 22: waehrend einer laengeren Antwort abbrechen koennen.
        self.stop_button = ttk.Button(buttons, text="Generierung stoppen",
                                      command=self._abbrechen, state="disabled")
        self.stop_button.pack(fill="x", pady=(4, 0))
        ttk.Button(buttons, text="Neue Unterhaltung", command=self._new_conversation).pack(
            fill="x", pady=(4, 0)
        )
        ttk.Button(buttons, text="Dokument hinzufuegen", command=self._add_document).pack(
            fill="x", pady=(4, 0)
        )
        ttk.Label(buttons, text="Strg+Eingabe sendet", foreground="#666666").pack(pady=(4, 0))

        right = ttk.Frame(panes)
        panes.add(right, weight=2)

        ttk.Label(right, text="Quellen der letzten Antwort", font=("Segoe UI", 10, "bold")).pack(
            anchor="w"
        )
        self.sources = scrolledtext.ScrolledText(
            right, wrap="word", font=("Segoe UI", 9), height=16, state="disabled"
        )
        self.sources.pack(fill="both", expand=True, pady=(2, PAD))

        ttk.Label(right, text="Unterhaltungen", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.conversation_list = tk.Listbox(right, height=8, font=("Segoe UI", 9))
        self.conversation_list.pack(fill="both", expand=True, pady=2)
        self.conversation_list.bind("<Double-Button-1>", self._open_conversation)
        ttk.Button(right, text="Unterhaltung exportieren", command=self._export_conversation).pack(
            fill="x"
        )

    # -- Registerkarte: Unternehmenswissen -----------------------------
    def _build_memory_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Unternehmenswissen")

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

        columns = ("schluessel", "kategorie", "titel", "inhalt", "version")
        self.memory_tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
        for column, heading, width in (
            ("schluessel", "Schluessel", 220), ("kategorie", "Kategorie", 150),
            ("titel", "Titel", 180), ("inhalt", "Inhalt", 460), ("version", "V", 40),
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
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Belege")
        ttk.Button(frame, text="Beleg hinzufuegen", command=self._add_document).pack(
            anchor="w", pady=(0, PAD)
        )
        columns = ("titel", "art", "hinzugefuegt", "status", "pfad")
        self.document_tree = ttk.Treeview(frame, columns=columns, show="headings")
        for column, heading, width in (
            ("titel", "Titel", 320), ("art", "Art", 90), ("hinzugefuegt", "Hinzugefuegt", 180),
            ("status", "Status", 120), ("pfad", "Ablage auf dem Datentraeger", 420),
        ):
            self.document_tree.heading(column, text=heading)
            self.document_tree.column(column, width=width, anchor="w")
        self.document_tree.pack(fill="both", expand=True)
        self._refresh_documents()

    # -- Registerkarte: Wissensupdate ----------------------------------
    def _build_update_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Wissen aktualisieren")

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

    # -- Registerkarte: Einstellungen ----------------------------------
    def _build_settings_tab(self) -> None:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Einstellungen und Status")

        left = ttk.Frame(frame)
        left.pack(side="left", fill="both", expand=True)

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

        ttk.Button(left, text="Einstellungen speichern", command=self._save_settings).pack(
            anchor="w", pady=PAD
        )

        right = ttk.Frame(frame)
        right.pack(side="right", fill="both", expand=True, padx=(PAD * 2, 0))
        ttk.Label(right, text="Status", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.status_text = scrolledtext.ScrolledText(
            right, wrap="word", font=FONT_MONO, height=26, state="disabled"
        )
        self.status_text.pack(fill="both", expand=True)
        ttk.Button(right, text="Status aktualisieren", command=self._refresh_status).pack(
            anchor="w", pady=PAD
        )

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
            self._show_sources(outcome)
            self._refresh_conversations()
            self._ask_about_candidates(outcome)

        self._laufende_aufgabe = BackgroundTask(self.root)
        self.stop_button.configure(state="normal")
        self._laufende_aufgabe.run(work, done, on_tick=self._strom_ausgeben)
        return "break"

    def _antwort_anzeigen(self, text: str) -> None:
        """Zeigt die fertige Antwort - notfalls anstelle des Stroms.

        Waehrend der Erzeugung steht der rohe Modelltext im Fenster. Am Ende
        tritt der gepruefte Text an seine Stelle: mit Quellenteil, Wissensstand
        und den Hinweisen der Anwendung, und in der lesbaren Darstellung. Was
        angezeigt bleibt, ist damit genau das, was auch gespeichert wurde.
        """
        self._strom_zuruecksetzen()
        self._append_chat(self._sprecher_ki, text)

    def _abbrechen(self) -> None:
        """Bricht eine laufende Erzeugung ab (Abschnitt 22)."""
        if getattr(self, "_laufende_aufgabe", None) is not None:
            self._laufende_aufgabe.abbrechen()
            self.stop_button.configure(state="disabled")

    def _show_sources(self, outcome: AskOutcome) -> None:
        references = outcome.answer.used_references or outcome.answer.references
        self.sources.configure(state="normal")
        self.sources.delete("1.0", "end")
        if not references:
            self.sources.insert("end", "Zu dieser Frage wurde lokal keine Fundstelle gefunden.\n")
        for reference in references:
            self.sources.insert("end", f"[{reference.number}] {reference.reference}\n")
            self.sources.insert("end", f"    {reference.priority_label}\n")
            if reference.url:
                self.sources.insert("end", f"    {reference.url}\n")
            self.sources.insert("end", f"    {reference.excerpt}\n\n")
        self.sources.configure(state="disabled")

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
        try:
            result = self.controller.add_document(Path(filename))
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
        for item in self.controller.documents():
            self.document_tree.insert(
                "", "end",
                values=(item["title"], item["kind"] or "-", item["added_at"][:19],
                        item["status"], item["path"]),
            )

    # -- Unternehmenswissen --------------------------------------------
    def _refresh_memory(self) -> None:
        query = self.memory_query.get().strip() if hasattr(self, "memory_query") else ""
        entries = self.controller.memory.search(query, limit=200) if query \
            else self.controller.memory.list(limit=500)
        for row in self.memory_tree.get_children():
            self.memory_tree.delete(row)
        for entry in entries:
            self.memory_tree.insert(
                "", "end",
                values=(entry.mem_key, CATEGORIES.get(entry.category, entry.category),
                        entry.title, entry.content[:160], entry.version),
            )
        done, total = self.controller.onboarding_progress()
        self.onboarding_label.configure(text=f"Onboarding: {done} von {total} beantwortet")

    def _show_all_memory(self) -> None:
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

        def work():
            return self.controller.run_update(
                trigger="gui", dry_run=dry_run, progress=progress
            )

        def done(report, error) -> None:
            self._set_busy(False)
            self.update_progress.configure(value=100 if error is None else 0)
            if error is not None:
                self._write_update_log(f"Update fehlgeschlagen:\n{error}")
                return
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

    # -- Status --------------------------------------------------------
    def _refresh_status(self) -> None:
        import json

        status = self.controller.status()
        self.status_text.configure(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", json.dumps(status, indent=2, ensure_ascii=False))
        self.status_text.configure(state="disabled")

        self._refresh_update_lage()
        lage = self.controller.lage
        self.mode_label.configure(text=f"Betriebsmodus: {lage.modus.value}")
        # Internetstatus getrennt anzeigen: "OFFLINE gewaehlt, Internet
        # verfuegbar" ist ein gueltiger und wichtiger Zustand.
        self.internet_label.configure(text=f"Internet: {lage.internet_text}")
        if self.mode_var.get() != lage.modus.value:
            self.mode_var.set(lage.modus.value)
        knowledge_date = status["wissensstand"]
        self.knowledge_label.configure(
            text=f"Wissensstand: {knowledge_date[:10] if knowledge_date else 'unbekannt'}"
        )
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
        for key, variable in self.setting_vars.items():
            value = variable.get()
            if key == "retrieval.top_k":
                value = int(value)
            changes[key] = value
        path = self.controller.save_settings(changes)
        self.controller.rag.top_k = int(self.controller.config.get("retrieval.top_k", 8))
        messagebox.showinfo("Einstellungen", f"Gespeichert in:\n{path}", parent=self.root)

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


def run() -> int:
    """Startet Systempruefung und Hauptfenster."""
    controller = AppController(console_logging=False)
    proceed, report = StartupWindow(controller).run()
    if not proceed:
        controller.shutdown()
        return 0
    MainWindow(controller, report).run()
    return 0
