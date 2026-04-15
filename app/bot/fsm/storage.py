"""
FSM Storage implementations.

Supports both Redis (production) and Memory (development/testing) storage.
"""

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class FSMStorage:
    """Base abstract class for FSM storage."""
    
    async def get_data(self, user_id: int) -> dict[str, Any]:
        """Get user data from storage."""
        raise NotImplementedError
    
    async def set_data(self, user_id: int, data: dict[str, Any]) -> None:
        """Save user data to storage."""
        raise NotImplementedError
    
    async def delete_data(self, user_id: int) -> None:
        """Delete user data from storage."""
        raise NotImplementedError
    
    async def update_data(self, user_id: int, update_data: dict[str, Any]) -> None:
        """Update specific fields in user data."""
        raise NotImplementedError


class MemoryFSMStorage(FSMStorage):
    """In-memory storage for development/testing."""
    
    def __init__(self):
        self._storage: dict[int, dict[str, Any]] = {}
    
    async def get_data(self, user_id: int) -> dict[str, Any]:
        """Get user data from memory."""
        return self._storage.get(user_id, {})
    
    async def set_data(self, user_id: int, data: dict[str, Any]) -> None:
        """Save user data to memory."""
        self._storage[user_id] = data
        logger.debug(f"FSM data saved for user {user_id}: {data}")
    
    async def delete_data(self, user_id: int) -> None:
        """Delete user data from memory."""
        if user_id in self._storage:
            del self._storage[user_id]
            logger.debug(f"FSM data deleted for user {user_id}")
    
    async def update_data(self, user_id: int, update_data: dict[str, Any]) -> None:
        """Update specific fields in user data."""
        if user_id not in self._storage:
            self._storage[user_id] = {}
        
        self._storage[user_id].update(update_data)
        logger.debug(f"FSM data updated for user {user_id}: {update_data}")


class RedisFSMStorage(FSMStorage):
    """Redis-based storage for production."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._redis = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        self._prefix = "fsm:user:"
    
    async def get_data(self, user_id: int) -> dict[str, Any]:
        """Get user data from Redis."""
        key = f"{self._prefix}{user_id}"
        data = await self._redis.get(key)
        
        if data:
            return json.loads(data)
        return {}
    
    async def set_data(self, user_id: int, data: dict[str, Any]) -> None:
        """Save user data to Redis."""
        key = f"{self._prefix}{user_id}"
        await self._redis.set(key, json.dumps(data))
        logger.debug(f"FSM data saved to Redis for user {user_id}: {data}")
    
    async def delete_data(self, user_id: int) -> None:
        """Delete user data from Redis."""
        key = f"{self._prefix}{user_id}"
        await self._redis.delete(key)
        logger.debug(f"FSM data deleted from Redis for user {user_id}")
    
    async def update_data(self, user_id: int, update_data: dict[str, Any]) -> None:
        """Update specific fields in user data."""
        current_data = await self.get_data(user_id)
        current_data.update(update_data)
        await self.set_data(user_id, current_data)
        logger.debug(f"FSM data updated in Redis for user {user_id}: {update_data}")
    
    async def close(self):
        """Close Redis connection."""
        await self._redis.close()


def create_fsm_storage(
    use_redis: bool = False,
    redis_url: str = "redis://localhost:6379/0",
) -> FSMStorage:
    """
    Create FSM storage instance.
    
    Args:
        use_redis: If True, use Redis storage. Otherwise, use memory.
        redis_url: Redis connection URL (only used if use_redis=True).
    
    Returns:
        FSMStorage instance.
    """
    if use_redis:
        return RedisFSMStorage(redis_url)
    return MemoryFSMStorage()
