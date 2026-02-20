from django.urls import path

from .views import SubjectsListAPIView, ReturnTaskAPIView, TasksListAPIView

urlpatterns = [
    path('', TasksListAPIView.as_view()),
    path('<int:pk>/', ReturnTaskAPIView.as_view()),
    path('subjects/', SubjectsListAPIView.as_view()),
]
