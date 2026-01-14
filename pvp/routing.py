from django.urls import path

from .consumers import PvpConsumer, DatabaseConsumer

websocket_urlpatterns = [
    path('ws/pvp/<int:room_id>/', PvpConsumer.as_asgi()),
    path('ws/pvp/', DatabaseConsumer.as_asgi()),
]
