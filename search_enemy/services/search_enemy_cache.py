import hashlib
import os
from functools import lru_cache

from django.conf import settings
from redis.asyncio import Redis

from django.core.cache import cache


class CorrectAnswerCache:
    TTL = 60 * 60

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
        self._scripts = {}

    async def _load_script(self, name: str) -> str:
        if name not in self._scripts:
            path = self.return_base_path_to_script() + name
            with open(path, 'r') as f:
                code = f.read()
                self._scripts[name] = {
                    'code': code,
                    'sha': await self.redis.script_load(code),
                }
        return self._scripts[name]

    async def add_player(self, subject: str, user_id: int, rating: int) -> None:
        await self.redis.zadd(subject, {str(user_id): rating})

    async def search_player(
            self, subject: str, rating: int, excluded_user: int
    ) -> int | None:
        delta = 300
        lua_script = await self._load_script('find_and_return_user.lua')

        user_id = await self.redis.evalsha(
            lua_script['sha'], 1, subject, rating - delta, rating + delta, excluded_user
        )

        return int(user_id) if user_id else None

    async def remove_player(self, subject: str, user_id: int) -> None:
        print(f"Trying to remove: subject={subject}, user_id={user_id}, type={type(user_id)}")
        result = await self.redis.zrem(subject, str(user_id))
        print(f"Removed {result} elements")

    async def is_player_in_search(self, subject: str, user_id: int) -> bool:
        return (await self.redis.zscore(subject, str(user_id))) is not None

    async def remove_both_users(
            self, subject: str, first_user_id: int, second_user_id: int
    ) -> None:
        lua_script = await self._load_script('remove_two_users.lua')

        await self.redis.evalsha(
            lua_script['sha'], 1, subject, first_user_id, second_user_id
        )

    def return_base_path_to_script(self) -> str:
        return os.path.join(settings.BASE_DIR, 'search_enemy/services', 'lua_scripts/')

# async def main():
#     player = PlayerInSearchCache(get_redis_connection())
#     await player.add_player('math', 123, 122)
#
# asyncio.run(main())
