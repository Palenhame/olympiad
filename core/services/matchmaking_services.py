from search_enemy.services.search_enemy_cache import PlayerInSearchCache


class MatchmakingService:

    def __init__(self, cache: PlayerInSearchCache):
        self.cache = cache

    async def find_enemy(self, subject, user_id, rating):
        if await self.cache.is_player_in_search(subject, user_id):
            print(f"[find_enemy] {user_id} уже в очереди")
            return None

        await self.cache.add_player(subject, user_id, rating)
        print(f"find_enemy {user_id} добавлен, рейтинг={rating}")

        enemy = await self.cache.search_player(
            subject=subject, rating=rating, excluded_user=user_id
        )
        print(f"find_enemy враг для {user_id}: {enemy}")

        if not enemy:
            return None

        await self.cache.remove_player(subject, user_id)

        return enemy

    async def determine_winner(
            self, round_id: int, user_id: int, enemy_id: int, statistics_cache
    ) -> int | None:
        user_tasks = await statistics_cache.get_all_tasks(round_id, user_id)
        enemy_tasks = await statistics_cache.get_all_tasks(round_id, enemy_id)
        user_correct, user_time = self.count_correct_and_time(user_tasks)
        enemy_correct, enemy_time = self.count_correct_and_time(enemy_tasks)

        if user_correct > enemy_correct:
            return user_id
        elif enemy_correct > user_correct:
            return enemy_id
        else:
            if user_time < enemy_time:
                return user_id
            elif enemy_time < user_time:
                return enemy_id
            else:
                return None

    @staticmethod
    def count_correct_and_time(tasks):
        correct_count = sum(
            1 for t in tasks.values() if t.get("is_correct") is True
        )
        total_time = sum(t.get("total_time") or 0 for t in tasks.values())
        return correct_count, total_time
