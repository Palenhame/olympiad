from django.conf import settings
from django.db import models

from tasks.models import Task


class RoundStatus(models.TextChoices):
    WAITING = 'waiting', 'Waiting'
    IN_PROGRESS = 'in_progress', 'In progress'
    FINISHED = 'finished', 'Finished'


class Round(models.Model):
    status = models.CharField(
        max_length=20,
        choices=RoundStatus.choices,
        default=RoundStatus.WAITING,
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_rounds',
    )

    started_at = models.DateTimeField(null=True, blank=True)
    planed_finish = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Round №{self.id}'


class RoundTask(models.Model):
    round = models.ForeignKey(
        Round,
        on_delete=models.CASCADE,
        related_name='round_tasks',
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='round_tasks',
    )

    order = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('round', 'order')
        ordering = ['order']

    def __str__(self):
        return f'Round {self.round_id} – Task {self.order}'
