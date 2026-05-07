# ============================================================
# app/core/security.py
# Password hashing and JWT token utilities.
# Used by the auth route and the get_current_user dependency.
# ============================================================

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ------------------------------------------------------------
# Password hashing
# Use PBKDF2-SHA256 for broad compatibility in local/dev environments.
# (bcrypt backend/version mismatches can break startup on some systems.)
# ------------------------------------------------------------
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return PBKDF2-SHA256 hash of a plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ------------------------------------------------------------
# JWT tokens
# Tokens are signed with SECRET_KEY using HS256.
# The payload contains: sub (user id), exp (expiry timestamp).
# ------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Dict to encode — must include {"sub": str(user_id)}.
        expires_delta: Custom TTL. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode a JWT token and return the subject (user id).

    Returns:
        User id string if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        return user_id
    except JWTError:
        return None
