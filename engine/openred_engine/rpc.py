"""JSON-RPC 2.0-ish dispatcher over stdio (one JSON document per line).

Requests:  {"id": 1, "method": "ns.method", "params": {...}}
Responses: {"id": 1, "result": {...}} | {"id": 1, "error": {code, message, detail}}
Events:    {"method": "event", "params": {"name": "<event>", ...}}

The transport is a newline-delimited JSON stream. stdout carries protocol messages
only; diagnostics go to stderr (see logging_setup).
"""

from __future__ import annotations

import json
import threading
import traceback
from collections.abc import Callable
from typing import Any

from . import __version__

# ---------------------------------------------------------------------------
# Error codes (see contracts/methods.md §2)
# ---------------------------------------------------------------------------
E_PARSE = -32700
E_METHOD = -32601
E_PARAMS = -32602
E_NO_WORKDIR = 1001
E_NOT_FOUND = 1002
E_INVALID_FILE = 1003
E_ALREADY_EXISTS = 1004
E_CANCELLED = 1005
E_NO_CONVERGENCE = 1006
E_UNSUPPORTED = 1007
E_NO_SERIAL = 1008
E_INTERNAL = 2000


class RpcError(Exception):
    """Domain error that maps to a JSON-RPC error object."""

    def __init__(self, code: int, message: str, detail: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail


class Cancelled(RpcError):
    def __init__(self, detail: Any = None):
        super().__init__(E_CANCELLED, "Operation cancelled", detail)


class RequestContext:
    """Per-request context handed to handlers: identity, cancellation and events."""

    def __init__(self, request_id: Any, server: RpcServer):
        self.id = request_id
        self._server = server
        self._cancelled = threading.Event()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    def cancel(self) -> None:
        self._cancelled.set()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise Cancelled()

    def check_cancelled(self) -> bool:
        return self.cancelled

    def notify(self, name: str, **payload: Any) -> None:
        self._server.notify(name, **payload)


Handler = Callable[[dict[str, Any], RequestContext], Any]


class RpcServer:
    def __init__(self, stdin, stdout, dispatcher: Callable[[], dict[str, Handler]] | dict[str, Handler]):
        self._stdin = stdin
        self._stdout = stdout
        self._write_lock = threading.Lock()
        self._dispatcher = dispatcher
        self._dispatcher_resolved: dict[str, Handler] | None = None
        self._contexts: dict[Any, RequestContext] = {}
        self._contexts_lock = threading.Lock()
        self._threads: list[threading.Thread] = []
        self._stop = threading.Event()

    # -- plumbing ----------------------------------------------------------
    def _resolve_dispatcher(self) -> dict[str, Handler]:
        if self._dispatcher_resolved is None:
            self._dispatcher_resolved = self._dispatcher() if callable(self._dispatcher) else self._dispatcher
        return self._dispatcher_resolved

    def _write(self, message: dict[str, Any]) -> None:
        line = json.dumps(message, ensure_ascii=False, allow_nan=False)
        with self._write_lock:
            self._stdout.write(line + "\n")
            self._stdout.flush()

    def notify(self, name: str, **payload: Any) -> None:
        self._write({"method": "event", "params": {"name": name, **payload}})

    def respond(self, request_id: Any, result: Any) -> None:
        try:
            self._write({"id": request_id, "result": result})
        except ValueError as exc:  # NaN/Infinity in payload: report instead of crashing
            self._write(
                {
                    "id": request_id,
                    "error": {
                        "code": E_INTERNAL,
                        "message": f"Non serializable result: {exc}",
                        "detail": None,
                    },
                }
            )

    def respond_error(self, request_id: Any, error: RpcError) -> None:
        self._write(
            {
                "id": request_id,
                "error": {"code": error.code, "message": error.message, "detail": error.detail},
            }
        )

    # -- lifecycle ---------------------------------------------------------
    def serve_forever(self) -> None:
        self.notify("ready", version=__version__, pid=_pid())
        while not self._stop.is_set():
            line = self._stdin.readline()
            if not line:  # EOF: parent closed the pipe
                break
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                self._write(
                    {"id": None, "error": {"code": E_PARSE, "message": "Invalid JSON", "detail": str(exc)}}
                )
                continue
            self._handle(message)
        # Drain workers (bounded).
        for thread in list(self._threads):
            thread.join(timeout=2.0)

    def _handle(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params") or {}
        if not isinstance(method, str):
            self._write({"id": request_id, "error": {"code": E_PARSE, "message": "Missing method", "detail": None}})
            return
        if method == "request.cancel":
            target = params.get("id")
            with self._contexts_lock:
                ctx = self._contexts.get(target)
            if ctx is not None:
                ctx.cancel()
                self.respond(request_id, {"cancelled": True})
            else:
                self.respond(request_id, {"cancelled": False})
            return
        if method == "app.shutdown":
            self.respond(request_id, {"ok": True})
            self.notify("exiting")
            self._stop.set()
            return

        handler = self._resolve_dispatcher().get(method)
        if handler is None:
            self._write(
                {
                    "id": request_id,
                    "error": {"code": E_METHOD, "message": f"Unknown method: {method}", "detail": None},
                }
            )
            return
        if request_id is None:
            return  # notifications other than cancel are ignored
        ctx = RequestContext(request_id, self)
        with self._contexts_lock:
            self._contexts[request_id] = ctx
        thread = threading.Thread(target=self._run, args=(handler, method, params, ctx), daemon=True)
        self._threads.append(thread)
        thread.start()

    def _run(self, handler: Handler, method: str, params: Any, ctx: RequestContext) -> None:
        try:
            if not isinstance(params, dict):
                raise RpcError(E_PARAMS, "params must be an object", None)
            result = handler(params, ctx)
            self.respond(ctx.id, result)
        except Cancelled as exc:
            self.respond_error(ctx.id, exc)
            self.notify("job_done", job=method, status="cancelled")
        except RpcError as exc:
            self.respond_error(ctx.id, exc)
        except Exception as exc:  # noqa: BLE001 - boundary of the sidecar
            self.respond_error(
                ctx.id,
                RpcError(E_INTERNAL, f"{type(exc).__name__}: {exc}", traceback.format_exc(limit=8)),
            )
        finally:
            with self._contexts_lock:
                self._contexts.pop(ctx.id, None)


def _pid() -> int:
    import os

    return os.getpid()
