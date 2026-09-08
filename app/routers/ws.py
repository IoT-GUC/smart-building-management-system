import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.connection import get_db_connection as db
from app.services.websockets import manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Sent when the handshake carries no usable session. 1008 is the WebSocket
# "policy violation" close code.
WS_POLICY_VIOLATION = 1008


def resolve_allowed_client_ids(conn, user_id: int) -> set[int]:
    """
    Every client a user can see, resolved upward from whatever level their
    grants were issued at (client, site, building or floor).
    """
    rows = conn.execute(
        """
        SELECT DISTINCT COALESCE(
            ua.client_id,
            s.client_id,
            s2.client_id,
            s3.client_id
        ) AS client_id
        FROM user_access ua
        LEFT JOIN sites     s  ON s.id  = ua.site_id
        LEFT JOIN buildings b  ON b.id  = ua.building_id
        LEFT JOIN sites     s2 ON s2.id = b.site_id
        LEFT JOIN floors    f  ON f.id  = ua.floor_id
        LEFT JOIN buildings b2 ON b2.id = f.building_id
        LEFT JOIN sites     s3 ON s3.id = b2.site_id
        WHERE ua.user_id = ?
        """,
        (user_id,),
    ).fetchall()

    return {row["client_id"] for row in rows if row["client_id"] is not None}


@router.websocket("/ws/alarms")
async def websocket_endpoint(websocket: WebSocket):
    # The HTTP auth middleware never runs for websocket scopes, so the session
    # has to be checked here. Without this the socket streamed every tenant's
    # live alarms to anyone who connected.
    from app.main import get_current_user_from_request

    try:
        user = get_current_user_from_request(websocket)
    except Exception as exc:
        logger.info("Websocket session lookup failed: %s", exc)
        user = None

    if not user:
        await websocket.close(code=WS_POLICY_VIOLATION)
        return

    role = (user.get("role") or "").lower()

    if role == "admin":
        allowed_client_ids: set[int] = set()
    elif role == "client":
        conn = db()
        try:
            allowed_client_ids = resolve_allowed_client_ids(conn, user["id"])
        finally:
            conn.close()

        if not allowed_client_ids:
            # A client with no grants has nothing to subscribe to.
            await websocket.close(code=WS_POLICY_VIOLATION)
            return
    else:
        await websocket.close(code=WS_POLICY_VIOLATION)
        return

    await manager.connect(
        websocket,
        role=role,
        allowed_client_ids=allowed_client_ids,
        user_id=user["id"],
    )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "subscribe":
                    manager.set_scope(
                        websocket,
                        client_id=msg.get("client_id"),
                        site_id=msg.get("site_id"),
                    )
            except Exception:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        # An abnormal close raises something other than WebSocketDisconnect;
        # without this the connection stays in the manager's list forever.
        manager.disconnect(websocket)
