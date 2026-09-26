"""Paridad dorada del generador CAD (``back_2``) contra el legacy.

Se ejecuta el módulo original ``legacy/back_modules/back_2.py`` con los stubs
compartidos de ``tests._legacy`` (``customtkinter`` simulado; tkinter sí existe
en el entorno del motor) y un CWD temporal con ``temp_dir.txt``, y se comparan:

- ``get_sketch`` para los bocetos de motor/cubierta y los cuatro bocetos que
  componen las herramientas (``MouldCover``, ``MouldCoverFix``, ``NutUp``,
  ``NutDown``); ``'Tools'`` no es una clave válida de ``get_sketch`` en el
  legacy (``export_tools`` compone esos cuatro), y el puerto reproduce el mismo
  error.
- Los CSV de ``export_engine``/``export_cover``/``export_tools`` byte a byte.
"""

import json
from pathlib import Path

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg", force=True)

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_ROOT = REPO_ROOT / "legacy"
LEGACY_WORKDIR = LEGACY_ROOT / "workingDirectory"
NOZZLE_FILE = "BN1.json"
ENGINE_FILE = "KNSU-32-RT65.json"

# Claves de `entries` (se convierten a float) y de `checkboxes` (bool) tal como
# las produce `front_cad.collect_widget_values`.
CHECK_KEYS = {
    "on_Cartridge",
    "on_Propellant",
    "on_Engine",
    "on_Cover",
    "on_CoverCast1",
    "on_CoverCast2",
    "on_CastBolt",
    "on_Mould",
    "on_CastNut",
}

SKETCHES = [
    "Engine",
    "Cover",
    "Cartridge",
    "Propellant",
    "MouldCover",
    "MouldCoverFix",
    "Mould",
    "ExtraMould",
    "NutUp",
    "NutDown",
]

EXPORT_KINDS = ["engine", "cover", "tools"]


def _install_legacy_stubs():
    """Instala los stubs del legacy con el helper compartido ``tests._legacy``.

    ``_install_stubs`` coloca ``legacy/`` en ``sys.path``, crea el stub de
    ``customtkinter`` (tkinter sí está presente) y neutraliza
    ``tkinter.messagebox``.
    """
    from tests import _legacy

    _legacy._install_stubs()


def _user_settings():
    config = json.loads((LEGACY_WORKDIR / "config.json").read_text(encoding="utf-8"))
    settings = {}
    for key, value in config["tabs"]["tab_3"].items():
        if key == "NozzleConfig":
            continue
        if key == "type":
            settings[key] = value
        elif key in CHECK_KEYS:
            settings[key] = bool(value)
        else:
            settings[key] = float(value)
    return settings


@pytest.fixture()
def builders(tmp_path, monkeypatch):
    """Instancia el builder legacy (con CWD simulado) y el del motor."""
    cwd = tmp_path / "legacy_cwd"
    cwd.mkdir()
    (cwd / "temp_dir.txt").write_text(str(LEGACY_WORKDIR), encoding="utf-8")
    monkeypatch.chdir(cwd)

    _install_legacy_stubs()
    import back_modules.back_2 as legacy_back_2

    from openred_engine.modules.back_2 import EngineCADBuilder_ConventionalNozzle

    legacy = legacy_back_2.EngineCADBuilder_ConventionalNozzle(NOZZLE_FILE)
    engine = EngineCADBuilder_ConventionalNozzle(str(LEGACY_WORKDIR / "Nozzles" / NOZZLE_FILE))
    return legacy, engine


@pytest.mark.golden
@pytest.mark.parametrize("sketch", SKETCHES)
def test_get_sketch_parity(builders, sketch):
    legacy, engine = builders
    settings = _user_settings()

    legacy_x, legacy_y = legacy.get_sketch(settings, sketch)
    engine_x, engine_y = engine.get_sketch(settings, sketch)

    assert len(legacy_x) == len(engine_x)
    assert len(legacy_y) == len(engine_y)
    np.testing.assert_allclose(engine_x, legacy_x, rtol=1e-12, atol=0)
    np.testing.assert_allclose(engine_y, legacy_y, rtol=1e-12, atol=0)


@pytest.mark.golden
def test_tools_is_not_a_get_sketch_key(builders):
    """Paridad del borde: 'Tools' tampoco es válido en el puerto."""
    legacy, engine = builders
    settings = _user_settings()

    with pytest.raises(UnboundLocalError):
        legacy.get_sketch(settings, sketch="Tools")
    with pytest.raises(UnboundLocalError):
        engine.get_sketch(settings, sketch="Tools")


@pytest.mark.golden
@pytest.mark.parametrize("kind", EXPORT_KINDS)
def test_export_parity_bytes(builders, tmp_path, kind):
    legacy, engine = builders
    settings = _user_settings()

    legacy_path = tmp_path / f"legacy_{kind}.csv"
    engine_path = tmp_path / f"engine_{kind}.csv"
    getattr(legacy, f"export_{kind}")(settings, str(legacy_path))
    getattr(engine, f"export_{kind}")(settings, str(engine_path))

    legacy_bytes = legacy_path.read_bytes()
    assert engine_path.read_bytes() == legacy_bytes
    assert legacy_bytes.splitlines()[0] == b"Sketch,Plane,x,y,z"
    assert legacy_bytes.endswith(b"\r\n")


@pytest.mark.golden
def test_export_engine_does_not_need_temp_dir(tmp_path, monkeypatch):
    """El puerto no depende de temp_dir.txt/CWD (el legacy sí)."""
    monkeypatch.chdir(tmp_path)
    from openred_engine.modules.back_2 import EngineCADBuilder_ConventionalNozzle

    engine = EngineCADBuilder_ConventionalNozzle(str(LEGACY_WORKDIR / "Nozzles" / NOZZLE_FILE))
    out = tmp_path / "engine.csv"
    engine.export_engine(_user_settings(), str(out))

    assert out.read_bytes().splitlines()[0] == b"Sketch,Plane,x,y,z"
    assert engine.engineUsed == ENGINE_FILE  # el motor se resolvió junto al JSON de tobera
