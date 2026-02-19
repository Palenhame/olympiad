from datetime import timedelta

from asgiref.sync import async_to_sync
from django.utils.timezone import now

from core.services.redis_services import statistics_cache
from tasks.models import Task
from trainings.models import Training, TrainingTask

class TrainingService:


    def start_training(self, user_id: int, difficulty: str, theme_id: int | None, subject_id: int | None) -> Training:
        tasks = self._get_tasks(difficulty, theme_id, subject_id)
        training = self._create_training(user_id)
        training_tasks = self._create_training_tasks(training, tasks)
        self._create_statistics(training.id, user_id, training_tasks)
        return training

    def _get_tasks(self, difficulty: str, theme_id: int | None, subject_id: int | None) -> list[Task]:
        qs = Task.objects.all()

        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if theme_id:
            qs = qs.filter(theme_id=theme_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)

        tasks = list(qs.order_by('?')[:10])

        if not tasks:
            raise ValueError('Задачи по заданным параметрам не найдены')

        return tasks

    def _create_training(self, user_id: int) -> Training:
        current_time = now()
        return Training.objects.create(
            players_id=user_id,
            started_at=current_time,
            planed_finish=current_time + timedelta(hours=2),
        )

    def _create_training_tasks(self, training: Training, tasks: list[Task]) -> list[TrainingTask]:
        TrainingTask.objects.bulk_create([
            TrainingTask(training=training, task=task, order=i)
            for i, task in enumerate(tasks, start=1)
        ])
        return list(training.trainings_tasks.all())

    def _create_statistics(self, training_id: int, user_id: int, training_tasks: list[TrainingTask]) -> None:
        for task_index, training_task in enumerate(training_tasks):
            async_to_sync(statistics_cache.create_statistics_tables)(
                training_id,
                user_id,
                training_task.id,
                task_index,
            )