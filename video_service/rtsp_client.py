"""RTSP client placeholder for future extension."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class RtspClient:
    """Reserved for RTSP camera sources."""

    def __init__(self, url: str) -> None:
        self.url = url

    def connect(self) -> None:
        logger.info("RTSP client is not implemented yet: %s", self.url)
