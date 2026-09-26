"""OpenRED headless calculation engine.

The package is intentionally import-light: importing ``openred_engine`` must not
pull numpy/scipy/matplotlib so the JSON-RPC sidecar can start quickly. Import the
submodule you need (``paths``, ``store``, ``mathutils``, ``figures``, ...).
"""

__version__ = "0.2.0"

__all__ = ["__version__"]
