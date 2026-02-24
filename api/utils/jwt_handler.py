"""
JWT Token Handler
File: api/utils/jwt_handler.py

Handles creation and verification of access tokens, refresh tokens.
Raw tokens are NEVER stored in the database; only bcrypt hashes.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.db.database import get_db
from api.utils.settings import settings


# ---------------------------------------------------------------------------
# Crypto context (bcrypt for hashing refresh / reset tokens in DB)
# ---------------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token extractor
_security = HTTPBearer()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


def _hash_token(raw_token: str) -> str:
    """Return a bcrypt hash of a raw token for safe DB storage."""
    return _pwd_context.hash(raw_token)


def _verify_hashed_token(raw_token: str, hashed: str) -> bool:
    """Verify a raw token against its stored bcrypt hash."""
    return _pwd_context.verify(raw_token, hashed)


def _sha256_hex(value: str) -> str:
    """Return the SHA-256 hex digest of a string (used for reset tokens)."""
    return hashlib.sha256(value.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return _password_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return _password_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# Access token
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data:          Payload dict – must include at least ``sub`` (user id).
        expires_delta: Custom expiry.  Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = _utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update(
        {
            "exp": expire,
            "iat": _utcnow(),
            "token_type": "access",
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ---------------------------------------------------------------------------
# Refresh token (JWT-based, rotated on each use)
# ---------------------------------------------------------------------------

def create_refresh_token(data: dict) -> str:
    """
    Create a signed JWT refresh token (long-lived, 7 days by default).

    Returns:
        Encoded JWT string (raw – caller must hash before storing in DB).
    """
    to_encode = data.copy()
    expire = _utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRY)
    to_encode.update(
        {
            "exp": expire,
            "iat": _utcnow(),
            "token_type": "refresh",
            # Add a random jti so every issued token is unique
            "jti": secrets.token_hex(16),
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_refresh_token(token: str) -> Dict:
    """
    Decode and validate a refresh JWT.

    Raises:
        HTTPException 401 – if token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Password-reset token (opaque random bytes, SHA-256 hashed for DB)
# ---------------------------------------------------------------------------

RESET_TOKEN_EXPIRE_MINUTES = 60  # 1 hour


def create_reset_token() -> tuple[str, str, datetime]:
    """
    Generate a secure password-reset token.

    Returns:
        (raw_token, sha256_hex_for_db, expiry_datetime_utc)
    """
    raw = secrets.token_urlsafe(48)
    hashed = _sha256_hex(raw)
    expires_at = _utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    return raw, hashed, expires_at


def verify_reset_token_hash(raw_token: str, stored_hash: str) -> bool:
    """Compare raw token against the SHA-256 hash stored in DB."""
    return _sha256_hex(raw_token) == stored_hash


# ---------------------------------------------------------------------------
# Access token verification
# ---------------------------------------------------------------------------

def verify_access_token(token: str) -> Dict:
    """
    Decode and validate a JWT access token.

    Raises:
        HTTPException 401 – if credentials cannot be validated.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependency: get_current_user
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency that extracts and validates the Bearer JWT,
    then returns the corresponding User object from the database.
    """
    from api.v1.models.users import User  # noqa: PLC0415

    token = credentials.credentials
    payload = verify_access_token(token)

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).filter(User.id == user_id))
    user: Optional[User] = result.scalars().first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    return user


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """
    Convenience dependency – same as get_current_user but named explicitly
    for routes that want to emphasise the 'active' constraint.
    """
    return current_user
