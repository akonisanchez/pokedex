import time
from typing import Any
# In-memory cache to reduce repeated PokéAPI calls.
# Key -> (expires_at, value)
CACHE: dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 60 * 10  # 10 minutes

def cache_get(key: str):
    item = CACHE.get(key)
    if not item:
        return None
    expires_at, value = item
    if time.time() > expires_at:
        CACHE.pop(key, None)
        return None
    return value


def cache_set(key: str, value, ttl: int = CACHE_TTL_SECONDS):
    CACHE[key] = (time.time() + ttl, value)