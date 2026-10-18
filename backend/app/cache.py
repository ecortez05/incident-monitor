import redis
import redis.asyncio as aioredis

from .config import REDIS_URL

_sync = redis.from_url(REDIS_URL, decode_responses=True)


# kept as functions (not module-level clients) so tests can swap them out
def get_redis() -> redis.Redis:
    return _sync


def get_async_redis() -> aioredis.Redis:
    # websocket handlers open their own connection for pub/sub
    return aioredis.from_url(REDIS_URL, decode_responses=True)
