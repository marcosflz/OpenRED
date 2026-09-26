"""SQLite DAO for the OpenRED database (stdlib ``sqlite3`` only).

The schema is byte-identical to ``legacy/functions.initialize_database`` and the
quirks of the original windows are preserved:

* duplicated component names are allowed;
* IDs are reassigned to 1..N (ordered by the old id) after every add/edit/delete
  (see ``front_chemWin.reassign_ids`` / ``front_propWin.reassign_ids``);
* a single snapshot ``database.db.bak`` is taken before the first write of the
  process (contract §3.3, retention: 1).

Every public operation opens (and closes) its own connection; the database path
is resolved through :mod:`openred_engine.paths` and never from the CWD.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from typing import Any

from openred_engine import paths
from openred_engine.mathutils import convert_to_latex

__all__ = [
    "COMPONENT_COLUMNS",
    "PROPELLANT_COLUMNS",
    "backup_once",
    "component_row",
    "components",
    "delete_component",
    "delete_propellant",
    "initialize_database",
    "insert_component",
    "insert_propellant",
    "propellant_value",
    "propellants",
    "reassign_ids",
    "update_component",
    "update_propellant",
]

# Columns as created by ``legacy/functions.initialize_database`` (``id`` first).
COMPONENT_COLUMNS: tuple[str, ...] = (
    "Component", "MolWeight", "Hf0",
    "minColdTemp", "maxColdTemp", "minHotTemp", "maxHotTemp",
    "a1_cold", "a2_cold", "a3_cold", "a4_cold", "a5_cold",
    "a1_hot", "a2_hot", "a3_hot", "a4_hot", "a5_hot",
)
PROPELLANT_COLUMNS: tuple[str, ...] = (
    "Propelente", "T_ad", "MolWeight", "Cp", "Cv", "R", "gamma",
    "cChar", "Density", "P1_min", "P1_max", "a", "n",
)

_TABLES: dict[str, tuple[str, ...]] = {
    "termoquimica": ("id",) + COMPONENT_COLUMNS,
    "propelente": ("id",) + PROPELLANT_COLUMNS,
}

_CREATE_TERMOQUIMICA = '''
        CREATE TABLE IF NOT EXISTS termoquimica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Component TEXT,
            MolWeight NUMERIC,
            Hf0 NUMERIC,
            minColdTemp NUMERIC,
            maxColdTemp NUMERIC,
            minHotTemp NUMERIC,
            maxHotTemp NUMERIC,
            a1_cold NUMERIC,
            a2_cold NUMERIC,
            a3_cold NUMERIC,
            a4_cold NUMERIC,
            a5_cold NUMERIC,
            a1_hot NUMERIC,
            a2_hot NUMERIC,
            a3_hot NUMERIC,
            a4_hot NUMERIC,
            a5_hot NUMERIC
        )
    '''

_CREATE_PROPELLENTE = '''
        CREATE TABLE IF NOT EXISTS propelente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Propelente TEXT,
            T_ad NUMERIC,
            MolWeight NUMERIC,
            Cp NUMERIC,
            Cv NUMERIC,
            R NUMERIC,
            gamma NUMERIC,
            cChar NUMERIC,
            Density NUMERIC,
            P1_min NUMERIC,
            P1_max NUMERIC,
            a NUMERIC,
            n NUMERIC
        )
    '''

_backup_done = False  # per-process flag, see ``backup_once``


# ---------------------------------------------------------------------------
# connection helpers
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(str(paths.db_path()))
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create both tables when missing (idempotent, DDL identical to legacy)."""
    connection = _connect()
    try:
        cursor = connection.cursor()
        cursor.execute(_CREATE_TERMOQUIMICA)
        cursor.execute(_CREATE_PROPELLENTE)
        connection.commit()
    finally:
        connection.close()


def backup_once() -> Path | None:
    """Snapshot ``database.db`` to ``database.db.bak`` before the first write.

    Retention is 1: the previous ``.bak`` is overwritten. Returns the backup
    path, or ``None`` when it was already taken or the database does not exist.
    """
    global _backup_done
    if _backup_done:
        return None
    database = paths.db_path()
    if not database.is_file():
        _backup_done = True
        return None
    backup = database.with_name(database.name + ".bak")
    shutil.copy2(database, backup)
    _backup_done = True
    return backup


def _prepare_write() -> None:
    initialize_database()
    backup_once()


# ---------------------------------------------------------------------------
# generic SQL helpers
# ---------------------------------------------------------------------------

def _clean_values(table: str, values: dict[str, Any]) -> dict[str, Any]:
    """Keep only real column names (``id`` is never written explicitly)."""
    columns = _TABLES[table]
    return {key: value for key, value in values.items() if key in columns and key != "id"}


def _insert(connection: sqlite3.Connection, table: str, values: dict[str, Any]) -> None:
    if values:
        columns = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        connection.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(values.values())
        )
    else:
        connection.execute(f"INSERT INTO {table} DEFAULT VALUES")


def _update(connection: sqlite3.Connection, table: str, row_id: Any, values: dict[str, Any]) -> None:
    if not values:
        return
    assignments = ", ".join(f"{column}=?" for column in values)
    connection.execute(
        f"UPDATE {table} SET {assignments} WHERE id=?", (*values.values(), row_id)
    )


def _reassign_ids(connection: sqlite3.Connection, table: str) -> None:
    """Renumber ``table`` to 1..N keeping the order by the current id."""
    records = connection.execute(f"SELECT id FROM {table} ORDER BY id").fetchall()
    new_id = 1
    for record in records:
        old_id = record[0]
        connection.execute(f"UPDATE {table} SET id=? WHERE id=?", (new_id, old_id))
        new_id += 1


def _write(table: str, operation: Any) -> None:
    _prepare_write()
    connection = _connect()
    try:
        operation(connection)
        _reassign_ids(connection, table)
        connection.commit()
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# termoquimica
# ---------------------------------------------------------------------------

def components() -> list[dict]:
    """Return every thermochemical component (all columns plus ``latex``)."""
    connection = _connect()
    try:
        rows = connection.execute("SELECT * FROM termoquimica ORDER BY id").fetchall()
    finally:
        connection.close()
    return [{**dict(row), "latex": convert_to_latex(row["Component"])} for row in rows]


def component_row(name: str) -> dict | None:
    """Return the first component named ``name`` (dict with all columns) or None."""
    connection = _connect()
    try:
        row = connection.execute(
            "SELECT * FROM termoquimica WHERE Component = ? ORDER BY id LIMIT 1", (name,)
        ).fetchone()
    finally:
        connection.close()
    return dict(row) if row is not None else None


def insert_component(values: dict) -> None:
    """Insert a component (column-named keys, no ``id``) and reassign IDs."""
    _write("termoquimica", lambda connection: _insert(connection, "termoquimica", _clean_values("termoquimica", values)))


def update_component(id: Any, values: dict) -> None:
    """Update the component ``id`` and reassign IDs."""
    _write("termoquimica", lambda connection: _update(connection, "termoquimica", id, _clean_values("termoquimica", values)))


def delete_component(id: Any) -> None:
    """Delete the component ``id`` and reassign IDs."""
    _write("termoquimica", lambda connection: connection.execute("DELETE FROM termoquimica WHERE id=?", (id,)))


# ---------------------------------------------------------------------------
# propelente
# ---------------------------------------------------------------------------

def propellants() -> list[dict]:
    """Return every propellant (all columns)."""
    connection = _connect()
    try:
        rows = connection.execute("SELECT * FROM propelente ORDER BY id").fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def insert_propellant(values: dict) -> None:
    """Insert a propellant (column-named keys, no ``id``) and reassign IDs."""
    _write("propelente", lambda connection: _insert(connection, "propelente", _clean_values("propelente", values)))


def update_propellant(id: Any, values: dict) -> None:
    """Update the propellant ``id`` and reassign IDs."""
    _write("propelente", lambda connection: _update(connection, "propelente", id, _clean_values("propelente", values)))


def delete_propellant(id: Any) -> None:
    """Delete the propellant ``id`` and reassign IDs."""
    _write("propelente", lambda connection: connection.execute("DELETE FROM propelente WHERE id=?", (id,)))


def propellant_value(column: str, name: str) -> list:
    """Distinct values of ``column`` for the propellant named ``name``.

    ``column`` is validated against the ``propelente`` schema whitelist before
    being interpolated (the legacy code interpolated a raw f-string).
    """
    if column not in _TABLES["propelente"]:
        raise ValueError(f"Invalid propellant column: {column}")
    connection = _connect()
    try:
        rows = connection.execute(
            f"SELECT DISTINCT {column} FROM propelente WHERE propelente.Propelente = ?", (name,)
        ).fetchall()
    finally:
        connection.close()
    return [row[0] for row in rows]


# ---------------------------------------------------------------------------
# maintenance
# ---------------------------------------------------------------------------

def reassign_ids(table: str) -> None:
    """Renumber ``table`` (``termoquimica`` / ``propelente``) to 1..N by old id."""
    if table not in _TABLES:
        raise ValueError(f"Invalid table: {table}")
    _prepare_write()
    connection = _connect()
    try:
        _reassign_ids(connection, table)
        connection.commit()
    finally:
        connection.close()


# The legacy application created the schema at startup; keep that behaviour.
initialize_database()
