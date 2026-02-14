import json
from typing import Any
from redis.asyncio import Redis


class StatisticsCache:
    TTL = 60 * 60  # 1 час

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def key(self, round_id: int, user_id: int) -> str:
        return f"stats:{round_id}:{user_id}"

    def total_time_key(self, round_id: int, user_id: int) -> str:
        return f"stats:{round_id}:{user_id}:total_time"

    async def register_attempt(
            self,
            round_id: int,
            user_id: int,
            round_task_id: int,
            answer: str,
            is_correct: bool,
    ) -> None:
        key = self.key(round_id, user_id)
        task_key = str(round_task_id)

        task_data_raw = await self.redis.hget(key, task_key)

        if task_data_raw:
            task_data = json.loads(task_data_raw)
        else:
            task_data = {
                "attempts": 0,
                "last_answer": None,
                "is_correct": None,
            }

        task_data["attempts"] += 1
        task_data["last_answer"] = answer
        task_data["is_correct"] = int(is_correct)

        await self.redis.hset(key, task_key, json.dumps(task_data))
        await self.redis.expire(key, self.TTL)

    async def set_total_time(
            self,
            round_id: int,
            user_id: int,
            total_time: float,  # секунды
    ) -> None:
        time_key = self.total_time_key(round_id, user_id)
        await self.redis.set(time_key, str(total_time), ex=self.TTL)

    async def get_total_time(
            self,
            round_id: int,
            user_id: int,
    ) -> float | None:
        time_key = self.total_time_key(round_id, user_id)
        total_time_raw = await self.redis.get(time_key)

        if not total_time_raw:
            return None

        return float(total_time_raw)

    async def get(
            self, round_id: int, user_id: int, round_task_id: int
    ) -> dict[str, Any]:
        key = self.key(round_id, user_id)
        task_key = str(round_task_id)

        task_data_raw = await self.redis.hget(key, task_key)
        if not task_data_raw:
            return {
                "attempts": 0,
                "last_answer": None,
                "is_correct": None,
                "total_time": None,
            }

        task_data = json.loads(task_data_raw)

        # Получаем total_time из отдельного ключа
        total_time = await self.get_total_time(round_id, user_id)

        return {
            "attempts": int(task_data.get("attempts", 0)),
            "last_answer": task_data.get("last_answer"),
            "is_correct": (
                bool(int(task_data.get("is_correct")))
                if task_data.get("is_correct") is not None
                else None
            ),
            "total_time": total_time,
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

        exists = await self.redis.hexists(key, task_key)
        if exists:
            return

        initial_data = {
            "attempts": 0,
            "last_answer": None,
            "is_correct": None,
        }

        await self.redis.hset(key, task_key, json.dumps(initial_data))
        await self.redis.expire(key, self.TTL)

    async def is_finish_solving(self, round_id: int, user_id: int) -> bool:
        key = self.key(round_id, user_id)

        if not await self.redis.exists(key):
            return False

        all_tasks = await self.redis.hgetall(key)
        if not all_tasks:
            return False

        for raw in all_tasks.values():
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8')

            task_data = json.loads(raw)

            if task_data.get("is_correct") is None:
                return False

        return True

    async def get_all_tasks(
            self, round_id: int, user_id: int
    ) -> dict[str, dict[str, Any]]:
        """
        Получить все задачи пользователя в раунде.

        Возвращает словарь вида:
        {
            "task_id": {
                "attempts": int,
                "last_answer": str | None,
                "is_correct": bool | None,
                "total_time": float | None
            },
            ...
        }
        """
        key = self.key(round_id, user_id)

        all_tasks_raw = await self.redis.hgetall(key)
        if not all_tasks_raw:
            return {}

        # Получаем total_time из отдельного ключа
        total_time = await self.get_total_time(round_id, user_id)

        result = {}
        for task_key, raw in all_tasks_raw.items():
            # Декодируем ключ и значение если они в bytes
            if isinstance(task_key, bytes):
                task_key = task_key.decode('utf-8')
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8')

            task_data = json.loads(raw)

            result[task_key] = {
                "attempts": int(task_data.get("attempts", 0)),
                "last_answer": task_data.get("last_answer"),
                "is_correct": (
                    bool(int(task_data.get("is_correct")))
                    if task_data.get("is_correct") is not None
                    else None
                ),
                "total_time": total_time,
            }

        return result

    async def delete_all_about_round(self, round_id: int, user_id: int, enemy_id: int) -> None:
        user_key = self.key(round_id, user_id)
        enemy_key = self.key(round_id, enemy_id)
        user_time_key = self.total_time_key(round_id, user_id)
        enemy_time_key = self.total_time_key(round_id, enemy_id)

        await self.redis.delete(user_key, enemy_key, user_time_key, enemy_time_key)