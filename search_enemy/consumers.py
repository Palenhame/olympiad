import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from core.services.redis_services import players_in_search, matchmaking_service
from users.models import User
from pvp.services.rounds_services import RoundService

round_service = RoundService()


class SearchEnemyConsumer(AsyncWebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.subject = None

    async def connect(self):
        self.user = self.scope['user']
        self.user_id = self.user.id
        print('connected')

        if self.user.is_authenticated:
            self.group_name = f'user_{self.user_id}'
            await self.accept()
            await self.channel_layer.group_add(self.group_name, self.channel_name)

        else:
            await self.close()

    async def disconnect(self, code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            if self.subject:
                print('have subject')
                await players_in_search.remove_player(self.subject, self.user_id)
                self.subject = None

    async def receive(self, text_data: json):
        data = json.loads(text_data)

        subject = data['subject']
        self.subject = subject

        if data["type"] == "is_search" and data["is_search"]:


            if await players_in_search.is_player_in_search(
                subject=subject,
                user_id=self.user_id,
            ):
                print(f'players_in_search {self.user_id}')
                return

            rating = await self.get_user_rating()

            self.enemy = await matchmaking_service.find_enemy(
                subject=subject, rating=rating, user_id=self.user_id
            )
            print(self.enemy)

            if not self.enemy:
                return

            self.room_id = await self.start_round()

            await self.send_inf_message()

    @database_sync_to_async
    def get_user_rating(self):
        return User.objects.get(pk=self.user_id).rating

    async def start_round(self):
        return await round_service.start_round(self.user_id, self.enemy)

    async def room_id_message(self, event):
        room_id = event['message']

        await self.send(text_data=json.dumps({'type': 'room_id', 'room_id': room_id}))

    async def send_inf_message(self):
        for user in (self.user_id, self.enemy):
            await self.channel_layer.group_send(
                f'user_{user}',
                {
                    'type': 'room_id_message',
                    'message': self.room_id,
                },
            )
