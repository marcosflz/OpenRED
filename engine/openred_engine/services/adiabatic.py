"""Adiabatic flame temperature service (T0)."""

from __future__ import annotations

from typing import Any

from ..modules import back_0
from ..rpc import E_PARAMS, RpcError

_RESULT_KEYS = ["tSol", "molWeight", "cp", "cv", "R", "gamma", "cChar"]


def _moles(value: Any) -> float:
    """Legacy parity: empty/non-numeric moles degrade to 0 instead of raising (T0-4)."""
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def _mixture(raw: Any, label: str) -> list[tuple[float, str]]:
    if not isinstance(raw, list):
        raise RpcError(E_PARAMS, f"{label} must be a list", None)
    mixture: list[tuple[float, str]] = []
    for item in raw:
        if isinstance(item, dict):
            mixture.append((_moles(item.get("moles")), str(item.get("component") or "")))
        elif isinstance(item, list | tuple) and len(item) >= 2:
            mixture.append((_moles(item[0]), str(item[1])))
        else:
            raise RpcError(E_PARAMS, f"Invalid {label} entry: {item!r}", None)
    return mixture


def calculate(params: dict[str, Any], ctx) -> dict[str, Any]:
    reac = _mixture(params.get("reac"), "reac")
    prod = _mixture(params.get("prod"), "prod")
    if not reac or not prod:
        raise RpcError(E_PARAMS, "reac and prod must not be empty", None)
    t0 = _moles(params.get("t0"))
    t_guess = _moles(params.get("tGuess"))
    h_step = _moles(params.get("hStep"))
    if h_step <= 0:
        # Legacy message kept for parity (T0-4).
        raise RpcError(E_PARAMS, "Invalid integration step value.", None)
    try:
        output = back_0.adiabaticTemp_calc(reac, prod, t0, t_guess, h_step)
    except ValueError as exc:
        raise RpcError(E_PARAMS, str(exc), None) from exc
    if output is None:
        raise RpcError(E_PARAMS, "Adiabatic temperature calculation failed.", None)
    return dict(zip(_RESULT_KEYS, (float(value) for value in output)))


def component_info(params: dict[str, Any], ctx) -> dict[str, Any]:
    from ..store import component_row

    name = str(params.get("component") or "")
    row = component_row(name)
    if row is None:
        raise RpcError(E_PARAMS, f"No data found for component: {name}", None)
    return {
        key: row.get(key)
        for key in (
            "MolWeight",
            "Hf0",
            "minColdTemp",
            "maxColdTemp",
            "minHotTemp",
            "maxHotTemp",
        )
    }


def save_propellant(params: dict[str, Any], ctx) -> dict[str, Any]:
    from . import db

    return db.propellants_add(params, ctx)


METHODS = {
    "adiabatic.calculate": calculate,
    "adiabatic.component_info": component_info,
    "adiabatic.save_propellant": save_propellant,
}
