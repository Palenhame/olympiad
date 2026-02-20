from functools import lru_cache

from redis.asyncio import Redis

from core.services.matchmaking_services import MatchmakingService
from search_enemy.services.search_enemy_cache import PlayerInSearchCache
from user_statistics.services.user_statistics_cache import StatisticsCache


@lru_cache
def get_redis_connection() -> Redis:
    return Redis(host="127.0.0.1", port=6379, db=1)


statistics_cache = StatisticsCache(get_redis_connection())
players_in_search = PlayerInSearchCache(get_redis_connection())
matchmaking_service = MatchmakingService(players_in_search)
