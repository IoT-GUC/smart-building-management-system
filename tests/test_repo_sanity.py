from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_python_files_parse():
    for path in (ROOT / "app").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_run_scripts_use_current_entrypoint():
    assert "app.main:app" in (ROOT / "linux/run.sh").read_text(encoding="utf-8")
    assert "app.main:app" in (ROOT / "windows/run.bat").read_text(encoding="utf-8")


def test_missing_dependency_fixed():
    assert "pydantic-settings" in (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()


def test_debug_route_removed():
    text = "".join([p.read_text(encoding="utf-8") for p in (ROOT / "app/routers").glob("*.py")])
    assert '@router.get("/test-token-refresh")' not in text


def test_credentials_route_unique():
    count = 0
    for path in (ROOT / "app/routers").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        count += text.count('@router.put("/users/{user_id}/credentials")')
    assert count == 1


def test_service_worker_scope():
    text = (ROOT / "app/routers/pages.py").read_text(encoding="utf-8")
    assert "register('/uploads/service-worker.js')" not in text
    assert 'register("/uploads/service-worker.js")' not in text


def test_no_old_alarm_timestamp_query():
    text = "".join([p.read_text(encoding="utf-8") for p in (ROOT / "app/routers").glob("*.py")])
    assert "alarm_history WHERE timestamp" not in text


def test_no_duplicate_routes_within_router_file():
    pattern = re.compile(
        r'@(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']'
    )
    for path in (ROOT / "app").rglob("*.py"):
        seen = set()
        for method, route in pattern.findall(path.read_text(encoding="utf-8")):
            key = (method.upper(), route)
            assert key not in seen, f"duplicate {key} in {path}"
            seen.add(key)
