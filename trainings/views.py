from asgiref.sync import async_to_sync
from django.http import HttpRequest, Http404
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.redis_services import statistics_cache
from trainings.models import Training
from trainings.serializers import TrainingStateSerializer


def training(request, training_id):
    return render(request, 'trainings.html', {
        'training_id': training_id
    })

def get_training_tasks(training_id: int):
    from trainings.models import TrainingTask
    return TrainingTask.objects.filter(
        training_id=training_id
    ).select_related('task').order_by('order')


class TrainingApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest, training_id: int) -> Response:
        user_id = request.user.id

        if not async_to_sync(statistics_cache.is_exists)(training_id, user_id):
            raise Http404

        training_tasks = get_training_tasks(training_id)

        tasks_data = []
        user_solved_count = 0

        for training_task in training_tasks:
            user_stats = async_to_sync(statistics_cache.get)(
                training_id, user_id, training_task.id
            )

            if user_stats["is_correct"]:
                user_solved_count += 1

            tasks_data.append(
                {
                    "question": training_task.task.question,
                    "is_correct": user_stats["is_correct"],
                }
            )

        response_data = {
            "tasks": tasks_data,
            "solved_count": user_solved_count,
        }

        serializer = TrainingStateSerializer(response_data)
        return Response(serializer.data)

class StartTrainingApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest) -> Response:
        pass