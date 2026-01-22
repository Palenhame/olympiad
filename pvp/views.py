from django.shortcuts import render, get_object_or_404

from pvp.models import Round

# Create your views here.
def pvp(request, room_id):
    round = get_object_or_404(Round, pk=room_id)
    tasks = list(round.tasks.all().values_list('question', flat=True))
    print(tasks)

    return render(request, 'pvp.html', {'room_id': room_id, 'tasks': tasks})
