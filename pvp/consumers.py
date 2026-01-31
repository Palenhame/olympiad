import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from pydantic import ValidationError

from pvp.api.shemas import AnswerMessage
from pvp.exceptions import EnemyNotFound, RoundNotFound, RoundTaskNotFound
from pvp.models import Round, RoundTask
from pvp.serializer import MessageType, ResultMessageSerializer
from user_statistics.services.user_statistics_server import update_or_create_statistics, register_answer


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

        if not await self.check_user_enemy_round():
            return

        await self.accept()
        await self.add_to_groups()

    async def disconnect(self, code):
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f'user_{self.user.id}',
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)

        try:
            answer_message = AnswerMessage(**data)
        except ValidationError as error:
            await self.ws_return_error_message(error.errors())
            return

        task_index = answer_message.task_index
        answer = answer_message.answer

        try:
            is_correct = await self.change_task_status(task_index + 1, answer)
        except RoundTaskNotFound:
            return

        await self.send_data_to_frontend(task_index, is_correct)

    async def ws_result(self, event):
        serializer = ResultMessageSerializer(
            data={
                'type': event['type_of_message'],
                'task_index': event['task_index'],
                'is_correct': event['is_correct']
            }
        )

        serializer.is_valid(raise_exception=True)

        await self.send(
            text_data=json.dumps(serializer.data)
        )

    @database_sync_to_async
    def return_round(self):
        try:
            return Round.objects.get(pk=self.round_id)
        except Round.DoesNotExist:
            raise RoundNotFound

    @database_sync_to_async
    def return_enemy(self):
        enemy = self.round.players.exclude(pk=self.user.id).first()
        if enemy is None:
            raise EnemyNotFound
        return enemy

    @database_sync_to_async
    def change_task_status_in_db(self,
                                 round_task: RoundTask,
                                 is_correct: bool,
                                 user_answer: str
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
            round=self.round,
            order=order
        )

    async def ws_return_error_message(self, error_message):
        await self.send(
            text_data=json.dumps({
                'type': 'error',
                'errors': error_message,
            })
        )

    async def change_task_status(self, task_index, answer) -> bool:




        return is_correct

    async def send_data_to_frontend(self, task_index: int, is_correct: bool) -> None:
        for player_id in (self.user.id, self.enemy.id):
            message_type = MessageType.ANSWER if player_id == self.user.id else MessageType.ENEMY_RESULT

            await self.channel_layer.group_send(
                f'user_{player_id}',
                {
                    'type': 'ws_result',
                    'type_of_message': message_type,
                    'task_index': task_index,
                    'is_correct': is_correct
                }
            )

    async def check_user_enemy_round(self) -> bool:
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return False

        try:
            self.round = await self.return_round()
        except RoundNotFound:
            await self.close(code=4004)
            return False

        if not await self.is_player_in_round():
            await self.close(code=4004)
            return False

        try:
            self.enemy = await self.return_enemy()
        except EnemyNotFound:
            await self.close(code=4009)
            return False

        return True

    async def add_to_groups(self):
        for user in (self.user, self.enemy):
            await self.channel_layer.group_add(
                f'user_{user.id}',
                self.channel_name
            )
