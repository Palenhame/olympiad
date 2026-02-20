from django.urls import path

from .views import RoundApiView, pvp

urlpatterns = [
    path('<int:round_id>/', pvp),
    path('api/<int:round_id>/', RoundApiView.as_view()),
]
