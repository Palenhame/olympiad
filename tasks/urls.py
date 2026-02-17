from django.urls import path

from .views import SubjectsListAPIView

urlpatterns = [
    path('<int:pk>/', SubjectsListAPIView.as_view()),
    path('subjects/', SubjectsListAPIView.as_view()),
]
