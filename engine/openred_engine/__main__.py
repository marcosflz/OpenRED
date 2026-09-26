"""Entry point: ``python -s -X utf8 -m openred_engine`` (JSON-RPC over stdio)."""

from __future__ import annotations

import sys


def main() -> int:
    # Keep stdout pristine: it is the protocol channel.
    from . import paths  # noqa: F401 - sets MPLCONFIGDIR as an import side effect
    from .logging_setup import setup_logging

    logger = setup_logging()
    try:
        from . import store
        from .rpc import RpcServer
        from .services import build_dispatcher
        from .warmup import warm_up

        store.initialize_database()
        warm_up()
        server = RpcServer(sys.stdin, sys.stdout, build_dispatcher)
        server.serve_forever()
        return 0
    except BrokenPipeError:
        return 0
    except Exception as exc:  # noqa: BLE001 - top-level boundary
        logger.exception("Fatal error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
