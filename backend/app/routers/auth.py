from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, PasswordReset, PasswordResetConfirm
from app.services.auth import (
    verify_password, get_password_hash, create_access_token, decode_token
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


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
    # Verify user still exists
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


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=data.email, hashed_password=get_password_hash(data.password))
    db.add(user)
    await db.flush()
    return user


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.post("/reset-password")
async def request_password_reset(data: PasswordReset, db: AsyncSession = Depends(get_db)):
    """Request a password reset. Always returns success to prevent email enumeration."""
    # In production, send email with reset token.
    # For now, just acknowledge.
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password/confirm")
async def confirm_password_reset(data: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """Confirm password reset with token."""
    payload = decode_token(data.token)
    if not payload or "reset" not in payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(data.new_password)
    await db.flush()
    return {"message": "Password updated successfully"}
