import json
import time

from asgiref.sync import sync_to_async, async_to_sync
from celery import shared_task

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from pvp.exceptions import EnemyNotFound, RoundNotFound, RoundTaskNotFound
from tasks.models import Task
from users.models import User
from pvp.models import Round, RoundTask
from pvp.serializer import MessageType, ResultMessageSerializer, AnswerMessageSerializer
from user_statistics.services.user_statistics_server import (
    update_or_create_statistics,
)
from core.services.redis_services import statistics_cache, matchmaking_service
from search_enemy.consumers import round_service


@shared_task
def round_must_finish(winner_id: int, round_id: int, user_id: int, enemy_id):
    round_service.finish_round(round_id, user_id, enemy_id, winner_id)
    channel_layer = get_channel_layer()
    for user in (user_id, enemy_id):
        async_to_sync(channel_layer.group_send)(
            f'user_{user}',
            {
                'type': 'ws_message_finish_round',
            },
        )


class PvpConsumer(AsyncWebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.round_id = None
        self.user = None
        self.enemy = None
        self.round = None

    async def connect(self):
        self.round_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.user = self.scope["user"]
        print("CONNECT:", self.scope["user"], self.scope["url_route"]["kwargs"])

        if not await self.check_user_enemy_round():
            return

        await self.accept()
        await self.add_to_groups()

    async def disconnect(self, code):
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f'user_{self.user.id}', self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        answer_message = AnswerMessageSerializer(data=data)

        answer_message.is_valid(raise_exception=True)

        task_index = answer_message.validated_data['task_index']
        answer = answer_message.validated_data['answer']

        try:
            is_correct = await self.change_task_status(task_index + 1, answer)
        except RoundTaskNotFound:
            return

        await self.send_data_to_frontend(task_index, is_correct)

        if await statistics_cache.is_finish_solving(self.round_id, self.user.id):
            await self.save_total_time(self.user.id)
            print('total_time', self.user.id)

        if await statistics_cache.is_finish_solving(
            self.round_id, self.user.id
        ) and await statistics_cache.is_finish_solving(self.round_id, self.enemy.id):
            print('finish_solving')
            await self.finish_round()

    async def ws_result(self, event):
        serializer = ResultMessageSerializer(
            data={
                'type': event['type_of_message'],
                'task_index': event['task_index'],
                'is_correct': event['is_correct'],
            }
        )

        serializer.is_valid(raise_exception=True)

        await self.send(text_data=json.dumps(serializer.data))

    @database_sync_to_async
    def return_round(self):
        try:
            return Round.objects.get(pk=self.round_id)
        except Round.DoesNotExist:
            raise RoundNotFound

    @database_sync_to_async
    def return_enemy(self) -> User:
        enemy = self.round.players.exclude(pk=self.user.id).first()
        if enemy is None:
            raise EnemyNotFound
        return enemy

    @database_sync_to_async
    def change_task_status_in_db(
        self, round_task: RoundTask, is_correct: bool, user_answer: str
    ):
        update_or_create_statistics(
            round_task,
            self.user,
            is_correct,
            user_answer,
        )

    @database_sync_to_async
    def is_player_in_round(self):
        return self.round.players.filter(pk=self.user.id).exists()

    @database_sync_to_async
    def get_round_task(self, order: int) -> RoundTask:
        return RoundTask.objects.select_related("task").get(
            round=self.round, order=order
        )

    async def ws_return_error_message(self, error_message):
        await self.send(
            text_data=json.dumps(
                {
                    'type': 'error',
                    'errors': error_message,
                }
            )
        )

    async def change_task_status(self, task_index, answer) -> bool:
        correct_answer, round_task_id = await self.get_answer_to_task(
            task_index, self.round_id
        )
        await sync_to_async(print)(answer)
        await sync_to_async(print)(correct_answer)
        is_correct = answer == correct_answer
        await statistics_cache.register_attempt(
            self.round_id,
            self.user.id,
            round_task_id,
            answer,
            is_correct,
        )
        return is_correct

    async def send_data_to_frontend(self, task_index: int, is_correct: bool) -> None:
        for player_id in (self.user.id, self.enemy.id):
            message_type = (
                MessageType.RESULT
                if player_id == self.user.id
                else MessageType.ENEMY_RESULT
            )

            await self.channel_layer.group_send(
                f'user_{player_id}',
                {
                    'type': 'ws_result',
                    'type_of_message': message_type,
                    'task_index': task_index,
                    'is_correct': is_correct,
                },
            )

    async def check_user_enemy_round(self) -> bool:
        if not self.user.is_authenticated:
            print("WS: user not authenticated")
            await self.close(code=4001)
            return False

        try:
            self.round = await self.return_round()
        except RoundNotFound:
            print("WS: round not found")
            await self.close(code=4004)
            return False

        if not await self.is_player_in_round():
            print("WS: user not in round")
            await self.close(code=4004)
            return False

        try:
            self.enemy = await self.return_enemy()
        except EnemyNotFound:
            print("WS: enemy not found")
            await self.close(code=4009)
            return False

        print("WS: ok, accept")
        return True

    async def add_to_groups(self):
        for user in (self.user, self.enemy):
            await self.channel_layer.group_add(f'user_{user.id}', self.channel_name)

    @database_sync_to_async
    def get_answer_to_task(self, task_id, round_id):
        task = Task.objects.only("correct_answer").get(pk=task_id)
        round_task = RoundTask.objects.only("id").get(task=task_id, round=round_id)
        return task.correct_answer, round_task.id

    async def ws_message_finish_round(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    'type': 'finish_round',
                }
            )
        )

    async def finish_round(self):
        winner_id = await matchmaking_service.determine_winner(
            self.round_id,
            self.user.id,
            self.enemy.id,
            statistics_cache
        )
        await round_service.finish_round(
            self.round_id,
            self.user.id,
            self.enemy.id,
            winner_id,
        )
        for player in (self.user.id, self.enemy.id):
            await self.channel_layer.group_send(
                f'user_{player}',
                {
                    'type': 'ws_message_finish_round',
                }
            )

        await statistics_cache.delete_all_about_round(
            self.round_id,
            self.user.id,
            self.enemy.id
        )
        await self.disconnect(2000)


    async def save_total_time(self, user_id: int) -> None:
        round_obj = await Round.objects.aget(id=self.round_id)

        now = timezone.now()
        total_time = (now - round_obj.started_at).total_seconds()

        await statistics_cache.set_total_time(
            round_id=self.round_id,
            user_id=user_id,
            total_time=total_time
        )
