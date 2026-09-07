import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

class ConnectionManager:
    def __init__(self):
        # Store connections with their scopes: list of dicts like {"ws": websocket, "client_id": int, "site_id": int}
        self.active_connections: List[Dict[str, Any]] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append({
            "ws": websocket,
            "client_id": None,
            "site_id": None
        })

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [c for c in self.active_connections if c["ws"] != websocket]

    def set_scope(self, websocket: WebSocket, client_id: Optional[int] = None, site_id: Optional[int] = None):
        for c in self.active_connections:
            if c["ws"] == websocket:
                if client_id is not None:
                    c["client_id"] = client_id
                if site_id is not None:
                    c["site_id"] = site_id
                break

    async def broadcast(self, message: Any, client_id: Optional[int] = None, site_id: Optional[int] = None):
        # Accept both dict and pre-serialized string
        if isinstance(message, str):
            text = message
        else:
            text = json.dumps(message)
        
        # Iterate over a copy to avoid mutation during iteration
        disconnected = []
        for connection in list(self.active_connections):
            # Check scope
            if client_id is not None and connection.get("client_id") != client_id:
                # If broadcast requires a specific client, skip if no match
                # Wait, if broadcast is for a specific client_id, we send it to connections that have that client_id OR have no scope?
                # Usually we only send to matched scope.
                # Actually, admin might not have client_id. We'll send to connections where client_id is None (admin) or matches.
                if connection.get("client_id") is not None and connection.get("client_id") != client_id:
                    continue
            
            if site_id is not None and connection.get("site_id") != site_id:
                if connection.get("site_id") is not None and connection.get("site_id") != site_id:
                    continue
            
            try:
                await connection["ws"].send_text(text)
            except Exception:
                disconnected.append(connection["ws"])
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()
