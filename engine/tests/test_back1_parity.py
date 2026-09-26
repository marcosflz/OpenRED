"""Golden parity test for :mod:`openred_engine.modules.back_1`.

A short LSM simulation (Tubular grain, KNSU) is run twice with the *same*
initial level set: once with the ported engine class (``on_message`` callback)
and once with the legacy class (fake textbox). Pressure, mass flow, mass, time
(and the level-set field) must match bit-for-bit.
"""

from __future__ import annotations

import numpy as np
import pytest

from openred_engine import store
from openred_engine.modules import back_1 as engine_back_1
from openred_engine.plugins import load_library
from tests import _legacy

pytestmark = pytest.mark.golden

DT = 0.005
DH = 0.0005
# NOTE (legacy bug, preserved on purpose): ``back_1`` builds
# ``self.time = np.round(np.arange(0, int(maxIters * dt) + dt, dt), 8)``, so the
# array has only ``int(maxIters * dt) + 1`` elements. With ``maxIters=40`` and
# ``dt=0.005`` (0.2 s) it has a single sample and the legacy ``run()`` raises
# ``IndexError`` formatting the second console line. The engine keeps the same
# formula, so the parity test uses ``maxIters=400`` (2 s horizon) — the run
# stops early through the P1 range check anyway (``test_time_vector_quirk``
# pins the original behaviour).
MAX_ITERS = 400
R_OUT = 0.016
WORKING_PRECISION = 8
IMAGE_RESOLUTION = 30
SPEC_INPUTS = {"cx_real": 0.005, "cy_real": 0.0, "r_in": 0.005}


def _init_data(a_scale: float) -> dict:
    """KNSU row of the database, as ``front_propDes.get_inputs`` builds it.

    ``a_scale`` reproduces the value used by the task specification
    (``a * 1e-2``); ``a_scale=1.0`` is the production path (the raw database
    value — ``back_1`` scales it by ``1e-2`` internally).
    """
    propellant = next(item for item in store.propellants() if item["Propelente"] == "KNSU")
    return {
        "P0": 1e5,
        "Rt": 0.0065,
        "R2": 0.016,
        "Lc": 0.1,
        "dt": DT,
        "dh": DH,
        "It": MAX_ITERS,
        "a": float(propellant["a"]) * a_scale,
        "n": float(propellant["n"]),
        "R": float(propellant["R"]),
        "T1": float(propellant["T_ad"]),
        "cChar": float(propellant["cChar"]),
        "rho_b": float(propellant["Density"]),
        "P1_min": float(propellant["P1_min"]),
        "P1_max": float(propellant["P1_max"]),
    }


def _phi0():
    grain_class = load_library("GrainLibrary")["Tubular-Grain"]
    grain = grain_class(dict(SPEC_INPUTS), R_OUT, DH)
    return grain.getPhi()


@pytest.mark.parametrize("a_scale", [1e-2, 1.0], ids=["a-times-1e-2", "a-raw"])
def test_lsm_matches_legacy(legacy_env, a_scale):
    _legacy.legacy_cwd()
    _legacy_back_0, legacy_back_1 = _legacy.legacy_back_modules()

    init_data = {**_init_data(a_scale), "dt": DT, "dh": DH, "It": MAX_ITERS}
    phi0 = _phi0()

    engine_messages: list[str] = []
    engine_simulation = engine_back_1.PropellantRegresionLSM(
        on_message=engine_messages.append,
        cancel_check=None,
        dt=DT,
        dh=DH,
        maxIters=MAX_ITERS,
        phi0=phi0,
        init_data=init_data,
        workingPrecision=WORKING_PRECISION,
        image_resolution=IMAGE_RESOLUTION,
    )
    engine_results = engine_simulation.run()

    legacy_textbox = _legacy.FakeTextbox()
    legacy_simulation = legacy_back_1.PropellantRegresionLSM(
        textbox=legacy_textbox,
        dt=DT,
        dh=DH,
        maxIters=MAX_ITERS,
        phi0=phi0,
        init_data=init_data,
        workingPrecision=WORKING_PRECISION,
        image_resolution=IMAGE_RESOLUTION,
    )
    legacy_results = legacy_simulation.run(legacy_textbox)

    # Same console output, same stop point, same numbers.
    assert engine_messages == legacy_textbox.messages
    assert engine_simulation.iterationCount == legacy_simulation.iterationCount
    for key in ("P1", "GP", "MP", "TIME"):
        np.testing.assert_allclose(engine_results[key], legacy_results[key], rtol=1e-12)
    np.testing.assert_array_equal(engine_results["PHI"], legacy_results["PHI"])


def test_time_vector_quirk(legacy_env):
    """The legacy time-vector formula is kept verbatim (see MAX_ITERS note)."""
    init_data = {**_init_data(1.0), "dt": DT, "dh": DH, "It": 40}

    engine_simulation = engine_back_1.PropellantRegresionLSM(
        on_message=lambda message: None,
        dt=DT,
        dh=DH,
        maxIters=40,
        phi0=_phi0(),
        init_data=init_data,
        workingPrecision=WORKING_PRECISION,
        image_resolution=IMAGE_RESOLUTION,
    )
    assert engine_simulation.time.shape == (1,)

    _legacy.legacy_cwd()
    _legacy_back_0, legacy_back_1 = _legacy.legacy_back_modules()
    textbox = _legacy.FakeTextbox()
    legacy_simulation = legacy_back_1.PropellantRegresionLSM(
        textbox=textbox,
        dt=DT,
        dh=DH,
        maxIters=40,
        phi0=_phi0(),
        init_data=init_data,
        workingPrecision=WORKING_PRECISION,
        image_resolution=IMAGE_RESOLUTION,
    )
    with pytest.raises(IndexError):
        engine_simulation.run()
    with pytest.raises(IndexError):
        legacy_simulation.run(textbox)


def test_lsm_matches_legacy_reference_trajectory(legacy_env):
    """Longer trajectory: same geometry as the golden engine fixture.

    ``KNSU-32-RT65.json`` was generated with a centred hole (``cx_real=0``) and
    ``dh=0.0001``; with that geometry the pressure rises and the run does not
    stop early, so 200 iterations of the front update are compared too.
    """
    _legacy.legacy_cwd()
    _legacy_back_0, legacy_back_1 = _legacy.legacy_back_modules()

    init_data = {**_init_data(1.0), "dh": 0.0001, "It": 200}
    grain_class = load_library("GrainLibrary")["Tubular-Grain"]
    phi0 = grain_class({"cx_real": 0.0, "cy_real": 0.0, "r_in": 0.005}, R_OUT, 0.0001).getPhi()

    engine_messages: list[str] = []
    engine_simulation = engine_back_1.PropellantRegresionLSM(
        on_message=engine_messages.append,
        cancel_check=None,
        dt=DT,
        dh=0.0001,
        maxIters=200,
        phi0=phi0,
        init_data=init_data,
        workingPrecision=WORKING_PRECISION,
        image_resolution=IMAGE_RESOLUTION,
    )
    engine_results = engine_simulation.run()

    legacy_textbox = _legacy.FakeTextbox()
    legacy_simulation = legacy_back_1.PropellantRegresionLSM(
        textbox=legacy_textbox,
        dt=DT,
        dh=0.0001,
        maxIters=200,
        phi0=phi0,
        init_data=init_data,
        workingPrecision=WORKING_PRECISION,
        image_resolution=IMAGE_RESOLUTION,
    )
    legacy_results = legacy_simulation.run(legacy_textbox)

    assert engine_simulation.iterationCount == 200
    assert engine_messages == legacy_textbox.messages
    for key in ("P1", "GP", "MP", "TIME"):
        np.testing.assert_allclose(engine_results[key], legacy_results[key], rtol=1e-12)
    np.testing.assert_array_equal(engine_results["PHI"], legacy_results["PHI"])


def test_cancel_check_stops_and_reports(legacy_env):
    messages: list[str] = []
    calls = {"count": 0}

    def cancel_check() -> bool:
        calls["count"] += 1
        return calls["count"] >= 3

    simulation = engine_back_1.PropellantRegresionLSM(
        on_message=messages.append,
        cancel_check=cancel_check,
        dt=DT,
        dh=DH,
        maxIters=MAX_ITERS,
        phi0=_phi0(),
        init_data=_init_data(1.0),
        workingPrecision=WORKING_PRECISION,
        image_resolution=IMAGE_RESOLUTION,
    )
    simulation.run()

    assert simulation.cancelled is True
    assert messages[-1] == "\nSimulación cancelada.\n"
    assert len(messages) == 3  # two iteration lines plus the cancellation line
