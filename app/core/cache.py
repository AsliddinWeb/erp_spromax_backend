import json
import redis
from typing import Any, Optional
from app.config import settings

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    try:
        raw = get_redis().get(key)
        return json.loads(raw) if raw is not None else None
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """ttl — seconds. Default 5 minutes."""
    try:
        get_redis().setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def cache_delete(key: str) -> None:
    try:
        get_redis().delete(key)
    except Exception:
        pass


def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching pattern, e.g. 'dashboard:*'"""
    try:
        r = get_redis()
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception:
        pass
