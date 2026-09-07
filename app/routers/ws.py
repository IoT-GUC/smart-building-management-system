import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websockets import manager

router = APIRouter()

@router.websocket("/ws/alarms")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "subscribe":
                    client_id = msg.get("client_id")
                    site_id = msg.get("site_id")
                    manager.set_scope(websocket, client_id=client_id, site_id=site_id)
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
