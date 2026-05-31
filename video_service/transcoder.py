"""Transcode recordings for HTML5 video playback."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def _find_ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def transcode_mp4_for_browser(source: Path) -> Path:
    """Re-encode MPEG-4 Part 2 (mp4v) to H.264 for browser/Electron playback."""
    if not source.exists():
        return source

    ffmpeg = _find_ffmpeg()
    if ffmpeg is None:
        logger.warning("ffmpeg not found; browser playback may fail for %s", source)
        return source

    temp_path = source.with_name(f"{source.stem}.browser{source.suffix}")
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(temp_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        logger.error("ffmpeg transcode failed for %s: %s", source, exc.stderr)
        temp_path.unlink(missing_ok=True)
        return source

    if not temp_path.exists() or temp_path.stat().st_size == 0:
        temp_path.unlink(missing_ok=True)
        logger.error("ffmpeg produced empty output for %s", source)
        return source

    source.unlink(missing_ok=True)
    temp_path.replace(source)
    logger.info("Transcoded recording for browser playback: %s", source)
    return source
