import json
from random import randint, choice

from channels.generic.websocket import AsyncWebsocketConsumer

ROOM_PLAYERS = {}


class PvpConsumer(AsyncWebsocketConsumer):
    @staticmethod
    def task_list():
        a = []
        for i in range(10):
            task = f'{randint(1, 100)} {choice(('+', '-', '*', '/'))} {randint(1, 100)}'
            answer = eval(task)
            a.append((task, answer))
        return a

    tasks = task_list()

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.session_key = self.scope["session"].session_key

        if self.room_id not in ROOM_PLAYERS:
            ROOM_PLAYERS[self.room_id] = []

        ROOM_PLAYERS[self.room_id].append(self.channel_name)

        await self.accept()

        await self.send(
            text_data=json.dumps(
                {
                    'type': 'tasks',
                    'tasks': [i[0] for i in self.tasks]
                }
            )
        )

    async def disconnect(self, code):
        players = ROOM_PLAYERS.get(self.room_id, [])

        ROOM_PLAYERS[self.room_id] = [
            c for c in players if c != self.channel_namez
        ]

    async def receive(self, text_data: json):
        data = json.loads(text_data)

        type = data.get('type')
        task_index = data.get('task_index')
        answer = data.get('answer')

        is_correct = None

        if type == 'answer':
            is_correct = (answer == str(self.tasks[task_index][1]))

        await self.send(
            text_data=json.dumps(
                {
                    'type': 'result',
                    'task_index': task_index,
                    'correct': is_correct
                }
            )
        )
        enemy_channel_layer = self.get_opponent_channel()

        if enemy_channel_layer:
            await self.channel_layer.send(
                enemy_channel_layer,
                {
                    'type': 'enemy_result',
                    'task_index': task_index,
                    'correct': is_correct
                }
            )

    def get_opponent_channel(self):
        for channel in ROOM_PLAYERS[self.room_id]:
            if channel != self.channel_name:
                return channel

    async def enemy_result(self, event):
        await self.send(
            text_data=json.dumps({
                'type': 'enemy_result',
                'task_index': event['task_index'],
                'correct': event['correct'],
            })
        )
