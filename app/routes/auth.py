# ============================================================
# app/routes/auth.py
# Authentication routes: register and login.
# POST /auth/register  — create a new user account
# POST /auth/login     — exchange credentials for a JWT token
# GET  /auth/me        — return the authenticated user's profile
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import TokenOut, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _issue_token_for_credentials(email: str, password: str, db: Session) -> TokenOut:
    """Validate credentials and return a signed bearer token response."""
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": str(user.id)})
    return TokenOut(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


# ------------------------------------------------------------
# POST /auth/register
# ------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new SME or Admin account",
)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.

    - Checks that the email is not already registered.
    - Hashes the password before storing (never plain-text).
    - Returns the new user's public profile (no password hash).
    """
    # Check for duplicate email
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    # Create ORM object with hashed password
    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Reload from DB to get auto-generated id & created_at

    return new_user


# ------------------------------------------------------------
# POST /auth/login
# ------------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenOut,
    summary="Login and receive a JWT access token",
)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate with email and password.

    Returns a JWT bearer token. Include this in subsequent requests:
        Authorization: Bearer <token>

    Note: We return the same error for wrong email AND wrong password
    to prevent user enumeration attacks.
    """
    return _issue_token_for_credentials(payload.email, payload.password, db)


@router.post(
    "/token",
    response_model=TokenOut,
    summary="OAuth2 token endpoint for Swagger Authorize",
)
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2-compatible token endpoint used by Swagger UI.

    In this project, `username` maps to the user's email.
    """
    return _issue_token_for_credentials(form_data.username, form_data.password, db)


# ------------------------------------------------------------
# GET /auth/me
# ------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserOut,
    summary="Get the currently authenticated user's profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of the user attached to the Bearer token.
    Useful for the frontend to load user info after login.
    """
    return current_user
