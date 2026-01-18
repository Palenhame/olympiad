from django.urls import path

from .consumers import PvpConsumer

websocket_urlpatterns = [
    path('ws/pvp/<int:room_id>/', PvpConsumer.as_asgi()),
]
