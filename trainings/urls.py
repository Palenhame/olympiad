from django.urls import path

from .views import training, TrainingApiView

urlpatterns = [
    path('<int:training_id>/', training),
    path('api/<int:round_id>/', TrainingApiView.as_view()),
    path('api/start_training/', TrainingApiView.as_view()),
]
