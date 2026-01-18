import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from users.models import User
from pvp.models import Round
from tasks.models import Task


class SearchEnemyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.user_id = self.user.id

        if self.user.is_authenticated:
            self.group_name = f'user_{self.user_id}'
            await self.accept()

        else:
            await self.close()



    async def disconnect(self, code):
        pass

    async def receive(self, text_data: json):

        if text_data == 'true':
            enemy = await self.get_user(self.user_id)



    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.exclude(pk=user_id).first()

    @database_sync_to_async
    def start_round(self, user_id, enemy_id):
        task = Task.objects.first()
        user = User.objects.get(pk=user_id)
        enemy = User.objects.get(pk=enemy_id)