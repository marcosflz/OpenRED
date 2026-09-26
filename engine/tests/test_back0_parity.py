"""Golden parity test for :mod:`openred_engine.modules.back_0`.

Same inputs as ``legacy/workingDirectory/config.json`` (tab_0) are run through
the ported module and through the legacy module imported in-process with
``tests/_legacy.py``; the full result tuple must match (``rtol=1e-12``).
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from openred_engine.modules import back_0 as engine_back_0
from tests import _legacy

pytestmark = pytest.mark.golden

# Verified reference value (matches legacy/database.db propelente.KNSU.T_ad).
EXPECTED_T_AD = 1790.9602394045733


@pytest.fixture
def tab0_scenario(legacy_env):
    """Reactants, products and settings of ``config.json`` tab_0."""
    _legacy.legacy_cwd()
    tab0 = json.loads(_legacy.CONFIG_JSON.read_text(encoding="utf-8"))["tabs"]["tab_0"]
    reac = [(float(moles), name) for moles, name in tab0["reactivos"]]
    prod = [(float(moles), name) for moles, name in tab0["productos"]]
    return reac, prod, float(tab0["initial_temp"]), float(tab0["temp_guess"]), float(tab0["temp_Int_step"])


def test_adiabatic_temp_matches_legacy(tab0_scenario):
    reac, prod, t0, t_guess, h_step = tab0_scenario
    legacy_back_0, _ = _legacy.legacy_back_modules()

    result = engine_back_0.adiabaticTemp_calc(reac, prod, t0, t_guess, h_step)
    expected = legacy_back_0.adiabaticTemp_calc(reac, prod, t0, t_guess, h_step)

    assert result[0] == pytest.approx(EXPECTED_T_AD, rel=1e-12)
    np.testing.assert_allclose(np.asarray(result, dtype=float), np.asarray(expected, dtype=float), rtol=1e-12)


def test_polynomial_cp_matches_legacy(tab0_scenario):
    legacy_back_0, _ = _legacy.legacy_back_modules()
    component = "KNO3 (S)"
    engine_cp = engine_back_0.PolynomialCp(component)
    legacy_cp = legacy_back_0.PolynomialCp(component)
    for temperature in (298.0, 600.0, 1500.0):
        assert engine_cp.cp(temperature) == legacy_cp.cp(temperature)


def test_invalid_step_raises_value_error(tab0_scenario):
    reac, prod, t0, t_guess, _ = tab0_scenario
    with pytest.raises(ValueError, match="Invalid integration step value."):
        engine_back_0.adiabaticTemp_calc(reac, prod, t0, t_guess, 0.0)


def test_missing_component_raises_value_error(tab0_scenario):
    with pytest.raises(ValueError, match="No data found for component: Unobtainium"):
        engine_back_0.adiabaticTemp_calc([(1.0, "Unobtainium")], [(1.0, "N2")], 293.0, 1500.0, 1.0)
