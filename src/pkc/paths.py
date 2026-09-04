"""Portable path resolution.

Der gesamte Datenbestand des portablen KI-Mitarbeiters liegt relativ zum
Programmwurzelverzeichnis (dem Ordner auf der externen SSD).  Es darf kein
fester Laufwerksbuchstabe und kein fester Benutzerpfad verdrahtet werden.

Auflösungsreihenfolge fuer die Wurzel:

1. Umgebungsvariable ``KIM_ROOT`` (Tests, Sonderfaelle)
2. Bei eingefrorener Anwendung (PyInstaller): Verzeichnis der EXE bzw. dessen
   Elternverzeichnis, sofern dort die Markerdatei liegt.
3. Aufwaertssuche ab dieser Quelldatei nach der Markerdatei
   ``.portable_root``.
4. Aufwaertssuche nach einem Verzeichnis, das ``src/pkc`` enthaelt.

Alle Pfade werden als ``pathlib.Path`` zurueckgegeben und funktionieren mit
Leerzeichen sowie beliebigen Laufwerksbuchstaben.
"""

from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

MARKER_NAME = ".portable_root"

#: Name -> Unterverzeichnis relativ zur Wurzel.
LAYOUT: dict[str, str] = {
    "app": "src",
    "config": "config",
    "models": "models",
    "knowledge": "knowledge",
    "resources": "resources",
    "resources_raw": "resources/raw",
    "resources_normalized": "resources/normalized",
    "resources_metadata": "resources/metadata",
    "resources_index": "resources/index",
    "company": "company",
    "database": "database",
    "conversations": "conversations",
    "workspace": "workspace",
    "connectors": "connectors",
    "runtime": "runtime",
    "logs": "logs",
    "updates": "updates",
    "backups": "backups",
    "data": "data",
    "profiles": "src/profiles",
    "checkpoints": "checkpoints",
    "tools": "tools",
    "docs": "docs",
}

#: Verzeichnisse, die zum *Programm* gehoeren (nicht zu den Nutzdaten).
PROGRAM_DIRS = frozenset({"app", "profiles", "tools", "docs"})

#: Verzeichnisse, die beim Start angelegt werden duerfen/sollen.
RUNTIME_DIRS = (
    "config",
    "models",
    "knowledge",
    "resources",
    "resources_raw",
    "resources_normalized",
    "resources_metadata",
    "resources_index",
    "company",
    "database",
    "conversations",
    "workspace",
    "connectors",
    "runtime",
    "logs",
    "updates",
    "backups",
    "data",
    "checkpoints",
)


def is_frozen() -> bool:
    """True, wenn die Anwendung als gepackte EXE laeuft (PyInstaller)."""
    return bool(getattr(sys, "frozen", False))


def _marker_dir(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / MARKER_NAME).is_file():
            return candidate
    return None


def _src_dir(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "src" / "pkc" / "paths.py").is_file():
            return candidate
    return None


def _source_root() -> Path | None:
    """Wurzel des mitgelieferten Programmcodes (Verzeichnis ueber ``src``)."""
    if is_frozen():
        exe_dir = Path(sys.executable).resolve().parent
        for candidate in [exe_dir, *exe_dir.parents]:
            if (candidate / "src" / "profiles").is_dir():
                return candidate
        return None
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "src" / "profiles").is_dir():
            return candidate
    return None


def detect_root() -> Path:
    """Ermittelt das portable Wurzelverzeichnis."""
    env = os.environ.get("KIM_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    if is_frozen():
        exe_dir = Path(sys.executable).resolve().parent
        found = _marker_dir(exe_dir)
        if found is not None:
            return found
        # onedir-Build: EXE liegt in <root>/runtime/app/ -> zwei Ebenen hoch
        return exe_dir

    here = Path(__file__).resolve()
    found = _marker_dir(here)
    if found is not None:
        return found
    found = _src_dir(here)
    if found is not None:
        return found
    return here.parents[2]


@dataclass(frozen=True)
class Paths:
    """Zugriff auf alle Verzeichnisse relativ zur portablen Wurzel."""

    root: Path

    @classmethod
    def detect(cls) -> "Paths":
        return cls(detect_root())

    def __getattr__(self, name: str) -> Path:
        """Bequemer Zugriff: ``paths.models`` entspricht ``paths.get("models")``.

        Beide Wege muessen dasselbe liefern - sonst waere ein Verzeichnis je
        nach Schreibweise ein anderes.
        """
        if name not in LAYOUT:
            raise AttributeError(name)
        return self.get(name)

    def get(self, name: str) -> Path:
        """Verzeichnis nach Layout-Name (explizite, typsichere Variante)."""
        if name in PROGRAM_DIRS:
            return self.program_root / LAYOUT[name]
        return self.root / LAYOUT[name]

    @property
    def program_root(self) -> Path:
        """Wurzel der *Programmdateien* (Code, Mitarbeiterprofile).

        Im Normalbetrieb ist das dieselbe Wurzel wie die der Daten: alles liegt
        zusammen auf der SSD.  Sind die Daten ausnahmsweise woanders (Tests,
        getrennte Datenablage, schreibgeschuetztes Programmverzeichnis), wird
        der Ort des Programmcodes verwendet.  So findet die Anwendung ihr
        Mitarbeiterprofil auch dann, wenn nur der Datenbereich verschoben wurde.
        """
        if (self.root / "src" / "profiles").is_dir():
            return self.root
        source_root = _source_root()
        return source_root if source_root is not None else self.root

    # -- konkrete, haeufig benutzte Dateien -----------------------------
    @property
    def company_db(self) -> Path:
        return self.get("database") / "company.db"

    @property
    def knowledge_db(self) -> Path:
        return self.get("resources_index") / "knowledge.db"

    @property
    def settings_file(self) -> Path:
        return self.get("config") / "settings.json"

    @property
    def source_registry(self) -> Path:
        return self.get("config") / "source_registry.json"

    @property
    def secrets_file(self) -> Path:
        return self.get("config") / "secrets.enc"

    @property
    def state_file(self) -> Path:
        return self.get("runtime") / "state.json"

    def ensure_runtime_dirs(self) -> list[Path]:
        """Legt alle Laufzeitverzeichnisse an und gibt sie zurueck."""
        created: list[Path] = []
        for name in RUNTIME_DIRS:
            path = self.get(name)
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
        return created

    def relative(self, path: Path | str) -> str:
        """Pfad relativ zur Wurzel als String mit ``/`` (fuer Logs/Reports)."""
        p = Path(path)
        try:
            return p.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return p.as_posix()

    def is_writable(self) -> bool:
        """Prueft echten Schreibzugriff auf die Wurzel (nicht nur Flags)."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.root, prefix=".wtest-"):
                pass
            return True
        except OSError:
            return False

    def write_marker(self) -> Path:
        """Schreibt die Markerdatei, die die Wurzel eindeutig kennzeichnet."""
        marker = self.root / MARKER_NAME
        if not marker.is_file():
            marker.write_text(
                "Portable-KI-Mitarbeiter Wurzelverzeichnis.\n"
                "Diese Datei nicht loeschen - sie markiert den portablen Datenbestand.\n",
                encoding="utf-8",
            )
        return marker


_CACHED: Paths | None = None


def get_paths(refresh: bool = False) -> Paths:
    """Prozessweit gecachte Pfadinstanz."""
    global _CACHED
    if _CACHED is None or refresh:
        _CACHED = Paths.detect()
    return _CACHED
