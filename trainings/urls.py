from django.urls import path

from .views import training, TrainingApiView, StartTrainingApiView

urlpatterns = [
    path('<int:training_id>/', training),
    path('<int:round_id>/', TrainingApiView.as_view()),
    path('start_training/', StartTrainingApiView.as_view()),
]
