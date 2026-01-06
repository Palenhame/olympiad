import json

from channels.generic.websocket import AsyncWebsocketConsumer


class PvpConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'pvp'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.send(
            text_data=json.dumps(
                    {'message': 'Соединение установленно'}
            )
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

