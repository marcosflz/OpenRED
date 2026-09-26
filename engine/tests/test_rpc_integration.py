"""End-to-end integration tests for the JSON-RPC sidecar over stdio.

These tests spawn the real process (``python -m openred_engine``) and speak the
contract from ``contracts/methods.md``: envelopes, events, golden T0 numbers,
workspace persistence, plugin discovery and cancellation.
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ENGINE_DIR = REPO / "engine"
LEGACY = REPO / "legacy"
WORKED_DIR = LEGACY / "workingDirectory"


class SidecarClient:
    """Minimal stdio client with a background reader (supports out-of-band events)."""

    def __init__(self, workdir: Path) -> None:
        env = dict(os.environ)
        env.update(
            {
                "PYTHONPATH": str(ENGINE_DIR),
                "PYTHONNOUSERSITE": "1",
                "PYTHONUTF8": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "MPLBACKEND": "Agg",
                "MPLCONFIGDIR": str(workdir / "mpl-data"),
                "OPENRED_DATA_DIR": str(workdir),
                "OPENRED_RESOURCE_DIR": str(ENGINE_DIR),
                "OPENRED_WORKDIR": str(workdir),
            }
        )
        self.workdir = workdir
        self.process = subprocess.Popen(
            [sys.executable, "-s", "-X", "utf8", "-m", "openred_engine"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=env,
            cwd=str(workdir),
        )
        self.messages: queue.Queue[dict] = queue.Queue()
        self._next_id = 1
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self.messages.put(json.loads(line))
            except json.JSONDecodeError:
                self.messages.put({"raw": line})

    def send(self, method: str, params: dict | None = None) -> int:
        request_id = self._next_id
        self._next_id += 1
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps({"id": request_id, "method": method, "params": params or {}}) + "\n")
        self.process.stdin.flush()
        return request_id

    def call(self, method: str, params: dict | None = None, timeout: float = 120.0):
        request_id = self.send(method, params)
        events: list[dict] = []
        while True:
            message = self.messages.get(timeout=timeout)
            if message.get("method") == "event":
                events.append(message["params"])
                continue
            assert message.get("id") == request_id, message
            return message, events

    def wait_event(self, name: str, timeout: float = 120.0) -> dict:
        while True:
            message = self.messages.get(timeout=timeout)
            if message.get("method") == "event" and message["params"].get("name") == name:
                return message["params"]

    def drain_events(self) -> list[dict]:
        events = []
        while True:
            try:
                message = self.messages.get_nowait()
            except queue.Empty:
                return events
            if message.get("method") == "event":
                events.append(message["params"])

    def close(self) -> None:
        try:
            self.send("app.shutdown")
        except Exception:  # noqa: BLE001
            pass
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.process.kill()
        if self.process.stderr is not None:
            self.process.stderr.close()


@pytest.fixture()
def sidecar(tmp_path: Path):
    shutil.copy(LEGACY / "database.db", tmp_path / "database.db")
    for folder in ("Engines", "Nozzles", "Sketches", "Tests"):
        (tmp_path / folder).mkdir()
    shutil.copy(WORKED_DIR / "Engines" / "KNSU-32-RT65.json", tmp_path / "Engines" / "KNSU-32-RT65.json")
    shutil.copy(WORKED_DIR / "Nozzles" / "BN1.json", tmp_path / "Nozzles" / "BN1.json")
    shutil.copy(WORKED_DIR / "checklist.json", tmp_path / "checklist.json")
    client = SidecarClient(tmp_path)
    ready = client.wait_event("ready", timeout=90)
    assert ready["version"]
    try:
        yield client
    finally:
        client.close()


def test_ping_and_unknown_method(sidecar: SidecarClient) -> None:
    response, _ = sidecar.call("app.ping")
    assert response["result"]["version"]
    assert response["result"]["python"].startswith("3.12")

    response, _ = sidecar.call("does.not.exist")
    assert response["error"]["code"] == -32601


def test_workspace_round_trip(sidecar: SidecarClient) -> None:
    config = json.loads((WORKED_DIR / "config.json").read_text(encoding="utf-8"))
    response, _ = sidecar.call("workspace.save_config", {"config": config, "force": True})
    assert Path(response["result"]["path"]).is_file()

    response, _ = sidecar.call("workspace.load_config")
    assert response["result"]["config"] == config

    response, _ = sidecar.call("workspace.save_config", {"config": config})
    assert response["error"]["code"] == 1004


def test_adiabatic_matches_legacy_golden(sidecar: SidecarClient) -> None:
    params = {
        "reac": [
            {"moles": 1, "component": "C12H22O11 (Solid)"},
            {"moles": 6.288, "component": "KNO3 (S)"},
        ],
        "prod": [
            {"moles": 3.796, "component": "CO2"},
            {"moles": 5.205, "component": "CO"},
            {"moles": 7.794, "component": "H2O"},
            {"moles": 3.065, "component": "H2"},
            {"moles": 3.143, "component": "N2"},
            {"moles": 2.998, "component": "K2CO3 (L)"},
            {"moles": 0.274, "component": "KOH (G)"},
        ],
        "t0": 293,
        "tGuess": 1500,
        "hStep": 1,
    }
    response, _ = sidecar.call("adiabatic.calculate", params)
    result = response["result"]
    assert result["tSol"] == pytest.approx(1790.9602394045733, rel=1e-12)
    assert result["cChar"] == pytest.approx(989.8131693939902, rel=1e-12)

    response, _ = sidecar.call("adiabatic.calculate", {**params, "hStep": 0})
    assert response["error"]["code"] == -32602
    assert response["error"]["message"] == "Invalid integration step value."


def test_plugins_and_engine_geometry(sidecar: SidecarClient) -> None:
    response, _ = sidecar.call("plugins.list", {"library": "GrainLibrary"})
    assert list(response["result"]["plugins"]) == ["Tubular-Grain"]

    response, _ = sidecar.call("plugins.list", {"library": "NozzleLibrary"})
    assert set(response["result"]["plugins"]) == {"CONE-LN", "TOPN-BN"}

    response, _ = sidecar.call(
        "engine.geometry",
        {
            "propellant": "KNSU",
            "grain": "Tubular-Grain",
            "spec": {
                "P0": 1e5,
                "Rt": 0.0065,
                "R2": 0.016,
                "Lc": 0.1,
                "dt": 0.005,
                "dh": 0.0005,
                "It": 1000,
                "cx_real": 0.005,
                "cy_real": 0.0,
                "r_in": 0.005,
            },
        },
    )
    result = response["result"]
    assert result["png_b64"]
    assert len(result["cad"]["x"]) == 100


def test_nozzle_load_engine_and_op_point(sidecar: SidecarClient) -> None:
    response, _ = sidecar.call(
        "nozzle.load_engine", {"path": str(sidecar.workdir / "Engines" / "KNSU-32-RT65.json")}
    )
    lane = response["result"]
    assert lane["n_samples"] == 375
    assert lane["meanPressure"] == pytest.approx(790190.5221096972, rel=1e-12)

    engine = json.loads((sidecar.workdir / "Engines" / "KNSU-32-RT65.json").read_text(encoding="utf-8"))
    response, _ = sidecar.call(
        "nozzle.op_point",
        {
            "engine": engine,
            "nozzleType": "TOPN-BN",
            "p1t": 790190.5221096972,
            "p0": 101325,
            "n": 50,
            "dt": 0.01,
            "defCheck": 1,
            "spec": {
                "TOP-BN_k": 0.25,
                "TOP-BN_theta_t": 30,
                "TOP-BN_theta_e": 6,
                "TOP-BN_cone_length_percent": 1,
            },
        },
    )
    result = response["result"]
    assert result["regime"] in {
        "Subsonic",
        "Normal Shock Inside",
        "Normal Shock Exit",
        "Over-Expanded",
        "Design-Point",
        "Under-Expanded",
    }
    assert set(result["ratios"]) == {"PR0", "PR1", "PR2", "PR3", "p0_p1", "pe_p1", "pe_p0"}
    assert len(result["curves"]["x"]) == len(result["curves"]["mach"]) == len(result["curves"]["pr"]) > 0


def test_cad_load_and_export(sidecar: SidecarClient) -> None:
    response, _ = sidecar.call("cad.load_nozzle", {"path": str(sidecar.workdir / "Nozzles" / "BN1.json")})
    loaded = response["result"]
    assert loaded["architecture"] == "conventional"
    assert len(loaded["fields"]) == 25

    # No `name`/`path`: headless default (the parity harness uses this form).
    response, _ = sidecar.call(
        "cad.export",
        {
            "kind": "engine",
            "config": loaded["config"],
            "settings": {"type": "Fitted", "n_conv": 50, "KIn": 0.5, "alpha": 0.5, "t_factor": 0.5},
        },
    )
    assert Path(response["result"]["path"]).is_file()


def test_testbed_replay_matches_legacy_csv(sidecar: SidecarClient) -> None:
    fixture = json.loads((REPO / "contracts" / "fixtures" / "tests_replay.json").read_text(encoding="utf-8"))
    response, _ = sidecar.call("testbed.mock", fixture["rpc"]["params"])
    assert response.get("result", {}).get("ok") is True, response

    response, _ = sidecar.call("testbed.run", {"nozzleFile": "BN1.json"})
    test_file = Path(response["result"]["testFile"])
    assert test_file.is_file()

    expected_records = len(fixture["records"])
    for _ in range(200):
        state, _ = sidecar.call("testbed.state")
        if state["result"]["records"] >= expected_records:
            break
        time.sleep(0.05)
    assert state["result"]["records"] == expected_records

    with open(test_file, encoding="utf-8", newline="") as handle:
        actual = handle.read()
    assert actual == fixture["csv"]
    sidecar.call("testbed.mock", {"enabled": False})


def test_engine_calculate_rejects_short_time_vector(sidecar: SidecarClient) -> None:
    """DEF-0002: the legacy crashes with a bare IndexError; the clone returns -32602."""
    params = {
        "propellant": "KNSU",
        "grain": "Tubular-Grain",
        "spec": {
            "P0": 1e5,
            "Rt": 0.0065,
            "R2": 0.016,
            "Lc": 0.1,
            "dt": 0.005,
            "dh": 0.0005,
            "It": 300,
            "cx_real": 0.005,
            "cy_real": 0.0,
            "r_in": 0.005,
        },
        "propellantData": {
            "a": 0.0100306326677,
            "n": 0.3195768787656,
            "R": 223.55903930128062,
            "T1": 1790.9602394045733,
            "cChar": 989.8131693939902,
            "rho_b": 1845,
            "P1_min": 86487.80487804883,
            "P1_max": 10580341.463414632,
        },
    }
    response, _ = sidecar.call("engine.calculate", params)
    assert response["error"]["code"] == -32602
    assert "ItMax=300" in response["error"]["message"]


def test_engine_calculate_streams_and_cancels(sidecar: SidecarClient) -> None:
    propellant = {
        "a": 0.0100306326677,
        "n": 0.3195768787656,
        "R": 223.55903930128062,
        "T1": 1790.9602394045733,
        "cChar": 989.8131693939902,
        "rho_b": 1845,
        "P1_min": 86487.80487804883,
        "P1_max": 10580341.463414632,
    }
    spec = {
        "P0": 1e5,
        "Rt": 0.0065,
        "R2": 0.016,
        "Lc": 0.1,
        "dt": 0.005,
        "dh": 0.0005,
        "It": 100000,
        "cx_real": 0.005,
        "cy_real": 0.0,
        "r_in": 0.005,
    }
    request_id = sidecar.send(
        "engine.calculate",
        {"propellant": "KNSU", "grain": "Tubular-Grain", "spec": spec, "propellantData": propellant},
    )
    first_console = sidecar.wait_event("console", timeout=120)
    assert "Iter:" in first_console["line"]

    cancel_id = sidecar.send("request.cancel", {"id": request_id})
    cancelled = False
    while True:
        message = sidecar.messages.get(timeout=120)
        if message.get("method") == "event":
            continue
        if message.get("id") == cancel_id:
            assert message["result"]["cancelled"] is True
        if message.get("id") == request_id:
            assert message["error"]["code"] == 1005
            cancelled = True
            break
    assert cancelled


@pytest.mark.slow
def test_engine_calculate_matches_legacy_payload(sidecar: SidecarClient) -> None:
    """Full T1 run with the real config; compares the export payload with the legacy fixture."""
    fixture_path = REPO / "contracts" / "fixtures" / "engine_knsu.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    params = fixture["rpc"]["params"]
    expected = fixture["expected"]["payload"]

    response, events = sidecar.call("engine.calculate", params, timeout=1800)
    payload = response["result"]["payload"]

    assert payload["inputs"]["Propellant"] == expected["inputs"]["Propellant"]
    assert payload["inputs"]["CAD0"] == expected["inputs"]["CAD0"]
    for key, value in expected["inputs"].items():
        if key in {"Propellant", "GrainGeo", "CADx", "CADy", "CAD0"}:
            continue
        assert payload["inputs"][key] == pytest.approx(value, rel=1e-12), key
    for key, value in expected["results"].items():
        if key == "tree_data":
            continue
        assert payload["results"][key] == pytest.approx(value, rel=1e-12), key
    for key, values in expected["results"]["tree_data"].items():
        assert payload["results"]["tree_data"][key] == pytest.approx(values, rel=1e-12), key

    console = [event["line"].strip("\n") for event in events if event.get("name") == "console"]
    assert console[0] == fixture["console"][0]
    assert console[-1].strip() == fixture["stop_message"].strip()
