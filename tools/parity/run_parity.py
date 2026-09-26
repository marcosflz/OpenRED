#!/usr/bin/env python3
"""Parity harness: run the openred_engine sidecar and compare against golden fixtures.

Usage:
    uv run python tools/parity/run_parity.py
    uv run python tools/parity/run_parity.py --engine "C:\\path\\to\\python.exe -m openred_engine"
    uv run python tools/parity/run_parity.py --only t0,t2 --report parity-report.json

Behaviour
---------
* Launches the engine (default: the ``engine/.venv`` interpreter running
  ``python -s -X utf8 -m openred_engine`` with a temporary
  ``OPENRED_DATA_DIR`` / ``OPENRED_RESOURCE_DIR`` / ``OPENRED_WORKDIR`` and a
  workspace seeded from ``contracts/fixtures/inputs``).
* Replays the same RPC calls recorded in the fixtures (``rpc`` objects) and
  compares results against the fixture references:
  - numbers: ``numpy.allclose(rtol=1e-9, atol=0)``
  - CSV/text: exact after normalizing line endings (CRLF -> LF)
  - console lines: exact sequence
  - JSON structure: key set exact (key order is irrelevant)
* Writes ``parity-report.json`` and exits 0 (all pass), 1 (parity failures) or
  2 (the sidecar could not be started - no cryptic traceback).

Documented normalizations
-------------------------
* ``DP. Thrust (kg)1`` is a legacy typo exclusive to the CONE-LN plugin; the
  TOPN-BN fixtures use the corrected label and ``nozzle.save`` normalizes it
  (R10/T2-9).
* Key order in JSON/CSV is not compared; only key sets and values.
* CSV comparison normalizes CRLF to LF (both legacy and clone write CRLF).
* ``engine.calculate`` has no ``stop_reason`` field in the contract: it is
  derived from the final console line (same mapping as gen_fixtures.py).
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
RTOL = 1e-9
ATOL = 0.0


class EngineError(RuntimeError):
    """Raised when the sidecar cannot be started or dies."""


class RpcError(RuntimeError):
    def __init__(self, error: dict) -> None:
        super().__init__(f"engine error {error.get('code')}: {error.get('message')}")
        self.error = error


def default_engine_cmd() -> list[str]:
    venv = REPO_ROOT / "engine" / ".venv"
    candidates = [venv / "Scripts" / "python.exe", venv / "bin" / "python"]
    python = next((path for path in candidates if path.is_file()), Path(sys.executable))
    return [str(python), "-s", "-X", "utf8", "-m", "openred_engine"]


class EngineClient:
    """Minimal JSONL JSON-RPC client with an event queue."""

    def __init__(self, cmd: list[str], cwd: Path, env: dict, timeout: float) -> None:
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.timeout = timeout
        self.process: subprocess.Popen | None = None
        self._responses: dict[str, dict] = {}
        self._events: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self._next_id = 1
        self._stderr: list[str] = []
        self._dead = threading.Event()
        self._exit_code: int | None = None

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        try:
            self.process = subprocess.Popen(
                self.cmd,
                cwd=str(self.cwd),
                env=self.env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except FileNotFoundError as exc:
            raise EngineError(f"engine command not found: {self.cmd[0]} ({exc})") from None
        threading.Thread(target=self._read_stdout, name="engine-stdout", daemon=True).start()
        threading.Thread(target=self._read_stderr, name="engine-stderr", daemon=True).start()

    def _read_stdout(self) -> None:
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self._stderr.append(f"non-JSON stdout line: {line[:200]}")
                continue
            if message.get("method") == "event":
                self._events.put(message)
            elif "id" in message:
                with self._lock:
                    self._responses[str(message["id"])] = message
            else:
                self._stderr.append(f"unexpected message: {line[:200]}")
        self._exit_code = self.process.poll() if self.process else None
        self._dead.set()

    def _read_stderr(self) -> None:
        assert self.process and self.process.stderr
        for line in self.process.stderr:
            self._stderr.append(line.rstrip())
            if len(self._stderr) > 400:
                del self._stderr[:200]

    def wait_ready(self, timeout: float) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._dead.is_set() and self._events.empty():
                raise EngineError(self._diagnosis("engine exited before the ready event"))
            try:
                event = self._events.get(timeout=0.1)
            except queue.Empty:
                continue
            if event.get("params", {}).get("name") == "ready":
                return event["params"]
            self._events.put(event)
            time.sleep(0.01)
        raise EngineError(self._diagnosis(f"no ready event within {timeout:.0f}s"))

    def _diagnosis(self, reason: str) -> str:
        tail = "\n".join(self._stderr[-25:]) or "(empty stderr)"
        return (
            f"{reason}.\n"
            f"  command: {' '.join(self.cmd)}\n"
            f"  cwd: {self.cwd}\n"
            f"  exit code: {self._exit_code}\n"
            f"  stderr tail:\n{tail}"
        )

    def stop(self) -> None:
        if not self.process:
            return
        if self.process.poll() is None:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
            except OSError:
                pass
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)

    # -- rpc ---------------------------------------------------------------
    def call(self, method: str, params: dict, timeout: float | None = None) -> dict:
        if not self.process or self.process.poll() is not None:
            raise EngineError(self._diagnosis("engine is not running"))
        with self._lock:
            request_id = self._next_id
            self._next_id += 1
        payload = json.dumps({"id": request_id, "method": method, "params": params}, ensure_ascii=False)
        try:
            assert self.process.stdin
            self.process.stdin.write(payload + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise EngineError(self._diagnosis(f"broken stdin while calling {method}: {exc}")) from None
        limit = timeout or self.timeout
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            with self._lock:
                response = self._responses.pop(str(request_id), None)
            if response is not None:
                if "error" in response:
                    raise RpcError(response["error"])
                return response.get("result", {})
            if self._dead.is_set() and self.process.poll() is not None:
                raise EngineError(self._diagnosis(f"engine exited during {method}"))
            time.sleep(0.02)
        raise EngineError(self._diagnosis(f"timeout ({limit:.0f}s) waiting for {method}"))

    def drain_events(self) -> list[dict]:
        events = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except queue.Empty:
                return events

    def queued_events(self) -> int:
        return self._events.qsize()

    def wait_event(self, name: str, timeout: float, job: str | None = None) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                event = self._events.get(timeout=0.1)
            except queue.Empty:
                if self._dead.is_set() and self.process and self.process.poll() is not None:
                    raise EngineError(self._diagnosis(f"engine exited while waiting for event {name}")) from None
                continue
            params = event.get("params", {})
            if params.get("name") == name and (job is None or params.get("job") == job):
                return event
        raise EngineError(self._diagnosis(f"timeout waiting for event {name}"))


# --------------------------------------------------------------------------- #
# comparison helpers
# --------------------------------------------------------------------------- #
def compare_values(
    expected, actual, path: str, problems: list[str], *, rtol: float = RTOL, allow_extra: bool = False
) -> None:
    """Recursive comparison: numbers allclose, lists elementwise, dicts by key set, others exact.

    ``allow_extra=True`` permits additional keys in ``actual`` (forward-compatible
    result extensions); expected keys are still required.
    """
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            problems.append(f"{path}: expected object, got {type(actual).__name__}")
            return
        for key in sorted(set(expected) - set(actual)):
            problems.append(f"{path}.{key}: missing in engine result")
        if not allow_extra:
            for key in sorted(set(actual) - set(expected)):
                problems.append(f"{path}.{key}: unexpected in engine result")
        for key in sorted(set(expected) & set(actual)):
            compare_values(expected[key], actual[key], f"{path}.{key}", problems, rtol=rtol, allow_extra=allow_extra)
        return
    if isinstance(expected, list):
        if not isinstance(actual, list):
            problems.append(f"{path}: expected array, got {type(actual).__name__}")
            return
        if len(expected) != len(actual):
            problems.append(f"{path}: length {len(expected)} expected, got {len(actual)}")
            return
        for index, (exp, act) in enumerate(zip(expected, actual)):
            compare_values(exp, act, f"{path}[{index}]", problems, rtol=rtol, allow_extra=allow_extra)
        return
    if isinstance(expected, bool) or isinstance(actual, bool):
        if expected != actual:
            problems.append(f"{path}: expected {expected!r}, got {actual!r}")
        return
    if isinstance(expected, int | float) and isinstance(actual, int | float):
        if not np.allclose(
            np.asarray(expected, dtype=float), np.asarray(actual, dtype=float),
            rtol=rtol, atol=ATOL, equal_nan=True,
        ):
            problems.append(f"{path}: expected {expected!r}, got {actual!r}")
        return
    if expected != actual:
        problems.append(f"{path}: expected {expected!r}, got {actual!r}")


def compare_error(expected: dict, actual: dict, path: str, problems: list[str]) -> None:
    """Error envelopes: code and message are normative, ``detail`` is free-form."""
    for key in ("code", "message"):
        if key in expected:
            if key not in actual:
                problems.append(f"{path}.{key}: missing in engine error")
            elif expected[key] != actual[key]:
                problems.append(f"{path}.{key}: expected {expected[key]!r}, got {actual[key]!r}")
    if "detail" in expected:
        compare_values(expected["detail"], actual.get("detail"), f"{path}.detail", problems)


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip("\n")


def compare_text(expected: str, actual: str, label: str, problems: list[str], limit: int = 2) -> None:
    expected_norm = normalize_text(expected)
    actual_norm = normalize_text(actual)
    if expected_norm == actual_norm:
        return
    expected_lines = expected_norm.split("\n")
    actual_lines = actual_norm.split("\n")
    if len(expected_lines) != len(actual_lines):
        problems.append(f"{label}: expected {len(expected_lines)} lines, got {len(actual_lines)}")
    shown = 0
    for index, (exp, act) in enumerate(zip(expected_lines, actual_lines)):
        if exp != act:
            problems.append(f"{label}: line {index + 1} expected {exp!r}, got {act!r}")
            shown += 1
            if shown >= limit:
                break


def stop_reason_from_console(lines: list[str]) -> str:
    if not lines:
        return "max_iters"
    last = lines[-1]
    if last.startswith("Simulación terminada en el tiempo"):
        return "mass"
    if last.startswith("Presión calculada fuera de rango"):
        return "pressure_range"
    if last.startswith("Diveregencia Detectada"):
        return "divergence"
    return "max_iters"


def normalize_console(line: str) -> str:
    """Legacy textbox lines carry a trailing/leading newline; the contract line does not."""
    return line.strip("\n")


def _fmt_ui(value: float) -> float:
    """front_nozDes.update_results_entries: %.4e for >=1e6 else %.4f, parsed back."""
    value = float(value)
    return float(f"{value:.4e}") if value >= 1e6 else float(f"{value:.4f}")


def _fmt6(value: float) -> float:
    """GEOMETRY treeview formatting."""
    return float(f"{float(value):.6f}")


def _map_numbers(value, fn):
    if isinstance(value, dict):
        return {key: _map_numbers(item, fn) for key, item in value.items()}
    if isinstance(value, list):
        return [_map_numbers(item, fn) for item in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return fn(float(value))
    return value


def _normalize_ratios(ratios) -> dict:
    """Accept both fixture naming (P0_P1t) and the engine naming (p0_p1)."""
    ratios = ratios or {}
    return {
        "P0_P1t": ratios.get("P0_P1t", ratios.get("p0_p1")),
        "Pe_P1t": ratios.get("Pe_P1t", ratios.get("pe_p1")),
        "Pe_P0": ratios.get("Pe_P0", ratios.get("pe_p0")),
    }


def compare_section(
    label: str,
    expected_canonical,
    expected_raw,
    actual,
    problems: list[str],
    notes: list[str],
    formatter,
    *,
    allow_extra: bool = False,
) -> None:
    """Compare a result section that the clone may expose raw or display-formatted.

    The fixture keeps the display representation (legacy UI/export output) as the
    canonical result and the unformatted doubles under ``raw``. If the engine
    returns raw numbers, parity is enforced at rtol=1e-9 against ``raw``; if it
    returns already-formatted numbers, the canonical representation is compared
    (documented normalization).
    """
    if actual is None:
        problems.append(f"{label}: missing in engine result")
        return
    if _map_numbers(actual, formatter) != actual:
        before = len(problems)
        compare_values(expected_raw, actual, label, problems, allow_extra=allow_extra)
        if len(problems) == before:
            notes.append(f"{label}: raw values checked at rtol=1e-9")
    else:
        before = len(problems)
        compare_values(expected_canonical, actual, label, problems, allow_extra=allow_extra)
        if len(problems) == before:
            notes.append(f"{label}: display-formatted values")


# --------------------------------------------------------------------------- #
# report + checks
# --------------------------------------------------------------------------- #
class Report:
    def __init__(self) -> None:
        self.checks: list[dict] = []

    def add(self, check_id: str, status: str, detail: str = "", **extra) -> None:
        entry = {"id": check_id, "status": status, "detail": detail}
        entry.update(extra)
        self.checks.append(entry)

    def pass_(self, check_id: str, detail: str = "", **extra) -> None:
        self.add(check_id, "pass", detail, **extra)

    def fail(self, check_id: str, detail: str, **extra) -> None:
        self.add(check_id, "fail", detail, **extra)

    def skip(self, check_id: str, detail: str) -> None:
        self.add(check_id, "skip", detail)

    @property
    def failed(self) -> list[dict]:
        return [check for check in self.checks if check["status"] == "fail"]


def load_fixture(fixtures: Path, name: str):
    path = fixtures / name
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def check_t0(client: EngineClient, fixtures: Path, report: Report, timeout: float) -> None:
    fixture = load_fixture(fixtures, "adiabatic_knsu.json")
    if fixture is None:
        report.skip("t0_adiabatic", "adiabatic_knsu.json not found")
    else:
        try:
            result = client.call(fixture["rpc"]["method"], fixture["rpc"]["params"], timeout)
            problems: list[str] = []
            compare_values(fixture["outputs"], result, "outputs", problems)
            if problems:
                report.fail("t0_adiabatic", problems[0], problems=problems[:10])
            else:
                report.pass_("t0_adiabatic", "7 outputs match rtol=1e-9")
        except RpcError as exc:
            report.fail("t0_adiabatic", f"unexpected RPC error: {exc.error}")

    error_fixture = load_fixture(fixtures, "adiabatic_error.json")
    if error_fixture is None:
        report.skip("t0_error", "adiabatic_error.json not found")
    else:
        try:
            client.call(error_fixture["rpc"]["method"], error_fixture["rpc"]["params"], timeout)
            report.fail("t0_error", "expected error -32602 for hStep=0, got a successful result")
        except RpcError as exc:
            problems = []
            compare_error(error_fixture["error"], exc.error, "error", problems)
            if problems:
                report.fail("t0_error", problems[0], problems=problems[:10])
            else:
                report.pass_("t0_error", "hStep=0 -> -32602 'Invalid integration step value.'")


def check_t1(client: EngineClient, fixtures: Path, report: Report, timeout: float, full: bool) -> None:
    targets = [("t1_engine_smoke", "engine_knsu_smoke.json")]
    if full:
        targets.append(("t1_engine_full", "engine_knsu.json"))
    for check_id, filename in targets:
        fixture = load_fixture(fixtures, filename)
        if fixture is None:
            report.skip(check_id, f"{filename} not found")
            continue
        client.drain_events()
        try:
            result = client.call(fixture["rpc"]["method"], fixture["rpc"]["params"], timeout)
        except RpcError as exc:
            report.fail(check_id, f"unexpected RPC error: {exc.error}")
            continue
        problems: list[str] = []

        arrays = result.get("arrays")
        if arrays is None:
            problems.append("result.arrays missing")
        else:
            compare_values(fixture["arrays"], arrays, "arrays", problems)

        payload = result.get("payload")
        if isinstance(payload, dict):
            compare_values(fixture["expected"]["payload"], payload, "payload", problems)
        else:
            problems.append("result.payload missing")

        events = client.drain_events()
        console = [
            normalize_console(event["params"].get("line") or "")
            for event in events
            if event.get("params", {}).get("name") == "console"
        ]
        if console != fixture["console"]:
            if len(console) != len(fixture["console"]):
                problems.append(f"console: expected {len(fixture['console'])} lines, got {len(console)} lines")
            for index, (exp, act) in enumerate(zip(fixture["console"], console)):
                if exp != act:
                    problems.append(f"console[{index}]: expected {exp!r}, got {act!r}")
                    break
        reason = stop_reason_from_console(console)
        if reason != fixture["stop_reason"]:
            problems.append(f"stop_reason: expected {fixture['stop_reason']!r}, got {reason!r}")
        job_done = [event for event in events if event.get("params", {}).get("name") == "job_done"]
        if job_done and job_done[-1]["params"].get("status") not in (None, "ok"):
            problems.append(f"job_done status: {job_done[-1]['params'].get('status')!r}")

        if problems:
            report.fail(check_id, problems[0], problems=problems[:10])
        else:
            report.pass_(
                check_id,
                f"{len(arrays.get('time', [])) if arrays else 0} samples, "
                f"{len(console)} console lines, stop={reason}",
            )


def check_t2(client: EngineClient, fixtures: Path, report: Report, timeout: float) -> None:
    fixture = load_fixture(fixtures, "nozzle_bn1.json")
    if fixture is None:
        report.skip("t2_nozzle", "nozzle_bn1.json not found")
        return
    rpc = fixture["rpc"]
    engine_obj = rpc["params"]["engine"]
    tree = engine_obj["results"]["tree_data"]

    # -- nozzle.load_engine -------------------------------------------------
    load_problems: list[str] = []
    for setup in rpc.get("setup", []):
        try:
            lane = client.call(setup["method"], setup["params"], timeout)
        except RpcError as exc:
            load_problems.append(f"{setup['method']}: {exc.error}")
            continue
        problems: list[str] = []
        expected_lane = {
            "n_samples": len(tree["Time (s)"]),
            "p1_min": min(tree["Pressure (Pa)"]),
            "p1_max": max(tree["Pressure (Pa)"]),
        }
        compare_values(expected_lane, {key: lane.get(key) for key in expected_lane}, "lane", problems)
        p_curve = lane.get("p_curve") or {}
        if list(p_curve.get("t", [])) != list(tree["Time (s)"]):
            problems.append("lane.p_curve.t does not match engine tree_data")
        load_problems.extend(problems)
    if load_problems:
        report.fail("t2_load_engine", load_problems[0], problems=load_problems[:10])
    else:
        report.pass_("t2_load_engine", f"{len(tree['Time (s)'])} samples, p1 range OK")

    # -- nozzle.calculate ---------------------------------------------------
    try:
        result = client.call(rpc["method"], rpc["params"], timeout)
    except RpcError as exc:
        report.fail("t2_nozzle", f"unexpected RPC error: {exc.error}")
        return
    problems = []
    notes: list[str] = []
    compare_section(
        "calculatedResults",
        fixture["result"]["calculatedResults"],
        fixture["raw"]["calculatedResults"],
        result.get("calculatedResults"),
        problems,
        notes,
        _fmt_ui,
        allow_extra=True,
    )
    compare_section(
        "geometry_data",
        fixture["result"]["geometry_data"],
        fixture["raw"]["geometry_data"],
        result.get("geometry_data"),
        problems,
        notes,
        _fmt6,
    )
    compare_section(
        "timeResults_data",
        fixture["result"]["timeResults_data"],
        fixture["raw"]["timeResults_data"],
        result.get("timeResults_data"),
        problems,
        notes,
        _fmt_ui,
    )
    payload = result.get("payload")
    if isinstance(payload, dict):
        # T2-9: the payload is the exported Nozzles/*.json structure -> strict keys
        compare_values(fixture["result"]["payload"], payload, "payload", problems)
    else:
        problems.append("payload: missing in engine result")
    if problems:
        report.fail("t2_nozzle", problems[0], problems=problems[:10])
    else:
        report.pass_(
            "t2_nozzle",
            f"{len(fixture['result']['timeResults_data']['Time (s)'])} time samples, 21 results "
            f"[{'; '.join(notes)}]",
        )

    # -- op points ---------------------------------------------------------
    op_fixture = load_fixture(fixtures, "nozzle_bn1_op_points.json")
    if op_fixture is None:
        report.skip("t2_op_points", "nozzle_bn1_op_points.json not found")
        return
    base = op_fixture["rpc"]["params_base"]
    problems = []
    regimes = []
    for index, point in enumerate(op_fixture["points"]):
        params = {**base, **point["params"]}
        try:
            result = client.call(op_fixture["rpc"]["method"], params, timeout)
        except RpcError as exc:
            problems.append(f"point[{index}]: RPC error {exc.error}")
            continue
        regimes.append(result.get("regime"))
        expected = dict(point["result"])
        expected["ratios"] = _normalize_ratios(expected["ratios"])
        actual = {
            "F": result.get("F"),
            "Pe": result.get("Pe"),
            "PR": result.get("PR"),
            "ratios": _normalize_ratios(result.get("ratios")),
            "regime": result.get("regime"),
        }
        if result.get("F") != _fmt_ui(result.get("F") or 0.0):
            # engine returned raw values -> 1e-9 against the raw reference
            expected_raw = dict(point["raw"])
            expected_raw["ratios"] = _normalize_ratios(expected_raw["ratios"])
            compare_values(expected_raw, actual, f"point[{index}]", problems)
        else:
            compare_values(expected, actual, f"point[{index}]", problems)
        if len(problems) > 6:
            problems = problems[:6]
    if problems:
        report.fail("t2_op_points", problems[0], problems=problems[:10])
    else:
        report.pass_("t2_op_points", f"{len(op_fixture['points'])} points: {regimes}")


def _read_written_file(result: dict, workspace: Path) -> str:
    path = Path(result.get("path", ""))
    if not path.is_absolute():
        path = workspace / path
    if not path.is_file():
        raise FileNotFoundError(f"cad.export reported {result.get('path')!r} but the file is missing")
    with path.open(encoding="utf-8", newline="") as fh:
        return fh.read()


def check_t3(client: EngineClient, fixtures: Path, report: Report, timeout: float, workspace: Path) -> None:
    sketches = load_fixture(fixtures, "cad_bn1_sketches.json")
    if sketches is None:
        report.skip("t3_cad", "cad_bn1_sketches.json not found")
        return
    try:
        loaded = client.call("cad.load_nozzle", {"path": sketches["nozzleFile"]}, timeout)
    except RpcError as exc:
        report.fail("t3_cad", f"cad.load_nozzle: {exc.error}")
        return
    config = loaded.get("config", loaded)
    problems: list[str] = []
    for kind, csv_name in sketches["csv"]["files"].items():
        try:
            result = client.call(
                "cad.export",
                {"kind": kind, "config": config, "settings": sketches["settings"], "overwrite": True},
                timeout,
            )
        except RpcError as exc:
            problems.append(f"{kind}: RPC error {exc.error}")
            continue
        try:
            actual = _read_written_file(result, workspace)
        except FileNotFoundError as exc:
            problems.append(str(exc))
            continue
        with (fixtures / csv_name).open(encoding="utf-8", newline="") as fh:
            expected = fh.read()
        compare_text(expected, actual, csv_name, problems)
    if problems:
        report.fail("t3_cad", problems[0], problems=problems[:10])
    else:
        report.pass_("t3_cad", f"{len(sketches['csv']['files'])} CSV exports byte-equal (CRLF normalized)")


def check_t4(client: EngineClient, fixtures: Path, report: Report, timeout: float, workspace: Path) -> None:
    fixture = load_fixture(fixtures, "tests_replay.json")
    if fixture is None:
        report.skip("t4_replay", "tests_replay.json not found")
        return
    client.drain_events()
    try:
        client.call(fixture["rpc"]["method"], fixture["rpc"]["params"], timeout)
    except RpcError as exc:
        report.fail("t4_replay", f"testbed.mock: {exc.error}")
        return
    try:
        run_result = client.call("testbed.run", {"nozzleFile": "BN1.json"}, timeout)
    except RpcError as exc:
        report.fail("t4_replay", f"testbed.run: {exc.error}")
        return

    # The scripted transport replays asynchronously: wait until testbed.state reports all
    # records (or the event queue goes quiet) before comparing, otherwise the harness races
    # the monitor thread. `records` is an additive field of testbed.state.
    expected_records = len(fixture["records"])
    deadline = time.monotonic() + min(timeout, 120.0)
    previous_marker = -1
    quiet_since: float | None = None
    while time.monotonic() < deadline:
        count = -1
        try:
            state = client.call("testbed.state", {}, min(10.0, timeout))
            if isinstance(state, dict) and isinstance(state.get("records"), int):
                count = state["records"]
        except (RpcError, EngineError):
            pass
        marker = max(count, client.queued_events())
        if count >= expected_records:
            break
        if marker == previous_marker:
            quiet_since = quiet_since or time.monotonic()
            if time.monotonic() - quiet_since > 1.0:
                break
        else:
            previous_marker = marker
            quiet_since = None
        time.sleep(0.1)

    events = client.drain_events()

    problems: list[str] = []
    records = [
        [event["params"].get("t"), event["params"].get("F"), event["params"].get("T")]
        for event in events
        if event.get("params", {}).get("name") == "record"
    ]
    if records:
        if len(records) != len(fixture["records"]):
            problems.append(f"record events: expected {len(fixture['records'])}, got {len(records)}")
        for index, (exp, act) in enumerate(zip(fixture["records"], records)):
            if not np.allclose(np.asarray(exp, dtype=float), np.asarray(act, dtype=float), rtol=0, atol=0):
                problems.append(f"record[{index}]: expected {exp}, got {act}")
                break
    else:
        problems.append("no event/record notifications received")

    test_file = run_result.get("testFile") if isinstance(run_result, dict) else None
    csv_path = Path(test_file) if test_file else None
    if csv_path and not csv_path.is_absolute():
        csv_path = workspace / csv_path
    if not csv_path or not csv_path.is_file():
        candidates = sorted((workspace / "Tests").glob("*.csv"), key=lambda p: p.stat().st_mtime)
        csv_path = candidates[-1] if candidates else None
    if not csv_path or not csv_path.is_file():
        problems.append("recording CSV not found in <workdir>/Tests")
    else:
        with csv_path.open(encoding="utf-8", newline="") as fh:
            actual = fh.read()
        compare_text(fixture["csv"], actual, "tests csv", problems)

    if problems:
        report.fail("t4_replay", problems[0], problems=problems[:10])
    else:
        report.pass_("t4_replay", f"{len(fixture['records'])} records, CSV byte-equal")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def prepare_workspace(base: Path, fixtures: Path) -> Path:
    workspace = base / "workspace"
    for sub in ("Engines", "Nozzles", "Sketches", "Tests"):
        (workspace / sub).mkdir(parents=True, exist_ok=True)
    inputs = fixtures / "inputs"
    mapping = {
        "KNSU-32-RT65.json": workspace / "Engines",
        "BN1.json": workspace / "Nozzles",
        "config.json": workspace,
        "checklist.json": workspace,
    }
    for name, target in mapping.items():
        source = inputs / name
        if source.is_file():
            target.mkdir(parents=True, exist_ok=True)
            (target / name).write_bytes(source.read_bytes())
    # Seed the engine database (D6: mutable data lives in OPENRED_DATA_DIR).
    database = inputs / "database.db"
    if database.is_file():
        (base / "data").mkdir(parents=True, exist_ok=True)
        (base / "data" / "database.db").write_bytes(database.read_bytes())
    return workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixtures", default=str(REPO_ROOT / "contracts" / "fixtures"))
    parser.add_argument("--engine", default="", help="engine command (default: engine/.venv python -m openred_engine)")
    parser.add_argument("--resource-dir", default=str(REPO_ROOT / "engine"))
    parser.add_argument("--report", default="parity-report.json")
    parser.add_argument("--only", default="t0,t1,t2,t3,t4")
    parser.add_argument("--full", action="store_true", help="also run the full T1 fixture (engine_knsu.json)")
    parser.add_argument("--timeout", type=float, default=600.0, help="per-RPC timeout in seconds")
    parser.add_argument("--startup-timeout", type=float, default=20.0, help="seconds to wait for event/ready")
    args = parser.parse_args(argv)

    fixtures = Path(args.fixtures).resolve()
    if not fixtures.is_dir():
        print(f"ERROR: fixtures directory not found: {fixtures}")
        print("  Generate them with: uv run python tools/parity/gen_fixtures.py --legacy legacy --out contracts/fixtures")
        return 2
    selected = {token.strip() for token in args.only.split(",") if token.strip()}
    unknown = selected - {"t0", "t1", "t2", "t3", "t4"}
    if unknown:
        parser.error(f"unknown --only tokens: {sorted(unknown)}")

    cmd = shlex.split(args.engine, posix=(os.name != "nt")) if args.engine else default_engine_cmd()
    tmp = Path(tempfile.mkdtemp(prefix="openred_parity_"))
    workspace = prepare_workspace(tmp, fixtures)
    env = dict(os.environ)
    env.update({
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "MPLBACKEND": "Agg",
        "MPLCONFIGDIR": str(tmp / "mpl-data"),
        "OPENRED_DATA_DIR": str(tmp / "data"),
        "OPENRED_RESOURCE_DIR": str(Path(args.resource_dir).resolve()),
        "OPENRED_WORKDIR": str(workspace),
    })
    (tmp / "mpl-data").mkdir(parents=True, exist_ok=True)
    (tmp / "data").mkdir(parents=True, exist_ok=True)

    print(f"engine cmd : {' '.join(cmd)}")
    print(f"engine cwd : {REPO_ROOT / 'engine'}")
    print(f"fixtures   : {fixtures}")
    print(f"workspace  : {workspace}")

    client = EngineClient(cmd, REPO_ROOT / "engine", env, args.timeout)
    report = Report()
    ready: dict | None = None
    try:
        client.start()
    except EngineError as exc:
        print(f"\nERROR: could not start the openred_engine sidecar.\n{exc}")
        print("\nIf the sidecar is not implemented yet, this is expected: run this harness once")
        print("engine/openred_engine is runnable (python -m openred_engine).")
        return 2

    try:
        ready = client.wait_ready(args.startup_timeout)
        print(f"ready      : version={ready.get('version')} pid={ready.get('pid')}\n")
    except EngineError as exc:
        print(f"\nERROR: the openred_engine sidecar did not become ready.\n{exc}")
        print("\nIf the sidecar is not implemented yet, this is expected: run this harness once")
        print("engine/openred_engine is runnable (python -m openred_engine).")
        client.stop()
        return 2

    try:
        if "t0" in selected:
            check_t0(client, fixtures, report, args.timeout)
        if "t1" in selected:
            check_t1(client, fixtures, report, args.timeout, args.full)
        if "t2" in selected:
            check_t2(client, fixtures, report, args.timeout)
        if "t3" in selected:
            check_t3(client, fixtures, report, args.timeout, workspace)
        if "t4" in selected:
            check_t4(client, fixtures, report, args.timeout, workspace)
    except EngineError as exc:
        lines = str(exc).splitlines()
        report.fail("engine", lines[0] if lines else "engine failure", diagnosis=lines[:40])
    finally:
        client.stop()

    summary = {
        "total": len(report.checks),
        "passed": sum(1 for check in report.checks if check["status"] == "pass"),
        "failed": len(report.failed),
        "skipped": sum(1 for check in report.checks if check["status"] == "skip"),
    }
    payload = {
        "report_version": 1,
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "engine": {"cmd": cmd, "ready": ready},
        "fixtures": str(fixtures),
        "tolerances": {"numbers": {"rtol": RTOL, "atol": ATOL}, "text": "exact after CRLF normalization"},
        "checks": report.checks,
        "summary": summary,
        "passed": summary["failed"] == 0,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print("results:")
    for check in report.checks:
        marker = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[check["status"]]
        print(f"  [{marker}] {check['id']}: {check['detail']}")
    print(f"\nsummary: {summary['passed']} passed, {summary['failed']} failed, {summary['skipped']} skipped")
    print(f"report : {report_path}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
