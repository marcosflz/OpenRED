"""Database service: CRUD over termoquimica/propelente with legacy semantics (D-1..D-4)."""

from __future__ import annotations

from typing import Any

from .. import store
from ..mathutils import convert_to_latex
from ..rpc import RpcError

_COMPONENT_NUMERIC = [
    "MolWeight",
    "Hf0",
    "minColdTemp",
    "maxColdTemp",
    "minHotTemp",
    "maxHotTemp",
    *(f"a{i}_{phase}" for phase in ("cold", "hot") for i in range(1, 6)),
]
_PROPELLANT_NUMERIC = ["T_ad", "MolWeight", "Cp", "Cv", "R", "gamma", "cChar", "Density", "P1_min", "P1_max", "a", "n"]

_COMPONENT_FIELDS = ["Component", *_COMPONENT_NUMERIC]
_PROPELLANT_FIELDS = ["Propelente", *_PROPELLANT_NUMERIC]


def _clean_values(raw: Any, fields: list[str], numeric: list[str]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RpcError(-32602, "values must be an object", None)
    values: dict[str, Any] = {}
    for field in fields:
        if field not in raw:
            continue
        value = raw[field]
        if field in numeric:
            if value in (None, ""):
                raise RpcError(-32602, f"Field '{field}' is required", None)
            try:
                values[field] = float(str(value).replace(",", "."))
            except (TypeError, ValueError) as exc:
                raise RpcError(-32602, f"Field '{field}' is not numeric: {value!r}", None) from exc
        else:
            values[field] = "" if value is None else str(value)
    return values


def _with_latex(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in items:
        item["latex"] = convert_to_latex(item.get("Component") or "")
    return items


def components_list(params: dict[str, Any], ctx) -> dict[str, Any]:
    return {"items": _with_latex(store.components())}


def components_add(params: dict[str, Any], ctx) -> dict[str, Any]:
    values = _clean_values(params.get("values"), _COMPONENT_FIELDS, _COMPONENT_NUMERIC)
    if not values.get("Component"):
        raise RpcError(-32602, "Component is required", None)
    store.insert_component(values)
    return {"items": _with_latex(store.components())}


def components_edit(params: dict[str, Any], ctx) -> dict[str, Any]:
    record_id = params.get("id")
    if record_id is None:
        raise RpcError(-32602, "id is required", None)
    values = _clean_values(params.get("values"), _COMPONENT_FIELDS, _COMPONENT_NUMERIC)
    store.update_component(int(record_id), values)
    return {"items": _with_latex(store.components())}


def components_delete(params: dict[str, Any], ctx) -> dict[str, Any]:
    record_id = params.get("id")
    if record_id is None:
        raise RpcError(-32602, "id is required", None)
    store.delete_component(int(record_id))
    return {"items": _with_latex(store.components())}


def propellants_list(params: dict[str, Any], ctx) -> dict[str, Any]:
    return {"items": store.propellants()}


def propellants_add(params: dict[str, Any], ctx) -> dict[str, Any]:
    values = _clean_values(params.get("values"), _PROPELLANT_FIELDS, _PROPELLANT_NUMERIC)
    if not values.get("Propelente"):
        raise RpcError(-32602, "Propelente is required", None)
    store.insert_propellant(values)
    return {"items": store.propellants()}


def propellants_edit(params: dict[str, Any], ctx) -> dict[str, Any]:
    record_id = params.get("id")
    if record_id is None:
        raise RpcError(-32602, "id is required", None)
    values = _clean_values(params.get("values"), _PROPELLANT_FIELDS, _PROPELLANT_NUMERIC)
    store.update_propellant(int(record_id), values)
    return {"items": store.propellants()}


def propellants_delete(params: dict[str, Any], ctx) -> dict[str, Any]:
    record_id = params.get("id")
    if record_id is None:
        raise RpcError(-32602, "id is required", None)
    store.delete_propellant(int(record_id))
    return {"items": store.propellants()}


def propellants_burning_rate(params: dict[str, Any], ctx) -> dict[str, Any]:
    name = params.get("name")
    if not name:
        raise RpcError(-32602, "name is required", None)
    n_points = int(params.get("n_points") or 1000)
    rows = [row for row in store.propellants() if row.get("Propelente") == name]
    if not rows:
        raise RpcError(-32602, f"Propellant not found: {name}", None)
    row = rows[0]
    a = float(row["a"])
    n = float(row["n"])
    p_min = float(row["P1_min"])
    p_max = float(row["P1_max"])
    import numpy as np

    pressures = np.linspace(p_min, p_max, n_points)
    rates = a * pressures**n
    return {
        "P": pressures.tolist(),
        "r": rates.tolist(),
        "a": a,
        "n": n,
        "P1_min": p_min,
        "P1_max": p_max,
    }


def clean_name(params: dict[str, Any], ctx) -> dict[str, Any]:
    from ..mathutils import get_clean_component_name

    return {"clean": get_clean_component_name(str(params.get("name") or ""))}


METHODS = {
    "db.components.list": components_list,
    "db.components.add": components_add,
    "db.components.edit": components_edit,
    "db.components.delete": components_delete,
    "db.propellants.list": propellants_list,
    "db.propellants.add": propellants_add,
    "db.propellants.edit": propellants_edit,
    "db.propellants.delete": propellants_delete,
    "db.propellants.burning_rate": propellants_burning_rate,
    "db.clean_name": clean_name,
}
