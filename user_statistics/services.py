from django.db.models import F

from user_statistics.models import Statistics
from pvp.models import RoundTask
from users.models import User


def update_or_create_statistics(
        round_task: RoundTask,
        user: User,
        is_correct: bool,
        user_answer: str,
):
    statistics, is_change = Statistics.objects.update_or_create(
        round_task=round_task,
        user=user,
    )

    statistics.is_correct = is_correct
    statistics.user_answer = user_answer

    if not is_change:
        statistics.number_of_attempts = F('number_of_attempts') + 1

    statistics.save()
