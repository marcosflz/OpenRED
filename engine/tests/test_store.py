"""Tests for the SQLite DAO (:mod:`openred_engine.store`) and path resolution."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from openred_engine import paths, store
from tests import _legacy

EXPECTED_TERMOQUIMICA = [
    ("id", "INTEGER"),
    ("Component", "TEXT"),
    ("MolWeight", "NUMERIC"),
    ("Hf0", "NUMERIC"),
    ("minColdTemp", "NUMERIC"),
    ("maxColdTemp", "NUMERIC"),
    ("minHotTemp", "NUMERIC"),
    ("maxHotTemp", "NUMERIC"),
    ("a1_cold", "NUMERIC"),
    ("a2_cold", "NUMERIC"),
    ("a3_cold", "NUMERIC"),
    ("a4_cold", "NUMERIC"),
    ("a5_cold", "NUMERIC"),
    ("a1_hot", "NUMERIC"),
    ("a2_hot", "NUMERIC"),
    ("a3_hot", "NUMERIC"),
    ("a4_hot", "NUMERIC"),
    ("a5_hot", "NUMERIC"),
]

EXPECTED_PROPELLENTE = [
    ("id", "INTEGER"),
    ("Propelente", "TEXT"),
    ("T_ad", "NUMERIC"),
    ("MolWeight", "NUMERIC"),
    ("Cp", "NUMERIC"),
    ("Cv", "NUMERIC"),
    ("R", "NUMERIC"),
    ("gamma", "NUMERIC"),
    ("cChar", "NUMERIC"),
    ("Density", "NUMERIC"),
    ("P1_min", "NUMERIC"),
    ("P1_max", "NUMERIC"),
    ("a", "NUMERIC"),
    ("n", "NUMERIC"),
]


def _schema(db_path) -> dict[str, str]:
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall()
    finally:
        connection.close()
    return {name: sql for name, sql in rows}


def _columns(db_path, table: str) -> list[tuple[str, str]]:
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    finally:
        connection.close()
    return [(row[1], row[2]) for row in rows]


def _raw(sql: str, params: tuple = ()) -> None:
    connection = sqlite3.connect(paths.db_path())
    try:
        connection.execute(sql, params)
        connection.commit()
    finally:
        connection.close()


def test_ddl_matches_legacy(tmp_path, monkeypatch):
    legacy_functions = _legacy.legacy_functions()
    fresh_legacy = tmp_path / "fresh_legacy"
    fresh_legacy.mkdir()
    monkeypatch.chdir(fresh_legacy)
    legacy_functions.initialize_database()
    legacy_db = fresh_legacy / "database.db"

    fresh_engine = tmp_path / "fresh_engine"
    fresh_engine.mkdir()
    monkeypatch.setenv("OPENRED_DATA_DIR", str(fresh_engine))
    store.initialize_database()
    engine_db = fresh_engine / "database.db"

    assert _schema(engine_db) == _schema(legacy_db)
    assert _columns(engine_db, "termoquimica") == EXPECTED_TERMOQUIMICA
    assert _columns(engine_db, "propelente") == EXPECTED_PROPELLENTE
    assert _columns(legacy_db, "termoquimica") == EXPECTED_TERMOQUIMICA
    assert _columns(legacy_db, "propelente") == EXPECTED_PROPELLENTE


def test_components_listing(legacy_env):
    items = store.components()
    assert [item["id"] for item in items] == list(range(1, len(items) + 1))
    assert set(items[0]) == {"id", *store.COMPONENT_COLUMNS, "latex"}
    assert items[0]["Component"] == "C12H22O11 (Solid)"
    assert items[0]["latex"] == "C_{12}H_{22}O_{11}"
    assert store.component_row("N2 (10)") is None
    assert store.component_row("N2")["Component"] == "N2"
    assert store.component_row("Unobtainium") is None


def test_component_crud_reassigns_ids(legacy_env):
    initial = store.components()

    store.insert_component({"Component": "Test (99)", "MolWeight": 28.0, "Hf0": -110.5})
    inserted = store.component_row("Test (99)")
    assert inserted is not None
    assert inserted["MolWeight"] == 28.0
    assert [item["id"] for item in store.components()] == list(range(1, len(initial) + 2))

    store.update_component(inserted["id"], {"Component": "Test (100)", "MolWeight": 30.0})
    updated = store.component_row("Test (100)")
    assert updated is not None
    assert updated["MolWeight"] == 30.0
    assert store.component_row("Test (99)") is None

    store.delete_component(updated["id"])
    assert store.component_row("Test (100)") is None
    assert len(store.components()) == len(initial)
    assert [item["id"] for item in store.components()] == list(range(1, len(initial) + 1))


def test_propellants_and_whitelist(legacy_env):
    assert store.propellant_value("Propelente", "KNSU") == ["KNSU"]
    assert store.propellant_value("a", "KNSU") == [0.0100306326677]
    assert set(store.propellants()[0]) == {"id", *store.PROPELLANT_COLUMNS}

    with pytest.raises(ValueError, match="Invalid propellant column"):
        store.propellant_value("Component; DROP TABLE propelente", "KNSU")


def test_propellant_crud_reassigns_ids(legacy_env):
    initial = store.propellants()

    store.insert_propellant({"Propelente": "TEST", "a": 1.0, "n": 0.5})
    assert [item["id"] for item in store.propellants()] == list(range(1, len(initial) + 2))

    row = next(item for item in store.propellants() if item["Propelente"] == "TEST")
    store.update_propellant(row["id"], {"a": 2.0})
    assert store.propellant_value("a", "TEST") == [2.0]

    store.delete_propellant(row["id"])
    assert len(store.propellants()) == len(initial)
    assert [item["id"] for item in store.propellants()] == list(range(1, len(initial) + 1))


def test_reassign_ids_after_raw_delete(legacy_env):
    total = len(store.components())
    _raw("DELETE FROM termoquimica WHERE id=?", (2,))
    assert [item["id"] for item in store.components()] == [1] + list(range(3, total + 1))

    store.reassign_ids("termoquimica")
    assert [item["id"] for item in store.components()] == list(range(1, total))

    with pytest.raises(ValueError, match="Invalid table"):
        store.reassign_ids("propelente; DROP TABLE propelente")


def test_backup_once_before_first_write(legacy_env):
    original = (legacy_env / "database.db").read_bytes()

    store.insert_component({"Component": "Backup"})

    backup = legacy_env / "database.db.bak"
    assert backup.is_file()
    assert backup.read_bytes() == original
    assert store.backup_once() is None


def test_paths_are_env_driven(legacy_env, tmp_path, monkeypatch):
    assert paths.data_dir() == legacy_env
    assert paths.db_path() == legacy_env / "database.db"
    assert paths.mpldata_dir() == legacy_env / "mpl-data"

    monkeypatch.delenv("OPENRED_WORKDIR", raising=False)
    assert paths.workdir() is None
    assert paths.workdir_selected() is False

    selected = tmp_path / "workspace"
    paths.set_workdir(selected)
    assert Path(paths.workdir()) == selected.resolve()
    assert paths.workdir_selected() is True
    assert json.loads(paths.app_config_file().read_text(encoding="utf-8"))["workdir"] == str(selected.resolve())

    created = paths.ensure_workdir_dirs(selected)
    assert {Path(entry).name for entry in created} == {"Engines", "Nozzles", "Sketches", "Tests"}
    assert paths.ensure_workdir_dirs(selected) == []
    assert paths.default_workdir().endswith("OpenRED")
