from django.http.response import Http404
from django.shortcuts import render, get_object_or_404
from django.http.request import HttpRequest

from pvp.models import Round, RoundTask


# TODO Prefetch

def pvp(request: HttpRequest, room_id):
    round = get_object_or_404(Round, pk=room_id)
    users = list(round.players.all().values_list('pk', flat=True))
    if request.user.id not in users:
        raise Http404

    tasks = round.tasks.all().values_list('pk', 'question')
    frontend_tasks = []
    for task in tasks:
        round_task = RoundTask.objects.get(round=round, task=task[0])
        statistics = round_task.statistics
        is_solve = None
        if statistics.exists():
            is_solve = statistics.get(user=request.user).is_correct
        frontend_tasks.append((task[1], is_solve))

    return render(request, 'pvp.html', {'room_id': room_id, 'tasks': frontend_tasks})
