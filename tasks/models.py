from django.db import models


class TaskSource(models.Model):
    name = models.CharField(max_length=255)
    is_ai = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}-{self.is_ai}'


class TaskTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    tags = models.ManyToManyField(
        TaskTag,
        related_name='tasks',
        blank=True,
    )
    source = models.ForeignKey(
        TaskSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
    )
    question = models.TextField()
    solution = models.TextField()
    correct_answer = models.TextField()
    difficulty = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Task №{self.id}'

    class Meta:
        indexes = [
            models.Index(fields=['difficulty']),
        ]
