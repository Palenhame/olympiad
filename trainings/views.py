from asgiref.sync import async_to_sync
from django.http import HttpRequest, Http404
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.redis_services import statistics_cache
from trainings.models import Training
from trainings.serializers import TrainingStateSerializer
from trainings.services.trainings_services import TrainingService

training_service = TrainingService()


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
        difficulty = request.query_params.get('difficulty')
        theme_id = request.query_params.get('theme_id')
        subject_id = request.query_params.get('subject_id')

        try:
            training = training_service.start_training(
                user_id=request.user.id,
                difficulty=difficulty,
                theme_id=theme_id,
                subject_id=subject_id,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                'training_id': training.id,
                'started_at': training.started_at,
                'planed_finish': training.planed_finish,
            },
            status=status.HTTP_201_CREATED,
        )