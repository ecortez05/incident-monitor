import json

from . import cache
from .config import CHANNEL, STATS_KEY


def publish(kind: str, payload: dict) -> None:
    cache.get_redis().publish(CHANNEL, json.dumps({"type": kind, "data": payload}))


def clear_stats_cache() -> None:
    cache.get_redis().delete(STATS_KEY)
