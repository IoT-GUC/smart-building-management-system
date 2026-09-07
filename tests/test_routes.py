from __future__ import annotations

from app.main import app


def test_no_duplicate_route_paths_and_methods():
    seen = set()
    duplicates = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if methods and path:
            for method in methods:
                key = (method, path)
                if key in seen:
                    duplicates.append(key)
                seen.add(key)

    assert not duplicates, f"Duplicate routes found in FastAPI app: {duplicates}"


def test_static_files_route_mounted():
    mount_paths = [getattr(r, "path", None) for r in app.routes]
    assert "/static" in mount_paths or "/static/{path:path}" in mount_paths or any(
        p and p.startswith("/static") for p in mount_paths
    )


def test_service_worker_route_exists():
    paths = [getattr(r, "path", None) for r in app.routes]
    assert "/service-worker.js" in paths
