"""Rate limiting configuration for visitors."""

from fastapi import Request, HTTPException
from app.core.rate_limit import rate_limiter
from app.models.user import User, UserRole


# Visitor-specific rate limits (more restrictive)
VISITOR_RATE_LIMITS = {
    "per_minute": 10,  # 10 requests per minute
    "per_hour": 100,   # 100 requests per hour
    "per_day": 500,    # 500 requests per day
}

# Standard user rate limits
STANDARD_RATE_LIMITS = {
    "per_minute": 60,
    "per_hour": 1000,
    "per_day": 10000,
}


async def check_visitor_rate_limit(request: Request, user: User):
    """
    Check rate limit specifically for visitors.
    Visitors have more restrictive limits than other users.
    """
    if not rate_limiter.enabled:
        return
    
    # Get rate limits based on role
    if user.role == UserRole.VISITOR:
        limits = VISITOR_RATE_LIMITS
    else:
        limits = STANDARD_RATE_LIMITS
    
    # Check per-minute limit
    key_minute = f"rate_limit:user:{user.id}:minute"
    is_limited = await rate_limiter.is_rate_limited(
        key_minute,
        limits["per_minute"],
        window_seconds=60
    )
    
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {limits['per_minute']} requests per minute."
        )
    
    # Check per-hour limit
    key_hour = f"rate_limit:user:{user.id}:hour"
    is_limited = await rate_limiter.is_rate_limited(
        key_hour,
        limits["per_hour"],
        window_seconds=3600
    )
    
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {limits['per_hour']} requests per hour."
        )
    
    # Check per-day limit (only for visitors)
    if user.role == UserRole.VISITOR:
        key_day = f"rate_limit:user:{user.id}:day"
        is_limited = await rate_limiter.is_rate_limited(
            key_day,
            limits["per_day"],
            window_seconds=86400
        )
        
        if is_limited:
            raise HTTPException(
                status_code=429,
                detail=f"Daily rate limit exceeded. Maximum {limits['per_day']} requests per day."
            )


async def get_rate_limit_info(user: User) -> dict:
    """Get rate limit information for a user."""
    if user.role == UserRole.VISITOR:
        limits = VISITOR_RATE_LIMITS
    else:
        limits = STANDARD_RATE_LIMITS
    
    return {
        "role": user.role.value,
        "limits": {
            "per_minute": limits["per_minute"],
            "per_hour": limits["per_hour"],
            "per_day": limits.get("per_day"),
        },
        "note": "Visitor accounts have more restrictive rate limits"
    }