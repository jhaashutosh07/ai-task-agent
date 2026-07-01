from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta
from typing import Optional, List
import os
from pathlib import Path

from .models import Base, UserModel, APIKeyModel, UsageLogModel
from auth.models import User, UserInDB, APIKey
from auth.jwt_handler import verify_api_key
from config import settings

# Build database URL — prefers DATABASE_URL env var (PostgreSQL on Neon/Render),
# falls back to local SQLite for development
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

if _db_url:
    DATABASE_URL = _db_url
else:
    # SQLite fallback for local dev
    data_dir = Path(settings.auth_db_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite+aiosqlite:///{settings.auth_db_path}"

# Disable asyncpg's prepared-statement cache when talking to a connection
# pooler (e.g. Supabase pgbouncer) to avoid "prepared statement already exists".
_connect_args = {"statement_cache_size": 0} if "asyncpg" in DATABASE_URL else {}
engine = create_async_engine(DATABASE_URL, echo=False, connect_args=_connect_args)
# Create async session factory
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize the database — create tables if missing.

    NOTE: intentionally does NOT drop tables, so user accounts and data persist
    across deploys/restarts. Set RESET_DB=true to force a one-off schema reset
    (e.g. after a breaking model change).
    """
    reset = os.environ.get("RESET_DB", "").lower() in ("1", "true", "yes")
    async with engine.begin() as conn:
        if reset:
            await conn.run_sync(Base.metadata.drop_all)
            print("Database reset (RESET_DB enabled)")
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized")


async def get_db() -> AsyncSession:
    """Get a database session"""
    async with async_session() as session:
        yield session


# User operations
async def create_user(email: str, username: str, hashed_password: str, role: str = "user") -> User:
    """Create a new user"""
    async with async_session() as session:
        user = UserModel(
            email=email,
            username=username,
            hashed_password=hashed_password,
            role=role
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return User(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            usage_quota=user.usage_quota,
            usage_today=user.usage_today,
            total_usage=user.total_usage
        )


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email"""
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user = result.scalar_one_or_none()

        if user:
            return UserInDB(
                id=user.id,
                email=user.email,
                username=user.username,
                hashed_password=user.hashed_password,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
                usage_quota=user.usage_quota,
                usage_today=user.usage_today,
                total_usage=user.total_usage
            )
        return None


async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID"""
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Reset usage if new day
            if user.usage_reset_date.date() < datetime.utcnow().date():
                user.usage_today = 0
                user.usage_reset_date = datetime.utcnow()
                await session.commit()

            return User(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
                usage_quota=user.usage_quota,
                usage_today=user.usage_today,
                total_usage=user.total_usage
            )
        return None


async def get_user_by_api_key(api_key: str) -> Optional[User]:
    """Get user by API key"""
    if not api_key.startswith("sk-"):
        return None

    prefix = api_key[:11]

    async with async_session() as session:
        # Find keys with matching prefix
        result = await session.execute(
            select(APIKeyModel).where(
                APIKeyModel.prefix == prefix,
                APIKeyModel.is_active == True
            )
        )
        keys = result.scalars().all()

        # Verify the full key against each potential match
        for key_model in keys:
            if verify_api_key(api_key, key_model.hashed_key):
                # Update last used
                key_model.last_used = datetime.utcnow()
                await session.commit()

                # Get user
                return await get_user_by_id(key_model.user_id)

        return None


async def update_user_login(user_id: str):
    """Update user's last login time"""
    async with async_session() as session:
        await session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        await session.commit()


async def update_user_usage(user_id: str, tokens: int):
    """Update user's token usage"""
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Reset if new day
            if user.usage_reset_date.date() < datetime.utcnow().date():
                user.usage_today = tokens
                user.usage_reset_date = datetime.utcnow()
            else:
                user.usage_today += tokens

            user.total_usage += tokens
            await session.commit()


# API Key operations
async def create_api_key(user_id: str, name: str, hashed_key: str, prefix: str) -> APIKey:
    """Create a new API key"""
    async with async_session() as session:
        key = APIKeyModel(
            user_id=user_id,
            name=name,
            hashed_key=hashed_key,
            prefix=prefix
        )
        session.add(key)
        await session.commit()
        await session.refresh(key)

        return APIKey(
            id=key.id,
            user_id=key.user_id,
            name=key.name,
            key=hashed_key,  # Note: This is the hashed key
            prefix=key.prefix,
            created_at=key.created_at,
            last_used=key.last_used,
            is_active=key.is_active
        )


async def get_user_api_keys(user_id: str) -> List[APIKey]:
    """Get all API keys for a user"""
    async with async_session() as session:
        result = await session.execute(
            select(APIKeyModel).where(
                APIKeyModel.user_id == user_id,
                APIKeyModel.is_active == True
            )
        )
        keys = result.scalars().all()

        return [
            APIKey(
                id=key.id,
                user_id=key.user_id,
                name=key.name,
                key="***hidden***",  # Don't expose the hash
                prefix=key.prefix,
                created_at=key.created_at,
                last_used=key.last_used,
                is_active=key.is_active
            )
            for key in keys
        ]


async def delete_api_key(key_id: str, user_id: str) -> bool:
    """Delete (deactivate) an API key"""
    async with async_session() as session:
        result = await session.execute(
            update(APIKeyModel)
            .where(
                APIKeyModel.id == key_id,
                APIKeyModel.user_id == user_id
            )
            .values(is_active=False)
        )
        await session.commit()
        return result.rowcount > 0


async def get_all_users() -> List[User]:
    """Get all users (admin function)"""
    async with async_session() as session:
        result = await session.execute(select(UserModel))
        users = result.scalars().all()

        return [
            User(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
                usage_quota=user.usage_quota,
                usage_today=user.usage_today,
                total_usage=user.total_usage
            )
            for user in users
        ]


# Usage logging
async def log_usage(
    user_id: str,
    endpoint: str,
    method: str,
    tokens_used: int = 0,
    cost: float = 0.0,
    provider: str = "",
    model: str = "",
    request_type: str = "",
    success: bool = True,
    error_message: str = None
):
    """Log API usage"""
    async with async_session() as session:
        log = UsageLogModel(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            tokens_used=tokens_used,
            cost=cost,
            provider=provider,
            model=model,
            request_type=request_type,
            success=success,
            error_message=error_message
        )
        session.add(log)
        await session.commit()
