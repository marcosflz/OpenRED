"""Nozzle design service: step-by-step nozzle calculation, off-design op points and export (T2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .. import paths
from ..figures import fig_to_b64
from ..mathutils import read_json, write_json_atomic
from ..plugins import loader
from ..rpc import E_INVALID_FILE, E_NOT_FOUND, E_PARAMS, RpcError


def _fmt(value: Any) -> float:
    """Legacy display formatting: %.4e for >=1e6, %.4f otherwise, parsed back to float."""
    value = float(value)
    text = f"{value:.4e}" if value >= 1e6 else f"{value:.4f}"
    return float(text)


def _fmt6(value: Any) -> float:
    return float(f"{float(value):.6f}")


def _require_nozzle(params: dict[str, Any]):
    nozzle_type = str(params.get("nozzleType") or "")
    classes = loader.load_library("NozzleLibrary")
    nozzle_cls = classes.get(nozzle_type)
    if nozzle_cls is None:
        raise RpcError(E_PARAMS, f"Unknown nozzle type: {nozzle_type}", None)
    return nozzle_type, nozzle_cls


def _engine_payload(params: dict[str, Any]) -> dict[str, Any]:
    engine = params.get("engine")
    if isinstance(engine, dict):
        return engine
    if isinstance(engine, str) and engine:
        path = Path(engine)
        if not path.is_file():
            workdir = paths.workdir()
            if not workdir:
                raise RpcError(1001, "No working directory has been selected.", None)
            candidate = Path(workdir) / "Engines" / path.name
            path = candidate if candidate.is_file() else path
        if not path.is_file():
            raise RpcError(E_NOT_FOUND, f"Engine file not found: {engine}", None)
        try:
            return read_json(path)
        except (OSError, ValueError) as exc:
            raise RpcError(E_INVALID_FILE, "Invalid file.", str(exc)) from exc
    raise RpcError(E_PARAMS, "engine payload or path is required", None)


def _spec_floats(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        raise RpcError(E_PARAMS, "spec must be an object", None)
    values: dict[str, float] = {}
    for key, value in raw.items():
        try:
            values[key] = float(str(value).replace(",", "."))
        except (TypeError, ValueError) as exc:
            raise RpcError(E_PARAMS, f"Nozzle input '{key}' is not numeric: {value!r}", None) from exc
    return values


def _total_steps(engine: dict[str, Any], dt: float) -> int:
    time = engine["results"]["tree_data"]["Time (s)"]
    if not dt:
        pressure = engine["results"]["tree_data"]["Pressure (Pa)"]
        return len(pressure)
    return len(np.arange(time[0], time[-1], dt))


def _results_dict(nozzle: Any) -> dict[str, Any]:
    labels = nozzle.get_result_labels()
    data, _time_data, _geo_data, pr_data = nozzle.calculated_results()
    results = {label: _fmt(value) for label, value in zip(labels, data)}
    results["PR_Crit0"] = _fmt(pr_data[0])
    results["PR_Crit1"] = _fmt(pr_data[1])
    results["PR_Crit2"] = _fmt(pr_data[2])
    results["PR_Crit3"] = _fmt(pr_data[3])
    return results


def _time_results(nozzle: Any) -> dict[str, Any]:
    _data, time_data, _geo_data, _pr_data = nozzle.calculated_results()
    return {
        "Time (s)": [_fmt(value) for value in time_data[0]],
        "Thrust (kg)": [_fmt(value) for value in time_data[1]],
        "CF": [_fmt(value) for value in time_data[2]],
    }


def _geometry_data(nozzle: Any) -> dict[str, Any]:
    _data, _time_data, geo_data, _pr_data = nozzle.calculated_results()
    return {
        "X (m)": [_fmt6(value) for value in geo_data[0]],
        "Y (m)": [_fmt6(value) for value in geo_data[1]],
        "AR (m)": [_fmt6(value) for value in geo_data[2]],
    }


def load_engine(params: dict[str, Any], ctx) -> dict[str, Any]:
    raw = params.get("path")
    engine = _engine_payload({"engine": raw})
    try:
        results = engine["results"]
        lane = {
            "inputs": engine["inputs"],
            "n_samples": len(results["tree_data"]["Time (s)"]),
            "p1_min": float(results["minPressure"]),
            "p1_max": float(results["maxPressure"]),
            "meanPressure": float(results["meanPressure"]),
            "p_curve": {
                "t": list(results["tree_data"]["Time (s)"]),
                "P": list(results["tree_data"]["Pressure (Pa)"]),
            },
            "nozzleConfig": engine.get("inputs", {}).get("GrainGeo"),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise RpcError(E_INVALID_FILE, "Invalid file.", str(exc)) from exc
    return lane


def calculate(params: dict[str, Any], ctx) -> dict[str, Any]:
    nozzle_type, nozzle_cls = _require_nozzle(params)
    engine = _engine_payload(params)
    p1 = float(params.get("p1"))
    n = int(float(params.get("n")))
    dt = float(params.get("dt") or 0)
    def_check = 1 if params.get("defCheck") else 0
    spec = _spec_floats(params.get("spec") or {})
    engine_name = str(params.get("engineName") or "")

    total_steps = _total_steps(engine, dt)
    ctx.notify("progress", job="nozzle.calculate", value=0.0, label="0%")
    nozzle = nozzle_cls(def_check, p1, n, dt, engine, spec)
    nozzle.calculation_running = True
    for step in range(total_steps):
        ctx.raise_if_cancelled()
        nozzle.run_step(step)
        value = (step + 1) / total_steps if total_steps > 0 else 1.0
        ctx.notify("progress", job="nozzle.calculate", value=value, label=f"{int(value * 100)}%")
        if step % 10 == 0:
            ctx.raise_if_cancelled()

    try:
        figures = {
            "thrust": fig_to_b64(nozzle.thrust_plot()),
            "cf": fig_to_b64(nozzle.thrustCoeff_plot()),
            "geometry": fig_to_b64(nozzle.geom_plot()),
            "pres": fig_to_b64(nozzle.pres_plot(nozzle.P1)),
            "mach": fig_to_b64(nozzle.mach_plot(nozzle.P1)),
        }
    except Exception as exc:  # noqa: BLE001
        ctx.notify("log", level="warning", message=f"Nozzle figure rendering failed: {exc}")
        figures = {}

    results = _results_dict(nozzle)
    time_results = _time_results(nozzle)
    geometry = _geometry_data(nozzle)
    payload = {
        "Inputs": {
            "NozzleConfig": nozzle_type,
            "DefaultCheck": def_check,
            "P1": p1,
            "n": n,
            "EngineConfig": engine_name,
            "specInputs": spec,
        },
        "geometry_data": geometry,
        "timeResults_data": time_results,
        "calculatedResults": results,
    }
    return {
        "calculatedResults": results,
        "geometry_data": geometry,
        "timeResults_data": time_results,
        "figures": figures,
        "payload": payload,
    }


def op_point(params: dict[str, Any], ctx) -> dict[str, Any]:
    nozzle_type, nozzle_cls = _require_nozzle(params)
    engine = _engine_payload(params)
    p1t = float(params.get("p1t"))
    # front_nozDes builds the nozzle with the design P1 and then evaluates opPoint_plot(p1t, p0);
    # the geometry/curves (and the shock thresholds) depend on it.
    p1_design = float(params.get("p1") or params.get("p1Design") or p1t)
    p0 = float(params.get("p0"))
    n = int(float(params.get("n") or 100))
    dt = float(params.get("dt") or 0)
    def_check = 1 if params.get("defCheck") else 0
    spec = _spec_floats(params.get("spec") or {})

    nozzle = nozzle_cls(def_check, p1_design, n, dt, engine, spec)
    output = nozzle.opPoint_plot(p1t, p0)
    # Ratios exactly as front_nozDes.updateMapPlots (rounded to 4 decimals as text first).
    p0_p1 = float(f"{(p0 / p1t):.4f}")
    pe = float(output["Pe"])
    pe_p1 = float(f"{(pe / p1t):.4f}")
    pe_p0 = float(f"{(pe / p0):.4f}")
    pr0 = float(f"{nozzle.PR_crit ** -1:.4f}")
    pr1 = float(f"{nozzle.PRatio_1:.4f}")
    pr2 = float(f"{nozzle.PRatio_2:.4f}")
    pr3 = float(f"{nozzle.PRatio_3:.4f}")

    if p0_p1 > pr0:
        regime = "Subsonic"
    elif pr2 < pe_p1 < pr1:
        regime = "Normal Shock Inside"
    elif abs(pe_p1 - pr3) < 1e-2 and pe < p0:
        regime = "Over-Expanded"
    elif abs(pe_p1 - pr3) < 1e-2 and pe == p0:
        regime = "Design-Point"
    elif abs(pe_p1 - pr3) < 1e-2 and pe > p0:
        regime = "Under-Expanded"
    else:
        regime = "Normal Shock Exit"

    return {
        "F": float(f"{float(output['F']):.4f}"),
        "Pe": float(f"{pe:.4f}"),
        "PR": pe_p1,
        "ratios": {
            "PR0": pr0,
            "PR1": pr1,
            "PR2": pr2,
            "PR3": pr3,
            "p0_p1": p0_p1,
            "pe_p1": pe_p1,
            "pe_p0": pe_p0,
        },
        "regime": regime,
        "nozzleType": nozzle_type,
        "curves": {
            "x": _as_float_list(output.get("x", [])),
            "mach": _as_float_list(output.get("Mach", [])),
            "pr": _as_float_list(output.get("PR", [])),
        },
    }


def _as_float_list(values: Any) -> list[float]:
    return [float(value) for value in values]


def save(params: dict[str, Any], ctx) -> dict[str, Any]:
    workdir = paths.workdir()
    if not workdir:
        raise RpcError(1001, "No working directory has been selected.", None)
    payload = params.get("payload")
    if not isinstance(payload, dict):
        raise RpcError(E_PARAMS, "payload is required", None)
    name = str(params.get("name") or "").strip()
    if not name:
        raise RpcError(E_PARAMS, "name is required", None)
    if not name.endswith(".json"):
        name += ".json"
    folder = Path(workdir) / "Nozzles"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    write_json_atomic(path, payload, indent=4)
    return {"path": str(path)}


def load(params: dict[str, Any], ctx) -> dict[str, Any]:
    raw = params.get("path")
    if not raw:
        raise RpcError(E_PARAMS, "path is required", None)
    path = Path(str(raw))
    if not path.is_file() and paths.workdir():
        candidate = Path(paths.workdir()) / "Nozzles" / path.name
        path = candidate if candidate.is_file() else path
    if not path.is_file():
        raise RpcError(E_NOT_FOUND, f"File not found: {path}", None)
    try:
        payload = read_json(path)
    except (OSError, ValueError) as exc:
        raise RpcError(E_INVALID_FILE, "Invalid file.", str(exc)) from exc
    return {"payload": payload}


def list_nozzles(params: dict[str, Any], ctx) -> dict[str, Any]:
    from . import workspace

    return workspace.list_files({"kind": "Nozzles"}, ctx)


METHODS = {
    "nozzle.load_engine": load_engine,
    "nozzle.calculate": calculate,
    "nozzle.op_point": op_point,
    "nozzle.save": save,
    "nozzle.load": load,
    "nozzle.list": list_nozzles,
}
