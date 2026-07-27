from datetime import datetime, timedelta, timezone

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

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

TOKEN_TTL_CONFIRM = timedelta(hours=24)
TOKEN_TTL_RESET = timedelta(hours=1)
MIN_PASSWORD_LEN = 6


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(expires_at: datetime, now: datetime) -> bool:
    """Check if a token is expired, handling both aware and naive datetimes."""
    if expires_at.tzinfo is not None:
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
    else:
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
    return expires_at <= now


def _validate_password(password: str) -> None:
    """Validate password meets minimum requirements."""
    if len(password) < MIN_PASSWORD_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Passwort muss mindestens {MIN_PASSWORD_LEN} Zeichen lang sein."
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


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get current authenticated user."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one()


def _build_confirm_body(raw_token: str) -> str:
    link = f"{settings.app_base_url}/confirm-email?token={raw_token}"
    return (
        f"Willkommen bei Tracking Success!\n\n"
        f"Bitte bestätige deine E-Mail-Adresse, indem du auf den folgenden Link klickst:\n"
        f"{link}\n\n"
        f"Dieser Link ist 24 Stunden gültig."
    )


def _build_reset_body(raw_token: str) -> str:
    link = f"{settings.app_base_url}/reset-password?token={raw_token}"
    return (
        f"Du hast ein neues Passwort angefordert.\n\n"
        f"Klicke auf den folgenden Link, um dein Passwort zurückzusetzen:\n"
        f"{link}\n\n"
        f"Falls du das nicht warst, kannst du diese E-Mail ignorieren.\n"
        f"Dieser Link ist 1 Stunde gültig."
    )


CONFIRM_SUBJECT = "E-Mail bestätigen — Tracking Success"
RESET_SUBJECT = "Passwort zurücksetzen — Tracking Success"


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
            detail="E-Mail nicht bestätigt. Bitte überprüfe dein Postfach."
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
async def get_me(user: User = Depends(get_current_user)):
    return user