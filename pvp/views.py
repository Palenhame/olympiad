from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import login_required

from django.http import Http404, HttpResponse
from django.http import HttpRequest
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from core.services.redis_services import statistics_cache
from pvp.models import RoundTask, Round, RoundPlayer
from pvp.serializers import RoundTaskSerializer, RoundStateSerializer



def pvp(request: HttpRequest, round_id: int) -> HttpResponse:
    return render(request, 'pvp.html')


def get_round_task(round_id: int) -> list[RoundTask]:
    round_tasks = (
        RoundTask.objects.filter(round_id=round_id)
        .select_related('task')
        .only(
            'id',
            'order',
            'task__id',
            'task__question',
        )
        .order_by('order')
    )
    return list(round_tasks)


def get_enemy_id(round_id: int, user_id: int) -> int:
    enemy = (
        RoundPlayer.objects.filter(round=round_id)
        .exclude(player=user_id)
        .values_list("player_id", flat=True)
        .first()
    )

    return enemy


class RoundApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest, round_id: int) -> Response:
        user_id = request.user.id

        if async_to_sync(statistics_cache.is_technical_finish)(round_id):
            return Response(status=status.HTTP_409_CONFLICT)

        if not async_to_sync(statistics_cache.is_exists)(round_id, user_id):
            raise Http404

        enemy_id = get_enemy_id(round_id, user_id)
        round_tasks = get_round_task(round_id)

        tasks_data = []
        user_solved_count = 0
        enemy_solved_count = 0

        for round_task in round_tasks:
            user_stats = async_to_sync(statistics_cache.get)(
                round_id, user_id, round_task.id
            )

            enemy_stats = async_to_sync(statistics_cache.get)(
                round_id, enemy_id, round_task.id
            )

            if user_stats["is_correct"]:
                user_solved_count += 1

            if enemy_stats["is_correct"]:
                enemy_solved_count += 1

            tasks_data.append(
                {
                    "question": round_task.task.question,
                    "user_is_correct": user_stats["is_correct"],
                    "enemy_is_correct": enemy_stats["is_correct"],
                }
            )

        response_data = {
            "tasks": tasks_data,
            "user_solved_count": user_solved_count,
            "enemy_solved_count": enemy_solved_count,
        }

        serializer = RoundStateSerializer(response_data)
        return Response(serializer.data)
