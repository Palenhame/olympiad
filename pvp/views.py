
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.db.models import Prefetch
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async

from pvp.models import Round, RoundTask
from user_statistics.models import Statistics
from core.services.redis_services import statistics_cache


@login_required
async def pvp(request: HttpRequest, room_id: int):
    user_id = await sync_to_async(lambda: request.user.id)()

    if not await statistics_cache.is_exists(room_id, user_id):
        print(f'Room {room_id} does not exist')
        print(f'User {user_id} does not exist')
        raise Http404
        # print(1)
        # return HttpResponse('404')

    round_tasks = await get_round_task(request, room_id)
    # await sync_to_async(print)(round_tasks)
    # await sync_to_async(print)(round_tasks[0].user_statistics)
    frontend_tasks = []
    for round_task in round_tasks:
        is_solve = await statistics_cache.get(
            room_id, user_id, round_task.id
        )

        frontend_tasks.append({
            "question": round_task.task.question,
            "is_correct": is_solve["is_correct"]
        })
    print(frontend_tasks)

    return render(
        request,
        'pvp.html',
        {
            'room_id': room_id,
            'tasks': frontend_tasks,
        },
    )
    # return render(request, 'pvp.html')


@database_sync_to_async
def get_round_task(request: HttpRequest, round_id: int) -> list[RoundTask]:
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
