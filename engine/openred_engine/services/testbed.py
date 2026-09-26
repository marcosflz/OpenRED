"""Test Bed service: ESP32 serial protocol, checklist, records and CSV (T4)."""

from __future__ import annotations

import csv
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .. import paths, store
from ..mathutils import getSerialValues, read_json
from ..rpc import E_NO_SERIAL, E_NOT_FOUND, E_PARAMS, RpcError
from ..serial_transport import MockTransport, SerialMonitor, SerialTransport, Transport, list_ports


class TestbedState:
    def __init__(self) -> None:
        self.transport: Transport | None = None
        self.monitor: SerialMonitor | None = None
        self.connected = False
        self.wifi_ready = False
        self.recording = False
        self.checklist_enabled = False
        self.checklist: list[dict[str, Any]] = []
        self.checklist_title = "TEST CHECKLIST"
        self.records: list[tuple[float, float, float]] = []
        self.pending_lines: list[str] = []
        self.run_ready = False
        self.live_mock = False
        self.last_processed_line = ""
        self.file_path: str | None = None
        self.test_file: str | None = None
        self.nozzle_name: str | None = None
        self.max_thrust = 0.0
        self.max_temp = 0.0
        self.leds = {"serial": "off", "wifi": "off"}
        self.ports: list[dict[str, str]] = []
        self._ports_thread: threading.Thread | None = None
        self._ports_stop = threading.Event()
        self._lock = threading.RLock()

    def snapshot(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "wifiReady": self.wifi_ready,
            "recording": self.recording,
            "checklistComplete": bool(self.checklist) and all(item["done"] for item in self.checklist),
            "checklistEnabled": self.checklist_enabled,
            "leds": dict(self.leds),
            "testFile": self.test_file,
            "nozzle": self.nozzle_name,
            "maxThrust": self.max_thrust,
            "maxTemp": self.max_temp,
            "records": len(self.records),
        }


_state = TestbedState()
_mock_enabled = False


def _port_strings() -> list[str]:
    current = list_ports()
    if current:
        return [f"{port['device']} - {port['description']}" for port in current]
    return ["No COM ports found"]


def _emit_state(ctx=None, notify=None) -> None:
    payload = _state.snapshot()
    if notify:
        notify("state", **payload)
    if ctx is not None:
        ctx.notify("state", **payload)


# ---------------------------------------------------------------------------
# Records / CSV
# ---------------------------------------------------------------------------
def _save_record(record: tuple[float, float, float]) -> None:
    if not _state.file_path:
        return
    with open(_state.file_path, "a", newline="") as csvfile:
        csv.writer(csvfile).writerow(record)


def _reset_records() -> None:
    _state.records = []


def _handle_values_line(line: str, notify) -> None:
    """Legacy on_textbox_change semantics: parse, dedupe against all records, append CSV."""
    if not _state.recording or line == _state.last_processed_line:
        return
    result = getSerialValues(line)
    if not result:
        return
    record = tuple(float(value) for value in result)
    if any(record == existing for existing in _state.records):
        return
    _state.records.append(record)  # type: ignore[arg-type]
    _save_record(record)  # type: ignore[arg-type]
    notify("record", t=record[0], F=record[1], T=record[2], index=len(_state.records))


def _process_line(line: str, ctx, notify) -> None:
    with _state._lock:
        if "TEST-BENCH CONNECTED" in line:
            _state.wifi_ready = False
            _state.leds["wifi"] = "green"
            _write_command("WIFI_GREEN")
            _state.checklist_enabled = True
        elif "SERIAL STARTED" in line:
            _state.leds["serial"] = "green"
            _write_command("SERIAL_GREEN")
        elif "RESET" in line:
            _state.wifi_ready = True
        elif "ABORT" in line:
            notify("log", level="warning", message="ABORT received from test bench")
            abort(params={}, ctx=ctx)
        _emit_state(ctx=ctx, notify=notify)
        notify("serial_line", line=line)
        # CI/replay mode: value lines are buffered until `testbed.run` creates the CSV;
        # live emission is only enabled for the interactive demo (`demo: true`).
        if _mock_enabled and not _state.run_ready and getSerialValues(line):
            _state.pending_lines.append(line)
            if _state.live_mock and _state.recording:
                _handle_values_line(line, notify)
            return
        _handle_values_line(line, notify)


def _monitor_line(line: str, ctx, notify) -> None:
    try:
        _process_line(line, ctx, notify)
    except Exception as exc:  # noqa: BLE001 - monitor thread must survive
        notify("log", level="error", message=f"Serial line handling failed: {exc}")


def _write_command(command: str) -> None:
    if _state.transport is not None and _state.transport.connected:
        _state.transport.write_line(command)


def _make_transport() -> Transport:
    return MockTransport() if _mock_enabled else SerialTransport()


# ---------------------------------------------------------------------------
# Methods
# ---------------------------------------------------------------------------
def ports(params: dict[str, Any], ctx) -> dict[str, Any]:
    _state.ports = list_ports()
    return {"ports": [{"device": p["device"], "description": p["description"]} for p in _state.ports]}


def monitor_ports(params: dict[str, Any], ctx) -> dict[str, Any]:
    enabled = bool(params.get("enabled"))
    if not enabled:
        _state._ports_stop.set()
        return {"ok": True}
    if _state._ports_thread and _state._ports_thread.is_alive():
        return {"ok": True}
    _state._ports_stop.clear()

    def loop() -> None:
        previous: list[str] | None = None
        while not _state._ports_stop.is_set():
            current = _port_strings()
            if current != previous:
                previous = current
                ctx.notify("ports", ports=current)
            time.sleep(1)

    _state._ports_thread = threading.Thread(target=loop, daemon=True)
    _state._ports_thread.start()
    return {"ok": True}


def run(params: dict[str, Any], ctx) -> dict[str, Any]:
    raw = params.get("nozzleFile")
    if not raw:
        raise RpcError(E_PARAMS, "nozzleFile is required", None)
    workdir = paths.workdir()
    if not workdir:
        raise RpcError(1001, "No working directory has been selected.", None)
    nozzle_path = Path(str(raw))
    if not nozzle_path.is_file() and paths.workdir():
        candidate = Path(workdir) / "Nozzles" / nozzle_path.name
        nozzle_path = candidate if candidate.is_file() else nozzle_path
    if not nozzle_path.is_file():
        raise RpcError(E_NOT_FOUND, f"Nozzle file not found: {raw}", None)
    try:
        nozzle_data = read_json(nozzle_path)
        engine_name = nozzle_data["Inputs"]["EngineConfig"]
        engine_path = Path(workdir) / "Engines" / engine_name
        engine_data = read_json(engine_path)
        max_thrust = float(nozzle_data["calculatedResults"]["Med. Thrust (kg)"])
        propellant = engine_data["inputs"]["Propellant"]
        values = store.propellant_value("T_ad", propellant)
        max_temp = float(values[0])
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        raise RpcError(1003, "Invalid file.", str(exc)) from exc

    nozzle_name = nozzle_path.stem
    stamp = datetime.now().strftime("%H.%M.%S-%d.%m.%y")
    tests_folder = Path(workdir) / "Tests"
    tests_folder.mkdir(parents=True, exist_ok=True)
    csv_path = tests_folder / f"{nozzle_name}-{stamp}.csv"
    with open(csv_path, "w", newline="") as file:
        # The reference tests CSV (legacy/workingDirectory/Tests/*.csv) uses CRLF in the
        # header too; the current legacy code writes LF, a delta documented in T4-7.
        file.write("t(s),F(kg),T(K)\r\n")

    if _mock_enabled and _state.monitor is not None:
        # Deterministic replay: stop the scripted reader and replay the full script below.
        _state.monitor.stop()

    with _state._lock:
        _state.max_thrust = max_thrust
        _state.max_temp = max_temp
        _state.file_path = str(csv_path)
        _state.test_file = str(csv_path)
        _state.nozzle_name = nozzle_name
        _state.recording = False
        _reset_records()
        _state.last_processed_line = ""
        buffered = list(_state.pending_lines)
        _state.pending_lines.clear()
        _state.run_ready = True
        replay: list[str] = []
        if _mock_enabled:
            # CI/replay: the scripted transport is the test bench, start recording now.
            _state.recording = True
            transport = _state.transport
            if isinstance(transport, MockTransport) and transport.script:
                replay = list(transport.script)
            else:
                replay = buffered
        # Replay under the same lock so no other thread can interleave CSV rows.
        for line in replay:
            _handle_values_line(line, ctx.notify)
    _emit_state(ctx=ctx)
    if _mock_enabled:
        ctx.notify("job_done", job="testbed", status="ok")
    return {
        "testFile": str(csv_path),
        "nozzle": nozzle_name,
        "engine": engine_name,
        "maxThrust": max_thrust,
        "maxTemp": max_temp,
    }


def connect_com(params: dict[str, Any], ctx) -> dict[str, Any]:
    port = str(params.get("port") or "")
    if not port:
        raise RpcError(E_PARAMS, "port is required", None)
    port = port.split(" - ")[0].strip()
    disconnect(params={}, ctx=ctx, silent=True)
    transport = _make_transport()
    try:
        transport.open(port, baudrate=115200, timeout=1.0)
        transport.write_line("RESET")
    except Exception as exc:  # noqa: BLE001 - pyserial raises several types
        raise RpcError(E_NO_SERIAL, f"Could not connect to {port}: {exc}", None) from exc
    with _state._lock:
        _state.transport = transport
        _state.connected = True
        _state.recording = False
        _state.transport = transport
    monitor = SerialMonitor(transport, lambda line: _monitor_line(line, ctx, ctx.notify))
    monitor.start()
    _state.monitor = monitor
    _emit_state(ctx=ctx)
    return {"connected": True, "port": port}


def disconnect(params: dict[str, Any], ctx=None, silent: bool = False) -> dict[str, Any]:
    with _state._lock:
        transport = _state.transport
        monitor = _state.monitor
        _state.monitor = None
    if monitor is not None:
        monitor.stop()
    if transport is not None and transport.connected:
        try:
            transport.write_line("RESET")
            transport.write_line("SERIAL_BLUE")
            transport.write_line("WIFI_BLUE")
        except Exception:  # noqa: BLE001
            pass
        transport.close()
    with _state._lock:
        _state.transport = None
        _state.connected = False
        _state.recording = False
        _state.wifi_ready = False
        _state.checklist_enabled = False
        _state.leds = {"serial": "off", "wifi": "off"}
        _state.run_ready = False
        _state.pending_lines.clear()
    if ctx is not None:
        _emit_state(ctx=ctx)
    return {"connected": False}


def connect_wifi(params: dict[str, Any], ctx) -> dict[str, Any]:
    ssid = str(params.get("ssid") or "")
    password = str(params.get("password") or "")
    if not ssid or not password:
        raise RpcError(E_PARAMS, "ssid and password are required", None)
    if _state.transport is None or not _state.transport.connected:
        raise RpcError(E_NO_SERIAL, "La conexión serial no está abierta.", None)
    _state.transport.write_line(f"CONNECT {ssid} {password}")
    return {"sent": True}


def abort(params: dict[str, Any], ctx) -> dict[str, Any]:
    if _state.transport is not None and _state.transport.connected:
        try:
            _state.transport.write_line("ABORT")
            _state.transport.write_line("RESET")
        except Exception as exc:  # noqa: BLE001
            raise RpcError(E_NO_SERIAL, f"Failed to send ABORT: {exc}", None) from exc
    disconnect(params={}, ctx=ctx, silent=True)
    if ctx is not None:
        ctx.notify("log", level="info", message="Test aborted. Reset command sent.")
    return {"ok": True}


def checklist_load(params: dict[str, Any], ctx) -> dict[str, Any]:
    workdir = paths.workdir()
    items: list[str] = []
    if workdir:
        try:
            data = read_json(Path(workdir) / "checklist.json")
            items = [str(item) for item in data.get("Checklist", [])]
        except (OSError, ValueError):
            items = []
    with _state._lock:
        _state.checklist = [{"text": text, "done": False} for text in items]
        _state.checklist_title = "TEST CHECKLIST"
    return {"title": _state.checklist_title, "items": list(_state.checklist)}


def checklist_toggle(params: dict[str, Any], ctx) -> dict[str, Any]:
    index = int(params.get("index", -1))
    with _state._lock:
        if index < 0 or index >= len(_state.checklist):
            raise RpcError(E_PARAMS, f"Invalid checklist index: {index}", None)
        _state.checklist[index]["done"] = bool(params.get("done", not _state.checklist[index]["done"]))
        complete = bool(_state.checklist) and all(item["done"] for item in _state.checklist)
    if complete:
        _write_command("SWITCH START-RECORDING-LED")
        with _state._lock:
            _state.recording = True
            _reset_records()
    _emit_state(ctx=ctx)
    return {"items": list(_state.checklist), "complete": complete}


def state(params: dict[str, Any], ctx) -> dict[str, Any]:
    return _state.snapshot()


def mock(params: dict[str, Any], ctx) -> dict[str, Any]:
    global _mock_enabled
    _mock_enabled = bool(params.get("enabled"))
    script = params.get("script")
    demo = bool(params.get("demo"))
    if _mock_enabled and script:
        transport = MockTransport([str(line) for line in script])
        transport.open("MOCK")
        with _state._lock:
            _state.transport = transport
            _state.connected = True
            _state.run_ready = False
            _state.pending_lines.clear()
            _state.last_processed_line = ""
            # CI replay buffers until `testbed.run`; the interactive demo streams live.
            _state.recording = True
            _state.live_mock = demo
        _state.monitor = SerialMonitor(transport, lambda line: _monitor_line(line, ctx, ctx.notify))
        _state.monitor.start()
        _emit_state(ctx=ctx)
    elif not _mock_enabled:
        disconnect(params={}, ctx=ctx, silent=True)
        with _state._lock:
            _state.recording = False
            _state.live_mock = False
    return {"ok": True, "enabled": _mock_enabled}


METHODS = {
    "testbed.list_ports": ports,
    "testbed.monitor_ports": monitor_ports,
    "testbed.run": run,
    "testbed.connect_com": connect_com,
    "testbed.disconnect": disconnect,
    "testbed.connect_wifi": connect_wifi,
    "testbed.abort": abort,
    "testbed.checklist.load": checklist_load,
    "testbed.checklist.toggle": checklist_toggle,
    "testbed.state": state,
    "testbed.mock": mock,
}
