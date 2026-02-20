from django.conf import settings
from django.db import models

from tasks.models import Task
from users.models import User
from pvp.models import RoundStatus


class Training(models.Model):
    status = models.CharField(
        max_length=20,
        choices=RoundStatus.choices,
        default=RoundStatus.WAITING,
    )
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trainings')
    tasks = models.ManyToManyField(
        Task,
        related_name='trainings',
        through='TrainingTask',
    )

    started_at = models.DateTimeField(null=True, blank=True)
    planed_finish = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Round №{self.id}'


class TrainingTask(models.Model):
    training = models.ForeignKey(
        Training,
        on_delete=models.CASCADE,
        related_name='trainings_tasks',
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='trainings_tasks',
    )

    order = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('training', 'order')
        ordering = ['order']
        indexes = [
            models.Index(fields=['training']),
            models.Index(fields=['task']),
        ]

    def __str__(self):
        return f'Training {self.training_id} – Task {self.order}'