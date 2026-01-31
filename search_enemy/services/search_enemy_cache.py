from functools import lru_cache

from redis.asyncio import Redis

from django.core.cache import cache


@lru_cache
def get_redis_connection() -> Redis:
    return Redis(host="redis", port=6379, db=0)


class CorrectAnswerCache:
    TTL = 60 * 60  # 1 час

    @classmethod
    def key(cls, round_task_id: int, task_index: int) -> str:
        return f"correct_answer:round_task:{round_task_id}:task_index:{task_index}"

    @classmethod
    def set(
            cls,
            round_task_id: int,
            task_index: int,
            correct_answer,
            ttl: int | None = None,
    ) -> None:
        cache.set(
            cls.key(round_task_id, task_index),
            correct_answer,
            timeout=ttl or cls.TTL,
        )

    @classmethod
    def get(cls, round_task_id: int, task_index: int):
        return cache.get(cls.key(round_task_id, task_index))

    @classmethod
    def delete(cls, round_task_id: int, task_index: int) -> None:
        cache.delete(cls.key(round_task_id, task_index))


class PlayerInSearchCache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def add_player(self, subject: str, user_id: int, rating: int) -> None:
        await self.redis.zadd(subject, {f'{user_id}': rating})

    async def search_player(self, subject: str, rating: int) -> int | None:
        delta = 50
        with open('lua_scripts/find_and_return_user.lua', 'r') as file:
            lua_script = file.read()

        user_id = await self.redis.eval(
            lua_script,
            0,
            rating - delta,
            rating + delta
        )

        return int(user_id) if user_id else None

    async def remove_player(self, subject: str, user_id: int) -> None:
        await self.redis.zrem(subject, str(user_id))
