import os

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter()


@router.get("/")
def root(request: Request):
    # If an API client specifically requests JSON (and not HTML browser traffic)
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return {
            "status": "ok",
            "service": "Smart Building Management Server",
        }

    # Browser navigation: redirect authenticated users to dashboard or guests to login
    try:
        from app.main import get_current_user_from_request
        user = get_current_user_from_request(request)
        if user:
            role = (user.get("role") or "").lower()
            if role == "client":
                return RedirectResponse(url=f"/client-portal?user_id={user['id']}", status_code=302)
            return RedirectResponse(url="/admin/home", status_code=302)
    except Exception:
        pass

    return RedirectResponse(url="/login", status_code=302)


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