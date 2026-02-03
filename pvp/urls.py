from django.urls import path

from .views import pvp

urlpatterns = [path('<int:room_id>/', pvp)]
