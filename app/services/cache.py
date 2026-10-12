"""Redis cache service"""

import logging
from typing import Any, Optional

import redis.asyncio as redis

from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Redis client instance
redis_client: redis.Redis


async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    logger.info("Redis connection established")


async def close_redis():
    """Close Redis connection"""
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


async def cache(
    key: str,
    expire: int = 3600,
    default: Any = None,
):
    """
    Decorator for caching function results in Redis

    Usage:
        @cache("user_profile:{user_id}", expire=3600)
        async def get_user_profile(user_id: str):
            ...
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Format cache key with args
            formatted_key = key.format(*args, **kwargs)

            # Try to get from cache
            cached = await redis_client.get(formatted_key)
            if cached:
                return cached

            # Call function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await redis_client.setex(formatted_key, expire, result)

            return result or default

        return wrapper

    return decorator


async def get_cached(key: str) -> Optional[Any]:
    """Get value from cache"""
    return await redis_client.get(key)


async def set_cached(key: str, value: Any, expire: int = 3600) -> bool:
    """Set value in cache"""
    try:
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        logger.error(f"Failed to cache {key}: {e}")
        return False


async def delete_cached(key: str) -> bool:
    """Delete value from cache"""
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Failed to delete cache {key}: {e}")
        return False
