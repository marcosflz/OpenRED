"""User plugins: grain geometries and nozzle solvers.

See :mod:`openred_engine.plugins.loader` for the dynamic loading contract
(classes with a ``nozzle_type`` attribute, inherited from legacy R3).
"""

from openred_engine.plugins.loader import load_all, load_library, plugin_labels, reload

__all__ = ["load_all", "load_library", "plugin_labels", "reload"]
