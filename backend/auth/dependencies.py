from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional

from .jwt_handler import verify_token, verify_api_key
from .models import User, TokenData
from database.connection import get_user_by_id, get_user_by_api_key

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> User:
    """
    Get the current authenticated user from JWT token or API key.
    Raises 401 if not authenticated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try JWT token first
    if credentials and credentials.credentials:
        payload = verify_token(credentials.credentials, "access")
        if payload:
            user_id = payload.get("user_id")
            if user_id:
                user = await get_user_by_id(user_id)
                if user and user.is_active:
                    return user

    # Try API key
    if api_key:
        user = await get_user_by_api_key(api_key)
        if user and user.is_active:
            return user

    raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user, raise 403 if inactive"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.
    Does not raise exception if not authenticated.
    """
    # Try JWT token first
    if credentials and credentials.credentials:
        payload = verify_token(credentials.credentials, "access")
        if payload:
            user_id = payload.get("user_id")
            if user_id:
                user = await get_user_by_id(user_id)
                if user and user.is_active:
                    return user

    # Try API key
    if api_key:
        user = await get_user_by_api_key(api_key)
        if user and user.is_active:
            return user

    return None


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def check_usage_quota(user: User) -> bool:
    """Check if user has remaining usage quota"""
    return user.usage_today < user.usage_quota


async def require_quota(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require user to have remaining quota"""
    if not check_usage_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily usage quota exceeded"
        )
    return current_user
