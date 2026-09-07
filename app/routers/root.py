import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter()


@router.get("/")
def root():
    return {
        "status": "ok",
        "service": "Smart Building Management Server",
    }


@router.get("/service-worker.js", include_in_schema=False)
def serve_service_worker():
    """
    Serve the PWA service worker from the root scope so it can
    control the entire origin (scope = '/').

    Templates should register with:
        navigator.serviceWorker.register('/service-worker.js')
    NOT '/static/service-worker.js' (that would limit scope to /static/).
    """
    path = os.path.join("static", "service-worker.js")
    if not os.path.exists(path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="service-worker.js not found")
    return FileResponse(path, media_type="application/javascript")