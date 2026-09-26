"""Registro, etiquetas y paridad numérica de los plugins de tobera del motor.

- ``NozzleLibrary`` expone los dos tipos del legacy (``TOPN-BN`` y ``CONE-LN``)
  con las etiquetas de entrada exactas; se usa
  ``openred_engine.plugins.loader.load_library`` (ruta de producción) y, si el
  loader no existiese, se importarían los módulos directamente.
- Los tests ``golden`` comparan ``calculated_results`` y ``opPoint_plot`` de los
  solvers del motor contra el legacy importado con ``tests._legacy``.
"""

import importlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg", force=True)

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_WORKDIR = REPO_ROOT / "legacy" / "workingDirectory"
NOZZLE_FIXTURE = LEGACY_WORKDIR / "Nozzles" / "BN1.json"
ENGINE_FIXTURE = LEGACY_WORKDIR / "Engines" / "KNSU-32-RT65.json"

EXPECTED_CLASSES = {
    "TOPN-BN": "BellNozzle",
    "CONE-LN": "ConeNozzle",
}

EXPECTED_INPUT_LABELS = {
    "TOPN-BN": {
        "K (Factor Garganta)": "TOP-BN_k",
        "theta_t (deg)": "TOP-BN_theta_t",
        "theta_e (deg)": "TOP-BN_theta_e",
        "% (L. Cono)": "TOP-BN_cone_length_percent",
    },
    "CONE-LN": {
        "K (Factor Garganta)": "CONE-LN_k",
        "theta_t (deg)": "CONE-LN_theta_t",
    },
}

# Etiquetas de resultado literales del legacy (el typo de CONE-LN se conserva).
EXPECTED_RESULT_LABELS = {
    "TOPN-BN": [
        "DP. Thrust (kg)", "Med. Thrust (kg)",
        "CF (DP.)", "CF (Med.)",
        "Vs (DP.)", "Vs (Med.)",
        "Ts (DP.)", "Ts (Med.)",
        "Ps (DP.)", "Ps (Med.)",
        "It", "Isp",
        "AR", "MS",
        "Longitud (m)",
        "Rt (m)", "R2 (m)",
    ],
    "CONE-LN": [
        "DP. Thrust (kg)1", "Med. Thrust (kg)",
        "CF (DP.)", "CF (Med.)",
        "Vs (DP.)", "Vs (Med.)",
        "Ts (DP.)", "Ts (Med.)",
        "Ps (DP.)", "Ps (Med.)",
        "It", "Isp",
        "AR", "MS",
        "Longitud (m)",
        "Rt (m)", "R2 (m)",
    ],
}

# (módulo legacy, clase, specInputs) — los mismos valores que `config.json` tab_2.
SOLVERS = [
    (
        "back_modules.NozzleLibrary.TOPBN",
        "BellNozzle",
        {
            "TOP-BN_k": 0.25,
            "TOP-BN_theta_t": 30.0,
            "TOP-BN_theta_e": 6.0,
            "TOP-BN_cone_length_percent": 1.0,
        },
    ),
    (
        "back_modules.NozzleLibrary.LAVAL_CONE",
        "ConeNozzle",
        {"CONE-LN_k": 0.25, "CONE-LN_theta_t": 15.0},
    ),
]

# Barrido de puntos de operación que cubre los regímenes de `opPoint_plot`.
OP_POINT_SWEEP = (1e4, 5e4, 8e4, 9.5e4, 1e5, 1.05e5, 1.5e5, 3e5)


def _direct_import():
    from openred_engine.plugins.NozzleLibrary import LAVAL_CONE, TOPBN

    return {"CONE-LN": LAVAL_CONE.ConeNozzle, "TOPN-BN": TOPBN.BellNozzle}


def _as_mapping(loaded):
    if isinstance(loaded, dict):
        return loaded
    return {cls.nozzle_type: cls for cls in loaded if hasattr(cls, "nozzle_type")}


def load_nozzle_library():
    try:
        from openred_engine.plugins.loader import load_library
    except ImportError:
        return _direct_import()
    return _as_mapping(load_library("NozzleLibrary"))


def _assert_solver_parity(legacy, engine):
    legacy_data, legacy_time, legacy_geo, legacy_pr = legacy.calculated_results()
    engine_data, engine_time, engine_geo, engine_pr = engine.calculated_results()

    np.testing.assert_allclose(engine_data, legacy_data, rtol=1e-12, atol=0)
    for legacy_array, engine_array in zip(legacy_time, engine_time):
        np.testing.assert_allclose(engine_array, legacy_array, rtol=1e-12, atol=0, equal_nan=True)
    for legacy_array, engine_array in zip(legacy_geo, engine_geo):
        np.testing.assert_allclose(engine_array, legacy_array, rtol=1e-12, atol=0, equal_nan=True)
    np.testing.assert_allclose(engine_pr, legacy_pr, rtol=1e-12, atol=0, equal_nan=True)

    for p_off in OP_POINT_SWEEP:
        legacy_point = legacy.opPoint_plot(p_off, legacy.P0)
        engine_point = engine.opPoint_plot(p_off, engine.P0)
        for key in ("Mach", "PR", "x"):
            np.testing.assert_allclose(
                engine_point[key], legacy_point[key], rtol=1e-12, atol=0, equal_nan=True
            )
        np.testing.assert_allclose(engine_point["Pe"], legacy_point["Pe"], rtol=1e-12, atol=0, equal_nan=True)
        np.testing.assert_allclose(engine_point["F"], legacy_point["F"], rtol=1e-12, atol=0, equal_nan=True)


@pytest.fixture(scope="module")
def nozzle_library():
    return load_nozzle_library()


@pytest.fixture()
def legacy_plugins_env(legacy_env):
    """CWD temporal con ``database.db`` + ``temp_dir.txt`` y stubs del legacy."""
    from tests import _legacy

    _legacy._install_stubs()
    cwd = _legacy.legacy_cwd()
    (cwd / "temp_dir.txt").write_text(str(LEGACY_WORKDIR), encoding="utf-8")


@pytest.mark.parametrize("nozzle_type", sorted(EXPECTED_CLASSES))
def test_registered_nozzle_types(nozzle_library, nozzle_type):
    assert nozzle_type in nozzle_library
    cls = nozzle_library[nozzle_type]
    assert cls.__name__ == EXPECTED_CLASSES[nozzle_type]
    assert cls.nozzle_type == nozzle_type


@pytest.mark.parametrize("nozzle_type", sorted(EXPECTED_INPUT_LABELS))
def test_input_labels_exact(nozzle_library, nozzle_type):
    assert nozzle_library[nozzle_type].get_input_labels() == EXPECTED_INPUT_LABELS[nozzle_type]


@pytest.mark.parametrize("nozzle_type", sorted(EXPECTED_RESULT_LABELS))
def test_result_labels_exact(nozzle_library, nozzle_type):
    assert nozzle_library[nozzle_type].get_result_labels() == EXPECTED_RESULT_LABELS[nozzle_type]


def test_only_expected_types_registered(nozzle_library):
    assert set(nozzle_library) == set(EXPECTED_CLASSES)


@pytest.mark.golden
@pytest.mark.parametrize("legacy_module,class_name,spec_inputs", SOLVERS)
def test_solver_matches_legacy(legacy_plugins_env, legacy_module, class_name, spec_inputs):
    inputs = json.loads(NOZZLE_FIXTURE.read_text(encoding="utf-8"))["Inputs"]
    args = (bool(inputs["DefaultCheck"]), inputs["P1"], inputs["n"], 0.0)

    legacy_cls = getattr(importlib.import_module(legacy_module), class_name)
    engine_cls = next(cls for cls in _direct_import().values() if cls.__name__ == class_name)

    legacy = legacy_cls(*args, inputs["EngineConfig"], spec_inputs)
    engine = engine_cls(*args, str(ENGINE_FIXTURE), spec_inputs)

    _assert_solver_parity(legacy, engine)
