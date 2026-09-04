"""SQLite-Zugriff mit eingebauter Migrationsverwaltung.

Bewusste Entscheidung: eine *eingebettete* Datenbank (SQLite).  Damit ist im
Grundbetrieb kein Datenbankserver noetig; die Datei liegt auf dem portablen
Datentraeger und wandert mit ihm.
"""

from __future__ import annotations

import datetime as _dt
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable, Sequence

from ..logging_setup import get_logger

log = get_logger(__name__)


def utc_now() -> str:
    """ISO-8601 UTC-Zeitstempel (sekundengenau, sortierbar)."""
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def fts5_available(conn: sqlite3.Connection | None = None) -> bool:
    own = conn is None
    conn = conn or sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE __fts_probe USING fts5(x)")
        conn.execute("DROP TABLE __fts_probe")
        return True
    except sqlite3.Error:
        return False
    finally:
        if own:
            conn.close()


class Database:
    """Duenne, thread-sichere Huelle um eine SQLite-Datei.

    Verbindungen sind pro Thread getrennt (SQLite-Objekte sind nicht
    thread-sicher); die Datei selbst wird im WAL-Modus geteilt.
    """

    def __init__(self, path: Path, migrations: Sequence[tuple[int, str]]):
        self.path = Path(path)
        self.migrations = tuple(sorted(migrations, key=lambda m: m[0]))
        self._local = threading.local()
        self._migrate_lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    # -- Verbindung ----------------------------------------------------
    @property
    def conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.path), timeout=30.0, isolation_level=None)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=30000")
            self._local.conn = conn
        return conn

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    # -- Ausfuehren ----------------------------------------------------
    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, tuple(params))

    def executemany(self, sql: str, rows: Iterable[Sequence[Any]]) -> sqlite3.Cursor:
        return self.conn.executemany(sql, [tuple(r) for r in rows])

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, tuple(params)).fetchall()

    def one(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
        return self.conn.execute(sql, tuple(params)).fetchone()

    def scalar(self, sql: str, params: Iterable[Any] = (), default: Any = None) -> Any:
        row = self.one(sql, params)
        return row[0] if row is not None else default

    class _Tx:
        def __init__(self, db: "Database"):
            self.db = db

        def __enter__(self) -> sqlite3.Connection:
            self.db.conn.execute("BEGIN IMMEDIATE")
            return self.db.conn

        def __exit__(self, exc_type, exc, tb) -> bool:
            if exc_type is None:
                self.db.conn.execute("COMMIT")
            else:
                self.db.conn.execute("ROLLBACK")
            return False

    def transaction(self) -> "Database._Tx":
        return Database._Tx(self)

    # -- Migration -----------------------------------------------------
    def user_version(self) -> int:
        return int(self.scalar("PRAGMA user_version", default=0) or 0)

    def migrate(self) -> int:
        with self._migrate_lock:
            current = self.user_version()
            target = self.migrations[-1][0] if self.migrations else 0
            if current >= target:
                return current
            for version, script in self.migrations:
                if version <= current:
                    continue
                log.info("Migration %s -> %s (%s)", current, version, self.path.name)
                self.conn.executescript(script)
                self.conn.execute(f"PRAGMA user_version={int(version)}")
                current = version
            return current

    # -- Wartung -------------------------------------------------------
    def integrity_check(self) -> tuple[bool, str]:
        try:
            result = self.scalar("PRAGMA integrity_check", default="unbekannt")
        except sqlite3.DatabaseError as exc:
            return False, f"Datenbank nicht lesbar: {exc}"
        return (result == "ok"), str(result)

    def backup_to(self, target: Path) -> Path:
        """Konsistente Sicherung der Datei (auch waehrend des Betriebs)."""
        target.parent.mkdir(parents=True, exist_ok=True)
        dest = sqlite3.connect(str(target))
        try:
            self.conn.backup(dest)
        finally:
            dest.close()
        return target

    def vacuum(self) -> None:
        self.conn.execute("VACUUM")

    def table_names(self) -> list[str]:
        return [
            r[0]
            for r in self.query(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
