"""Plugin discovery methods (grain geometries and nozzle solvers)."""

from __future__ import annotations

from typing import Any

from ..plugins import loader
from ..rpc import E_PARAMS, RpcError


def _describe(library: str) -> dict[str, Any]:
    classes = loader.load_library(library)
    plugins = {}
    for nozzle_type, cls in classes.items():
        labels: dict[str, str] = {}
        if hasattr(cls, "get_input_labels"):
            labels = dict(cls.get_input_labels())
        plugins[nozzle_type] = {"labels": labels, "class": cls.__name__}
    return plugins


def list_plugins(params: dict[str, Any], ctx) -> dict[str, Any]:
    library = str(params.get("library") or "")
    if library not in {"GrainLibrary", "NozzleLibrary"}:
        raise RpcError(E_PARAMS, "library must be 'GrainLibrary' or 'NozzleLibrary'", None)
    return {"plugins": _describe(library)}


def reload_plugins(params: dict[str, Any], ctx) -> dict[str, Any]:
    loader.reload()
    return {
        "grain": list(_describe("GrainLibrary")),
        "nozzle": list(_describe("NozzleLibrary")),
    }


METHODS = {
    "plugins.list": list_plugins,
    "plugins.reload": reload_plugins,
}
