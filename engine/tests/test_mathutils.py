"""Unit tests for :mod:`openred_engine.mathutils` (and the figure helper)."""

from __future__ import annotations

import base64
import json
import math

import matplotlib.pyplot as plt
import numpy as np
import pytest

from openred_engine import figures, mathutils


def test_newton_raph_converges():
    root = mathutils.newtonRaph(lambda x: x**2 - 2, 1.0, 1e-12, 100, 1e-5)
    assert root == pytest.approx(math.sqrt(2), rel=1e-10)


def test_newton_raph_raises_on_zero_derivative():
    with pytest.raises(ValueError, match="Zero derivative"):
        mathutils.newtonRaph(lambda x: 5.0, 0.0, 1e-9, 10, 1e-5)


def test_newton_raph_raises_when_not_converging():
    with pytest.raises(ValueError, match="did not converge"):
        mathutils.newtonRaph(lambda x: x**2 - 2, 100.0, 1e-30, 1, 1e-5)


def test_integration_trapezoid():
    value = mathutils.integration(lambda x: x**2, 0.0, 1.0, 1e-3)
    assert value == pytest.approx(1.0 / 3.0, abs=2e-3)


def test_discrete_integration():
    assert mathutils.discreteIntegration([0.0, 1.0, 2.0], [0.0, 1.0, 2.0]) == pytest.approx(2.0)


def test_temp_schemes():
    f = [lambda u: u]
    u0 = np.array([1.0])
    assert mathutils.TempSchemes.Euler(f, u0, 0.1)[0] == pytest.approx(1.1)
    assert mathutils.TempSchemes.Heun(f, u0, 0.1)[0] == pytest.approx(1.105)
    assert mathutils.TempSchemes.RK4(f, u0, 0.1)[0] == pytest.approx(1.1051708333333333)


def test_numerical_derivative():
    x = np.array([0.0, 1.0, 2.0, 3.0])
    df = mathutils.numerical_derivative(x, x**2)
    np.testing.assert_allclose(df, [1.0, 2.0, 4.0, 5.0])
    with pytest.raises(ValueError):
        mathutils.numerical_derivative(x, x[:2])


def test_solve_ode_system_euler_and_errors():
    sol, t = mathutils.solve_ode_system([lambda u: np.array([1.0])], np.array([0.0]), 0.1, "Euler", 1.0)
    assert sol[-1][0] == pytest.approx(1.0)
    assert t[-1] == pytest.approx(1.0)

    with pytest.raises(ValueError, match="Euler"):
        mathutils.solve_ode_system([lambda u: u], np.array([0.0]), 0.1, "Nope", 1.0)

    with pytest.raises(RuntimeError, match="divergence"):
        mathutils.solve_ode_system([lambda u: np.array([1e9])], np.array([0.0]), 0.1, "Euler", 1.0)

    with pytest.raises(RuntimeError, match="custom stop condition"):
        mathutils.solve_ode_system([lambda u: u], np.array([0.0]), 0.1, "Euler", 1.0, stop_conditions=[lambda u: True])


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("-3.2", True),
        (".5", True),
        ("1e5", True),
        ("-3.2E-4", True),
        ("1,5", False),
        ("abc", False),
        ("", False),
        ("1e", False),
    ],
)
def test_validate_scientific_notation(value, expected):
    assert mathutils.validate_scientific_notation(value) is expected


def test_convert_to_latex():
    assert mathutils.convert_to_latex("C12H22O11 (Solid)") == "C_{12}H_{22}O_{11}"


def test_get_clean_component_name():
    assert mathutils.get_clean_component_name("H2O (12)") == "H2O"
    assert mathutils.get_clean_component_name("KNSU (1)") == "KNSU"
    assert mathutils.get_clean_component_name("KNO3 (S)") == "KNO3 (S)"


def test_get_serial_values():
    assert mathutils.getSerialValues("t(s): 0.025 F(kg): 0.049 T(K): 301.4") == (0.025, 0.049, 301.4)
    assert mathutils.getSerialValues("noise") is None


def test_get_circle_points():
    x, y = mathutils.get_circle_points(2.0, center=(1.0, 1.0), num_points=4)
    assert x.shape == y.shape == (4,)
    np.testing.assert_allclose(np.hypot(x - 1.0, y - 1.0), 2.0)
    assert (x[0], y[0]) == (3.0, 1.0)


def test_write_json_atomic(tmp_path):
    target = tmp_path / "config.json"
    payload = {"tabs": {"tab_0": {"initial_temp": "293"}}}
    mathutils.write_json_atomic(target, payload)
    assert mathutils.read_json(target) == payload
    assert json.loads(target.read_text(encoding="utf-8")) == payload
    assert not (tmp_path / "config.json.tmp").exists()


def test_write_text_atomic(tmp_path):
    target = tmp_path / "notes.txt"
    mathutils.write_text_atomic(target, "hello")
    assert target.read_text(encoding="utf-8") == "hello"
    assert not (tmp_path / "notes.txt.tmp").exists()


def test_fig_to_b64_returns_png_and_closes_the_figure():
    fig, ax = plt.subplots()
    ax.plot([0.0, 1.0], [0.0, 1.0])
    encoded = figures.fig_to_b64(fig, dpi=50)
    assert base64.b64decode(encoded).startswith(b"\x89PNG\r\n\x1a\n")
    assert plt.get_fignums() == []
    assert figures.b64_png_from_figure is figures.fig_to_b64
