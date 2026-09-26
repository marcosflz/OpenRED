"""Service registry: every JSON-RPC method exposed by the engine."""

from __future__ import annotations

import threading

from ..rpc import Handler
from . import adiabatic as _adiabatic
from . import app as _app
from . import db as _db
from . import plugins as _plugins
from . import workspace as _workspace


def _lazy(module_name: str, methods_name: str = "METHODS"):
    """Import heavy services lazily so a broken module does not kill the sidecar."""

    def loader() -> dict[str, Handler]:
        from importlib import import_module

        module = import_module(f".{module_name}", __package__)
        return getattr(module, methods_name)

    return loader


def build_dispatcher() -> dict[str, Handler]:
    dispatcher: dict[str, Handler] = {}
    for module in (_app, _workspace, _db, _adiabatic, _plugins):
        dispatcher.update(module.METHODS)
    # Heavy modules (matplotlib/scipy/plugin loading) are resolved on demand.
    for _name, module_name in (
        ("engine.", "engine"),
        ("nozzle.", "nozzle"),
        ("cad.", "cad"),
        ("testbed.", "testbed"),
    ):
        loader = _lazy(module_name)
        for method in _method_names(module_name):
            dispatcher[method] = _make_proxy(loader, method)
    return dispatcher


def _method_names(module_name: str) -> list[str]:
    # Static method lists keep the dispatcher importable even if a service module is
    # temporarily broken (e.g. during incremental development).
    return _KNOWN_METHODS[module_name]


_RESOLVE_LOCK = threading.RLock()


def _make_proxy(loader, method: str) -> Handler:
    def handler(params, ctx):
        with _RESOLVE_LOCK:
            service = loader()[method]
        return service(params, ctx)

    return handler


_KNOWN_METHODS = {
    "engine": [
        "engine.geometry",
        "engine.calculate",
        "engine.save",
        "engine.load",
        "engine.list",
    ],
    "nozzle": [
        "nozzle.load_engine",
        "nozzle.calculate",
        "nozzle.op_point",
        "nozzle.save",
        "nozzle.load",
        "nozzle.list",
    ],
    "cad": [
        "cad.load_nozzle",
        "cad.views",
        "cad.export",
    ],
    "testbed": [
        "testbed.list_ports",
        "testbed.monitor_ports",
        "testbed.run",
        "testbed.connect_com",
        "testbed.disconnect",
        "testbed.connect_wifi",
        "testbed.abort",
        "testbed.checklist.load",
        "testbed.checklist.toggle",
        "testbed.state",
        "testbed.mock",
    ],
}
