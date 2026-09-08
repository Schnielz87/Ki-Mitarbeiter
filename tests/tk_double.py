"""Ein Tkinter-Ersatz fuer automatische Tests.

**Was das ist und was nicht.** In der Entwicklungsumgebung gab es weder
Tkinter noch einen Bildschirm. Damit die Oberflaechenlogik trotzdem geprueft
werden kann, wird hier ein Doppel eingesetzt, das die verwendeten
Tkinter-Bausteine nachbildet: Widgets werden erzeugt, Texte gespeichert,
Rueckrufe registriert und koennen ausgeloest werden.

Das prueft echte Fehler im Oberflaechencode - falsche Aufrufe, fehlende
Attribute, kaputte Rueckrufe, falsche Ablaeufe. Es prueft **nicht** das
Aussehen, das Layout oder das Verhalten des echten Tk. Ein echter GUI-Test auf
Windows bleibt erforderlich (siehe docs/ABNAHME.md).
"""

from __future__ import annotations

import sys
import time
import types
from typing import Any, Callable


class _Widget:
    """Ein Widget, das seine Kinder, Texte und Rueckrufe merkt."""

    def __init__(self, master: Any = None, **options):
        self.master = master
        self.options = dict(options)
        self.children: list[_Widget] = []
        self.commands: dict[str, Callable] = {}
        self.bindings: dict[str, Callable] = {}
        self.after_jobs: list[tuple[int, Callable]] = []
        self.destroyed = False
        #: Ob das Widget angezeigt wird. Erst ein pack/grid/place macht es
        #: sichtbar - genau wie im echten Tk.
        self.sichtbar = False
        if isinstance(master, _Widget):
            master.children.append(self)
        command = options.get("command")
        if callable(command):
            self.commands["command"] = command

    # Geometrie ist fuer das Aussehen bedeutungslos - ob ein Widget
    # ueberhaupt sichtbar ist, aber nicht. Ohne diese Buchfuehrung koennte
    # ein Test nur ein Merkmal pruefen ("eingeklappt = True") statt die
    # Wirkung ("das Feld ist weg"). Genau daran ist eine Gegenprobe zu den
    # Recherche-Details vorbeigelaufen.
    def pack(self, *a, **k):
        self.sichtbar = True
        return self

    def grid(self, *a, **k):
        self.sichtbar = True
        return self

    def place(self, *a, **k):
        self.sichtbar = True
        return self

    def pack_forget(self, *a, **k):
        self.sichtbar = False
        return self

    def grid_forget(self, *a, **k):
        self.sichtbar = False
        return self
    def columnconfigure(self, *a, **k): return self
    def rowconfigure(self, *a, **k): return self
    def grid_columnconfigure(self, *a, **k): return self
    def grid_rowconfigure(self, *a, **k): return self
    # Groessenweitergabe abschalten: echtes Tk laesst einen Rahmen damit
    # seine gesetzte Groesse behalten, statt auf den Inhalt zu schrumpfen.
    # Das Doppel muss es kennen, sonst faellt der Aufbau hier aus - und
    # der Fehler haette nichts mit dem zu tun, was geprueft werden soll.
    def grid_propagate(self, *a, **k): return self
    def pack_propagate(self, *a, **k): return self
    def title(self, *a, **k): return self
    def geometry(self, *a, **k): return self
    def minsize(self, *a, **k): return self
    # Fenstersymbol: fuer den Test bedeutungslos, aber es wird aufgerufen,
    # sobald eine Icondatei vorliegt. Wir merken uns die Aufrufe, damit ein
    # Test pruefen kann, dass ueberhaupt ein Symbol gesetzt wird.
    def iconbitmap(self, *a, **k):
        self.options["iconbitmap"] = a[0] if a else k.get("default", "")
        return self

    def iconphoto(self, *a, **k):
        self.options["iconphoto"] = a[1] if len(a) > 1 else None
        return self
    def transient(self, *a, **k): return self
    def focus_set(self): return self
    def see(self, *a, **k): return self
    def start(self, *a, **k): return self
    def stop(self, *a, **k): return self
    def yview(self, *a, **k): return self
    def bbox(self, *a, **k): return (0, 0, 100, 100)
    def create_window(self, *a, **k): return 1
    def create_line(self, *a, **k): return 1
    def protocol(self, name, callback=None):
        if callback:
            self.commands[name] = callback
    def destroy(self):
        self.destroyed = True
    def configure(self, **kwargs):
        self.options.update(kwargs)
        if callable(kwargs.get("command")):
            self.commands["command"] = kwargs["command"]
        return self
    config = configure
    def cget(self, key): return self.options.get(key)
    def bind(self, sequence, callback, *a):
        self.bindings[sequence] = callback
    #: Schutz gegen endlose Rueckruf-Ketten im Test.
    _MAX_AFTER_DEPTH = 400
    _after_depth = 0

    def after(self, delay, callback=None, *args):
        """Fuehrt den Rueckruf aus, statt eine Ereignisschleife zu betreiben.

        Wartezeiten werden tatsaechlich abgewartet (verkuerzt), damit
        Hintergrundarbeit in einem anderen Thread fertig werden kann - sonst
        wuerde eine Warteschleife wie in ``BackgroundTask`` endlos wiederholen.
        """
        if callback is None:
            return "job"
        self.after_jobs.append((delay, callback))
        if delay:
            time.sleep(min(int(delay), 50) / 1000.0)
        _Widget._after_depth += 1
        try:
            if _Widget._after_depth > _Widget._MAX_AFTER_DEPTH:
                raise AssertionError(
                    "Die Oberflaeche wartet unerwartet lange auf ein Ergebnis "
                    "(mehr als 400 Durchlaeufe)."
                )
            return callback(*args)
        finally:
            _Widget._after_depth -= 1
    def after_cancel(self, job): return None
    def mainloop(self): return None
    def update(self): return None
    def update_idletasks(self): return None
    def winfo_children(self): return list(self.children)

    # -- Fensterverwaltung -------------------------------------------
    # Gebraucht vom Begruessungsbild und spaeter von der neuen Schale.
    # Ohne diese Methoden faengt der defensive Code der Oberflaeche jeden
    # Aufruf ab - und ein Test kaeme dann zum richtigen Ergebnis aus dem
    # falschen Grund. Genau das ist bei den ersten Startbildtests passiert.
    def overrideredirect(self, *a, **k): return self
    def withdraw(self): return self
    def deiconify(self): return self
    def lift(self, *a, **k): return self
    def attributes(self, *a, **k): return self
    def focus_force(self): return self
    def grab_set(self): return self
    def grab_release(self): return self
    def resizable(self, *a, **k): return self
    def maxsize(self, *a, **k): return self
    def state(self, *a, **k): return "normal"

    def wait_window(self, fenster=None):
        """Kehrt sofort zurueck - es gibt keine Ereignisschleife.

        Die ``after``-Rueckrufe sind zu diesem Zeitpunkt bereits gelaufen
        (siehe ``after``), das Fenster ist also schon geschlossen.
        """
        return None

    def winfo_reqwidth(self): return 400
    def winfo_reqheight(self): return 260
    def winfo_width(self): return 400
    def winfo_height(self): return 260
    def winfo_screenwidth(self): return 1920
    def winfo_screenheight(self): return 1080
    def winfo_exists(self): return not self.destroyed
    def winfo_toplevel(self): return self

    def invoke(self):
        """Loest den Button-Rueckruf aus."""
        callback = self.commands.get("command")
        if callback is None:
            raise AssertionError("Dieses Widget hat keinen Rueckruf.")
        return callback()


class _TextWidget(_Widget):
    """Text-/ScrolledText-Ersatz mit einfacher Pufferverwaltung."""

    def __init__(self, master=None, **options):
        super().__init__(master, **options)
        self.buffer = ""
        #: Marken zeigen auf eine Stelle im Puffer - so laesst sich, wie in
        #: Tk, ein bestimmter Bereich wieder entfernen (schrittweise Ausgabe).
        self.marks: dict[str, int] = {}

    def insert(self, index, text, *tags):
        if str(index) in ("1.0", "0.0"):
            self.buffer = str(text) + self.buffer
        else:
            self.buffer += str(text)
        return self

    def mark_set(self, name, index="end"):
        self.marks[str(name)] = len(self.buffer)
        return self

    def mark_gravity(self, name, direction=None): return self

    def mark_unset(self, *names):
        for name in names:
            self.marks.pop(str(name), None)
        return self

    def delete(self, start=None, end=None):
        stelle = self.marks.get(str(start))
        if stelle is not None:
            self.buffer = self.buffer[:stelle]
        else:
            self.buffer = ""
        return self

    def get(self, start="1.0", end="end"):
        return self.buffer

    def tag_configure(self, *a, **k): return self
    def index(self, *a, **k): return "1.0"


class _ListboxWidget(_Widget):
    def __init__(self, master=None, **options):
        super().__init__(master, **options)
        self.items: list[str] = []
        self._selection: tuple[int, ...] = ()

    def insert(self, index, text):
        self.items.append(str(text))

    def delete(self, first, last=None):
        self.items = []

    def curselection(self):
        return self._selection

    def select(self, index: int):
        self._selection = (index,)

    def size(self):
        return len(self.items)


class _TreeviewWidget(_Widget):
    def __init__(self, master=None, **options):
        super().__init__(master, **options)
        self.rows: dict[str, dict] = {}
        self._counter = 0
        self._selection: tuple[str, ...] = ()

    def heading(self, column, **kwargs): return self
    def column(self, column, **kwargs): return self

    def insert(self, parent, index, values=(), **kwargs):
        self._counter += 1
        key = f"I{self._counter}"
        self.rows[key] = {"values": list(values)}
        return key

    def get_children(self, item=""):
        return list(self.rows)

    def delete(self, *items):
        for item in items:
            self.rows.pop(item, None)

    def item(self, key, option=None):
        return self.rows[key]

    def selection(self):
        return self._selection

    def select_row(self, index: int = 0):
        keys = list(self.rows)
        self._selection = (keys[index],) if keys else ()


class _PhotoImage:
    """Bildplatzhalter - laedt nichts, merkt sich nur den Pfad."""

    def __init__(self, file: str = "", **k):
        self.file = str(file)

    def height(self) -> int: return 64
    def width(self) -> int: return 64
    def subsample(self, *a, **k): return self


class _Variable:
    def __init__(self, master=None, value=None, **kwargs):
        self._value = value
    def get(self): return self._value
    def set(self, value): self._value = value


class _StringVar(_Variable):
    def __init__(self, master=None, value="", **kwargs):
        super().__init__(master, value)


class _BooleanVar(_Variable):
    def __init__(self, master=None, value=False, **kwargs):
        super().__init__(master, bool(value))


class _Combobox(_Widget):
    def __init__(self, master=None, **options):
        super().__init__(master, **options)
        self._value = ""
        self.variable = options.get("textvariable")
    def set(self, value):
        self._value = value
        if self.variable is not None:
            self.variable.set(value)
    def get(self):
        return self.variable.get() if self.variable is not None else self._value


class _Entry(_Widget):
    def __init__(self, master=None, **options):
        super().__init__(master, **options)
        self._value = ""
    def insert(self, index, text): self._value += str(text)
    def delete(self, first, last=None): self._value = ""
    def get(self): return self._value


class _Dialogs:
    """Erfasst Dialogaufrufe und liefert vorgegebene Antworten."""

    def __init__(self):
        self.messages: list[tuple[str, str, str]] = []
        self.answers: list[bool] = []
        self.open_file: str | None = None
        self.default_answer = False

    def _record(self, kind: str, title: str, message: str):
        self.messages.append((kind, title, message))

    def showinfo(self, title, message, **k): self._record("info", title, message)
    def showwarning(self, title, message, **k): self._record("warnung", title, message)
    def showerror(self, title, message, **k): self._record("fehler", title, message)

    def askyesno(self, title, message, **k):
        self._record("frage", title, message)
        return self.answers.pop(0) if self.answers else self.default_answer

    #: Wohin ein "Speichern unter" fuehrt. None heisst: abgebrochen.
    save_file = None
    #: Was eine Texteingabe liefert, wenn ``answers`` leer ist.
    default_string = None

    def askopenfilename(self, **k): return self.open_file or ""

    def asksaveasfilename(self, **k):
        """Wohin gespeichert werden soll. Wie beim Oeffnen gesteuert ueber
        ``save_file``; ohne Vorgabe bricht der Benutzer ab."""
        return self.save_file or ""

    def askstring(self, titel, frage, **k):
        """Eine Texteingabe. ``answers`` liefert die Antwort - so laesst
        sich auch der Abbruch (None) im Test nachstellen."""
        self.messages.append(("eingabe", titel, frage))
        return self.answers.pop(0) if self.answers else self.default_string


DIALOGS = _Dialogs()


class _Button(_Widget):
    """Ein Knopf - und zwar als solcher erkennbar.

    Warum eine eigene Klasse: ohne sie ist ein Knopf im Doppel nicht von
    einem Rahmen zu unterscheiden. Ein Test, der tote Knoepfe suchen soll,
    findet dann nur die Knoepfe MIT Rueckruf - und uebersieht ausgerechnet
    die, um die es geht. Genau daran ist eine Gegenprobe vorbeigelaufen,
    die einen Knopf ohne Rueckruf einbaute.
    """


class _Toplevel(_Widget):
    """Ein eigenstaendiges Fenster - mitgezaehlt.

    Warum eine eigene Klasse: ein Test muss pruefen koennen, dass ein
    Fenster **nicht** aufgeht. Solange alles derselbe Platzhalter ist,
    laesst sich das nicht unterscheiden - und ein Test, der das nicht
    unterscheiden kann, besteht auch dann, wenn die Anwendung ein leeres
    Fenster oeffnet.
    """

    #: Alle seit dem letzten ``install()`` erzeugten Fenster.
    ERZEUGT: list["_Toplevel"] = []

    def __init__(self, master: Any = None, **options):
        super().__init__(master, **options)
        _Toplevel.ERZEUGT.append(self)


#: Die Namen, die ``install`` in ``sys.modules`` ersetzt.
TKINTER_NAMEN = ("tkinter", "tkinter.ttk", "tkinter.scrolledtext",
                 "tkinter.filedialog", "tkinter.messagebox",
                 "tkinter.simpledialog")

#: Was vor dem ersten ``install`` unter diesen Namen stand. Wird gebraucht,
#: um das echte Tkinter wiederherzustellen.
_ECHTES: dict[str, object] = {}


def entfernen() -> None:
    """Nimmt das Doppel wieder heraus und stellt das echte Tkinter her.

    Ohne das bleibt das Doppel fuer den ganzen Prozess stehen. Tests, die
    danach ein **echtes** Fenster oeffnen wollen
    (``test_echte_oberflaeche.py``), bekaemen dann wieder das Doppel und
    wuerden entweder falsch bestehen oder mit einem Fehler abbrechen, der
    nichts mit ihrer Sache zu tun hat.
    """
    for name in TKINTER_NAMEN:
        vorher = _ECHTES.get(name, "fehlte")
        if vorher == "fehlte":
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = vorher
    ui_module_freigeben()


def ui_module_freigeben() -> None:
    """Loescht die Oberflaechenmodule **und das Paket** aus dem Zwischenspeicher.

    Das Paket mitzuloeschen ist keine Uebervorsicht: ``del
    sys.modules["ui.tk_app"]`` nimmt zwar den Eintrag heraus, aber das
    Paketobjekt ``ui`` traegt weiterhin ein Attribut ``tk_app`` mit dem
    alten Modul. ``from ui import tk_app`` liefert dann genau dieses alte
    Modul zurueck - mitsamt dem Tkinter, gegen das es geladen wurde.

    Gefunden, als echte und gedoppelte Oberflaechentests im selben Lauf
    aufeinandertrafen: das Hauptfenster baute Flaechen mit dem echten ttk
    auf einem Elternteil aus dem Doppel.
    """
    for name in [m for m in sys.modules if m == "ui" or m.startswith("ui.")]:
        del sys.modules[name]


def install() -> _Dialogs:
    """Registriert das Doppel als ``tkinter`` und gibt die Dialogerfassung."""
    _Toplevel.ERZEUGT.clear()
    for name in TKINTER_NAMEN:
        if name not in _ECHTES:
            _ECHTES[name] = sys.modules.get(name, "fehlte")
    tk = types.ModuleType("tkinter")
    tk.Tk = _Widget
    tk.Toplevel = _Toplevel
    tk.Frame = _Widget
    tk.Label = _Widget
    tk.Button = _Button
    tk.Canvas = _Widget
    tk.Text = _TextWidget
    tk.Listbox = _ListboxWidget
    tk.Misc = _Widget
    tk.Variable = _Variable
    tk.StringVar = _StringVar
    tk.BooleanVar = _BooleanVar
    tk.IntVar = _Variable
    tk.END = "end"
    tk.TclError = Exception

    ttk = types.ModuleType("tkinter.ttk")
    for name in ("Frame", "Label", "Checkbutton", "Scrollbar", "Progressbar",
                 "PanedWindow", "Notebook", "Separator", "LabelFrame"):
        setattr(ttk, name, _Widget)
    ttk.Button = _Button
    ttk.Entry = _Entry
    ttk.Combobox = _Combobox
    tk.PhotoImage = _PhotoImage
    ttk.Treeview = _TreeviewWidget

    def _notebook_add(self, child, **kwargs):
        """Nimmt eine Flaeche auf - aber nur einmal.

        Ein ``ttk.Frame(notebook)`` haengt sich schon beim Erzeugen bei
        seinem Elternteil ein. Ein zweites Anhaengen durch ``add`` fuehrte
        dazu, dass jedes Bedienelement in Auswertungen doppelt erschien -
        aufgefallen bei der Button-Funktionsmatrix, die jeden Knopf zweimal
        auflistete.
        """
        if child not in self.children:
            self.children.append(child)
    ttk.Notebook = type("Notebook", (_Widget,), {"add": _notebook_add})
    ttk.PanedWindow = type("PanedWindow", (_Widget,), {"add": _notebook_add})

    scrolled = types.ModuleType("tkinter.scrolledtext")
    scrolled.ScrolledText = _TextWidget

    filedialog = types.ModuleType("tkinter.filedialog")
    filedialog.askopenfilename = DIALOGS.askopenfilename
    filedialog.asksaveasfilename = DIALOGS.asksaveasfilename

    simpledialog = types.ModuleType("tkinter.simpledialog")
    simpledialog.askstring = DIALOGS.askstring

    messagebox = types.ModuleType("tkinter.messagebox")
    messagebox.showinfo = DIALOGS.showinfo
    messagebox.showwarning = DIALOGS.showwarning
    messagebox.showerror = DIALOGS.showerror
    messagebox.askyesno = DIALOGS.askyesno

    tk.ttk = ttk
    tk.scrolledtext = scrolled
    tk.filedialog = filedialog
    tk.messagebox = messagebox
    tk.simpledialog = simpledialog

    for name, module in (
        ("tkinter", tk), ("tkinter.ttk", ttk), ("tkinter.scrolledtext", scrolled),
        ("tkinter.filedialog", filedialog), ("tkinter.messagebox", messagebox),
        ("tkinter.simpledialog", simpledialog),
    ):
        sys.modules[name] = module

    DIALOGS.messages.clear()
    DIALOGS.answers.clear()
    DIALOGS.default_answer = False
    DIALOGS.open_file = None
    DIALOGS.save_file = None
    DIALOGS.default_string = None
    return DIALOGS
