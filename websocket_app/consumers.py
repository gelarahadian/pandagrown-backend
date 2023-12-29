# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import json
import websockets

class HengrownConsumer(AsyncWebsocketConsumer):
    connected_clients = {}  # Dictionary to store WebSocket connections

    async def connect(self):
        # Retrieve a unique identifier for the client
        user_id = int(self.scope['url_route']['kwargs']['user_id'])

        # Store the WebSocket connection
        if user_id not in self.connected_clients:
            self.connected_clients[user_id] = []

        self.connected_clients[user_id].append(self)
        await self.accept()

    async def disconnect(self, close_code):
        # Retrieve the client identifier
        user_id = int(self.scope['url_route']['kwargs']['user_id'])

        # Remove the WebSocket connection from the list
        if user_id in self.connected_clients:
            self.connected_clients[user_id].remove(self)
            if not self.connected_clients[user_id]:
                del self.connected_clients[user_id]

    async def receive(self, text_data):
        # Process received data
        user_id = int(self.scope['url_route']['kwargs']['user_id'])
        if user_id == 0:
            data = json.loads(text_data)
            connections = self.connected_clients.get(data['user_id'], [])
            for connection in connections:
                await connection.send(data['data'])

    @classmethod
    async def send_json_to_client(cls, client_id, data):
        try:
            async with websockets.connect(settings.WS_URL) as websocket:
                # Sending data to the WebSocket server (optional)
                data_to_send = {
                    "user_id": client_id,
                    "data": json.dumps(data),
                }
                await websocket.send(json.dumps(data_to_send))
        except websockets.exceptions.ConnectionClosedError:
            print("WebSocket connection closed.")
        except Exception as e:
            print(f"Error: {e}")

