# from channels.generic.websocket import AsyncWebsocketConsumer
# import json

# class OrderBookConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.group_name = "orderbook"
#         self.user_group = f"user_{self.scope['user'].id}" if self.scope["user"].is_authenticated else None

#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         if self.user_group:
#             await self.channel_layer.group_add(self.user_group, self.channel_name)

#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)
#         if self.user_group:
#             await self.channel_layer.group_discard(self.user_group, self.channel_name)

#     async def send_orderbook(self, event):
#         await self.send(text_data=json.dumps({
#             "type": "orderbook_update",
#             "ltp": event["data"]["ltp"],
#             "asset": event["data"]["asset"],
#             "time": event["data"]["time"]
#         }))
        
#     async def send_portfolio(self, event):
#         await self.send(text_data=json.dumps({
#             "type": "portfolio",
#             "data": event["data"]
#         }))
    
#     async def send_trade(self, event):
#         await self.send(text_data=json.dumps(event["data"]))

#     async def send_notification(self, event):
#         await self.send(text_data=json.dumps({
#             "type": "notification",
#             "message": event["message"]
#         }))


import json
from channels.generic.websocket import AsyncWebsocketConsumer

# 1. Live Order Book Consumer
class OrderBookConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "orderbook"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_orderbook(self, event):
        await self.send(text_data=json.dumps(event["data"]))


# 2. Live Trade History Feed Consumer
class TradeHistoryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "tradehistory"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_trade(self, event):
        await self.send(text_data=json.dumps(event["data"]))


# 3. Per-User Portfolio / Notification Consumer
class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_portfolio(self, event):
        await self.send(text_data=json.dumps({
            "type": "portfolio_update",
            "data": event["data"]
        }))

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "message": event["message"]
        }))
