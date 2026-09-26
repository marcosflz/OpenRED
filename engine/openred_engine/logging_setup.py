"""Engine logging: JSON lines to stderr (for the Rust supervisor) and a rotating file."""

from __future__ import annotations

import json
import logging
import logging.handlers
import sys
from typing import Any

from . import paths


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_configured = False


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    global _configured
    logger = logging.getLogger("openred_engine")
    if _configured:
        return logger

    logger.setLevel(level)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(JsonFormatter())
    logger.addHandler(stderr_handler)

    try:
        logs_dir = paths.data_dir() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "engine.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)
    except OSError:  # read-only data dir: stderr is enough
        logger.warning("Could not open engine log file")
    _configured = True
    return logger
