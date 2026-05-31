"""Cross-platform helpers for paths and camera capture."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import cv2


def default_captures_save_path() -> str:
    return str(Path.home() / "Pictures" / "Camera_Captures")


def default_records_save_path() -> str:
    return str(Path.home() / "Pictures" / "Camera_Records")


def resolve_settings_path(configured: str | None, fallback: str) -> str:
    if configured and str(configured).strip():
        return str(configured)
    return fallback


def pick_directory(initial_path: str | None = None) -> str | None:
    """Open a native folder picker dialog. Returns None if cancelled."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        kwargs: dict[str, str] = {}
        if initial_path and str(initial_path).strip():
            candidate = Path(str(initial_path).strip().rstrip("/\\"))
            if candidate.is_dir():
                kwargs["initialdir"] = str(candidate)
        selected = filedialog.askdirectory(**kwargs)
        return selected or None
    finally:
        root.destroy()


def opencv_capture_backend() -> int:
    import cv2

    if sys.platform == "win32":
        return cv2.CAP_DSHOW
    if sys.platform == "darwin":
        return cv2.CAP_AVFOUNDATION
    return cv2.CAP_V4L2


def open_video_capture(index: int) -> cv2.VideoCapture:
    import cv2

    cap = cv2.VideoCapture(index, opencv_capture_backend())
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(index)
    return cap
