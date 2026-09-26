"""Tests for the dynamic plugin loader (contract §3.5, R3)."""

from __future__ import annotations

import sys

import numpy as np
import pytest

from openred_engine import paths
from openred_engine.plugins import load_all, load_library, plugin_labels, reload

EXPECTED_LABELS = {
    "X  (m)": "cx_real",
    "Y  (m)": "cy_real",
    "R1 (m)": "r_in",
}


def test_load_grain_library(legacy_env):
    library = load_library("GrainLibrary")
    assert set(library) == {"Tubular-Grain"}

    tubular = library["Tubular-Grain"]
    assert tubular.nozzle_type == "Tubular-Grain"
    assert tubular.__module__ == "openred_engine.plugins.GrainLibrary.TUBULAR"
    assert plugin_labels(tubular) == EXPECTED_LABELS


def test_plugin_labels_returns_a_copy(legacy_env):
    tubular = load_library("GrainLibrary")["Tubular-Grain"]
    labels = plugin_labels(tubular)
    labels["X  (m)"] = "mutated"
    assert plugin_labels(tubular) == EXPECTED_LABELS


def test_square_is_kept_but_not_registered(legacy_env):
    library = load_library("GrainLibrary")
    assert "Square-Grain" not in library
    assert (paths.plugins_dir("GrainLibrary") / "SQUARE.py").is_file()
    assert "openred_engine.plugins.GrainLibrary.SQUARE" in sys.modules


def test_no_bare_global_module_names(legacy_env):
    sys.modules.pop("TUBULAR", None)
    sys.modules.pop("SQUARE", None)
    load_library("GrainLibrary")
    assert "TUBULAR" not in sys.modules
    assert "SQUARE" not in sys.modules


def test_load_all_and_reload(legacy_env):
    reloaded = reload()
    assert set(reloaded) == {"grain", "nozzle"}
    assert reloaded["grain"]["Tubular-Grain"].__module__ == "openred_engine.plugins.GrainLibrary.TUBULAR"
    assert isinstance(reloaded["nozzle"], dict)

    assert load_all()["grain"]["Tubular-Grain"] is reloaded["grain"]["Tubular-Grain"]


def test_plugin_instance_builds_the_level_set(legacy_env):
    tubular = load_library("GrainLibrary")["Tubular-Grain"]
    grain = tubular({"cx_real": 0.005, "cy_real": 0.0, "r_in": 0.005}, 0.016, 0.0005)
    phi, x, y = grain.getPhi()
    assert phi.shape == x.shape == y.shape
    distance = np.hypot(x - 0.005, y - 0.0)
    index = np.unravel_index(np.argmin(distance), phi.shape)
    assert phi[index] < 0  # the propellant hole is inside the grain
    assert phi[0, 0] > 0  # the corners are outside the grain

    center_propHole, prop_geometry = grain.sketchCAD()
    assert center_propHole == (0.005, 0.0)
    assert len(prop_geometry[0]) == 100


@pytest.mark.parametrize("library", ["DoesNotExist"])
def test_missing_library_returns_empty(legacy_env, library):
    assert load_library(library) == {}


def test_plugins_dir_flat_layout_fallback(legacy_env, tmp_path, monkeypatch):
    flat = tmp_path / "install" / "plugins" / "GrainLibrary"
    flat.mkdir(parents=True)
    (flat / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.setenv("OPENRED_RESOURCE_DIR", str(tmp_path / "install"))
    assert paths.plugins_dir("GrainLibrary") == flat
