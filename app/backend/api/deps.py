"""FastAPI dependencies."""

from __future__ import annotations

from app.backend.core.container import AppContainer, get_container


def get_app_container() -> AppContainer:
    return get_container()
