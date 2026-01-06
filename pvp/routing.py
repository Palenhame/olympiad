from django.urls import path

from .consumers import PvpConsumer

websocket_urlpatterns = [
    path('ws/pvp/', PvpConsumer.as_asgi())
]
