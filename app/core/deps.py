# ============================================================
# app/core/deps.py
# Reusable FastAPI dependency functions.
# Inject these into routes with: Depends(get_current_user)
# ============================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# OAuth2 scheme — FastAPI reads the Bearer token from the Authorization header.
# tokenUrl points to the form-based token endpoint used by Swagger Authorize.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the JWT token from the request.
    Returns the authenticated User ORM object.

    Raises:
        401 Unauthorized if token is missing, invalid, or expired.
        401 Unauthorized if the user no longer exists in the database.

    Usage in a route:
        @router.get("/me")
        def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token → get user_id string
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception

    # Look up user in DB
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that additionally checks the user has the ADMIN role.
    Chain after get_current_user.

    Raises:
        403 Forbidden if the user is not an admin.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
