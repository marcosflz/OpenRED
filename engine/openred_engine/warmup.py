"""Eager import of heavy third-party modules.

scipy's lazy submodule loader is not thread-safe: two request threads importing
``scipy.interpolate`` for the first time at the same moment can deadlock. The
engine serves each request in its own thread, so all heavy imports are performed
once, single-threaded, before the RPC loop starts.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("openred_engine")


def warm_up() -> None:
    """Import numpy/scipy/matplotlib/pyserial before any request thread exists."""
    import matplotlib
    import numpy  # noqa: F401
    import scipy.interpolate  # noqa: F401
    import scipy.optimize  # noqa: F401

    matplotlib.use("Agg", force=True)
    import matplotlib.cm  # noqa: F401
    import matplotlib.patches  # noqa: F401
    import matplotlib.pyplot  # noqa: F401

    try:
        import serial  # noqa: F401
        import serial.tools.list_ports  # noqa: F401
    except ImportError:  # pragma: no cover - pyserial is a core dependency
        logger.warning("pyserial is not available; Test Bed hardware will be disabled")
    logger.info("Engine warm-up complete")
