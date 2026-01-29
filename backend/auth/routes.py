from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from typing import List

from .models import (
    User, UserCreate, UserLogin, Token,
    APIKey, APIKeyCreate, APIKeyResponse, UsageStats
)
from .jwt_handler import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token,
    verify_token, generate_api_key
)
from .dependencies import get_current_user, get_current_active_user, require_admin
from database.connection import (
    create_user, get_user_by_email, get_user_by_id,
    create_api_key, get_user_api_keys, delete_api_key,
    update_user_login, get_all_users
)
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if email already exists
        existing_user = await get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user with hashed password
        hashed_password = get_password_hash(user_data.password)
        user = await create_user(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )

        return user
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Registration error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access token"""
    # Get user by email
    user = await get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Update last login
    await update_user_login(user.id)

    # Create tokens
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    payload = verify_token(refresh_token, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Get user
    user = await get_user_by_id(payload.get("user_id"))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new tokens
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user


@router.get("/usage", response_model=UsageStats)
async def get_usage(current_user: User = Depends(get_current_active_user)):
    """Get current user's usage statistics"""
    return UsageStats(
        user_id=current_user.id,
        tokens_used_today=current_user.usage_today,
        tokens_quota=current_user.usage_quota,
        total_tokens_used=current_user.total_usage,
        requests_today=0,  # TODO: Track requests
        cost_today=0.0,  # TODO: Track costs
        cost_total=0.0
    )


# API Key Management
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_new_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new API key"""
    # Generate key
    full_key, hashed_key = generate_api_key()
    prefix = full_key[:11]  # "sk-" + first 8 chars

    # Store in database
    api_key = await create_api_key(
        user_id=current_user.id,
        name=key_data.name,
        hashed_key=hashed_key,
        prefix=prefix
    )

    # Return full key (only time it's shown)
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=full_key,
        prefix=prefix,
        created_at=api_key.created_at
    )


@router.get("/api-keys", response_model=List[APIKey])
async def list_api_keys(current_user: User = Depends(get_current_active_user)):
    """List user's API keys (without the actual key)"""
    keys = await get_user_api_keys(current_user.id)
    return keys


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Revoke (delete) an API key"""
    success = await delete_api_key(key_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return {"message": "API key revoked"}


# Admin endpoints
@router.get("/users", response_model=List[User])
async def list_users(admin: User = Depends(require_admin)):
    """List all users (admin only)"""
    return await get_all_users()
