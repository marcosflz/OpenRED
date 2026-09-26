"""CAD service: conventional nozzle engine sketches and CSV export (T3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import paths
from ..figures import fig_to_b64
from ..mathutils import read_json
from ..modules import back_2
from ..rpc import E_ALREADY_EXISTS, E_INVALID_FILE, E_NOT_FOUND, E_PARAMS, RpcError

# Legacy front_cad.entriesLabelsDic: keys with '(' in the label are numeric entries,
# the rest are checkboxes; 'type' is the wall-type option menu.
_ENTRY_LABELS: dict[str, str] = {
    "type": "Wall type in nozzle",
    "n_conv": "Puntos Arco Convergente (n)",
    "t_cartridge": "Espesor de Cartucho (m)",
    "KIn": "Coeficiente radio entrada (%)",
    "alpha": "Angulo zona convergente (deg)",
    "wall_t": "Espesor de pared (m)",
    "bolt_OffSet": "Longitud tornillo (m)",
    "hBoltFactor": "Factor de altura del tornillo (%)",
    "cover_t": "Espesor de la cubierta (m)",
    "dy_elect": "Distancia entre electrodos (m)",
    "d_elect": "Diámetro del electrodo (m)",
    "on_Cartridge": "Mostrar Cartucho",
    "on_Propellant": "Mostrar Propelente",
    "on_Engine": "Mostrar Motor",
    "on_Cover": "Mostrar Cubierta",
    "t_factor": "Factor Espesor Tools (%)",
    "extra_len": "Longitud Extra de molde (m)",
    "cover_len": "Longitud exterior molde (m)",
    "on_CoverCast1": "Cubierta de molde",
    "on_CoverCast2": "Sujección de molde",
    "on_CastBolt": "Tornillo de Tuerca",
    "on_Mould": "Molde de propelente",
    "on_CastNut": "Tuerca de molde",
    "nut_h": "Altura de Tuerca (m)",
    "nut_dr": "Incremento radio de Tuerca (m)",
}
_CHECKBOXES = [key for key in _ENTRY_LABELS if key.startswith("on_")]
_NUMERIC = [key for key in _ENTRY_LABELS if key not in _CHECKBOXES and key != "type"]

_METHODS = {
    "engine": "export_engine",
    "cover": "export_cover",
    "tools": "export_tools",
}


def _resolve_nozzle(params: dict[str, Any]) -> dict[str, Any]:
    raw = params.get("config", params.get("path"))
    if isinstance(raw, dict):
        return raw
    path = Path(str(raw or ""))
    if not path.is_file() and paths.workdir():
        candidate = Path(paths.workdir()) / "Nozzles" / path.name
        path = candidate if candidate.is_file() else path
    if not path.is_file():
        raise RpcError(E_NOT_FOUND, f"File not found: {raw}", None)
    try:
        return read_json(path)
    except (OSError, ValueError) as exc:
        raise RpcError(E_INVALID_FILE, "Invalid file.", str(exc)) from exc


def _settings(raw: Any) -> dict[str, Any]:
    provided = raw if isinstance(raw, dict) else {}
    settings: dict[str, Any] = {"type": str(provided.get("type") or "Fitted")}
    for key in _NUMERIC:
        value = provided.get(key, 0)
        try:
            settings[key] = float(str(value).replace(",", ".")) if value not in (None, "") else 0.0
        except (TypeError, ValueError) as exc:
            raise RpcError(E_PARAMS, f"Setting '{key}' is not numeric: {value!r}", None) from exc
    for key in _CHECKBOXES:
        value = provided.get(key, True)
        settings[key] = 1 if value in (True, 1, "1", "true", "True") else 0
    return settings


def _builder(nozzle: dict[str, Any]):
    try:
        return back_2.EngineCADBuilder_ConventionalNozzle(nozzle)
    except KeyError as exc:
        raise RpcError(E_INVALID_FILE, "Invalid file.", f"Missing key: {exc}") from exc
    except ValueError as exc:
        raise RpcError(E_INVALID_FILE, str(exc), None) from exc


def load_nozzle(params: dict[str, Any], ctx) -> dict[str, Any]:
    nozzle = _resolve_nozzle(params)
    try:
        architecture = nozzle["Inputs"]["NozzleConfig"]
    except (KeyError, TypeError) as exc:
        raise RpcError(E_INVALID_FILE, "Invalid file.", str(exc)) from exc
    if architecture == "AS-Nozzle":
        return {
            "config": nozzle,
            "architecture": "as-nozzle",
            "fields": [],
            "checks": [],
            "message": "AS-Nozzle architecture is not supported by the CAD module.",
        }
    fields = []
    for key, label in _ENTRY_LABELS.items():
        if key == "type":
            fields.append({"key": key, "label": label, "type": "select", "options": ["Fitted", "Bulk"], "default": "Fitted"})
        elif key in _CHECKBOXES:
            fields.append({"key": key, "label": label, "type": "checkbox", "default": True})
        else:
            fields.append({"key": key, "label": label, "type": "number", "default": 0})
    # Suggested values from the saved configuration (tab_3), when available.
    suggested: dict[str, Any] = {}
    workdir = paths.workdir()
    if workdir:
        config_path = Path(workdir) / "config.json"
        if config_path.is_file():
            try:
                tab3 = read_json(config_path).get("tabs", {}).get("tab_3", {})
                suggested = {key: value for key, value in tab3.items() if key in _ENTRY_LABELS}
            except (OSError, ValueError):
                suggested = {}
    return {
        "config": nozzle,
        "architecture": "conventional",
        "fields": fields,
        "checks": [field for field in fields if field["type"] == "checkbox"],
        "suggested": suggested,
    }


def views(params: dict[str, Any], ctx) -> dict[str, Any]:
    nozzle = _resolve_nozzle(params)
    settings = _settings(params.get("settings"))
    builder = _builder(nozzle)
    try:
        figures = {
            "engine": fig_to_b64(builder.plot_Engine(settings)),
            "coverFront": fig_to_b64(builder.plot_CoverFront(settings)),
            "nozzleFront": fig_to_b64(builder.plot_NozzleFront(settings)),
            "tools": fig_to_b64(builder.plot_Tools(settings)),
            "toolMould": fig_to_b64(builder.plot_ToolMould(settings)),
            "toolMouldFix": fig_to_b64(builder.plot_ToolMouldFix(settings)),
        }
    except (KeyError, ValueError) as exc:
        raise RpcError(E_PARAMS, f"Invalid CAD settings: {exc}", None) from exc
    return {"views": figures}


def export(params: dict[str, Any], ctx) -> dict[str, Any]:
    kind = str(params.get("kind") or "")
    if kind not in _METHODS:
        raise RpcError(E_PARAMS, f"kind must be one of {sorted(_METHODS)}", None)
    workdir = paths.workdir()
    if not workdir:
        raise RpcError(1001, "No working directory has been selected.", None)
    nozzle = _resolve_nozzle(params)
    settings = _settings(params.get("settings"))
    folder = Path(workdir) / "Sketches"
    folder.mkdir(parents=True, exist_ok=True)
    name = str(params.get("name") or "").strip()
    raw_path = params.get("path")
    if raw_path:
        target = Path(str(raw_path))
        if not target.is_absolute():
            target = folder / target.name
        if target.suffix.lower() != ".csv":
            target = target.with_suffix(target.suffix + ".csv") if target.suffix else target.with_suffix(".csv")
    else:
        if not name:
            # Headless default (the legacy UI asked the user for a name).
            name = f"OPENRED_{kind.upper()}_CAD.csv"
        if not name.endswith(".csv"):
            name += ".csv"
        target = folder / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not params.get("overwrite"):
        raise RpcError(E_ALREADY_EXISTS, f"El archivo {target.name} ya existe. ¿Quieres sobrescribirlo?", str(target))

    builder = _builder(nozzle)
    try:
        method = getattr(builder, _METHODS[kind])
        method(settings, str(target))
    except (KeyError, ValueError, TypeError) as exc:
        raise RpcError(E_PARAMS, f"Export failed: {exc}", None) from exc
    if not target.is_file():  # builders write atomically; verify the result exists
        raise RpcError(2000, f"Export did not produce {target}", None)
    return {"path": str(target), "kind": kind}


METHODS = {
    "cad.load_nozzle": load_nozzle,
    "cad.views": views,
    "cad.export": export,
}
