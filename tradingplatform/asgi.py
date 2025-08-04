# tradingPlatform/asgi.py
import os
import django
from channels.routing import get_default_application

import backend

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradingPlatform.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from backend.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_default_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(backend.routing.websocket_urlpatterns)
    ),
})
