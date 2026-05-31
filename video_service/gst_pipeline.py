"""GStreamer pipeline helpers."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_gst_module: Any | None = None
_gst_checked = False
_gst_unavailable_reason: str | None = None


def configure_gstreamer_env(gstreamer_bin: str) -> None:
    """Add GStreamer binaries and plugins to the process environment."""
    if not gstreamer_bin or not gstreamer_bin.strip():
        return

    bin_path = Path(gstreamer_bin)
    if not bin_path.exists():
        logger.warning("GStreamer bin path not found: %s", bin_path)
        return

    gst_root = bin_path.parent.parent
    plugin_path = gst_root / "lib" / "gstreamer-1.0"
    pygi_path = gst_root / "lib" / "site-packages"

    path_entries = [str(bin_path), str(gst_root / "bin")]
    current_path = os.environ.get("PATH", "")
    path_parts = current_path.split(os.pathsep) if current_path else []
    for entry in path_entries:
        if entry not in path_parts:
            path_parts.insert(0, entry)
    os.environ["PATH"] = os.pathsep.join(path_parts)

    if plugin_path.exists():
        os.environ["GST_PLUGIN_PATH"] = str(plugin_path)
    if pygi_path.exists() and str(pygi_path) not in sys.path:
        sys.path.insert(0, str(pygi_path))


def try_import_gst() -> Any | None:
    global _gst_module, _gst_checked, _gst_unavailable_reason
    if _gst_checked:
        return _gst_module

    _gst_checked = True
    try:
        from gi.repository import Gst  # type: ignore

        Gst.init(None)
        _gst_module = Gst
        return Gst
    except Exception as exc:  # noqa: BLE001
        _gst_unavailable_reason = str(exc)
        logger.info(
            "GStreamer Python bindings unavailable, using OpenCV backend: %s",
            exc,
        )
        return None


def is_gstreamer_available() -> bool:
    return try_import_gst() is not None


def build_capture_pipeline(
    Gst: Any,
    camera_config: dict[str, Any],
    video_config: dict[str, Any],
) -> str:
    width = int(camera_config.get("width", 1920))
    height = int(camera_config.get("height", 1080))
    fps = int(camera_config.get("fps", 30))
    quality = int(video_config.get("jpeg_quality", 85))
    device_name = camera_config.get("device_name") or ""

    if sys.platform == "win32":
        source = f'dshowvideosrc device-name="{device_name}"' if device_name else "ksvideosrc"
    elif sys.platform == "darwin":
        device_index = int(camera_config.get("device_index", 0))
        source = f"avfvideosrc device-index={device_index}"
    else:
        source = f"v4l2src device={device_name}" if device_name else "v4l2src"

    return (
        f"{source} ! videoconvert ! videoscale ! "
        f"video/x-raw,width={width},height={height},framerate={fps}/1 ! "
        f"jpegenc quality={quality} ! appsink name=sink emit-signals=false sync=false "
        f"max-buffers=1 drop=true"
    )
