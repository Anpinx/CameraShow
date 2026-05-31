"""Logging setup."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.backend.core.config import get_app_config, resolve_path


def configure_logging() -> None:
    app_cfg = get_app_config()
    logging_cfg = app_cfg.get("logging", {})
    level_name = str(logging_cfg.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    log_dir = resolve_path(str(logging_cfg.get("dir", "logs")))
    log_file = log_dir / str(logging_cfg.get("filename", "camera_demo.log"))

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=int(logging_cfg.get("max_bytes", 10_485_760)),
        backupCount=int(logging_cfg.get("backup_count", 5)),
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
