"""User settings persistence."""

from __future__ import annotations

import json
from pathlib import Path

from app.backend.core.config import get_app_config, get_project_root
from platform_utils import (
    default_captures_save_path,
    default_records_save_path,
    resolve_settings_path,
)


class SettingsService:
    def __init__(self) -> None:
        app_cfg = get_app_config()
        settings_cfg = app_cfg.get("settings", {})
        default_path = resolve_settings_path(
            settings_cfg.get("default_save_path"),
            default_captures_save_path(),
        )
        default_record_path = resolve_settings_path(
            settings_cfg.get("default_record_save_path"),
            default_records_save_path(),
        )
        self._settings_file = get_project_root() / "data" / "temp" / "settings.json"
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        loaded = self._load_settings(default_path, default_record_path)
        self._save_path = loaded["save_path"]
        self._record_save_path = loaded["record_save_path"]

    def _load_settings(self, default_path: str, default_record_path: str) -> dict[str, str]:
        if not self._settings_file.exists():
            return {"save_path": default_path, "record_save_path": default_record_path}
        try:
            data = json.loads(self._settings_file.read_text(encoding="utf-8"))
            return {
                "save_path": str(data.get("save_path", default_path)),
                "record_save_path": str(
                    data.get("record_save_path", default_record_path)
                ),
            }
        except (json.JSONDecodeError, OSError):
            return {"save_path": default_path, "record_save_path": default_record_path}

    def _persist(self) -> None:
        self._settings_file.write_text(
            json.dumps(
                {
                    "save_path": self._save_path,
                    "record_save_path": self._record_save_path,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @property
    def save_path(self) -> str:
        return self._save_path

    @property
    def record_save_path(self) -> str:
        return self._record_save_path

    def get_all(self) -> dict[str, str]:
        return {
            "savePath": self._save_path,
            "recordSavePath": self._record_save_path,
        }

    def update_save_path(self, path: str) -> None:
        self._save_path = path
        self._persist()

    def update_record_save_path(self, path: str) -> None:
        self._record_save_path = path
        self._persist()
