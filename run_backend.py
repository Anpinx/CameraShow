"""Run backend with uvicorn."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    import uvicorn

    from app.backend.core.config import get_app_config

    settings = get_app_config().get("app", {})
    uvicorn.run(
        "app.backend.main:app",
        host=str(settings.get("host", "127.0.0.1")),
        port=int(settings.get("port", 8000)),
        reload=bool(settings.get("debug", False)),
    )
