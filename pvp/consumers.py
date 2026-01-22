import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from pvp.models import Round, RoundTask
from tasks.models import Task

ROOM_PLAYERS = {}


class PvpConsumer(AsyncWebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.round_id = None
        self.user = None
        self.enemy = None
        self.round = None

    async def connect(self):
        self.round_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.round = await self.return_round(self.round_id)
        self.user = self.scope["user"]
        self.enemy = await self.return_enemy(self.round, self.user.id)

        await self.accept()

        for user in (self.user, self.enemy):
            await self.channel_layer.group_add(
                f'user_{user.id}',
                self.channel_name
            )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            f'user_{self.user.id}',
            self.channel_name
        )

    async def receive(self, text_data: json):
        data = json.loads(text_data)

        type = data.get('type')
        task_index = data.get('task_index')
        answer = data.get('answer')

        is_correct = None
        # TODO
        if type == 'answer':
            task = None
            is_correct = True if answer == task.correct_answer else False

        await self.send(
            text_data=json.dumps(
                {
                    'type': 'result',
                    'task_index': task_index,
                    'correct': is_correct
                }
            )
        )
        # TODO
        if enemy_channel_layer:
            await self.channel_layer.send(
                enemy_channel_layer,
                {
                    'type': 'enemy_result',
                    'task_index': task_index,
                    'correct': is_correct
                }
            )

    async def enemy_result(self, event):
        await self.send(
            text_data=json.dumps({
                'type': 'enemy_result',
                'task_index': event['task_index'],
                'correct': event['correct'],
            })
        )

    def return_user_id(self):
        pass

    @database_sync_to_async
    def return_round(self, round_id):
        return Round.objects.get(pk=round_id)

    @database_sync_to_async
    def return_enemy(self, round, user_id):
        return round.user.exclude(pk=user_id)

    def get_tasks(self, round):
        return RoundTask.objects.get(round=round).task
