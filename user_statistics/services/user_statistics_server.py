from django.db.models import F

from user_statistics.services.user_statistics_cache import StatisticsCache
from user_statistics.models import RoundStatistics
from pvp.models import RoundTask, Round
from users.models import User


async def register_answer(
    round: Round,
    user: User,
    round_task: RoundTask,
    answer: str,
    is_correct: bool,
):
    await StatisticsCache.register_attempt(
        round_id=round.id,
        user_id=user.id,
        round_task_id=round_task.id,
        answer=answer,
        is_correct=is_correct,
    )


def update_or_create_statistics(
    round_task: RoundTask,
    user: User,
    is_correct: bool,
    user_answer: str,
):
    statistics, is_change = RoundStatistics.objects.update_or_create(
        round_task=round_task,
        user=user,
    )

    statistics.is_correct = is_correct
    statistics.user_answer = user_answer

    if not is_change:
        statistics.number_of_attempts = F('number_of_attempts') + 1

    statistics.save()
