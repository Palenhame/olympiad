from django.core.cache import cache


class StatisticsCache:
    TTL = 60 * 60  # 1 час

    @staticmethod
    def key_base(round_id, user_id, round_task_id):
        return f"stats:{round_id}:{user_id}:{round_task_id}"

    @classmethod
    def key_attempts(cls, round_id, user_id, round_task_id):
        return cls.key_base(round_id, user_id, round_task_id) + ":attempts"

    @classmethod
    def key_data(cls, round_id, user_id, round_task_id):
        return cls.key_base(round_id, user_id, round_task_id) + ":data"

    @classmethod
    def register_attempt(cls, round_id, user_id, round_task_id, answer, is_correct):
        attempts_key = cls.key_attempts(round_id, user_id, round_task_id)
        cache.add(attempts_key, 0, timeout=cls.TTL)
        cache.incr(attempts_key)

        cache.set(
            cls.key_data(round_id, user_id, round_task_id),
            {
                "last_answer": answer,
                "is_correct": is_correct,
            },
            timeout=cls.TTL
        )

    @classmethod
    def get(cls, round_id, user_id, round_task_id):
        attempts = cache.get(cls.key_attempts(round_id, user_id, round_task_id), 0)
        data = cache.get(cls.key_data(round_id, user_id, round_task_id), {})
        data["attempts"] = attempts
        return data
