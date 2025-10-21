"""Rate limiting utilities using Redis."""

from typing import Optional
import redis.asyncio as redis
from fastapi import Request, HTTPException, status

from app.config import settings
from app.exceptions import RateLimitError


class RateLimiter:
    """Redis-based rate limiter."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = settings.rate_limit_enabled
    
    async def init(self):
        """Initialize Redis connection."""
        if self.enabled:
            self.redis_client = redis.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=True,
            )
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> bool:
        """Check if a key is rate limited.
        
        Args:
            key: Unique identifier (e.g., user_id, ip_address)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            True if rate limited, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        # Use Redis INCR with expiry
        current = await self.redis_client.get(key)
        
        if current is None:
            await self.redis_client.setex(key, window_seconds, 1)
            return False
        
        if int(current) >= max_requests:
            return True
        
        await self.redis_client.incr(key)
        return False
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> None:
        """Check rate limit and raise exception if exceeded.
        
        Raises:
            RateLimitError: If rate limit exceeded
        """
        is_limited = await self.is_rate_limited(key, max_requests, window_seconds)
        if is_limited:
            raise RateLimitError(
                f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds."
            )


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_by_ip(request: Request, max_requests: int = 60):
    """Rate limit by IP address dependency."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:ip:{client_ip}"
    await rate_limiter.check_rate_limit(key, max_requests, window_seconds=60)


async def rate_limit_by_user(user_id: int, max_requests: int = 100):
    """Rate limit by user ID."""
    key = f"rate_limit:user:{user_id}"
    await rate_limiter.check_rate_limit(key, max_requests, window_seconds=60)