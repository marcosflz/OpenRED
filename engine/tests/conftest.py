"""Shared fixtures for the engine test-suite.

The environment is configured *at import time*, before any test module imports
``openred_engine`` (``store.initialize_database()`` runs at import time and must
not touch the developer's real ``%APPDATA%`` directory).
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ENGINE_DIR.parent
LEGACY_DB = REPO_ROOT / "legacy" / "database.db"

os.environ["MPLBACKEND"] = "Agg"
os.environ["OPENRED_RESOURCE_DIR"] = str(ENGINE_DIR)
os.environ.pop("OPENRED_WORKDIR", None)

_SESSION_DATA = Path(tempfile.mkdtemp(prefix="openred-engine-tests-"))
shutil.copy2(LEGACY_DB, _SESSION_DATA / "database.db")
os.environ["OPENRED_DATA_DIR"] = str(_SESSION_DATA)

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))


@pytest.fixture(scope="session", autouse=True)
def _cleanup_session_data():
    yield
    shutil.rmtree(_SESSION_DATA, ignore_errors=True)


@pytest.fixture
def legacy_env(tmp_path, monkeypatch):
    """Per-test data dir (copy of ``legacy/database.db``) plus clean module state.

    Yields the fresh data directory. Resets the per-process state of ``store``
    (backup flag) and the plugin loader cache, and restores the CWD afterwards
    (parity tests chdir into the legacy temp directory).
    """
    from openred_engine import store
    from openred_engine.plugins import loader

    data = tmp_path / "data"
    data.mkdir()
    shutil.copy2(LEGACY_DB, data / "database.db")

    monkeypatch.setenv("OPENRED_DATA_DIR", str(data))
    monkeypatch.setenv("OPENRED_RESOURCE_DIR", str(ENGINE_DIR))
    monkeypatch.delenv("OPENRED_WORKDIR", raising=False)

    store._backup_done = False
    loader._cache.clear()

    original_cwd = os.getcwd()
    yield data

    os.chdir(original_cwd)
    store._backup_done = False
    loader._cache.clear()
