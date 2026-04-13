"""SQLite connection manager."""

import sqlite3
from pathlib import Path


_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create and initialize a SQLite connection with WAL mode."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    schema = _SCHEMA_PATH.read_text()
    conn.executescript(schema)
    conn.commit()

    return conn
