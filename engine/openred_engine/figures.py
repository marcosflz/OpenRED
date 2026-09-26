"""matplotlib -> base64 PNG helpers.

The Agg backend is forced at import time: the sidecar is headless (contract
§1 sets ``MPLBACKEND=Agg`` as well) and figures are transferred to the UI as
base64 strings.
"""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

__all__ = ["b64_png_from_figure", "fig_to_b64"]


def fig_to_b64(fig: Figure, dpi: int = 100) -> str:
    """Render ``fig`` to a base64 encoded PNG string and close the figure.

    Accepts classic pyplot figures (``matplotlib.pyplot``). The figure is
    always closed, even if ``savefig`` fails, to avoid leaking memory.
    """
    buffer = io.BytesIO()
    try:
        fig.savefig(buffer, format="png", dpi=dpi)
    finally:
        plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


# Alias kept for readability at call sites that receive an already built figure.
b64_png_from_figure = fig_to_b64
