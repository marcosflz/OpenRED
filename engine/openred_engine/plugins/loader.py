"""Dynamic plugin loader (headless reimplementation of ``functions.importLibraries``).

Differences from the legacy loader:

* the directory is resolved through :func:`openred_engine.paths.plugins_dir`
  (``OPENRED_RESOURCE_DIR``) instead of ``os.getcwd()``;
* modules are imported with a unique dotted name
  (``openred_engine.plugins.<library>.<module>``) instead of polluting
  ``sys.modules`` with bare file names;
* the legacy flat layout ``<resource>/plugins/<library>`` is still supported.

A plugin class is registered when it is defined in the module (not imported)
and exposes a ``nozzle_type`` attribute. ``SQUARE.py`` defines no such class,
so it is intentionally *not* registered (contract §3.5).
"""

from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
import threading
from pathlib import Path
from types import ModuleType

from openred_engine import paths

logger = logging.getLogger(__name__)

# library key used by ``plugins.reload``/``load_all`` -> folder name
LIBRARIES: dict[str, str] = {
    "grain": "GrainLibrary",
    "nozzle": "NozzleLibrary",
}

__all__ = ["LIBRARIES", "load_all", "load_library", "plugin_labels", "reload"]

_cache: dict[str, dict[str, type]] = {}
# scipy's lazy submodule loader deadlocks when two threads trigger a first import
# concurrently; plugin loading happens on request threads, so serialise it.
_LOAD_LOCK = threading.RLock()


def _module_name(library: str, stem: str) -> str:
    return f"openred_engine.plugins.{library}.{stem}"


def _forget_modules(library: str) -> None:
    directory = paths.plugins_dir(library)
    if directory.is_dir():
        for file in directory.glob("*.py"):
            sys.modules.pop(_module_name(library, file.stem), None)


def _load_file(library: str, file: Path) -> ModuleType | None:
    name = _module_name(library, file.stem)
    spec = importlib.util.spec_from_file_location(name, file)
    if spec is None or spec.loader is None:
        logger.warning("Cannot create an import spec for %s", file)
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001 - a broken user plugin must not kill the engine
        sys.modules.pop(name, None)
        logger.exception("Cannot import plugin module %s", file)
        return None
    return module


def load_library(name: str) -> dict[str, type]:
    """Load every plugin class of the ``name`` library (cached).

    Returns a ``{nozzle_type: class}`` mapping; ``{}`` when the folder does not
    exist.
    """
    cached = _cache.get(name)
    if cached is not None:
        return cached

    with _LOAD_LOCK:
        cached = _cache.get(name)
        if cached is not None:
            return cached
        classes: dict[str, type] = {}
        directory = paths.plugins_dir(name)
        if directory.is_dir():
            for file in sorted(directory.glob("*.py")):
                if file.name == "__init__.py":
                    continue
                module = _load_file(name, file)
                if module is None:
                    continue
                for _member, obj in inspect.getmembers(module, inspect.isclass):
                    if getattr(obj, "__module__", None) != module.__name__:
                        continue  # only classes defined in this module
                    if not hasattr(obj, "nozzle_type"):
                        continue
                    classes[obj.nozzle_type] = obj
        else:
            logger.warning("Plugin directory %s does not exist", directory)

        _cache[name] = classes
        return classes


def load_all() -> dict[str, dict[str, type]]:
    """Load the grain and nozzle libraries (``{"grain": {...}, "nozzle": {...}}``)."""
    return {key: load_library(library) for key, library in LIBRARIES.items()}


def reload() -> dict[str, dict[str, type]]:
    """Drop the cache (and loaded modules) and scan every library again."""
    for library in set(LIBRARIES.values()) | set(_cache):
        _forget_modules(library)
        _cache.pop(library, None)
    return load_all()


def plugin_labels(cls: type) -> dict:
    """Return the input labels of a plugin class (``{}`` when not provided)."""
    getter = getattr(cls, "get_input_labels", None)
    if not callable(getter):
        return {}
    labels = getter()
    return dict(labels) if labels else {}
