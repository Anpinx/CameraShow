"""Third-party tool base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ToolBase(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
