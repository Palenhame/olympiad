from django.conf import settings
from django.db import models


class RoundStatistics(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='round_statistics',
    )
    round_task = models.ForeignKey(
        'pvp.RoundTask',
        on_delete=models.CASCADE,
        related_name='round_statistics',
    )

    number_of_attempts = models.PositiveIntegerField(default=1)
    user_answer = models.TextField(null=True)
    is_correct = models.BooleanField(null=True)
    time_to_solve = models.FloatField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'round_statistics'
        unique_together = ('user', 'round_task')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['round_task']),
            models.Index(fields=['is_correct']),
        ]

    def __str__(self):
        return f'{self.user} – {self.round_task} – {self.is_correct}'


class TrainingStatistics(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='training_statistics',
    )
    training_task = models.ForeignKey(
        'trainings.TrainingTask',
        on_delete=models.CASCADE,
        related_name='statistics',
    )

    number_of_attempts = models.PositiveIntegerField(default=1)
    user_answer = models.TextField(null=True)
    is_correct = models.BooleanField(null=True)
    time_to_solve = models.FloatField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_statistics'
        unique_together = ('user', 'training_task')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['training_task']),
            models.Index(fields=['is_correct']),
        ]

    def __str__(self):
        return f'{self.user} – {self.training_task} – {self.is_correct}'