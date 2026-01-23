import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from pvp.models import Round, RoundTask
from user_statistics.services import update_or_create_statistics

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
        self.round = await self.return_round()
        self.user = self.scope["user"]
        self.enemy = await self.return_enemy()

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
            task = await self.get_task(task_index + 1)
            is_correct = True if answer == task.correct_answer else False

            await self.change_task_status(task, is_correct, answer)

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
            await self.channel_layer.group_send(
                f'user_{self.enemy.id}',
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

    @database_sync_to_async
    def return_round(self):
        return Round.objects.get(pk=self.round_id)

    @database_sync_to_async
    def return_enemy(self):
        return self.round.players.exclude(pk=self.user.id)[0]

    @database_sync_to_async
    def get_task(self, order):
        return RoundTask.objects.get(round=self.round, order=order).task

    @database_sync_to_async
    def change_task_status(self,
                           task_id: int,
                           is_correct: bool,
                           user_answer: str
                           ):
        round_task = RoundTask.objects.get(
            round=self.round,
            task=task_id
        )
        print(is_correct)
        print(user_answer)
        update_or_create_statistics(
            round_task,
            self.user,
            is_correct,
            user_answer,
        )
