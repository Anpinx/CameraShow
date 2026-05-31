"""Recording catalog and video serving helpers."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2

from app.backend.core.config import get_api_base_url, get_app_config, get_video_config, resolve_path
from app.backend.schemas.camera import RecordItem
from sdk_adapter.exceptions import RecordingError


class RecordCatalogService:
    def __init__(self) -> None:
        app_cfg = get_app_config()
        self._records_dir = resolve_path(str(app_cfg.get("paths", {}).get("records", "data/records")))
        self._thumbs_dir = self._records_dir / "thumbnails"
        self._index_file = self._records_dir / "index.json"
        self._max_records = int(app_cfg.get("settings", {}).get("max_records", 10))
        video_cfg = get_video_config().get("video", {})
        self._thumb_width = int(video_cfg.get("thumbnail_width", 320))
        self._thumb_height = int(video_cfg.get("thumbnail_height", 240))
        self._thumbs_dir.mkdir(parents=True, exist_ok=True)
        self._items: list[dict[str, Any]] = self._load_index()

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

    def _build_urls(self, record_id: str) -> tuple[str, str]:
        base = get_api_base_url()
        full_url = f"{base}/api/media/records/{record_id}/full"
        thumb_url = f"{base}/api/media/records/{record_id}/thumbnail"
        return full_url, thumb_url

    def _to_item(self, record: dict[str, Any]) -> RecordItem:
        full_url, thumb_url = self._build_urls(record["id"])
        return RecordItem(
            id=record["id"],
            filename=record["filename"],
            thumbnailUrl=thumb_url,
            fullUrl=full_url,
            recordedAt=record["recordedAt"],
        )

    def list_records(self) -> list[RecordItem]:
        return [self._to_item(item) for item in self._items]

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        for item in self._items:
            if item["id"] == record_id:
                return item
        return None

    def get_video_path(self, record_id: str) -> Path | None:
        record = self.get_record(record_id)
        if record is None:
            return None
        path = Path(record["filepath"])
        if not path.exists():
            return None
        if not record.get("browserReady"):
            from video_service.transcoder import transcode_mp4_for_browser

            transcode_mp4_for_browser(path)
            record["browserReady"] = True
            self._save_index()
        return path

    def get_thumbnail_path(self, record_id: str) -> Path | None:
        record = self.get_record(record_id)
        if record is None:
            return None
        thumb_name = record.get("thumbnail")
        if not thumb_name:
            return None
        path = self._thumbs_dir / thumb_name
        return path if path.exists() else None

    def add_record(self, filepath: str, frame_count: int) -> RecordItem:
        path = Path(filepath)
        if not path.exists():
            raise RecordingError(f"Recording file missing: {filepath}")

        record_id = f"rec-{uuid4().hex[:12]}"
        thumb_name = f"thumb_{record_id}.jpg"
        thumb_path = self._thumbs_dir / thumb_name
        self._create_thumbnail(path, thumb_path)

        recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "id": record_id,
            "filename": path.name,
            "filepath": str(path.resolve()),
            "thumbnail": thumb_name,
            "recordedAt": recorded_at,
            "frameCount": frame_count,
            "browserReady": True,
        }
        self._items.insert(0, record)
        self._items = self._items[: self._max_records]
        self._save_index()
        return self._to_item(record)

    def save_record_to_path(self, record_id: str, target_dir: str) -> Path:
        record = self.get_record(record_id)
        if record is None:
            raise RecordingError(f"Recording not found: {record_id}")

        source = Path(record["filepath"])
        if not source.exists():
            raise RecordingError(f"Recording file missing: {record['filename']}")

        destination_dir = Path(target_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / record["filename"]
        shutil.copy2(source, destination)
        return destination

    def _create_thumbnail(self, video_path: Path, thumb_path: Path) -> None:
        capture = cv2.VideoCapture(str(video_path))
        try:
            ok, frame = capture.read()
            if not ok or frame is None:
                raise RecordingError(f"Unable to read video for thumbnail: {video_path.name}")
            height, width = frame.shape[:2]
            scale = min(self._thumb_width / width, self._thumb_height / height, 1.0)
            if scale < 1.0:
                frame = cv2.resize(
                    frame,
                    (int(width * scale), int(height * scale)),
                    interpolation=cv2.INTER_AREA,
                )
            cv2.imwrite(str(thumb_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        finally:
            capture.release()
