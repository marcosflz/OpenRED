"""Centralised path resolution for the OpenRED engine.

Every path is resolved from environment variables; the current working
directory is *never* used (the legacy application relied on the CWD for
``database.db``, ``temp_dir.txt`` and the plugin folders — a known defect).

Environment variables (see ``contracts/methods.md`` §1):

* ``OPENRED_DATA_DIR``     -> mutable user data (database, mpl cache, app config).
                              Falls back to ``%APPDATA%\\OpenRED``.
* ``OPENRED_RESOURCE_DIR`` -> read-only installation resources.
                              Falls back to the directory containing the
                              ``openred_engine`` package.
* ``OPENRED_WORKDIR``      -> user selected working directory. The last selected
                              directory is also remembered in
                              ``<data>/config/app.json``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Installed trees are read-only (Program Files): never try to write ``.pyc``.
sys.dont_write_bytecode = True

_APP_NAME = "OpenRED"
_WORKDIR_KEY = "workdir"

__all__ = [
    "app_config_file",
    "data_dir",
    "db_path",
    "default_workdir",
    "ensure_workdir_dirs",
    "mpldata_dir",
    "package_dir",
    "plugins_dir",
    "read_app_config",
    "resource_dir",
    "set_workdir",
    "workdir",
    "workdir_selected",
    "write_app_config",
]


def package_dir() -> Path:
    """Return the directory that contains the ``openred_engine`` package."""
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    """Return the read-only resource directory (``<install>/engine``).

    ``OPENRED_RESOURCE_DIR`` wins; otherwise the package directory is used and
    two levels are walked up (``<resource>/openred_engine/paths.py`` ->
    ``<resource>``).
    """
    raw = os.environ.get("OPENRED_RESOURCE_DIR")
    if raw:
        return Path(raw).expanduser()
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    """Return the mutable user-data directory, creating it when needed."""
    raw = os.environ.get("OPENRED_DATA_DIR")
    if raw:
        path = Path(raw).expanduser()
    else:
        if os.name == "nt" or os.environ.get("APPDATA"):
            base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        path = base / _APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    """Return the path of the SQLite database (``<data>/database.db``)."""
    return data_dir() / "database.db"


def mpldata_dir() -> Path:
    """Return (and create) the matplotlib cache directory."""
    path = data_dir() / "mpl-data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def plugin_search_dirs(library: str) -> tuple[Path, Path]:
    """Return the plugin directories checked for ``library``, in priority order.

    R3: both the new layout (``<resource>/openred_engine/plugins/<library>``)
    and a flat layout (``<resource>/plugins/<library>``) are supported.
    """
    return (
        resource_dir() / "openred_engine" / "plugins" / library,
        resource_dir() / "plugins" / library,
    )


def plugins_dir(library: str) -> Path:
    """Return the existing plugin directory for ``library`` (canonical if none)."""
    candidates = plugin_search_dirs(library)
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


def default_workdir() -> str:
    """Return the default working directory (``<Documents>/OpenRED``)."""
    return str(Path.home() / "Documents" / _APP_NAME)


def ensure_workdir_dirs(path: str | os.PathLike[str]) -> list[str]:
    """Create ``Engines/ Nozzles/ Sketches/ Tests/`` inside ``path``.

    Returns the list of directories created by this call.
    """
    base = Path(path)
    created: list[str] = []
    for name in ("Engines", "Nozzles", "Sketches", "Tests"):
        directory = base / name
        if not directory.is_dir():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory))
    return created


def app_config_file() -> Path:
    """Return the path of the engine application config (``<data>/config/app.json``)."""
    return data_dir() / "config" / "app.json"


def read_app_config() -> dict[str, Any]:
    """Read ``app.json``; return an empty dict when missing or corrupt."""
    file = app_config_file()
    try:
        with open(file, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_app_config(data: dict[str, Any]) -> Path:
    """Atomically write ``app.json`` (tmp + ``os.replace``)."""
    file = app_config_file()
    file.parent.mkdir(parents=True, exist_ok=True)
    tmp = file.with_name(file.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, file)
    return file


def workdir() -> str | None:
    """Return the selected working directory, or ``None``.

    ``OPENRED_WORKDIR`` is authoritative; the persisted value in ``app.json``
    only remembers the last used directory across sessions.
    """
    raw = os.environ.get("OPENRED_WORKDIR")
    if raw:
        return raw
    stored = read_app_config().get(_WORKDIR_KEY)
    if isinstance(stored, str) and stored:
        return stored
    return None


def set_workdir(path: str | os.PathLike[str]) -> str:
    """Set (and persist) the working directory; return the absolute path."""
    resolved = str(Path(path).expanduser().resolve())
    os.environ["OPENRED_WORKDIR"] = resolved
    config = read_app_config()
    config[_WORKDIR_KEY] = resolved
    write_app_config(config)
    return resolved


def workdir_selected() -> bool:
    """Return ``True`` when a working directory has been selected."""
    return workdir() is not None


# ``MPLCONFIGDIR`` must exist before matplotlib is imported (contract §1).
if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = str(mpldata_dir())
