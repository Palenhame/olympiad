from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http.request import HttpRequest
from django.db.models import Prefetch

from pvp.models import Round, RoundTask
from user_statistics.models import Statistics


@login_required
def pvp(request: HttpRequest, room_id: int):
    round = get_object_or_404(
        Round.objects
        .only('id')
        .prefetch_related(
            Prefetch(
                'players',
                queryset=Round.players.rel.model.objects.only('id')
            )
        ),
        pk=room_id
    )

    player_ids = {player.id for player in round.players.all()}
    if request.user.id not in player_ids:
        raise Http404

    round_tasks = (
        RoundTask.objects
        .filter(round_id=round.id)
        .select_related('task')
        .only(
            'id',
            'order',
            'task__id',
            'task__question',
        )
        .prefetch_related(
            Prefetch(
                'statistics',
                queryset=Statistics.objects
                .filter(user_id=request.user.id)
                .only('is_correct', 'round_task_id'),
                to_attr='user_statistics'
            )
        )
        .order_by('order')
    )

    frontend_tasks = []
    for round_task in round_tasks:
        is_solve = None
        if round_task.user_statistics:
            is_solve = round_task.user_statistics[0].is_correct

        frontend_tasks.append(
            (round_task.task.question, is_solve)
        )

    return render(
        request,
        'pvp.html',
        {
            'room_id': room_id,
            'tasks': frontend_tasks,
        }
    )
