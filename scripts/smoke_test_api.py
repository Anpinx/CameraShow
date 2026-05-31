import json
import tempfile
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
TEST_CAPTURE_DIR = str(Path(tempfile.gettempdir()) / "camera_demo_captures")


def req(method: str, path: str, body: dict | None = None) -> str:
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode()


print("save-path:", req("PUT", "/api/settings/save-path", {"path": TEST_CAPTURE_DIR + "/"}))
print("open:", req("POST", "/api/stream/open"))
caps = json.loads(req("GET", "/api/captures"))
if caps:
    cap_id = caps[0]["id"]
    print(
        "save capture:",
        req(
            "POST",
            "/api/captures/save",
            {"captureId": cap_id, "path": TEST_CAPTURE_DIR + "/"},
        ),
    )
    with urllib.request.urlopen(f"{BASE}/api/media/captures/{cap_id}/full", timeout=15) as response:
        print("full image bytes:", len(response.read()))
print("close:", req("POST", "/api/stream/close"))
