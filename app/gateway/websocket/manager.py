from fastapi import WebSocket

class WebSocketConnectionManager:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)
    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)
    @staticmethod
    async def send_json(
            websocket: WebSocket,
            payload: dict,
    ) -> None:
        await websocket.send_json(payload)
websocket_connection_manager = WebSocketConnectionManager()