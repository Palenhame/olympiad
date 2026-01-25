import json
from datetime import timedelta

from django.utils.timezone import now
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from users.models import User
from pvp.models import Round, RoundTask, RoundStatus, RoundPlayer
from tasks.models import Task

PLAYERS_IN_SEARCH = set()


class SearchEnemyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.user_id = self.user.id
        self.enemy = None
        self.match_start = False

        if self.user.is_authenticated:
            self.group_name = f'user_{self.user_id}'
            await self.accept()
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

        else:
            await self.close()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        PLAYERS_IN_SEARCH.discard(self.user_id)

    async def receive(self, text_data: json):
        data = json.loads(text_data)

        if data["type"] == "is_search" and data["is_search"]:

            if self.match_start:
                return

            if self.user_id in PLAYERS_IN_SEARCH:
                return

            PLAYERS_IN_SEARCH.add(self.user_id)
            print(PLAYERS_IN_SEARCH)

            self.enemy = await self.get_user(self.user_id)

            if not self.enemy:
                print("Противники не найдены")
                await self.send(text_data=json.dumps({
                    "type": "status",
                    "message": "Противники не найдены"
                }))
                return

            PLAYERS_IN_SEARCH.discard(self.user_id)
            PLAYERS_IN_SEARCH.discard(self.enemy)

            self.room_id = await self.start_round(
                self.user_id,
                self.enemy
            )

            for user in (self.user_id, self.enemy):
                await self.channel_layer.group_send(
                    f'user_{user}',
                    {
                        'type': 'room_id_message',
                        'message': self.room_id,
                    }
                )

    @database_sync_to_async
    def get_user(self, user_id):
        for uid in PLAYERS_IN_SEARCH:
            if uid != user_id:
                return uid


    @database_sync_to_async
    def start_round(self, user_id, enemy_id):
        tasks = Task.objects.all()[:3]
        if not tasks:
            raise ValueError("Нет задач для раунда")

        user = User.objects.get(pk=user_id)
        enemy = User.objects.get(pk=enemy_id)

        game_round = Round.objects.create(
            status=RoundStatus.IN_PROGRESS,
            started_at=now(),
            planed_finish=now() + timedelta(hours=2),
        )

        RoundPlayer.objects.bulk_create([
            RoundPlayer(round=game_round, player=user),
            RoundPlayer(round=game_round, player=enemy),
        ])

        for i, task in enumerate(tasks, start=1):
            RoundTask.objects.create(
                round=game_round,
                task=task,
                order=i
            )

        return game_round.id

    async def room_id_message(self, event):
        room_id = event['message']

        await self.send(text_data=json.dumps({
            'type': 'room_id',
            'room_id': room_id
        }))
