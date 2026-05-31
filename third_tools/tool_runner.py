"""Run configured third-party tools."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ToolRunner:
    def __init__(self, tools_config: dict[str, Any]) -> None:
        self._config = tools_config

    @property
    def enabled(self) -> bool:
        return bool(self._config.get("enabled", False))

    def run(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            logger.info("Third-party tools are disabled")
            return {"ok": False, "reason": "disabled"}
        logger.info("Tool request received: %s", tool_name)
        return {"ok": False, "reason": "not_implemented", "tool": tool_name, "payload": payload}
