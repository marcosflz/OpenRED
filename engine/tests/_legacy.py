"""Helpers to import the legacy (CustomTkinter) modules in-process.

The legacy code is the parity reference, so the parity tests import it directly
instead of copying fixtures. To make that possible without installing
CustomTkinter this module:

* installs a stub ``customtkinter`` module when the real one is not available;
* patches ``tkinter.messagebox.showinfo/showerror/showwarning`` to no-ops;
* puts ``legacy/`` on ``sys.path``;
* provides :func:`legacy_cwd`, a temporary directory holding a copy of
  ``legacy/database.db`` (the legacy modules resolve ``database.db`` from the
  current working directory).
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

LEGACY_DIR = Path(__file__).resolve().parents[2] / "legacy"
LEGACY_DB = LEGACY_DIR / "database.db"
CONFIG_JSON = LEGACY_DIR / "workingDirectory" / "config.json"

# Attributes used by ``legacy/imports.py`` and the modules it re-exports.
_CTK_ATTRIBUTES = (
    "CTk", "CTkFrame", "CTkEntry", "CTkButton", "CTkLabel", "CTkTextbox",
    "CTkOptionMenu", "CTkComboBox", "CTkCheckBox", "CTkSwitch", "CTkSlider",
    "CTkProgressBar", "CTkScrollableFrame", "CTkTabview", "CTkSegmentedButton",
    "CTkToplevel", "CTkImage", "CTkFont", "CTkCanvas", "StringVar",
    "BooleanVar", "DoubleVar", "IntVar", "END", "NORMAL",
    "DISABLED", "TOP", "BOTTOM", "LEFT", "RIGHT", "BOTH", "X", "Y",
    "set_appearance_mode", "set_default_color_theme", "set_widget_scaling",
    "set_window_scaling", "get_appearance_mode",
)

_installed = False
_legacy_cwd: Path | None = None


def _noop(*args: Any, **kwargs: Any) -> None:
    """Silent replacement for ``messagebox``/widget methods."""
    return None


class _DummyWidget:
    """Anything the legacy modules touch at import time, without a GUI."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def __getattr__(self, name: str) -> Any:
        return _noop


def _make_ctk_stub() -> types.ModuleType:
    module = types.ModuleType("customtkinter")
    for attribute in _CTK_ATTRIBUTES:
        setattr(module, attribute, _DummyWidget)

    def __getattr__(name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        return _DummyWidget

    module.__getattr__ = __getattr__
    return module


def _install_stubs() -> None:
    global _installed
    if _installed:
        return
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        sys.modules["customtkinter"] = _make_ctk_stub()

    import tkinter.messagebox as messagebox

    messagebox.showinfo = _noop
    messagebox.showerror = _noop
    messagebox.showwarning = _noop

    if str(LEGACY_DIR) not in sys.path:
        sys.path.insert(0, str(LEGACY_DIR))
    _installed = True


def legacy_cwd() -> Path:
    """Change to a temp dir containing a copy of ``legacy/database.db``."""
    global _legacy_cwd
    if _legacy_cwd is None:
        _legacy_cwd = Path(tempfile.mkdtemp(prefix="openred-legacy-"))
        shutil.copy2(LEGACY_DB, _legacy_cwd / "database.db")
    os.chdir(_legacy_cwd)
    return _legacy_cwd


def legacy_functions():
    """Import and return ``legacy/functions.py`` (with stubs installed).

    The legacy modules resolve ``database.db`` from the current working
    directory, so the CWD is switched to the temporary copy first.
    """
    _install_stubs()
    legacy_cwd()
    import functions  # noqa: PLC0415 - imported on purpose from legacy/

    return functions


def legacy_back_modules() -> tuple[Any, Any]:
    """Import and return ``legacy back_modules.back_0`` and ``back_1``.

    The legacy modules resolve ``database.db`` from the current working
    directory, so the CWD is switched to the temporary copy first.
    """
    _install_stubs()
    legacy_cwd()
    import back_modules.back_0 as back_0  # noqa: PLC0415
    import back_modules.back_1 as back_1  # noqa: PLC0415

    return back_0, back_1


class FakeTextbox:
    """Minimal stand-in for ``CTkTextbox`` that accumulates inserted strings."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def insert(self, index: str, text: str) -> None:
        self.messages.append(text)

    def see(self, index: str) -> None:
        pass

    def update_idletasks(self) -> None:
        pass
