"""Workspace service: working directory lifecycle and config.json persistence (G2/G3/G4/G11)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import paths
from ..mathutils import read_json, write_json_atomic
from ..rpc import E_ALREADY_EXISTS, E_NOT_FOUND, RpcError
from ..store import backup_once

_KINDS = {"Engines", "Nozzles", "Sketches", "Tests"}


def _require_workdir() -> Path:
    workdir = paths.workdir()
    if not workdir:
        raise RpcError(1001, "No working directory has been selected.")
    return Path(workdir)


def get(params: dict[str, Any], ctx) -> dict[str, Any]:
    workdir = paths.workdir()
    return {"workdir": workdir, "workdirSelected": bool(workdir)}


def ensure_workdir(params: dict[str, Any], ctx) -> dict[str, Any]:
    workdir = paths.workdir() or str(paths.default_workdir())
    paths.ensure_workdir_dirs(workdir)
    paths.set_workdir(workdir)
    backup_once()
    return {"workdir": workdir}


def set_dir(params: dict[str, Any], ctx) -> dict[str, Any]:
    raw = params.get("path")
    if not raw or not isinstance(raw, str):
        raise RpcError(-32602, "path is required", None)
    target = Path(raw)
    if not target.is_dir():
        raise RpcError(E_NOT_FOUND, f"Directory not found: {raw}", None)
    created = paths.ensure_workdir_dirs(target)
    paths.set_workdir(str(target))
    backup_once()
    config_path = target / "config.json"
    has_config = config_path.is_file()
    config = None
    if has_config:
        try:
            config = read_json(config_path)
        except (OSError, json.JSONDecodeError) as exc:
            raise RpcError(1003, f"Invalid configuration file: {config_path}", str(exc)) from exc
    return {
        "workdir": str(target),
        "created": created,
        "hasConfig": has_config,
        "config": config,
    }


def load_config(params: dict[str, Any], ctx) -> dict[str, Any]:
    workdir = _require_workdir()
    config_path = workdir / "config.json"
    if not config_path.is_file():
        return {"config": None, "hasConfig": False}
    try:
        config = read_json(config_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise RpcError(1003, f"Invalid configuration file: {config_path}", str(exc)) from exc
    return {"config": config, "hasConfig": True}


def save_config(params: dict[str, Any], ctx) -> dict[str, Any]:
    workdir = _require_workdir()
    config = params.get("config")
    if config is None or not isinstance(config, dict):
        raise RpcError(-32602, "config object is required", None)
    force = bool(params.get("force"))
    config_path = workdir / "config.json"
    if config_path.is_file() and not force:
        raise RpcError(
            E_ALREADY_EXISTS,
            "A configuration file already exists. Please select another directory.",
            {"path": str(config_path)},
        )
    write_json_atomic(config_path, config)
    backup_once()
    return {"path": str(config_path)}


def list_files(params: dict[str, Any], ctx) -> dict[str, Any]:
    workdir = _require_workdir()
    kind = params.get("kind")
    if kind not in _KINDS:
        raise RpcError(-32602, f"kind must be one of {sorted(_KINDS)}", None)
    folder = workdir / str(kind)
    folder.mkdir(parents=True, exist_ok=True)
    files = []
    for entry in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if entry.is_file():
            stat = entry.stat()
            files.append({"name": entry.name, "size": stat.st_size, "mtime": stat.st_mtime})
    return {"files": files}


METHODS = {
    "workspace.get": get,
    "workspace.ensure_workdir": ensure_workdir,
    "workspace.set_dir": set_dir,
    "workspace.load_config": load_config,
    "workspace.save_config": save_config,
    "workspace.list": list_files,
}
