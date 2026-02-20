import json

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from pvp.exceptions import RoundNotFound
from tasks.models import Task
from pvp.serializers import ResultMessageSerializer, AnswerMessageSerializer
from core.services.redis_services import statistics_cache
from trainings.models import Training, TrainingTask
from trainings.services.trainings_services import TrainingService

training_service = TrainingService()


class TrainingConsumer(AsyncWebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.training_id = None
        self.user = None
        self.training = None

    async def connect(self):
        self.training_id = self.scope["url_route"]["kwargs"]["training_id"]
        self.user = self.scope["user"]


        if not await self.check_user_and_training():
            return

        await self.accept()
        await self.channel_layer.group_add(
            f'training_{self.user.id}',
            self.channel_name
        )

    async def disconnect(self, code):
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f'training_{self.user.id}',
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        answer_message = AnswerMessageSerializer(data=data)

        answer_message.is_valid(raise_exception=True)

        task_index = answer_message.validated_data['task_index']
        answer = answer_message.validated_data['answer']

        is_correct = await self.change_task_status(task_index + 1, answer)

        await self.send_result_to_frontend(task_index, is_correct)

        if await statistics_cache.is_finish_solving(self.training_id, self.user.id):
            await self.save_total_time()
            await self.finish_training()

    async def send_result_to_frontend(self, task_index: int, is_correct: bool) -> None:
        serializer = ResultMessageSerializer(
            data={
                'type': 'result',
                'task_index': task_index,
                'is_correct': is_correct,
            }
        )

        serializer.is_valid(raise_exception=True)

        await self.send(text_data=json.dumps(serializer.data))

    async def check_user_and_training(self) -> bool:
        if not self.user.is_authenticated:
            print("WS: user not authenticated")
            await self.close(code=4001)
            return False

        try:
            self.training = await self.return_training()
        except RoundNotFound:
            print("WS: training not found")
            await self.close(code=4004)
            return False

        if not await self.is_player_in_training():
            print("WS: user not in training")
            await self.close(code=4003)
            return False

        print("WS: ok, accept")
        return True

    @database_sync_to_async
    def return_training(self):
        try:
            return Training.objects.get(pk=self.training_id)
        except Training.DoesNotExist:
            raise RoundNotFound

    @database_sync_to_async
    def is_player_in_training(self):
        return self.training.player_id == self.user.id

    async def change_task_status(self, task_index, answer) -> bool:
        correct_answer, round_task_id = await self.get_answer_to_task(
            task_index, self.training_id
        )
        await sync_to_async(print)(answer)
        await sync_to_async(print)(correct_answer)

        is_correct = answer == correct_answer

        await statistics_cache.register_attempt(
            self.training_id,
            self.user.id,
            round_task_id,
            answer,
            is_correct,
        )

        return is_correct

    @database_sync_to_async
    def get_answer_to_task(self, task_order, training_id):
        training_task = TrainingTask.objects.select_related('task').get(
            order=task_order,
            training=training_id,
        )
        return training_task.task.correct_answer, training_task.id

    async def save_total_time(self) -> None:
        training_obj = await Training.objects.aget(id=self.training_id)

        now = timezone.now()
        total_time = (now - training_obj.started_at).total_seconds()

        await statistics_cache.set_total_time(
            round_id=self.training_id,
            user_id=self.user.id,
            total_time=total_time
        )

    async def finish_training(self):
        await training_service.finish_training(self.training_id, self.user.id)

        await self.send(text_data=json.dumps({
            'type': 'finish_round',
            'message': 'Тренировка завершена!'
        }))

    @database_sync_to_async
    def update_training_status(self):
        from pvp.models import RoundStatus

        Training.objects.filter(pk=self.training_id).update(
            status=RoundStatus.FINISHED,
            finished_at=timezone.now()
        )
