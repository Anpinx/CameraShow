"""Load YAML configuration files."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _load_yaml(relative_path: str) -> dict[str, Any]:
    path = PROJECT_ROOT / relative_path
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


@lru_cache
def get_app_config() -> dict[str, Any]:
    return _load_yaml("configs/app.yaml")


@lru_cache
def get_camera_config() -> dict[str, Any]:
    return _load_yaml("configs/camera.yaml")


@lru_cache
def get_video_config() -> dict[str, Any]:
    return _load_yaml("configs/video.yaml")


@lru_cache
def get_tools_config() -> dict[str, Any]:
    return _load_yaml("configs/tools.yaml")


def get_project_root() -> Path:
    return PROJECT_ROOT


def resolve_path(relative_path: str) -> Path:
    path = PROJECT_ROOT / relative_path
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_api_base_url() -> str:
    app_cfg = get_app_config().get("app", {})
    host = app_cfg.get("host", "127.0.0.1")
    port = int(app_cfg.get("port", 8000))
    return f"http://{host}:{port}"
