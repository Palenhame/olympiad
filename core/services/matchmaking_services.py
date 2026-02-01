from search_enemy.services.search_enemy_cache import PlayerInSearchCache


class MatchmakingService:

    def __init__(self, cache: PlayerInSearchCache):
        self.cache = cache

    async def find_enemy(self, subject, user_id, rating):
        if await self.cache.is_player_in_search(subject, user_id):
            return None

        await self.cache.add_player(subject, user_id, rating)

        enemy = await self.cache.search_player(
            subject=subject,
            rating=rating,
            excluded_user=user_id
        )

        if not enemy:
            return None

        await self.cache.remove_both_users(subject, user_id, enemy)

        return enemy
