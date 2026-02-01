from datetime import timedelta
from django.utils.timezone import now

from tasks.models import Task
from users.models import User
from pvp.models import RoundPlayer, Round, RoundStatus, RoundTask

class RoundService:
    @staticmethod
    def start_round(user_id: int, enemy_id: int) -> int:
        tasks = Task.objects.all()[:3]
        if not tasks:
            raise ValueError("Нет задач для раунда")

        user = User.objects.get(pk=user_id)
        enemy = User.objects.get(pk=enemy_id)

        game_round = Round.objects.create(
            status=RoundStatus.IN_PROGRESS,
            started_at=now(),
            planed_finish=now() + timedelta(hours=2),
        )

        RoundPlayer.objects.bulk_create([
            RoundPlayer(round=game_round, player=user),
            RoundPlayer(round=game_round, player=enemy),
        ])

        for i, task in enumerate(tasks, start=1):
            RoundTask.objects.create(
                round=game_round,
                task=task,
                order=i
            )

        return game_round.id
