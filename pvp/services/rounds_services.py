from datetime import timedelta

from django.db.models import F
from django.utils.timezone import now
from django.db import transaction
from channels.db import database_sync_to_async
from django.conf import settings

from tasks.models import Task
from users.models import User
from pvp.models import RoundPlayer, Round, RoundStatus, RoundTask
from core.services.redis_services import statistics_cache
from user_statistics.models import RoundStatistics


class RoundService:
    async def start_round(self, user_id: int, enemy_id: int):
        round_id, round_tasks = await database_sync_to_async(self.create_round_tables)(
            user_id, enemy_id
        )
        await self.create_statistics_tables(round_tasks, round_id, user_id, enemy_id)
        return round_id

    async def create_statistics_tables(
            self, round_tasks: list[RoundTask], round_id: int, user_id: int, enemy_id: int
    ) -> None:
        for task_index, round_task in enumerate(round_tasks):
            for player_id in (user_id, enemy_id):
                await statistics_cache.create_statistics_tables(
                    round_id,
                    player_id,
                    round_task.id,
                    task_index,
                )

    def create_round_tables(self, user_id: int, enemy_id: int) -> tuple[int, list[RoundTask]]:
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

            RoundPlayer.objects.bulk_create([
                RoundPlayer(round=game_round, player=player)
                for player in (user, enemy)
            ])

            round_tasks = RoundTask.objects.bulk_create([
                RoundTask(round=game_round, task=task, order=i)
                for i, task in enumerate(tasks, start=1)
            ])

            return game_round.id, round_tasks

    async def finish_round(
            self, round_id: int, user_id: int, enemy_id: int, winner_id: int | None
    ) -> None:
        await self.change_round_status(round_id, winner_id)

        round_tasks = await self.get_roundtasks(round_id)

        for player_id in (user_id, enemy_id):
            for round_task in round_tasks:
                stats = await statistics_cache.get(round_id, player_id, round_task.id)
                await RoundStatistics.objects.acreate(
                    user_id=player_id,
                    round_task_id=round_task.id,
                    number_of_attempts=stats["attempts"],
                    user_answer=stats["last_answer"],
                    is_correct=stats["is_correct"],
                )

        await self.change_rating(user_id, enemy_id, winner_id)

    async def technical_finish_round(
            self, round_id: int, user_id: int, enemy_id: int | None
    ) -> None:
        await self.change_round_status(round_id, None, is_technical=True)
        await statistics_cache.delete_all_about_round(round_id, user_id, enemy_id)

    @database_sync_to_async
    def change_round_status(
            self, round_id: int, winner_id: int | None, is_technical: bool = False
    ) -> None:
        Round.objects.filter(pk=round_id).update(
            status=RoundStatus.FINISHED if not is_technical else RoundStatus.TECHNICAL_ERROR,
            winner_id=winner_id,
            finished_at=now(),
        )

    @database_sync_to_async
    def get_roundtasks(self, round_id: int) -> list[RoundTask]:
        return list(RoundTask.objects.filter(round=round_id))

    @database_sync_to_async
    def change_rating(self, user_id: int, enemy_id: int, winner_id: int | None) -> None:
        if winner_id is None:
            User.objects.filter(id__in=[user_id, enemy_id]).update(
                rating=F("rating") + int(settings.DELTA * 0.5)
            )
        else:
            loser_id = enemy_id if winner_id == user_id else user_id
            User.objects.filter(id=winner_id).update(rating=F("rating") + settings.DELTA)
            User.objects.filter(id=loser_id).update(rating=F("rating") - settings.DELTA)