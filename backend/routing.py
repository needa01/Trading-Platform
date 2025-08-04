# backend/routing.py
from django.urls import path, re_path
from . import consumers


# websocket_urlpatterns = [
#     re_path(r'ws/orderbook/$', consumers.OrderBookConsumer.as_asgi()),
# ]

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/orderbook/$", consumers.OrderBookConsumer.as_asgi()),
    re_path(r"ws/tradehistory/$", consumers.TradeHistoryConsumer.as_asgi()),
    re_path(r"ws/user/$", consumers.UserConsumer.as_asgi()),  # auth middleware required
]
