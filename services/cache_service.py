"""
Redis Cache Service for Munch AI Dating Assistant
Provides caching layer for frequent API responses
"""
import json
import os
from typing import Optional, Any
from datetime import timedelta
import hashlib


class CacheService:
    """
    Redis-based caching service with graceful fallback.
    If Redis is unavailable, operations are no-ops.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL (default: from REDIS_URL env var)
        """
        self._redis = None
        self._available = False

        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            import redis
            self._redis = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self._redis.ping()
            self._available = True
            print(f"   Redis cache connected: {redis_url}")
        except ImportError:
            print("   Redis package not installed. Caching disabled.")
        except Exception as e:
            print(f"   Redis unavailable ({e}). Caching disabled.")

    @property
    def available(self) -> bool:
        """Check if Redis is available"""
        return self._available

    def _make_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments"""
        key_data = f"{prefix}:{':'.join(str(a) for a in args)}"
        return f"munch:{key_data}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/unavailable
        """
        if not self._available:
            return None

        try:
            data = self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 300
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl_seconds: Time to live in seconds (default: 5 minutes)

        Returns:
            True if cached successfully
        """
        if not self._available:
            return False

        try:
            self._redis.setex(key, ttl_seconds, json.dumps(value))
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self._available:
            return False

        try:
            self._redis.delete(key)
            return True
        except Exception:
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Redis pattern (e.g., "munch:conversation:123:*")

        Returns:
            Number of keys deleted
        """
        if not self._available:
            return 0

        try:
            keys = self._redis.keys(pattern)
            if keys:
                return self._redis.delete(*keys)
            return 0
        except Exception:
            return 0

    # ===================== CONVERSATION CACHING =====================

    def get_conversation(self, conversation_id: int) -> Optional[dict]:
        """Get cached conversation data"""
        key = self._make_key("conversation", conversation_id)
        return self.get(key)

    def set_conversation(self, conversation_id: int, data: dict, ttl: int = 300) -> bool:
        """Cache conversation data (5 min default)"""
        key = self._make_key("conversation", conversation_id)
        return self.set(key, data, ttl)

    def invalidate_conversation(self, conversation_id: int) -> bool:
        """Invalidate conversation cache"""
        pattern = f"munch:conversation:{conversation_id}*"
        self.delete_pattern(pattern)
        return self.delete(self._make_key("conversation", conversation_id))

    # ===================== USER CACHING =====================

    def get_user_stats(self, user_id: int) -> Optional[dict]:
        """Get cached user stats"""
        key = self._make_key("user_stats", user_id)
        return self.get(key)

    def set_user_stats(self, user_id: int, stats: dict, ttl: int = 120) -> bool:
        """Cache user stats (2 min default)"""
        key = self._make_key("user_stats", user_id)
        return self.set(key, stats, ttl)

    def invalidate_user_stats(self, user_id: int) -> bool:
        """Invalidate user stats cache"""
        return self.delete(self._make_key("user_stats", user_id))

    # ===================== ANALYTICS CACHING =====================

    def get_analytics_trends(
        self,
        user_id: int,
        start_date: str,
        end_date: str,
        granularity: str
    ) -> Optional[dict]:
        """Get cached analytics trends"""
        key = self._make_key("trends", user_id, start_date, end_date, granularity)
        return self.get(key)

    def set_analytics_trends(
        self,
        user_id: int,
        start_date: str,
        end_date: str,
        granularity: str,
        data: dict,
        ttl: int = 300
    ) -> bool:
        """Cache analytics trends (5 min default)"""
        key = self._make_key("trends", user_id, start_date, end_date, granularity)
        return self.set(key, data, ttl)

    def invalidate_analytics(self, user_id: int) -> int:
        """Invalidate all analytics cache for user"""
        return self.delete_pattern(f"munch:trends:{user_id}:*")

    # ===================== AI RESPONSE CACHING =====================

    def get_ai_suggestion(self, conversation_id: int, message_hash: str) -> Optional[str]:
        """Get cached AI suggestion"""
        key = self._make_key("ai_suggestion", conversation_id, message_hash)
        return self.get(key)

    def set_ai_suggestion(
        self,
        conversation_id: int,
        message_hash: str,
        suggestion: str,
        ttl: int = 600
    ) -> bool:
        """Cache AI suggestion (10 min default)"""
        key = self._make_key("ai_suggestion", conversation_id, message_hash)
        return self.set(key, suggestion, ttl)

    @staticmethod
    def hash_messages(messages: list) -> str:
        """Create a hash of message content for cache key"""
        content = json.dumps([m.content if hasattr(m, 'content') else m for m in messages[-5:]])
        return hashlib.md5(content.encode()).hexdigest()[:12]

    # ===================== RATE LIMIT HELPERS =====================

    def get_rate_limit_count(self, key: str) -> int:
        """Get current rate limit count"""
        if not self._available:
            return 0

        try:
            count = self._redis.get(f"ratelimit:{key}")
            return int(count) if count else 0
        except Exception:
            return 0

    def increment_rate_limit(self, key: str, ttl: int = 60) -> int:
        """Increment rate limit counter"""
        if not self._available:
            return 0

        try:
            full_key = f"ratelimit:{key}"
            count = self._redis.incr(full_key)
            if count == 1:
                self._redis.expire(full_key, ttl)
            return count
        except Exception:
            return 0


# Singleton instance
_cache_instance: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get the cache service singleton"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
