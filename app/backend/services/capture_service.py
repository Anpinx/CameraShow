"""Capture storage and image serving helpers."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image

from app.backend.core.config import get_api_base_url, get_app_config, resolve_path
from app.backend.schemas.camera import CaptureItem
from sdk_adapter.exceptions import CaptureError


class CaptureService:
    def __init__(self) -> None:
        app_cfg = get_app_config()
        self._captures_dir = resolve_path(str(app_cfg.get("paths", {}).get("captures", "data/captures")))
        self._index_file = self._captures_dir / "index.json"
        self._max_captures = int(app_cfg.get("settings", {}).get("max_captures", 10))
        self._video_config = {}
        self._load_video_config()
        self._items: list[dict[str, Any]] = self._load_index()

    def _load_video_config(self) -> None:
        from app.backend.core.config import get_video_config

        self._video_config = get_video_config().get("video", {})

    def _load_index(self) -> list[dict[str, Any]]:
        if not self._index_file.exists():
            return []
        try:
            return json.loads(self._index_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save_index(self) -> None:
        self._index_file.write_text(
            json.dumps(self._items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _build_urls(self, capture_id: str) -> tuple[str, str]:
        base = get_api_base_url()
        full_url = f"{base}/api/media/captures/{capture_id}/full"
        thumb_url = f"{base}/api/media/captures/{capture_id}/thumbnail"
        return full_url, thumb_url

    def _to_item(self, record: dict[str, Any]) -> CaptureItem:
        full_url, thumb_url = self._build_urls(record["id"])
        return CaptureItem(
            id=record["id"],
            filename=record["filename"],
            thumbnailUrl=thumb_url,
            fullUrl=full_url,
            capturedAt=record["capturedAt"],
        )

    def list_captures(self) -> list[CaptureItem]:
        return [self._to_item(item) for item in self._items]

    def get_capture(self, capture_id: str) -> dict[str, Any] | None:
        for item in self._items:
            if item["id"] == capture_id:
                return item
        return None

    def get_image_path(self, capture_id: str) -> Path | None:
        record = self.get_capture(capture_id)
        if record is None:
            return None
        path = self._captures_dir / record["filename"]
        return path if path.exists() else None

    def get_thumbnail_path(self, capture_id: str) -> Path | None:
        record = self.get_capture(capture_id)
        if record is None:
            return None
        thumb_name = record.get("thumbnail")
        if not thumb_name:
            return None
        path = self._captures_dir / thumb_name
        return path if path.exists() else None

    def add_capture(self, jpeg_bytes: bytes) -> CaptureItem:
        if not jpeg_bytes:
            raise CaptureError("Empty frame received")

        capture_id = f"cap-{uuid4().hex[:12]}"
        sequence = len(self._items) + 1
        filename = f"capture_{sequence:03d}.jpg"
        thumb_name = f"thumb_{sequence:03d}.jpg"
        image_path = self._captures_dir / filename
        thumb_path = self._captures_dir / thumb_name

        image_path.write_bytes(jpeg_bytes)
        self._create_thumbnail(jpeg_bytes, thumb_path)

        captured_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "id": capture_id,
            "filename": filename,
            "thumbnail": thumb_name,
            "capturedAt": captured_at,
        }
        self._items.insert(0, record)
        self._items = self._items[: self._max_captures]
        self._save_index()
        return self._to_item(record)

    def save_capture_to_path(self, capture_id: str, target_dir: str) -> Path:
        record = self.get_capture(capture_id)
        if record is None:
            raise CaptureError(f"Capture not found: {capture_id}")

        source = self._captures_dir / record["filename"]
        if not source.exists():
            raise CaptureError(f"Capture file missing: {record['filename']}")

        destination_dir = Path(target_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / record["filename"]
        shutil.copy2(source, destination)
        return destination

    def _create_thumbnail(self, jpeg_bytes: bytes, thumb_path: Path) -> None:
        width = int(self._video_config.get("thumbnail_width", 320))
        height = int(self._video_config.get("thumbnail_height", 240))
        with Image.open(BytesIO(jpeg_bytes)) as image:
            image = image.convert("RGB")
            image.thumbnail((width, height))
            image.save(thumb_path, format="JPEG", quality=85)
