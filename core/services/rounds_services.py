from datetime import timedelta

from django.utils.timezone import now
from django.db import transaction

from tasks.models import Task
from users.models import User
from pvp.models import RoundPlayer, Round, RoundStatus, RoundTask
from core.services.redis_services import statistics_cache


class RoundService:
    def start_round(self, user_id: int, enemy_id: int) -> int:
        with transaction.atomic():
            tasks = list(Task.objects.order_by("id")[:3])
            if len(tasks) < 3:
                raise ValueError("Нет задач для раунда")

            users = User.objects.in_bulk([user_id, enemy_id])
            try:
                user = users[user_id]
                enemy = users[enemy_id]
            except KeyError:
                raise ValueError("Пользователь не найден")

            current_time = now()

            game_round = Round.objects.create(
                status=RoundStatus.IN_PROGRESS,
                started_at=current_time,
                planed_finish=current_time + timedelta(hours=2),
            )

            round_tasks = [
                RoundTask(round=game_round, task=task, order=i)
                for i, task in enumerate(tasks, start=1)
            ]

            RoundTask.objects.bulk_create(round_tasks)

            for round_task in round_tasks:
                for player in (user, enemy):
                    self.create_statistics_tables(
                        game_round.id,
                        player.id,
                        round_task.id,
                    )

            return game_round.id

    def create_statistics_tables(
        self, round_id: int, user_id: int, round_task_id: int
    ) -> None:
        statistics_cache.create_statistics_tables(round_id, user_id, round_task_id)

