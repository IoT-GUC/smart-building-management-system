import json
from collections.abc import Iterable
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """
    Tracks live /ws/alarms subscribers and the tenant scope each one is
    allowed to see.

    Scope is resolved from the session at handshake time and stored here; it
    is never taken from the client. A socket may narrow what it receives, but
    it can never widen beyond the scope its session grants.
    """

    def __init__(self):
        self.active_connections: list[dict[str, Any]] = []

    async def connect(
        self,
        websocket: WebSocket,
        *,
        role: str,
        allowed_client_ids: Iterable[int] | None = None,
        user_id: int | None = None,
    ):
        await websocket.accept()
        self.active_connections.append({
            "ws": websocket,
            "role": (role or "").lower(),
            "user_id": user_id,
            # Authoritative, server-resolved tenant scope.
            "allowed_client_ids": {int(c) for c in (allowed_client_ids or ()) if c is not None},
            # Optional client-chosen narrowing within that scope.
            "client_id": None,
            "site_id": None,
        })

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            c for c in self.active_connections if c["ws"] != websocket
        ]

    def set_scope(
        self,
        websocket: WebSocket,
        client_id: int | None = None,
        site_id: int | None = None,
    ):
        """
        Narrow a connection's view. A non-admin asking for a client_id outside
        its granted scope is ignored rather than honoured.
        """
        for c in self.active_connections:
            if c["ws"] != websocket:
                continue

            if client_id is not None:
                try:
                    requested = int(client_id)
                except (TypeError, ValueError):
                    requested = None

                if requested is not None:
                    if c["role"] == "admin" or requested in c["allowed_client_ids"]:
                        c["client_id"] = requested

            if site_id is not None:
                try:
                    c["site_id"] = int(site_id)
                except (TypeError, ValueError):
                    pass
            break

    def _may_receive(
        self,
        connection: dict[str, Any],
        client_id: int | None,
        site_id: int | None,
    ) -> bool:
        role = connection.get("role")

        if role == "admin":
            allowed = True
        elif role == "client":
            # Fail closed: a client only ever receives events for a tenant it
            # has been granted access to. An event with no client_id cannot be
            # attributed to a tenant, so it is not delivered.
            allowed = (
                client_id is not None
                and int(client_id) in connection["allowed_client_ids"]
            )
        else:
            allowed = False

        if not allowed:
            return False

        # Honour the connection's own narrowing filters.
        chosen_client = connection.get("client_id")
        if chosen_client is not None and client_id is not None and chosen_client != client_id:
            return False

        chosen_site = connection.get("site_id")
        return not (
            chosen_site is not None
            and site_id is not None
            and chosen_site != site_id
        )

    async def broadcast(
        self,
        message: Any,
        client_id: int | None = None,
        site_id: int | None = None,
    ):
        text = message if isinstance(message, str) else json.dumps(message)

        disconnected = []
        for connection in list(self.active_connections):
            if not self._may_receive(connection, client_id, site_id):
                continue
            try:
                await connection["ws"].send_text(text)
            except Exception:
                disconnected.append(connection["ws"])

        for ws in disconnected:
            self.disconnect(ws)


manager = ConnectionManager()
