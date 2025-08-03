from channels.generic.websocket import AsyncWebsocketConsumer
import json

class OrderBookConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "orderbook"
        self.user_group = f"user_{self.scope['user'].id}" if self.scope["user"].is_authenticated else None

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        if self.user_group:
            await self.channel_layer.group_add(self.user_group, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if self.user_group:
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def send_orderbook(self, event):
        await self.send(text_data=json.dumps({
            "type": "orderbook_update",
            "ltp": event["data"]["ltp"],
            "asset": event["data"]["asset"],
            "time": event["data"]["time"]
        }))

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "message": event["message"]
        }))
