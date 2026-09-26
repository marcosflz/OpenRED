"""Engine design service: level-set burn regression with streaming console (T1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import paths
from ..figures import fig_to_b64
from ..mathutils import read_json, write_json_atomic
from ..modules.back_1 import PropellantRegresionLSM
from ..plugins import loader
from ..rpc import E_INVALID_FILE, E_NOT_FOUND, E_PARAMS, RpcError

_NUMERIC_SPEC_KEYS = (
    "P0",
    "Rt",
    "R2",
    "Lc",
    "dt",
    "dh",
    "It",
)


def _floats(raw: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    for key, value in raw.items():
        if isinstance(value, bool):
            values[key] = float(value)
        elif isinstance(value, int | float):
            values[key] = float(value)
        elif isinstance(value, str) and value.strip():
            try:
                values[key] = float(value.replace(",", "."))
            except ValueError as exc:
                raise RpcError(E_PARAMS, f"Input '{key}' is not numeric: {value!r}", None) from exc
    return values


def _prepare(params: dict[str, Any]):
    propellant = str(params.get("propellant") or "")
    grain = str(params.get("grain") or "")
    if not propellant or not grain:
        raise RpcError(E_PARAMS, "propellant and grain are required", None)
    spec = _floats(params.get("spec") or {})
    data = _floats(params.get("propellantData") or {})
    spec_inputs = {**spec, **data}
    for key in _NUMERIC_SPEC_KEYS:
        if key not in spec_inputs:
            raise RpcError(E_PARAMS, f"Missing input '{key}'", None)
    grain_classes = loader.load_library("GrainLibrary")
    grain_cls = grain_classes.get(grain)
    if grain_cls is None:
        raise RpcError(E_PARAMS, f"Unknown grain geometry: {grain}", None)
    labels = grain_cls.get_input_labels()
    init_specs = {}
    for key in labels.values():
        if key not in spec_inputs:
            raise RpcError(E_PARAMS, f"Missing grain input '{key}'", None)
        init_specs[key] = spec_inputs[key]
    return propellant, grain, spec_inputs, grain_cls, init_specs


def _build_payload(grain_cls, init_specs, spec_inputs, propellant, grain, sim, results):
    import numpy as np

    time = results["TIME"]
    pressure = results["P1"]
    mass_flow = results["GP"]
    mass = results["MP"]
    count = len(time)

    metrics = {
        "meanPressure": float(np.mean(pressure[1:])) if count > 1 else float(pressure[0]),
        "maxPressure": float(np.max(pressure[1:])) if count > 1 else float(pressure[0]),
        "minPressure": float(np.min(pressure[1:])) if count > 1 else float(pressure[0]),
        "meanMassFlow": float(np.mean(mass_flow[1:])) if count > 1 else float(mass_flow[0]),
        "maxMassFlow": float(np.max(mass_flow[1:])) if count > 1 else float(mass_flow[0]),
        "minMassFlow": float(np.min(mass_flow[1:])) if count > 1 else float(mass_flow[0]),
        "totalTime": float(time[-1]),
        "totalMass": float(mass[0]),
    }

    decimals = len(str(spec_inputs["dt"]).split(".")[-1].split("e")[0]) if "." in str(spec_inputs["dt"]) else 0
    tree_data = {
        "Time (s)": [float(f"{value:.{decimals}f}") for value in time[1:]],
        "Pressure (Pa)": [float(value) for value in pressure[1:]],
        "Mass Flow (kg/s)": [float(value) for value in mass_flow[1:]],
        "Mass (kg)": [float(value) for value in mass[1:]],
    }

    center, (cad_x, cad_y) = _sketch(grain_cls, init_specs, spec_inputs)
    inputs = {
        "Propellant": propellant,
        "GrainGeo": grain,
        "CADx": [float(value) for value in cad_x],
        "CADy": [float(value) for value in cad_y],
        "CAD0": list(center),
    }
    inputs.update(spec_inputs)

    payload = {"inputs": inputs, "results": {**metrics, "tree_data": tree_data}}
    arrays = {
        "time": [float(value) for value in time],
        "pressure": [float(value) for value in pressure],
        "massFlow": [float(value) for value in mass_flow],
        "mass": [float(value) for value in mass],
    }
    return payload, arrays


def _sketch(grain_cls, init_specs, spec_inputs):
    r_out = spec_inputs["R2"]
    dh = spec_inputs["dh"]
    geometry = grain_cls(init_specs, r_out, dh)
    center, (cad_x, cad_y) = geometry.sketchCAD()
    return tuple(center), (cad_x.tolist() if hasattr(cad_x, "tolist") else list(cad_x), cad_y.tolist() if hasattr(cad_y, "tolist") else list(cad_y))


def geometry(params: dict[str, Any], ctx) -> dict[str, Any]:
    propellant, grain, spec_inputs, grain_cls, init_specs = _prepare(params)
    geometry_obj = grain_cls(init_specs, spec_inputs["R2"], spec_inputs["dh"])
    cad = grain_cls(init_specs, spec_inputs["R2"], spec_inputs["dh"]).sketchCAD()
    center, (cad_x, cad_y) = cad
    figure = geometry_obj.plotGeometry()
    return {
        "png_b64": fig_to_b64(figure),
        "cad": {
            "center": list(center),
            "x": _as_list(cad_x),
            "y": _as_list(cad_y),
        },
    }


def _as_list(array) -> list[float]:
    if hasattr(array, "tolist"):
        return [float(value) for value in array.tolist()]
    return [float(value) for value in array]


def _time_samples(dt: float, max_iters: int) -> int:
    """Number of samples of the legacy time vector (see modules/back_1.py)."""
    import numpy as np

    if dt <= 0:
        return 0
    return int(len(np.round(np.arange(0, int(max_iters * dt) + dt, dt), 8)))


def calculate(params: dict[str, Any], ctx) -> dict[str, Any]:
    propellant, grain, spec_inputs, grain_cls, init_specs = _prepare(params)
    max_iters = int(spec_inputs["It"])
    samples = _time_samples(spec_inputs["dt"], max_iters)
    if samples < max_iters:
        # DEF-0002: the legacy crashes with a bare IndexError in a worker thread; the
        # clone reports a clear, actionable error instead (same limitation).
        raise RpcError(
            E_PARAMS,
            f"ItMax={max_iters} needs {max_iters} time samples but dt={spec_inputs['dt']} produces {samples}.",
            None,
        )
    ctx.notify("progress", job="engine.calculate", value=0.0, label="Initializing level-set geometry")
    try:
        geometry_obj = grain_cls(init_specs, spec_inputs["R2"], spec_inputs["dh"])
        phi0 = geometry_obj.getPhi()
    except (ValueError, KeyError) as exc:
        raise RpcError(E_PARAMS, f"Invalid geometry inputs: {exc}", None) from exc

    def on_message(message: str) -> None:
        ctx.notify("console", job="engine.calculate", line=message.rstrip("\n"))

    simulation = PropellantRegresionLSM(
        on_message=on_message,
        cancel_check=ctx.check_cancelled,
        dt=spec_inputs["dt"],
        dh=spec_inputs["dh"],
        maxIters=int(spec_inputs["It"]),
        phi0=phi0,
        init_data=spec_inputs,
        workingPrecision=8,
        image_resolution=30,
    )
    results = simulation.run()

    ctx.raise_if_cancelled()

    try:
        ctx.notify("progress", job="engine.calculate", value=0.9, label="Rendering figures")
        figures = {
            "regression": fig_to_b64(simulation.result_figure()),
            "pressure": fig_to_b64(simulation.plot_pressure()),
            "massFlow": fig_to_b64(simulation.plot_massFlow()),
            "massBurn": fig_to_b64(simulation.plot_massBurn()),
        }
    except Exception as exc:  # noqa: BLE001 - figures must never invalidate the numbers
        ctx.notify("log", level="warning", message=f"Figure rendering failed: {exc}")
        figures = {}

    payload, arrays = _build_payload(
        grain_cls, init_specs, spec_inputs, propellant, grain, simulation, results
    )
    ctx.notify("progress", job="engine.calculate", value=1.0, label="Done")
    return {
        "payload": payload,
        "arrays": arrays,
        "figures": figures,
        "stoppedReason": _stopped_reason(simulation, spec_inputs),
    }


def _stopped_reason(simulation, spec_inputs) -> str:
    import numpy as np

    count = len(simulation.time[: simulation.iterationCount])
    if count < int(spec_inputs["It"]):
        last_pressure = simulation.P1[count - 1]
        if simulation.Mp[count - 1] / simulation.Mp[0] < 0.001:
            return "mass"
        if not spec_inputs["P1_min"] <= last_pressure <= spec_inputs["P1_max"]:
            return "pressure"
        if count >= 2 and np.abs(np.diff(simulation.P1[count - 2 : count]))[0] > 1e6:
            return "divergence"
    return "completed"


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
    folder = Path(workdir) / "Engines"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    write_json_atomic(path, payload, indent=4)
    return {"path": str(path)}


def load(params: dict[str, Any], ctx) -> dict[str, Any]:
    raw = params.get("path")
    if not raw:
        raise RpcError(E_PARAMS, "path is required", None)
    path = Path(str(raw))
    if not path.is_file():
        raise RpcError(E_NOT_FOUND, f"File not found: {path}", None)
    try:
        payload = read_json(path)
        tree = payload["results"]["tree_data"]
        arrays = {
            "time": list(tree["Time (s)"]),
            "pressure": list(tree["Pressure (Pa)"]),
            "massFlow": list(tree["Mass Flow (kg/s)"]),
            "mass": list(tree["Mass (kg)"]),
        }
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise RpcError(E_INVALID_FILE, "Invalid file.", str(exc)) from exc
    return {"payload": payload, "arrays": arrays}


def list_engines(params: dict[str, Any], ctx) -> dict[str, Any]:
    from . import workspace

    return workspace.list_files({"kind": "Engines"}, ctx)


METHODS = {
    "engine.geometry": geometry,
    "engine.calculate": calculate,
    "engine.save": save,
    "engine.load": load,
    "engine.list": list_engines,
}
