from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse, FileResponse
from maintestfinal2 import *

router = APIRouter()

@router.post("/ttn-webhook")
async def ttn_webhook(data: dict, background_tasks: BackgroundTasks):
    """
    Receive a TTN uplink and instantly queue it for background processing
    to avoid blocking the HTTP response.
    """
    background_tasks.add_task(process_ttn_webhook_background, data)
    return {"status": "queued", "message": "Payload queued for background processing"}