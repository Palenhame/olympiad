from django.urls import path

from .consumers import TrainingConsumer

websocket_urlpatterns = [
    path('ws/training/<int:training_id>/', TrainingConsumer.as_asgi()),
]
