#!/usr/bin/env python3
"""Generate golden fixtures by executing the real legacy application headless.

Usage (from the repository root, or from engine/ with uv):

    uv run python tools/parity/gen_fixtures.py --legacy legacy --out contracts/fixtures
    uv run python tools/parity/gen_fixtures.py --full          # adds the full T1 run
    uv run python tools/parity/gen_fixtures.py --only t0,t4

What it does
------------
The legacy app (CustomTkinter) is *not* modified. The script prepares an
isolated CWD (a temporary directory that receives a copy of ``legacy/database.db``
and a ``temp_dir.txt`` pointing at a temporary workspace with
``Engines/ Nozzles/ Sketches/ Tests/``), stubs ``customtkinter`` (never used by
the back modules), patches ``tkinter.messagebox`` to capture dialogs, and calls
the real legacy functions:

* t0 ``back_0.adiabaticTemp_calc`` with ``tab_0`` of ``workingDirectory/config.json``
* t1 ``back_1.PropellantRegresionLSM`` with ``tab_1`` + the KNSU row of the DB
* t2 ``NozzleLibrary.TOPBN.BellNozzle`` with ``tab_2`` and
  ``workingDirectory/Engines/KNSU-32-RT65.json``
* t3 ``back_2.EngineCADBuilder_ConventionalNozzle`` with ``workingDirectory/Nozzles/BN1.json``
  and ``tab_3``
* t4 replay of ``workingDirectory/Tests/TOPBN-KNSU-32mm-19.28.35-15.09.24.csv``
  through ``functions.getSerialValues`` + the ``front_test`` dedupe

Determinism
-----------
Fixtures contain no absolute paths and no timestamps; re-running the script on the
same legacy revision produces byte-identical fixture files (the only exception is
``README.md``, which records the generation date/command as provenance).
The T1 smoke reduction uses ``It=300, dt=0.01`` because the legacy time vector
for ``It=300, dt=0.005`` overflows (see tests/defects/DEF-0002.md).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import UTC, datetime
from pathlib import Path

FIXTURE_VERSION = 1
SCRIPT_REL = "tools/parity/gen_fixtures.py"
T1_SMOKE_ITERS = 300
T1_SMOKE_DT = 0.01  # overrides tab_1 dt=0.005; see DEF-0002
NOZZLE_DT = 0.01  # front_nozDes timeNormalization entry used for BN1 fixtures
OP_POINT_COUNT = 8

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def to_jsonable(value):
    """Recursively convert numpy scalars/arrays into JSON-serializable objects."""
    import numpy as np

    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return [to_jsonable(v) for v in value.tolist()]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def dump_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(to_jsonable(payload), fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def provenance(command: str, legacy_commit: str | None) -> dict:
    return {
        "fixture_version": FIXTURE_VERSION,
        "generator": SCRIPT_REL,
        "command": command,
        "legacy_commit": legacy_commit,
        "python": sys.version.split()[0],
    }


def format_ui(value: float) -> str:
    """Same formatting rule as front_nozDes.update_results_entries."""
    return f"{value:.4e}" if value >= 1e6 else f"{value:.4f}"


class CapturingTextbox:
    """Minimal stand-in for ctk.CTkTextbox (insert/see/update_idletasks)."""

    def __init__(self) -> None:
        self.chunks: list[str] = []

    def insert(self, _index, text) -> None:  # noqa: ANN001
        self.chunks.append(str(text))

    def see(self, *_args, **_kwargs) -> None:
        pass

    def update_idletasks(self) -> None:
        pass

    def lines(self) -> list[str]:
        out: list[str] = []
        for chunk in self.chunks:
            text = chunk
            if text.endswith("\n"):
                text = text[:-1]
            if text.startswith("\n"):
                text = text[1:]
            out.append(text)
        return out


# --------------------------------------------------------------------------- #
# legacy harness
# --------------------------------------------------------------------------- #
class LegacyHarness:
    """Runs the legacy back modules in an isolated temporary CWD."""

    def __init__(self, legacy_dir: Path, workdir_inputs: bool = True) -> None:
        self.legacy = legacy_dir.resolve()
        self.tmp = Path(tempfile.mkdtemp(prefix="openred_fixtures_"))
        self.workdir = self.tmp / "workspace"
        self.messages: list[tuple[str, tuple, dict]] = []
        self._modules: dict[str, object] = {}
        self._imports_done = False
        self.workdir_inputs = workdir_inputs

    # -- setup -------------------------------------------------------------
    def _stub_customtkinter(self) -> None:
        ctk = types.ModuleType("customtkinter")
        for name in (
            "CTk", "CTkFrame", "CTkLabel", "CTkEntry", "CTkButton", "CTkOptionMenu",
            "CTkScrollableFrame", "CTkTabview", "CTkTextbox", "CTkSwitch", "CTkSlider",
            "CTkProgressBar", "CTkCheckBox", "CTkScrollbar", "CTkToplevel", "CTkImage",
            "DoubleVar", "StringVar", "IntVar", "BooleanVar", "CTkFont",
        ):
            setattr(ctk, name, type(name, (), {}))
        for const in ("TOP", "BOTTOM", "LEFT", "RIGHT", "BOTH", "X", "Y", "NSEW"):
            setattr(ctk, const, const.lower())
        ctk.set_appearance_mode = lambda *a, **k: None
        ctk.set_default_colors = lambda *a, **k: None
        ctk.set_default_color_theme = lambda *a, **k: None
        sys.modules.setdefault("customtkinter", ctk)

    def _patch_messagebox(self) -> None:
        import tkinter.messagebox as messagebox

        def _record(kind: str):
            def _inner(*args, **kwargs):
                self.messages.append((kind, args, kwargs))
                return None

            return _inner

        messagebox.showinfo = _record("info")
        messagebox.showerror = _record("error")
        messagebox.showwarning = _record("warning")
        messagebox.askyesno = _record("askyesno")

    def _prepare_workspace(self) -> None:
        self.workdir.mkdir(parents=True, exist_ok=True)
        for sub in ("Engines", "Nozzles", "Sketches", "Tests"):
            (self.workdir / sub).mkdir(exist_ok=True)
        shutil.copy2(self.legacy / "database.db", self.tmp / "database.db")
        (self.tmp / "temp_dir.txt").write_text(str(self.workdir), encoding="utf-8")
        if self.workdir_inputs:
            for sub in ("Engines", "Nozzles"):
                src = self.legacy / "workingDirectory" / sub
                if src.is_dir():
                    for item in sorted(src.iterdir()):
                        if item.is_file():
                            shutil.copy2(item, self.workdir / sub / item.name)
            checklist = self.legacy / "workingDirectory" / "checklist.json"
            if checklist.is_file():
                shutil.copy2(checklist, self.workdir / "checklist.json")

    def setup(self) -> None:
        if self._imports_done:
            return
        if not (self.legacy / "database.db").is_file():
            raise FileNotFoundError(f"legacy database.db not found in {self.legacy}")
        if not (self.legacy / "functions.py").is_file():
            raise FileNotFoundError(f"{self.legacy} does not look like the legacy tree")
        self.tmp.mkdir(parents=True, exist_ok=True)
        self._prepare_workspace()
        os.chdir(self.tmp)
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(self.legacy))
        self._stub_customtkinter()
        self._patch_messagebox()

        import functions  # noqa: PLC0415
        from back_modules import back_0, back_1  # noqa: PLC0415
        from back_modules.back_2 import EngineCADBuilder_ConventionalNozzle  # noqa: PLC0415
        from back_modules.GrainLibrary.TUBULAR import Tubular  # noqa: PLC0415
        from back_modules.NozzleLibrary.TOPBN import BellNozzle  # noqa: PLC0415

        self._modules = {
            "functions": functions,
            "back_0": back_0,
            "back_1": back_1,
            "cad": EngineCADBuilder_ConventionalNozzle,
            "grain_tubular": Tubular,
            "bell_nozzle": BellNozzle,
        }
        self._imports_done = True

    def cleanup(self) -> None:
        os.chdir(REPO_ROOT)
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- accessors ---------------------------------------------------------
    @property
    def functions(self):
        return self._modules["functions"]

    def config(self) -> dict:
        with (self.legacy / "workingDirectory" / "config.json").open(encoding="utf-8") as fh:
            return json.load(fh)["tabs"]

    def drain_messages(self) -> list[tuple[str, tuple, dict]]:
        out = list(self.messages)
        self.messages.clear()
        return out

    def propellant_row(self, name: str) -> dict:
        import sqlite3

        conn = sqlite3.connect(str(self.tmp / "database.db"))
        try:
            cursor = conn.execute(
                "SELECT Propelente, T_ad, MolWeight, Cp, Cv, R, gamma, cChar, Density, "
                "P1_min, P1_max, a, n FROM propelente WHERE Propelente = ?",
                (name,),
            )
            row = cursor.fetchone()
        finally:
            conn.close()
        if row is None:
            raise KeyError(f"propellant {name!r} not present in legacy database.db")
        keys = ("Propelente", "T_ad", "MolWeight", "Cp", "Cv", "R", "gamma", "cChar",
                "Density", "P1_min", "P1_max", "a", "n")
        return dict(zip(keys, (float(v) if k != "Propelente" else v for k, v in zip(keys, row))))


# --------------------------------------------------------------------------- #
# t0 - adiabatic temperature
# --------------------------------------------------------------------------- #
def gen_t0(harness: LegacyHarness, out: Path, prov: dict) -> dict[str, Path]:
    tab0 = harness.config()["tab_0"]
    reac = [{"moles": float(m), "component": c} for m, c in tab0["reactivos"]]
    prod = [{"moles": float(m), "component": c} for m, c in tab0["productos"]]
    t0 = float(tab0["initial_temp"])
    t_guess = float(tab0["temp_guess"])
    h_step = float(tab0["temp_Int_step"])

    back_0 = harness._modules["back_0"]
    outputs = back_0.adiabaticTemp_calc(
        [(r["moles"], r["component"]) for r in reac],
        [(p["moles"], p["component"]) for p in prod],
        t0,
        t_guess,
        h_step,
    )
    if outputs is None:
        raise RuntimeError("legacy adiabaticTemp_calc returned None for valid inputs")
    keys = ("tSol", "molWeight", "cp", "cv", "R", "gamma", "cChar")
    outputs = dict(zip(keys, (float(v) for v in outputs)))
    harness.drain_messages()

    params = {"reac": reac, "prod": prod, "t0": t0, "tGuess": t_guess, "hStep": h_step}
    fixture = {
        "id": "adiabatic_knsu",
        "tag": "full",
        "inputs": params,
        "outputs": outputs,
        "rpc": {"method": "adiabatic.calculate", "params": params, "result_from": "#/outputs"},
        "provenance": {**prov, "source": "workingDirectory/config.json tab_0 + legacy/database.db"},
    }
    path = out / "adiabatic_knsu.json"
    dump_json(path, fixture)

    # error case: hStep = 0 -> messagebox "Invalid integration step value."
    back_0.adiabaticTemp_calc(
        [(r["moles"], r["component"]) for r in reac],
        [(p["moles"], p["component"]) for p in prod],
        t0,
        t_guess,
        0.0,
    )
    captured = harness.drain_messages()
    message = None
    for kind, args, _kwargs in captured:
        if kind == "info" and len(args) >= 2 and args[1] == "Invalid integration step value.":
            message = args[1]
    if message is None:
        raise RuntimeError(f"expected 'Invalid integration step value.' messagebox, got {captured!r}")
    error_params = {**params, "hStep": 0.0}
    error_fixture = {
        "id": "adiabatic_error",
        "tag": "error",
        "inputs": error_params,
        "error": {"code": -32602, "message": message},
        "rpc": {
            "method": "adiabatic.calculate",
            "params": error_params,
            "error": {"code": -32602, "message": message, "detail": None},
        },
        "provenance": {**prov, "source": "workingDirectory/config.json tab_0 (hStep forced to 0)"},
    }
    error_path = out / "adiabatic_error.json"
    dump_json(error_path, error_fixture)
    return {"adiabatic_knsu": path, "adiabatic_error": error_path}


# --------------------------------------------------------------------------- #
# t1 - LSM engine simulation
# --------------------------------------------------------------------------- #
def _engine_spec(harness: LegacyHarness, cfg: dict, iters: float, dt: float) -> tuple[dict, dict]:
    tab1 = cfg
    prop = harness.propellant_row("KNSU")
    spec = {
        "P0": float(tab1["P0"]),
        "Rt": float(tab1["Rt"]),
        "R2": float(tab1["Rc"]),
        "Lc": float(tab1["Lc"]),
        "dt": float(dt),
        "dh": float(tab1["dh"]),
        "It": float(iters),
        "cx_real": float(tab1["Tubular-Grain_cx_real"]),
        "cy_real": float(tab1["Tubular-Grain_cy_real"]),
        "r_in": float(tab1["Tubular-Grain_r_in"]),
    }
    propellant_data = {
        "a": prop["a"],
        "n": prop["n"],
        "R": prop["R"],
        "T1": prop["T_ad"],
        "cChar": prop["cChar"],
        "rho_b": prop["Density"],
        "P1_min": prop["P1_min"],
        "P1_max": prop["P1_max"],
    }
    return spec, propellant_data


def _run_lsm(harness: LegacyHarness, spec: dict, propellant_data: dict) -> dict:
    tubular = harness._modules["grain_tubular"]
    back_1 = harness._modules["back_1"]
    grain = tubular(
        {"cx_real": spec["cx_real"], "cy_real": spec["cy_real"], "r_in": spec["r_in"]},
        spec["R2"],
        spec["dh"],
    )
    phi0 = grain.getPhi()
    center, (cad_x, cad_y) = grain.sketchCAD()

    lsm_inputs = {
        "P0": spec["P0"], "Rt": spec["Rt"], "R2": spec["R2"], "Lc": spec["Lc"],
        "a": propellant_data["a"], "n": propellant_data["n"], "R": propellant_data["R"],
        "T1": propellant_data["T1"], "cChar": propellant_data["cChar"],
        "rho_b": propellant_data["rho_b"], "P1_min": propellant_data["P1_min"],
        "P1_max": propellant_data["P1_max"],
    }
    box = CapturingTextbox()
    simulation = back_1.PropellantRegresionLSM(
        textbox=box,
        dt=spec["dt"],
        dh=spec["dh"],
        maxIters=int(spec["It"]),
        phi0=phi0,
        init_data=lsm_inputs,
        workingPrecision=8,
        image_resolution=30,
    )
    results = simulation.run(box)
    return {
        "arrays": {
            "time": [float(v) for v in results["TIME"]],
            "pressure": [float(v) for v in results["P1"]],
            "massFlow": [float(v) for v in results["GP"]],
            "mass": [float(v) for v in results["MP"]],
        },
        "chunks": box.lines(),
        "cad": {
            "CAD0": [float(center[0]), float(center[1])],
            "CADx": [float(v) for v in cad_x],
            "CADy": [float(v) for v in cad_y],
        },
    }


def _stop_reason(chunks: list[str]) -> tuple[str, str | None]:
    if not chunks:
        return "max_iters", None
    last = chunks[-1]
    if last.startswith("Simulación terminada en el tiempo"):
        return "mass", last
    if last.startswith("Presión calculada fuera de rango"):
        return "pressure_range", last
    if last.startswith("Diveregencia Detectada"):
        return "divergence", last
    return "max_iters", None


def _front_inputs(spec: dict, propellant_data: dict, cad: dict) -> dict:
    """The ``inputs`` dict written by front_propDes.export_results (specInputs + CAD)."""
    inputs = {"Propellant": "KNSU", "GrainGeo": "Tubular-Grain"}
    inputs.update(cad)
    inputs.update(spec)
    inputs.update(propellant_data)
    return inputs


def _expected_payload(spec: dict, propellant_data: dict, arrays: dict, cad: dict) -> dict:
    """Reproduce front_propDes.export_results / update_results for the clone payload."""
    time = arrays["time"][1:]
    pressure = arrays["pressure"][1:]
    mass_flow = arrays["massFlow"][1:]
    mass = arrays["mass"][1:]
    decimals = len(str(spec["dt"]).split(".")[-1])
    tree_data = {
        "Time (s)": [float(f"{v:.{decimals}f}") for v in time],
        "Pressure (Pa)": pressure,
        "Mass Flow (kg/s)": mass_flow,
        "Mass (kg)": mass,
    }
    import numpy as np

    p = np.asarray(pressure)
    g = np.asarray(mass_flow)
    inputs = _front_inputs(spec, propellant_data, cad)
    results = {
        "meanPressure": float(np.mean(p)),
        "maxPressure": float(np.max(p)),
        "minPressure": float(np.min(p)),
        "meanMassFlow": float(np.mean(g)),
        "maxMassFlow": float(np.max(g)),
        "minMassFlow": float(np.min(g)),
        "totalTime": float(time[-1]),
        "totalMass": float(arrays["mass"][0]),
        "tree_data": tree_data,
    }
    return {"payload": {"inputs": inputs, "results": results}, "arrays": arrays}


def gen_t1(harness: LegacyHarness, out: Path, prov: dict, full: bool) -> dict[str, Path]:
    cfg = harness.config()["tab_1"]
    written: dict[str, Path] = {}

    spec, propellant_data = _engine_spec(harness, cfg, T1_SMOKE_ITERS, T1_SMOKE_DT)
    run = _run_lsm(harness, spec, propellant_data)
    stop_reason, stop_message = _stop_reason(run["chunks"])
    expected = _expected_payload(spec, propellant_data, run["arrays"], run["cad"])
    rpc_params = {
        "propellant": "KNSU",
        "grain": "Tubular-Grain",
        "spec": dict(spec),
        "propellantData": propellant_data,
    }
    fixture = {
        "id": "engine_knsu_smoke",
        "tag": "smoke",
        "reduction": {
            "reason": "CI smoke run; the legacy time vector overflows for It=300, dt=0.005 (DEF-0002)",
            "It": T1_SMOKE_ITERS,
            "dt": T1_SMOKE_DT,
        },
        "inputs": _front_inputs(spec, propellant_data, run["cad"]),
        "arrays": run["arrays"],
        "console": run["chunks"],
        "stop_reason": stop_reason,
        "stop_message": stop_message,
        "expected": expected,
        "rpc": {"method": "engine.calculate", "params": rpc_params, "result_from": "#/expected"},
        "provenance": {**prov, "source": "workingDirectory/config.json tab_1 + KNSU row"},
    }
    path = out / "engine_knsu_smoke.json"
    dump_json(path, fixture)
    written["engine_knsu_smoke"] = path
    print(
        f"  t1 smoke: {len(run['arrays']['time'])} samples, "
        f"{len(run['chunks'])} console lines, stop={stop_reason}"
    )

    if full:
        import time as _time

        started = _time.perf_counter()
        full_spec, full_prop = _engine_spec(harness, cfg, float(cfg["ItMax"]), float(cfg["dt"]))
        full_run = _run_lsm(harness, full_spec, full_prop)
        elapsed = _time.perf_counter() - started
        stop_reason, stop_message = _stop_reason(full_run["chunks"])
        expected = _expected_payload(full_spec, full_prop, full_run["arrays"], full_run["cad"])
        rpc_params = {
            "propellant": "KNSU",
            "grain": "Tubular-Grain",
            "spec": dict(full_spec),
            "propellantData": full_prop,
        }
        fixture = {
            "id": "engine_knsu",
            "tag": "full",
            "inputs": _front_inputs(full_spec, full_prop, full_run["cad"]),
            "arrays": full_run["arrays"],
            "console": full_run["chunks"],
            "stop_reason": stop_reason,
            "stop_message": stop_message,
            "expected": expected,
            "rpc": {"method": "engine.calculate", "params": rpc_params, "result_from": "#/expected"},
            "provenance": {
                **prov,
                "source": "workingDirectory/config.json tab_1 + KNSU row (ItMax/dh as configured)",
            },
        }
        full_path = out / "engine_knsu.json"
        dump_json(full_path, fixture)
        written["engine_knsu"] = full_path
        print(
            f"  t1 full: {len(full_run['arrays']['time'])} samples, "
            f"{len(full_run['chunks'])} console lines, stop={stop_reason} ({elapsed:.1f}s)"
        )
    return written


# --------------------------------------------------------------------------- #
# t2 - nozzle design
# --------------------------------------------------------------------------- #
def _engine_payload(harness: LegacyHarness, engine_file: str) -> dict:
    """Raw engine JSON payload ({inputs, results}) consumed by nozzle.calculate/op_point."""
    with (harness.workdir / "Engines" / engine_file).open(encoding="utf-8") as fh:
        return json.load(fh)


def _classify_regime(p0: float, p1t: float, pe: float, pr_crit: list[float]) -> str:
    """front_nozDes.updateMapPlots classification (values rounded to 4 decimals, as in the UI)."""
    p0_p1 = float(f"{(p0 / p1t):.4f}")
    pe_p1 = float(f"{(pe / p1t):.4f}")
    prc0, prc1, prc2, prc3 = (float(f"{v:.4f}") for v in pr_crit)
    if p0_p1 > prc0:
        return "Subsonic"
    if prc2 < pe_p1 < prc1:
        return "Normal Shock Inside"
    if abs(pe_p1 - prc3) < 1e-2 and pe < p0:
        return "Over-Expanded"
    if abs(pe_p1 - prc3) < 1e-2 and pe == p0:
        return "Design-Point"
    if abs(pe_p1 - prc3) < 1e-2 and pe > p0:
        return "Under-Expanded"
    return "Normal Shock Exit"


def gen_t2(harness: LegacyHarness, out: Path, prov: dict) -> dict[str, Path]:
    tab2 = harness.config()["tab_2"]
    engine_file = tab2["engine_config"]
    nozzle_type = tab2["nozzle_type"]
    if nozzle_type != "TOPN-BN":
        raise RuntimeError(f"t2 fixture expects TOPN-BN, config has {nozzle_type!r}")
    spec = {
        "TOP-BN_k": float(tab2["TOPN-BN_TOP-BN_k"]),
        "TOP-BN_theta_t": float(tab2["TOPN-BN_TOP-BN_theta_t"]),
        "TOP-BN_theta_e": float(tab2["TOPN-BN_TOP-BN_theta_e"]),
        "TOP-BN_cone_length_percent": float(tab2["TOPN-BN_TOP-BN_cone_length_percent"]),
    }
    p1 = float(tab2["P1"])
    n = float(tab2["n_res"])
    default_check = int(tab2["SwitchState"])

    bell = harness._modules["bell_nozzle"]
    nozzle = bell(default_check, p1, n, NOZZLE_DT, engine_file, spec)
    nozzle.calculation_running = True
    for step in range(len(nozzle.P_t)):
        nozzle.run_step(step)

    labels = list(bell.get_result_labels())
    data, time_data, geo_data, pr_data = nozzle.calculated_results()
    calculated = {label: float(value) for label, value in zip(labels, data)}
    pr_keys = ("PR_Crit0", "PR_Crit1", "PR_Crit2", "PR_Crit3")
    for key, value in zip(pr_keys, pr_data):
        calculated[key] = float(value)

    engine_obj = _engine_payload(harness, engine_file)
    geometry = {
        "X (m)": [float(v) for v in geo_data[0]],
        "Y (m)": [float(v) for v in geo_data[1]],
        "AR (m)": [float(v) for v in geo_data[2]],
    }
    time_results = {
        "Time (s)": [float(v) for v in time_data[0]],
        "Thrust (kg)": [float(v) for v in time_data[1]],
        "CF": [float(v) for v in time_data[2]],
    }
    # Canonical contract result: the legacy UI/export representation (4/6 decimals).
    # `raw` keeps the unformatted doubles for 1e-9 numeric checks.
    fmt_calculated = {key: float(format_ui(value)) for key, value in calculated.items()}
    fmt_geometry = {key: [float(f"{value:.6f}") for value in values] for key, values in geometry.items()}
    fmt_time_results = {key: [float(format_ui(value)) for value in values] for key, values in time_results.items()}
    payload = {
        "Inputs": {
            "NozzleConfig": nozzle_type,
            "DefaultCheck": default_check,
            "P1": p1,
            "n": n,
            "EngineConfig": engine_file,
            "specInputs": spec,
        },
        "geometry_data": fmt_geometry,
        "timeResults_data": fmt_time_results,
        "calculatedResults": fmt_calculated,
    }
    result = {
        "calculatedResults": fmt_calculated,
        "geometry_data": fmt_geometry,
        "timeResults_data": fmt_time_results,
        "payload": payload,
    }
    fixture = {
        "id": "nozzle_bn1",
        "tag": "full",
        "inputs": {
            "nozzleType": nozzle_type,
            "p1": p1,
            "n": n,
            "dt": NOZZLE_DT,
            "defaultCheck": default_check,
            "spec": spec,
            "engineFile": engine_file,
        },
        "result": result,
        "raw": {
            "description": "Unformatted doubles from legacy calculated_results() (1e-9 reference).",
            "calculatedResults": calculated,
            "geometry_data": geometry,
            "timeResults_data": time_results,
        },
        "rpc": {
            "method": "nozzle.calculate",
            "setup": [{"method": "nozzle.load_engine", "params": {"path": engine_file}}],
            "params": {
                "engine": engine_obj,
                "nozzleType": nozzle_type,
                "p1": p1,
                "n": n,
                "dt": NOZZLE_DT,
                "defCheck": default_check,
                "engineName": engine_file,
                "spec": spec,
            },
            "result_from": "#/result",
        },
        "provenance": {
            **prov,
            "source": f"workingDirectory/Engines/{engine_file} + config.json tab_2 + DB KNSU row",
        },
    }
    path = out / "nozzle_bn1.json"
    dump_json(path, fixture)
    print(
        f"  t2: {len(nozzle.P_t)} time samples, n={n:g}, "
        f"DP.Thrust={calculated['DP. Thrust (kg)']:.6g} kg, L={calculated['Longitud (m)']:.6g} m"
    )

    # ---- op points -------------------------------------------------------
    import numpy as np

    pressure = np.asarray(engine_obj["results"]["tree_data"]["Pressure (Pa)"], dtype=float)
    t_min = float(np.min(pressure))
    t_max = float(np.max(pressure))
    p0_base = float(engine_obj["inputs"]["P0"])
    pr_crit = [calculated[k] for k in pr_keys]

    def p1_for(fraction: float) -> float:
        return t_min + fraction * (t_max - t_min)

    sweep = [
        (0.05, 1.0), (0.20, 1.0), (0.40, 1.0), (0.60, 1.0),
        (0.80, 1.0), (0.95, 1.0), (0.50, 0.5), (0.50, 1.5),
    ]
    points = []
    for fraction, p0_mult in sweep:
        p1t = p1_for(fraction)
        p0 = p0_base * p0_mult
        op = nozzle.opPoint_plot(p1t, p0)
        if op is None:
            raise RuntimeError(f"opPoint_plot returned None for p1t={p1t}, p0={p0}")
        pe = float(op["Pe"])
        thrust = float(op["F"])
        raw_ratios = {
            "P0_P1t": p0 / p1t,
            "Pe_P1t": pe / p1t,
            "Pe_P0": pe / p0,
        }
        regime = _classify_regime(p0, p1t, pe, pr_crit)
        # canonical: the values front_nozDes.updateMapPlots displays (4 decimals)
        formatted = {
            "F": float(format_ui(thrust)),
            "Pe": float(format_ui(pe)),
            "PR": float(format_ui(raw_ratios["Pe_P1t"])),
            "ratios": {key: float(format_ui(value)) for key, value in raw_ratios.items()},
            "regime": regime,
        }
        points.append({
            "params": {"p1t": p1t, "p0": p0},
            "result": formatted,
            "raw": {
                "F": thrust,
                "Pe": pe,
                "PR": raw_ratios["Pe_P1t"],
                "ratios": raw_ratios,
                "regime": regime,
            },
        })
    op_fixture = {
        "id": "nozzle_bn1_op_points",
        "tag": "full",
        "sweep": {
            "description": "P1t fraction over [min(P), max(P)] of the engine tree_data; P0 multiplier over engine P0",
            "designP1": p1,
            "designP1_note": "front_nozDes constructs the nozzle with the design P1 (entry value, default engine meanPressure) and then calls opPoint_plot(p1t, p0); the geometry/curves depend on it.",
            "points": [[f, m] for f, m in sweep],
        },
        "points": points,
        "rpc": {
            "method": "nozzle.op_point",
            "setup": [{"method": "nozzle.load_engine", "params": {"path": engine_file}}],
            "params_base": {
                "engine": engine_obj,
                "nozzleType": nozzle_type,
                "p1": p1,
                "n": n,
                "dt": NOZZLE_DT,
                "defCheck": default_check,
                "spec": spec,
            },
            "calls_from": "#/points",
        },
        "provenance": {**prov, "source": "TOPBN.BellNozzle.opPoint_plot + updateMapPlots regime rules"},
    }
    op_path = out / "nozzle_bn1_op_points.json"
    dump_json(op_path, op_fixture)
    print(f"  t2 op points: {[p['result']['regime'] for p in points]}")
    return {"nozzle_bn1": path, "nozzle_bn1_op_points": op_path}


# --------------------------------------------------------------------------- #
# t3 - CAD sketches
# --------------------------------------------------------------------------- #
def _cad_settings(tab3: dict) -> dict:
    settings: dict = {}
    for key, value in tab3.items():
        if key in ("NozzleConfig", "type"):
            settings[key] = value
        elif key.startswith("on_"):
            settings[key] = int(value)
        else:
            settings[key] = float(value)
    return settings


def gen_t3(harness: LegacyHarness, out: Path, prov: dict) -> dict[str, Path]:
    tab3 = harness.config()["tab_3"]
    nozzle_file = tab3["NozzleConfig"]
    settings = _cad_settings(tab3)
    builder_cls = harness._modules["cad"]
    builder = builder_cls(nozzle_file)

    written: dict[str, Path] = {}
    for kind in ("engine", "cover", "tools"):
        path = out / f"cad_bn1_{kind}.csv"
        getattr(builder, f"export_{kind}")(settings, str(path))
        written[f"cad_bn1_{kind}"] = path
    print(
        "  t3 CAD: "
        + ", ".join(f"{kind}={written[f'cad_bn1_{kind}'].stat().st_size}B" for kind in ("engine", "cover", "tools"))
    )

    sketches = {}
    for name in ("Engine", "Cover", "Cartridge", "Propellant", "MouldCover",
                 "MouldCoverFix", "Mould", "ExtraMould", "NutUp", "NutDown"):
        x, y = builder.get_sketch(settings, sketch=name)
        sketches[name] = {
            "x": [float(v) for v in x],
            "y": [float(v) for v in y],
        }
    fixture = {
        "id": "cad_bn1_sketches",
        "tag": "full",
        "nozzleFile": nozzle_file,
        "engineFile": builder.engineUsed,
        "settings": settings,
        "sketches": sketches,
        "csv": {
            "header": ["Sketch", "Plane", "x", "y", "z"],
            "scale": 100,
            "planes": ["XY", "YZ"],
            "files": {kind: f"cad_bn1_{kind}.csv" for kind in ("engine", "cover", "tools")},
        },
        "provenance": {**prov, "source": "back_2.EngineCADBuilder_ConventionalNozzle + config.json tab_3"},
    }
    path = out / "cad_bn1_sketches.json"
    dump_json(path, fixture)
    written["cad_bn1_sketches"] = path
    return written


# --------------------------------------------------------------------------- #
# t4 - testbed replay
# --------------------------------------------------------------------------- #
def gen_t4(harness: LegacyHarness, out: Path, prov: dict) -> dict[str, Path]:
    source = harness.legacy / "workingDirectory" / "Tests" / "TOPBN-KNSU-32mm-19.28.35-15.09.24.csv"
    with source.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [row for row in reader if row]
    if header != ["t(s)", "F(kg)", "T(K)"]:
        raise RuntimeError(f"unexpected test CSV header: {header!r}")

    lines = []
    for t, f, temp in rows:
        lines.append(f"t(s): {t} F(kg): {f} T(K): {temp}")

    get_serial_values = harness.functions.getSerialValues
    records: list[tuple[float, float, float]] = []
    last_line: str | None = None
    for line in lines:
        if line == last_line:
            continue
        values = get_serial_values(line)
        if values is None:
            raise RuntimeError(f"getSerialValues did not parse reconstructed line: {line!r}")
        record = tuple(float(v) for v in values)
        if record not in records:
            records.append(record)
        last_line = line

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(header)
    for record in records:
        writer.writerow(record)
    csv_text = buffer.getvalue()
    with source.open(encoding="utf-8", newline="") as fh:
        reference_text = fh.read()
    if csv_text != reference_text:
        raise RuntimeError(
            "replayed CSV differs from the legacy reference; refusing to write a non-reproducible fixture"
        )

    fixture = {
        "id": "tests_replay",
        "tag": "full",
        "source": source.name,
        "lines": lines,
        "records": [list(r) for r in records],
        "csv": csv_text,
        "rpc": {
            "method": "testbed.mock",
            "params": {"enabled": True, "script": lines},
            "result_from": "#/mock_result",
        },
        "mock_result": {"ok": True},
        "provenance": {**prov, "source": f"workingDirectory/Tests/{source.name}"},
    }
    path = out / "tests_replay.json"
    dump_json(path, fixture)
    print(f"  t4 replay: {len(lines)} serial lines -> {len(records)} records, CSV byte-identical")
    return {"tests_replay": path}


# --------------------------------------------------------------------------- #
# inputs + README
# --------------------------------------------------------------------------- #
def copy_inputs(harness: LegacyHarness, out: Path, prov: dict) -> dict[str, str]:
    mapping = {
        "KNSU-32-RT65.json": harness.legacy / "workingDirectory" / "Engines" / "KNSU-32-RT65.json",
        "BN1.json": harness.legacy / "workingDirectory" / "Nozzles" / "BN1.json",
        "config.json": harness.legacy / "workingDirectory" / "config.json",
        "checklist.json": harness.legacy / "workingDirectory" / "checklist.json",
        "database.db": harness.legacy / "database.db",
    }
    inputs_dir = out / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, src in mapping.items():
        dst = inputs_dir / name
        shutil.copy2(src, dst)
        hashes[name] = sha256_file(dst)
    dump_json(inputs_dir / "manifest.json", {
        "description": "Byte copies of the legacy inputs used by the fixtures (sha256 for provenance).",
        "files": hashes,
        "provenance": prov,
    })
    return hashes


def write_readme(out: Path, prov: dict, generated: dict[str, Path], hashes: dict[str, str], full: bool) -> None:
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    rows = []
    for path in sorted(generated.values()):
        tag = json.loads(path.read_text(encoding="utf-8")).get("tag", "?") if path.suffix == ".json" else "full"
        rows.append(f"| `{path.name}` | {tag} | {'derived from' if path.suffix == '.csv' else 'source'} |")
    lines = [
        "# Fixtures dorados — OpenRED Engine",
        "",
        "> **Generado** por `tools/parity/gen_fixtures.py`. No editar a mano: los cambios requieren RFC",
        "> (`contracts/RFC-*.md`) porque son la referencia de paridad T0–T4.",
        "",
        "## Provenance",
        "",
        f"- Fecha de generación: {date}",
        f"- Comando: `{prov['command']}`",
        f"- Commit legacy: `{prov['legacy_commit']}` (repo OpenRED, subdirectorio `legacy/`)",
        f"- Intérprete: Python {prov['python']}",
        "- Sin rutas absolutas ni timestamps dentro de los fixtures: la regeneración es determinista.",
        "",
        "## Cómo regenerar",
        "",
        "```bash",
        "uv run --project engine python tools/parity/gen_fixtures.py --legacy legacy --out contracts/fixtures",
        "uv run --project engine python tools/parity/gen_fixtures.py --full       # añade engine_knsu.json (ItMax real)",
        "uv run --project engine python tools/parity/gen_fixtures.py --only t0,t4 # subconjunto",
        "```",
        "",
        "El generador copia `legacy/database.db` a un CWD temporal, escribe `temp_dir.txt` apuntando a un",
        "workspace temporal con `Engines/ Nozzles/ Sketches/ Tests/`, stubea `customtkinter` y parchea",
        "`tkinter.messagebox` para capturar los avisos. **No modifica `legacy/`**.",
        "",
        "## Metodología",
        "",
        "Cada fixture JSON incrusta un objeto `rpc` con la llamada contractual reconstruida",
        "(`method`, `params`, `result_from`/`calls_from`), validado por `tools/parity/validate_schemas.py`",
        "contra `contracts/schemas/`. `rpc.result_from` es un puntero JSON al resultado esperado dentro del",
        "propio fixture. Los CSV se comparan byte a byte por `tools/parity/run_parity.py`.",
        "",
        "## Smoke vs full",
        "",
        "- **smoke**: reducción para CI rápido. `engine_knsu_smoke.json` usa `It=300, dt=0.01`",
        "  (el legacy con `It=300, dt=0.005` desborda su vector de tiempos, ver `tests/defects/DEF-0002.md`).",
        "- **full**: parámetros reales de `workingDirectory/config.json` (T0, T2, T3, T4 y, con `--full`,",
        "  `engine_knsu.json` con `ItMax=10000` y `dh=0.0001`).",
        "",
        "## Ficheros",
        "",
        "| Fixture | Tag | Origen |",
        "|---|---|---|",
        *rows,
        "",
        "### Notas de normalización",
        "",
        "- `adiabatic_error.json`: mensaje capturado de `messagebox.showinfo` → error `-32602`",
        "  `\"Invalid integration step value.\"`.",
        "- `engine_knsu_*.json`: `expected` reproduce `front_propDes.export_results` (incluye `tree_data`",
        "  sin la fila inicial y el tiempo formateado con los decimales de `dt`); `console` son las líneas",
        "  insertadas en el textbox, sin el `\\n` final. Las líneas deben compararse tras normalizar los",
        "  saltos de línea (el contrato `event/console {line}` no los incluye).",
        "- `nozzle_bn1.json`: `result.*` es la representación canónica del contrato (valores formateados",
        "  como la UI/export legacy: `:.4e` si ≥1e6, si no `:.4f`; geometría `:.6f`) y `raw.*` guarda los",
        "  dobles sin formato de `calculated_results()` para las comprobaciones a 1e-9. `rpc.params`",
        "  incluye `dt`, `defCheck` y `engineName`; `engine` es el payload crudo del motor",
        "  ({inputs, results}, igual que el fichero `Engines/*.json`). El typo `DP. Thrust (kg)1` solo",
        "  existe en `CONE-LN`, no en TOPN-BN.",
        "- `nozzle_bn1_op_points.json`: `regime` aplica las reglas de `front_nozDes.updateMapPlots`",
        "  (ratios redondeados a 4 decimales). La tobera se construye con la P1 de diseño",
        "  (`params_base.p1`, el valor de `tab_2`; por defecto `engine.results.meanPressure`), igual que",
        "  `updateMapPlots` sobre `self.calculatedNozzle` (ver `tests/defects/DEF-0004.md`).",
        "- `cad_bn1_*.csv`: bytes exactos de `back_2.export_*` (cabecera `Sketch,Plane,x,y,z`, `\\r\\n`).",
        "- `tests_replay.json`: líneas reconstruidas desde el CSV (`t(s): .. F(kg): .. T(K): ..`),",
        "  parseadas con `functions.getSerialValues` y deduplicadas como `front_test.on_textbox_change`;",
        "  el CSV resultante es byte-idéntico al de referencia.",
        "",
        "## Inputs",
        "",
        "Copias byte a byte de los ficheros de `legacy/` usados como entrada (`database.db` incluida:",
        "`run_parity.py` la siembra en `OPENRED_DATA_DIR` para que el motor encuentre componentes y",
        "propelentes). `manifest.json` repite los hashes para consumo programático.",
        "",
        "| Fichero | SHA-256 |",
        "|---|---|",
        *[f"| `inputs/{name}` | `{digest}` |" for name, digest in sorted(hashes.items())],
        "",
    ]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--legacy", default=str(REPO_ROOT / "legacy"), help="legacy source tree")
    parser.add_argument("--out", default=str(REPO_ROOT / "contracts" / "fixtures"), help="fixture output dir")
    parser.add_argument("--full", action="store_true", help="also generate the full T1 run (ItMax, dh reales)")
    parser.add_argument("--only", default="", help="comma list of t0,t1,t2,t3,t4")
    args = parser.parse_args(argv)

    legacy = Path(args.legacy).resolve()
    out = Path(args.out).resolve()
    selected = {token.strip() for token in args.only.split(",") if token.strip()} or {"t0", "t1", "t2", "t3", "t4"}
    unknown = selected - {"t0", "t1", "t2", "t3", "t4"}
    if unknown:
        parser.error(f"unknown --only tokens: {sorted(unknown)}")

    command = f"python {SCRIPT_REL} --legacy legacy --out contracts/fixtures" + (" --full" if args.full else "")
    prov = provenance(command, git_commit(REPO_ROOT))
    out.mkdir(parents=True, exist_ok=True)

    harness = LegacyHarness(legacy)
    generated: dict[str, Path] = {}
    try:
        print(f"preparing isolated legacy CWD: {harness.tmp}")
        harness.setup()
        print(f"legacy commit: {prov['legacy_commit']}  python: {prov['python']}")

        if "t0" in selected:
            print("t0 adiabatic ...")
            generated.update(gen_t0(harness, out, prov))
        if "t1" in selected:
            print("t1 engine LSM ...")
            generated.update(gen_t1(harness, out, prov, args.full))
        if "t2" in selected:
            print("t2 nozzle ...")
            generated.update(gen_t2(harness, out, prov))
        if "t3" in selected:
            print("t3 CAD ...")
            generated.update(gen_t3(harness, out, prov))
        if "t4" in selected:
            print("t4 testbed replay ...")
            generated.update(gen_t4(harness, out, prov))

        hashes = copy_inputs(harness, out, prov)
        write_readme(out, prov, generated, hashes, args.full)
    finally:
        harness.cleanup()

    print(f"\nOK: {len(generated)} fixtures + inputs written to {out}")
    for key, path in sorted(generated.items()):
        print(f"  {key:24s} {path.stat().st_size:>9d} B  {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
