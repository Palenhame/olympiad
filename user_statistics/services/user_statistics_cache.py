import json
from typing import Any

from redis.asyncio import Redis


class StatisticsCache:
    TTL = 60 * 60  # 1 час

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def key(self, round_id: int, user_id: int) -> str:
        return f"stats:{round_id}:{user_id}"

    async def register_attempt(
            self,
            round_id: int,
            user_id: int,
            round_task_id: int,
            answer: str,
            is_correct: bool,
    ) -> None:
        key = self.key(round_id, user_id)

        # Получаем текущие данные для заданий
        task_key = str(round_task_id)
        task_data_raw = await self.redis.hget(key, task_key)

        if task_data_raw:
            task_data = json.loads(task_data_raw)
        else:
            task_data = {"attempts": 0, "last_answer": None, "is_correct": None}

        # Обновляем данные для текущего задания
        task_data["attempts"] += 1
        task_data["last_answer"] = answer
        task_data["is_correct"] = int(is_correct)

        # Сохраняем обновленные данные
        await self.redis.hset(key, task_key, json.dumps(task_data))
        await self.redis.expire(key, self.TTL)

    async def get(
            self, round_id: int, user_id: int, round_task_id: int
    ) -> dict[str, Any]:
        key = self.key(round_id, user_id)
        task_key = str(round_task_id)

        task_data_raw = await self.redis.hget(key, task_key)
        if not task_data_raw:
            return {"attempts": 0, "last_answer": None, "is_correct": None}

        task_data = json.loads(task_data_raw)
        return {
            "attempts": int(task_data.get("attempts", 0)),
            "last_answer": task_data.get("last_answer"),
            "is_correct": (
                bool(int(task_data.get("is_correct")))
                if task_data.get("is_correct") is not None
                else None
            ),
        }

    async def is_exists(self, round_id: int, user_id: int) -> bool:
        key = self.key(round_id, user_id)
        return await self.redis.exists(key) == 1

    async def create_statistics_tables(
        self,
        round_id: int,
        user_id: int,
        round_task_id: int,
    ) -> None:
        key = self.key(round_id, user_id)
        task_key = str(round_task_id)

        # Если уже есть — ничего не делаем
        exists = await self.redis.hexists(key, task_key)
        if exists:
            return

        # Создаем базовую запись для задания
        initial_data = {
            "attempts": 0,
            "last_answer": None,
            "is_correct": None,
        }

        await self.redis.hset(key, task_key, json.dumps(initial_data))
        await self.redis.expire(key, self.TTL)