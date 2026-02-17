import json
from typing import Any
from redis.asyncio import Redis


class StatisticsCache:
    TTL = 60 * 60

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def key(self, round_id: int, user_id: int) -> str:
        return f"stats:{round_id}:{user_id}"

    def total_time_key(self, round_id: int, user_id: int) -> str:
        return f"stats:{round_id}:{user_id}:total_time"

    def index_map_key(self, round_id: int, user_id: int) -> str:
        return f"stats:{round_id}:{user_id}:index_map"

    async def create_statistics_tables(
            self,
            round_id: int,
            user_id: int,
            round_task_id: int,
            task_index: int,
    ) -> None:
        key = self.key(round_id, user_id)
        task_key = str(round_task_id)

        exists = await self.redis.hexists(key, task_key)
        if not exists:
            initial_data = {"attempts": 0, "last_answer": None, "is_correct": None}
            await self.redis.hset(key, task_key, json.dumps(initial_data))
            await self.redis.expire(key, self.TTL)

        map_key = self.index_map_key(round_id, user_id)
        await self.redis.hset(map_key, str(task_index), str(round_task_id))
        await self.redis.expire(map_key, self.TTL)

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
        task_data = json.loads(task_data_raw) if task_data_raw else {
            "attempts": 0, "last_answer": None, "is_correct": None
        }

        task_data["attempts"] += 1
        task_data["last_answer"] = answer
        task_data["is_correct"] = int(is_correct)

        await self.redis.hset(key, task_key, json.dumps(task_data))
        await self.redis.expire(key, self.TTL)

    async def set_total_time(self, round_id: int, user_id: int, total_time: float) -> None:
        await self.redis.set(self.total_time_key(round_id, user_id), str(total_time), ex=self.TTL)

    async def get_total_time(self, round_id: int, user_id: int) -> float | None:
        raw = await self.redis.get(self.total_time_key(round_id, user_id))
        return float(raw) if raw else None

    async def get(self, round_id: int, user_id: int, round_task_id: int) -> dict[str, Any]:
        key = self.key(round_id, user_id)
        task_data_raw = await self.redis.hget(key, str(round_task_id))
        if not task_data_raw:
            return {"attempts": 0, "last_answer": None, "is_correct": None, "total_time": None}

        task_data = json.loads(task_data_raw)
        total_time = await self.get_total_time(round_id, user_id)
        is_correct = task_data.get("is_correct")
        return {
            "attempts": int(task_data.get("attempts", 0)),
            "last_answer": task_data.get("last_answer"),
            "is_correct": bool(int(is_correct)) if is_correct is not None else None,
            "total_time": total_time,
        }

    async def is_exists(self, round_id: int, user_id: int) -> bool:
        return await self.redis.exists(self.key(round_id, user_id)) == 1

    async def is_finish_solving(self, round_id: int, user_id: int) -> bool:
        key = self.key(round_id, user_id)
        if not await self.redis.exists(key):
            return False
        all_tasks = await self.redis.hgetall(key)
        if not all_tasks:
            return False
        for raw in all_tasks.values():
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            if json.loads(raw).get("is_correct") is None:
                return False
        return True

    async def get_all_tasks(self, round_id: int, user_id: int) -> dict[str, dict[str, Any]]:
        key = self.key(round_id, user_id)
        all_tasks_raw = await self.redis.hgetall(key)
        if not all_tasks_raw:
            return {}

        total_time = await self.get_total_time(round_id, user_id)
        result = {}
        for task_key, raw in all_tasks_raw.items():
            if isinstance(task_key, bytes):
                task_key = task_key.decode("utf-8")
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            task_data = json.loads(raw)
            is_correct = task_data.get("is_correct")
            result[task_key] = {
                "attempts": int(task_data.get("attempts", 0)),
                "last_answer": task_data.get("last_answer"),
                "is_correct": bool(int(is_correct)) if is_correct is not None else None,
                "total_time": total_time,
            }
        return result

    async def _get_round_task_id(self, round_id: int, user_id: int, task_index: int) -> str | None:
        map_key = self.index_map_key(round_id, user_id)
        val = await self.redis.hget(map_key, str(task_index))
        if val is None:
            return None
        return val.decode("utf-8") if isinstance(val, bytes) else val

    async def both_answered(
            self, round_id: int, user_id: int, enemy_id: int, task_index: int
    ) -> bool:
        user_task_id = await self._get_round_task_id(round_id, user_id, task_index)
        enemy_task_id = await self._get_round_task_id(round_id, enemy_id, task_index)

        if not user_task_id or not enemy_task_id:
            return False

        user_raw = await self.redis.hget(self.key(round_id, user_id), user_task_id)
        enemy_raw = await self.redis.hget(self.key(round_id, enemy_id), enemy_task_id)

        if not user_raw or not enemy_raw:
            return False

        user_data = json.loads(user_raw)
        enemy_data = json.loads(enemy_raw)

        return (
                user_data.get("is_correct") is not None
                and enemy_data.get("is_correct") is not None
        )

    async def get_task_stats(self, round_id: int, user_id: int, task_index: int) -> dict:
        round_task_id = await self._get_round_task_id(round_id, user_id, task_index)
        if not round_task_id:
            return {"is_correct": None}

        raw = await self.redis.hget(self.key(round_id, user_id), round_task_id)
        if not raw:
            return {"is_correct": None}

        data = json.loads(raw)
        is_correct = data.get("is_correct")
        return {
            "is_correct": bool(int(is_correct)) if is_correct is not None else None
        }

    async def get_round_stats(self, round_id: int, user_id: int, enemy_id: int) -> dict:
        user_tasks = await self.get_all_tasks(round_id, user_id)
        enemy_tasks = await self.get_all_tasks(round_id, enemy_id)

        total_tasks = len(user_tasks)
        user_answered = sum(1 for t in user_tasks.values() if t["is_correct"] is not None)
        user_correct = sum(1 for t in user_tasks.values() if t["is_correct"] is True)
        enemy_correct = sum(1 for t in enemy_tasks.values() if t["is_correct"] is True)

        return {
            "total_tasks": total_tasks,
            "user_answered": user_answered,
            "user_correct": user_correct,
            "enemy_correct": enemy_correct,
        }

    async def delete_all_about_round(self, round_id: int, user_id: int, enemy_id: int) -> None:
        await self.redis.delete(
            self.key(round_id, user_id),
            self.key(round_id, enemy_id),
            self.total_time_key(round_id, user_id),
            self.total_time_key(round_id, enemy_id),
            self.index_map_key(round_id, user_id),
            self.index_map_key(round_id, enemy_id),
        )

    def technical_finish_key(self, round_id: int) -> str:
        return f"technical_finish:{round_id}"

    async def technical_finish_add(self, round_id: int) -> None:
        await self.redis.set(self.technical_finish_key(round_id), 1, ex=60)

    async def is_technical_finish(self, round_id: int) -> bool:
        a = await self.redis.exists(self.technical_finish_key(round_id))
        print(a)
        return await self.redis.exists(self.technical_finish_key(round_id)) == 1
