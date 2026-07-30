from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.email_token import EmailToken
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token,
    ForgotPassword, ResendConfirmation, PasswordResetConfirm,
)
from app.services.auth import (
    verify_password, get_password_hash, create_access_token, decode_token,
    hash_token, generate_token,
)
from app.services.email import send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

TOKEN_TTL_CONFIRM = timedelta(hours=24)
TOKEN_TTL_RESET = timedelta(hours=1)
MIN_PASSWORD_LEN = 6


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(expires_at: datetime, now: datetime) -> bool:
    # SQLite returns naive datetimes; PostgreSQL returns aware. Normalize.
    if expires_at.tzinfo is None and now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    elif expires_at.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return expires_at <= now


def _validate_password(password: str) -> None:
    """Validate password meets minimum requirements."""
    if len(password) < MIN_PASSWORD_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {MIN_PASSWORD_LEN} characters long."
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> int:
    """Extract and validate JWT token, return user ID."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="User not found")
    return user_id


def _build_confirm_body(raw_token: str) -> str:
    link = f"{settings.app_base_url}/confirm-email?token={raw_token}"
    return (
        f"Welcome to Tracking Success!\n\n"
        f"Please confirm your email address by clicking the link below:\n"
        f"{link}\n\n"
        f"This link is valid for 24 hours."
    )


def _build_reset_body(raw_token: str) -> str:
    link = f"{settings.app_base_url}/reset-password?token={raw_token}"
    return (
        f"You requested a new password.\n\n"
        f"Click the link below to reset your password:\n"
        f"{link}\n\n"
        f"If this wasn't you, you can ignore this email.\n"
        f"This link is valid for 1 hour."
    )


CONFIRM_SUBJECT = "Confirm your email — Tracking Success"
RESET_SUBJECT = "Reset your password — Tracking Success"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    _validate_password(data.password)
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        is_active=False,
    )
    db.add(user)
    await db.flush()

    raw_token = generate_token()
    token = EmailToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        token_type="confirm",
        expires_at=_utcnow() + TOKEN_TTL_CONFIRM,
    )
    db.add(token)
    await db.flush()

    await send_email(str(user.email), CONFIRM_SUBJECT, _build_confirm_body(raw_token))
    return user


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Email not confirmed"
        )
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@router.get("/confirm/{token}")
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(token)
    result = await db.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.token_type == "confirm",
        )
    )
    email_token = result.scalar_one_or_none()
    if not email_token or email_token.used_at is not None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if _is_expired(email_token.expires_at, _utcnow()):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_result = await db.execute(select(User).where(User.id == email_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.is_active = True
    email_token.used_at = _utcnow()
    await db.flush()
    return {"message": "Email confirmed successfully"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")

    raw_token = generate_token()
    token = EmailToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        token_type="reset",
        expires_at=_utcnow() + TOKEN_TTL_RESET,
    )
    db.add(token)
    await db.flush()

    await send_email(str(user.email), RESET_SUBJECT, _build_reset_body(raw_token))
    return {"message": "Password reset email sent"}


@router.post("/reset-password/confirm")
async def confirm_password_reset(data: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    _validate_password(data.new_password)
    token_hash = hash_token(data.token)
    result = await db.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.token_type == "reset",
        )
    )
    email_token = result.scalar_one_or_none()
    if not email_token or email_token.used_at is not None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if _is_expired(email_token.expires_at, _utcnow()):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_result = await db.execute(select(User).where(User.id == email_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.hashed_password = get_password_hash(data.new_password)
    email_token.used_at = _utcnow()

    # Invalidate all other unused reset tokens for this user (Kilo review fix)
    siblings = await db.execute(
        select(EmailToken).where(
            EmailToken.user_id == user.id,
            EmailToken.token_type == "reset",
            EmailToken.used_at.is_(None),
            EmailToken.id != email_token.id,
        )
    )
    for sibling in siblings.scalars():
        sibling.used_at = _utcnow()

    await db.flush()
    return {"message": "Password updated successfully"}


@router.post("/resend-confirmation")
async def resend_confirmation(data: ResendConfirmation, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_active:
        raise HTTPException(status_code=400, detail="Email already confirmed")

    raw_token = generate_token()
    token = EmailToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        token_type="confirm",
        expires_at=_utcnow() + TOKEN_TTL_CONFIRM,
    )
    db.add(token)
    await db.flush()

    await send_email(str(user.email), CONFIRM_SUBJECT, _build_confirm_body(raw_token))
    return {"message": "Confirmation email sent"}


@router.get("/me", response_model=UserResponse)
async def get_me(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user