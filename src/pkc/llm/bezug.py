"""Modelldatei beziehen - als Teil der Anwendung, nicht als Beiwerk.

Bisher lag das nur in ``tools/modell_einrichten.py``. Wer nur die EXE hat -
also jeder normale Anwender - konnte es damit nicht erreichen. Der Auftrag
(Abschnitt 14) verlangt aber ausdruecklich einen gefuehrten Weg zum Modell
und nicht bloss den Verweis auf eine Dokumentationsdatei.

Es wird **nie** ohne ausdrueckliche Angabe einer Adresse geladen: welche
Bezugsquelle in Frage kommt und unter welcher Lizenz ihr Modell steht, ist
eine bewusste Entscheidung des Betreibers.
"""

from __future__ import annotations

import hashlib
import shutil
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..logging_setup import get_logger

log = get_logger(__name__)

BLOCK = 512 * 1024


@dataclass
class Ladeergebnis:
    ok: bool
    pfad: Path | None
    pruefsumme: str = ""
    meldung: str = ""
    bytes_geladen: int = 0


def laden(
    url: str,
    zielordner: Path,
    erwartete_pruefsumme: str = "",
    name: str = "",
    ueberschreiben: bool = False,
    fortschritt: Callable[[int, int, float], None] | None = None,
) -> Ladeergebnis:
    """Laedt eine Modelldatei mit Pruefsumme.

    Bis zum Abschluss liegt die Datei unter ``.teil``. Erst wenn sie
    vollstaendig ist und die Pruefsumme stimmt, wird sie umbenannt - ein
    abgebrochener Download hinterlaesst so nie eine halbe Datei, die
    aussieht wie ein einsatzbereites Modell.
    """
    zielordner = Path(zielordner)
    zielordner.mkdir(parents=True, exist_ok=True)

    dateiname = name or url.split("/")[-1].split("?")[0] or "modell.gguf"
    ziel = zielordner / dateiname
    if ziel.exists() and not ueberschreiben:
        return Ladeergebnis(False, ziel,
                            meldung=f"Es gibt bereits {ziel.name}. "
                                    f"Mit --ueberschreiben erneut laden.")

    frei = shutil.disk_usage(zielordner).free
    teil = ziel.with_suffix(ziel.suffix + ".teil")
    pruefsumme = hashlib.sha256()
    begonnen = time.monotonic()
    geladen = 0

    try:
        anfrage = urllib.request.Request(
            url, headers={"User-Agent": "Portabler-KI-Mitarbeiter"})
        with urllib.request.urlopen(anfrage, timeout=60) as antwort, teil.open("wb") as datei:
            gesamt = int(antwort.headers.get("Content-Length", 0))
            if gesamt and gesamt > frei:
                teil.unlink(missing_ok=True)
                return Ladeergebnis(
                    False, None,
                    meldung=f"Zu wenig Speicherplatz: {gesamt/1024**3:.1f} GB "
                            f"noetig, {frei/1024**3:.1f} GB frei.")
            while True:
                block = antwort.read(BLOCK)
                if not block:
                    break
                datei.write(block)
                pruefsumme.update(block)
                geladen += len(block)
                if fortschritt is not None:
                    fortschritt(geladen, gesamt,
                                geladen / max(time.monotonic() - begonnen, 0.001))
    except (urllib.error.URLError, OSError, TimeoutError, ValueError) as exc:
        teil.unlink(missing_ok=True)
        log.warning("Modelldownload fehlgeschlagen: %s", exc)
        return Ladeergebnis(False, None, meldung=f"Download fehlgeschlagen: {exc}")

    tatsaechlich = pruefsumme.hexdigest()
    if erwartete_pruefsumme and erwartete_pruefsumme.strip().lower() != tatsaechlich:
        teil.unlink(missing_ok=True)
        return Ladeergebnis(
            False, None, pruefsumme=tatsaechlich, bytes_geladen=geladen,
            meldung="Die Pruefsumme stimmt NICHT. Die Datei wurde verworfen.")

    teil.replace(ziel)
    hinweis = ("Pruefsumme bestaetigt." if erwartete_pruefsumme else
               "Hinweis: ohne erwartete Pruefsumme ist die Datei nicht gegen "
               "Manipulation geprueft.")
    return Ladeergebnis(True, ziel, tatsaechlich,
                        f"Fertig: {ziel.name} "
                        f"({ziel.stat().st_size/1024**3:.2f} GB). {hinweis}",
                        geladen)


def uebernehmen(
    quelle: Path,
    zielordner: Path,
    name: str = "",
    ueberschreiben: bool = False,
    fortschritt: Callable[[int, int, float], None] | None = None,
) -> Ladeergebnis:
    """Nimmt eine bereits vorhandene Modelldatei auf den Datentraeger.

    Das Modell muss nicht auf jedem Rechner neu geladen werden. Wer es
    einmal hat - auf einem anderen Stick, im Firmennetz, auf einer externen
    Platte -, kann es hier uebernehmen. Genau dafuer gibt es diesen Weg:

    * ein zweiter Datentraeger fuer eine Kollegin,
    * ein Buero, in dem der Download gesperrt ist,
    * eine Leitung, ueber die man 4,7 GB nicht zweimal ziehen will.

    Kopiert wird bewusst, statt nur zu verweisen. Ein Verweis auf ein
    Netzlaufwerk waere kleiner, aber der Datentraeger waere dann nicht mehr
    fuer sich allein lauffaehig - und das ist der Sinn dieser Anwendung.
    """
    quelle = Path(quelle)
    zielordner = Path(zielordner)
    if not quelle.is_file():
        return Ladeergebnis(False, None, meldung=f"Es gibt keine Datei {quelle}.")
    if quelle.suffix.lower() != ".gguf":
        return Ladeergebnis(
            False, None,
            meldung=f"{quelle.name} ist keine GGUF-Datei. Andere Formate "
                    "(safetensors, GPTQ, AWQ) kann der Modelldienst nicht laden.")

    zielordner.mkdir(parents=True, exist_ok=True)
    ziel = zielordner / (name or quelle.name)
    try:
        if ziel.exists() and ziel.samefile(quelle):
            return Ladeergebnis(True, ziel, meldung=f"{ziel.name} liegt bereits hier.",
                                bytes_geladen=0)
    except OSError:                                # pragma: no cover - defensiv
        pass
    if ziel.exists() and not ueberschreiben:
        return Ladeergebnis(False, ziel,
                            meldung=f"Es gibt bereits {ziel.name}. "
                                    "Zum Ersetzen ausdruecklich ueberschreiben.")

    gesamt = quelle.stat().st_size
    frei = shutil.disk_usage(zielordner).free
    if gesamt > frei:
        return Ladeergebnis(
            False, None,
            meldung=f"Zu wenig Speicherplatz: {gesamt/1024**3:.1f} GB noetig, "
                    f"{frei/1024**3:.1f} GB frei.")

    # Dieselbe Vorsicht wie beim Download: bis zum Abschluss heisst die
    # Datei ".teil". Ein abgebrochener Vorgang - Stick abgezogen, Platte
    # voll - hinterlaesst so nie eine halbe Datei, die der Modelldienst
    # spaeter fuer ein Modell haelt.
    teil = ziel.with_suffix(ziel.suffix + ".teil")
    pruefsumme = hashlib.sha256()
    begonnen = time.monotonic()
    kopiert = 0
    try:
        with quelle.open("rb") as ein, teil.open("wb") as aus:
            while True:
                block = ein.read(BLOCK)
                if not block:
                    break
                aus.write(block)
                pruefsumme.update(block)
                kopiert += len(block)
                if fortschritt is not None:
                    fortschritt(kopiert, gesamt,
                                kopiert / max(time.monotonic() - begonnen, 0.001))
    except OSError as exc:
        teil.unlink(missing_ok=True)
        log.warning("Modelldatei liess sich nicht uebernehmen: %s", exc)
        return Ladeergebnis(False, None, meldung=f"Uebernahme fehlgeschlagen: {exc}")

    teil.replace(ziel)
    return Ladeergebnis(
        True, ziel, pruefsumme.hexdigest(),
        f"Uebernommen: {ziel.name} ({ziel.stat().st_size/1024**3:.2f} GB). "
        "Die Datei liegt jetzt auf diesem Datentraeger und wird auch ohne "
        "Internet verwendet.",
        kopiert)
