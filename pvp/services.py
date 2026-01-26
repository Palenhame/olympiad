from enum import StrEnum

import redis.asyncio as redis


class RedisFields(StrEnum):
    IS_CORRECT = 'is_correct'
    USER_ANSER = 'user_anser'


class RedisService:
    def __init__(self):
        self.redis = redis.Redis(host="localhost", port=6379, db=0)
        self.redis.flushdb()

    async def save_statistics(
            self,
            roudnd_task_id: int,
            user_id: int,
            is_correct: bool,
            user_anser: str
    ) -> None:
        await self.redis.hset(
            f'roudnd_task_id:{roudnd_task_id}:user_id:{user_id}',
            mapping={
                RedisFields.IS_CORRECT: is_correct,
                RedisFields.USER_ANSER: user_anser
            }
        )
