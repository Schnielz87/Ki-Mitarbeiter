"""Begruessungsbild beim Start - das Logo, drei Sekunden.

Warum es das gibt: der Start der Anwendung ist nicht sofort fertig. Es
werden Datenbanken geoeffnet, das Profil geladen, der Suchindex geprueft
und - der laengste Posten - der Modelldienst im Hintergrund hochgefahren.
Bis dahin stand bisher ein leerer Bildschirm oder ein halb aufgebautes
Fenster.

Die drei Sekunden kosten deshalb **keine** Zeit: sie fallen in eine
Zeitspanne, in der die Anwendung ohnehin arbeitet. Das Modell laedt
waehrenddessen weiter (siehe ``vorladen`` im Controller), nicht danach.

Zwei Dinge sind hier bewusst so gebaut:

* **Es haelt nie auf.** Kann kein Bild geladen werden, faellt das
  Begruessungsbild ersatzlos weg und die Anwendung startet normal. Ein
  Startbild, das den Start verhindert, waere die schlechteste aller
  Loesungen.
* **Es laesst sich wegklicken.** Wer eilig ist, klickt oder drueckt eine
  Taste und ist sofort drin. Wer die Anwendung ohne Begruessung will,
  startet mit ``--kein-startbild``.
"""

from __future__ import annotations

import tkinter as tk

from pkc.logging_setup import get_logger

log = get_logger(__name__)

#: Anzeigedauer in Millisekunden. Vom Auftraggeber vorgegeben: drei Sekunden.
DAUER_MS = 3000

#: Grund der Flaeche - dasselbe Marineblau wie die Seitenleiste, damit der
#: Uebergang ins Hauptfenster nicht blitzt.
GRUND = "#17202e"

#: Hoehe des Logos in Bildpunkten.
LOGO_HOEHE = 120


class Startbild:
    """Ein randloses Fenster mit dem Logo, das sich selbst wieder schliesst.

    Verwendung::

        bild = Startbild(brand, profil="Buchhalter")
        bild.zeigen()          # blockiert hoechstens DAUER_MS
    """

    def __init__(self, brand, profil: str = "", dauer_ms: int = DAUER_MS,
                 root: tk.Misc | None = None):
        self.brand = brand
        self.profil = profil
        self.dauer_ms = int(dauer_ms)
        self._eigenes_root = root is None
        self._root = root
        self.fenster = None
        self.gezeigt = False
        #: Laeuft gerade ``zeigen``? Dann raeumt ``schliessen`` das
        #: Wurzelfenster nicht ab - das erledigt ``zeigen`` selbst, nachdem
        #: sein ``wait_window`` zurueckgekehrt ist.
        self._wartet = False

    # -- Aufbau --------------------------------------------------------
    def _bild_laden(self, fenster):
        """Laedt die helle Logovariante, skaliert auf LOGO_HOEHE.

        Tk kann von Haus aus nur ganzzahlig verkleinern (``subsample``).
        Liegt Pillow vor, wird sauber skaliert; sonst wird ganzzahlig
        verkleinert. Beides ist besser als gar kein Bild.
        """
        pfad = self.brand.variante("dark") or self.brand.logo_pfad
        if pfad is None:
            return None
        try:
            from PIL import Image, ImageTk

            bild = Image.open(pfad).convert("RGBA")
            breite = max(1, round(bild.width * LOGO_HOEHE / bild.height))
            bild = bild.resize((breite, LOGO_HOEHE), Image.LANCZOS)
            return ImageTk.PhotoImage(bild, master=fenster)
        except Exception:               # Pillow fehlt oder kann die Datei nicht
            log.debug("Pillow nicht verfuegbar - Startbild wird ganzzahlig "
                      "verkleinert", exc_info=True)
        try:
            bild = tk.PhotoImage(file=str(pfad), master=fenster)
            teiler = max(1, round(bild.height() / LOGO_HOEHE))
            return bild.subsample(teiler, teiler) if teiler > 1 else bild
        except Exception:               # pragma: no cover - defensiv
            log.debug("Startbild konnte nicht geladen werden", exc_info=True)
            return None

    def _aufbauen(self) -> bool:
        if self._root is None:
            self._root = tk.Tk()
            self._root.withdraw()

        fenster = tk.Toplevel(self._root)
        fenster.configure(bg=GRUND)
        try:
            fenster.overrideredirect(True)      # ohne Rahmen und Titelleiste
        except Exception:                       # pragma: no cover - defensiv
            log.debug("randloses Fenster nicht moeglich", exc_info=True)

        bild = self._bild_laden(fenster)
        if bild is None:
            # Ohne Logo kein Begruessungsbild. Ein leerer blauer Kasten waere
            # keine Begruessung, sondern eine Stoerung.
            try:
                fenster.destroy()
            except Exception:                   # pragma: no cover
                pass
            return False

        rahmen = tk.Frame(fenster, bg=GRUND, padx=64, pady=48)
        rahmen.pack()
        marke = tk.Label(rahmen, image=bild, bg=GRUND, borderwidth=0)
        marke.image = bild                      # Referenz halten
        marke.pack()
        if self.profil:
            tk.Label(rahmen, text=self.brand.titel(self.profil), bg=GRUND,
                     fg="#8fb4dd", font=("Segoe UI", 11)).pack(pady=(18, 0))
        tk.Label(rahmen, text="wird gestartet ...", bg=GRUND, fg="#5c7796",
                 font=("Segoe UI", 9)).pack(pady=(6, 0))

        self.fenster = fenster
        self._mittig(fenster)
        for ereignis in ("<Button-1>", "<Key>", "<Escape>"):
            fenster.bind(ereignis, lambda _e: self.schliessen())
        try:
            fenster.focus_force()
        except Exception:                       # pragma: no cover - defensiv
            pass
        return True

    @staticmethod
    def _mittig(fenster) -> None:
        """Mittig auf dem Bildschirm - nicht in der Ecke."""
        try:
            fenster.update_idletasks()
            breite = fenster.winfo_reqwidth()
            hoehe = fenster.winfo_reqheight()
            x = max(0, (fenster.winfo_screenwidth() - breite) // 2)
            y = max(0, (fenster.winfo_screenheight() - hoehe) // 2)
            fenster.geometry(f"+{x}+{y}")
        except Exception:                       # pragma: no cover - defensiv
            log.debug("Startbild liess sich nicht mittig setzen", exc_info=True)

    # -- Anzeigen ------------------------------------------------------
    def oeffnen(self):
        """Zeigt das Bild, **ohne** auf sein Ende zu warten.

        Gedacht fuer die Bildaufnahme der Anleitung
        (``tools/oberflaeche_fotografieren.py``): dort soll das Bild
        stehenbleiben, bis es fotografiert ist. Gibt das Fenster zurueck
        oder ``None``, wenn keines aufgebaut werden konnte.

        **Wer hiermit oeffnet, muss ``schliessen`` aufrufen.** Sonst
        bleibt das selbst erzeugte Wurzelfenster stehen, und alles, was
        danach ohne ausdrueckliches Elternteil erzeugt wird - eine
        ``StringVar`` etwa -, haengt an diesem stehengebliebenen Fenster
        statt am neuen. Genau das ist passiert: der Betriebsmodus stand in
        einer Variablen des alten Fensters, und das Auswahlfeld im neuen
        Fenster zeigte deshalb nichts an. Es sah aus wie ein leeres Feld
        und war ein Fehler in der Aufraeumung.
        """
        try:
            if not self._aufbauen():
                return None
        except Exception:                       # pragma: no cover - defensiv
            log.debug("Startbild liess sich nicht oeffnen", exc_info=True)
            return None
        self.gezeigt = True
        return self.fenster

    def zeigen(self) -> bool:
        """Zeigt das Bild und kehrt nach spaetestens ``dauer_ms`` zurueck.

        Gibt zurueck, ob es tatsaechlich gezeigt wurde. Nie eine Ausnahme:
        was hier schiefgeht, darf den Start der Anwendung nicht verhindern.
        """
        try:
            if not self._aufbauen():
                return False
            self.gezeigt = True
            # Das Fenster in einer eigenen Bezeichnung festhalten, BEVOR der
            # Selbstschluss eingeplant wird: ``schliessen`` setzt
            # ``self.fenster`` auf None, und laeuft der Rueckruf frueh - beim
            # Klick des Benutzers oder in einem Test -, greife ich sonst
            # gleich danach auf None zu und das Begruessungsbild endet in
            # einem Fehler statt in der Anwendung.
            fenster = self.fenster
            self._wartet = True
            fenster.after(self.dauer_ms, self.schliessen)
            fenster.wait_window()
            return True
        except Exception:                       # pragma: no cover - defensiv
            log.debug("Startbild uebersprungen", exc_info=True)
            self.schliessen()
            return False
        finally:
            self._wartet = False
            self._root_aufraeumen()

    def schliessen(self) -> None:
        """Schliesst das Bild - und raeumt das Wurzelfenster mit ab.

        Das Abraeumen gehoert hierher und nicht nur ans Ende von
        ``zeigen``: sonst bleibt nach ``oeffnen`` ein unsichtbares
        Wurzelfenster stehen (siehe Erklaerung dort). Laeuft gerade
        ``zeigen``, wird es nicht hier abgeraeumt - dort wartet noch ein
        ``wait_window`` auf genau dieses Fenster.
        """
        fenster, self.fenster = self.fenster, None
        if fenster is not None:
            try:
                fenster.destroy()
            except Exception:                   # pragma: no cover - defensiv
                log.debug("Startbild liess sich nicht schliessen",
                          exc_info=True)
        if not self._wartet:
            self._root_aufraeumen()

    def _root_aufraeumen(self) -> None:
        """Das selbst erzeugte Wurzelfenster wieder abraeumen.

        Sonst bliebe eine unsichtbare Tk-Wurzel zurueck, und das naechste
        Fenster haette einen Vorfahren, den niemand mehr kennt.
        """
        if not self._eigenes_root or self._root is None:
            return
        root, self._root = self._root, None
        try:
            root.destroy()
        except Exception:                       # pragma: no cover - defensiv
            log.debug("Wurzelfenster des Startbilds liess sich nicht "
                      "abraeumen", exc_info=True)


def zeigen(brand, profil: str = "", dauer_ms: int = DAUER_MS) -> bool:
    """Bequemer Weg: Begruessungsbild einmal zeigen."""
    return Startbild(brand, profil, dauer_ms).zeigen()
