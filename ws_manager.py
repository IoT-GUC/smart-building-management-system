import json
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message):
        # Accept both dict and pre-serialized string
        if isinstance(message, str):
            text = message
        else:
            text = json.dumps(message)
        
        # Iterate over a copy to avoid mutation during iteration
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(text)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()
