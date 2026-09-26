"""Application-level methods (app.ping / app.info / app.version)."""

from __future__ import annotations

import platform
import sys
from typing import Any

from .. import __version__, paths


def _base() -> dict[str, Any]:
    workdir = paths.workdir()
    return {
        "version": __version__,
        "dataDir": str(paths.data_dir()),
        "resourceDir": str(paths.resource_dir()),
        "workdir": workdir,
        "workdirSelected": bool(workdir),
    }


def ping(params: dict[str, Any], ctx) -> dict[str, Any]:
    return {
        **_base(),
        "pid": __import__("os").getpid(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }


def info(params: dict[str, Any], ctx) -> dict[str, Any]:
    return _base()


METHODS = {
    "app.ping": ping,
    "app.info": info,
}
