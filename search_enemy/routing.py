from django.urls import path

from .consumers import SearchEnemyConsumer

websocket_urlpatterns = [
    path('ws/pvp/', SearchEnemyConsumer.as_asgi()),
]
