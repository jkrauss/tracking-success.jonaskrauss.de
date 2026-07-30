"""TDD tests for complete auth flows: email confirmation + password reset.

These tests cover:
1. Registration creates inactive user + sends confirmation email
2. Login blocked for inactive (unconfirmed) users
3. Email confirmation activates user
4. Forgot password: existing user gets reset email
5. Forgot password: nonexistent email returns 404 (per requirements)
6. Password reset with valid token works
7. Invalid/expired/used tokens rejected
8. Resend confirmation for inactive users

Token capture strategy: raw tokens only exist in the email body (captured via
mocked send_email). The DB stores sha256 hashes. Tests extract the token from
the mock call to simulate a user clicking the email link.
"""
import re
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.database import engine, Base, async_session
from app.models.user import User
from app.models.email_token import EmailToken
from sqlalchemy import select


def extract_token_from_email_body(mock_send):
    """Extract the raw token from a mocked send_email call's body argument.

    send_email is called as: send_email(to, subject, body) or send_email(to, subject, body, ...)
    The body contains a URL with ?token=XXX.
    """
    call = mock_send.call_args
    # Try keyword args first
    if call.kwargs and "body" in call.kwargs:
        body = call.kwargs["body"]
    elif call.kwargs and "content" in call.kwargs:
        body = call.kwargs["content"]
    elif len(call.args) >= 3:
        body = call.args[2]
    else:
        raise AssertionError(f"Could not find body in send_email call: {call}")
    match = re.search(r"[?&]token=([A-Za-z0-9_-]+)", body)
    assert match, f"No token found in email body: {body[:200]}"
    return match.group(1)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── 1. Registration ──────────────────────────────────────────────────────────


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_creates_inactive_user(self, client):
        """Register creates user with is_active=False."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock):
            resp = await client.post("/api/auth/register", json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_register_sends_confirmation_email(self, client):
        """Register triggers email send with a confirmation token."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock) as mock_send:
            resp = await client.post("/api/auth/register", json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            })
            assert resp.status_code == 201
            mock_send.assert_called_once()
            # The email body contains a confirmation link
            token = extract_token_from_email_body(mock_send)
            assert len(token) >= 20  # token_urlsafe(32) produces ~43 chars

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, client):
        """Duplicate email returns 409."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "dup@example.com", "password": "Pass123!"
            })
        with patch("app.routers.auth.send_email", new_callable=AsyncMock):
            resp = await client.post("/api/auth/register", json={
                "email": "dup@example.com", "password": "Pass456!"
            })
        assert resp.status_code == 409


# ── 2. Login gate on inactive ──────────────────────────────────────────────────


class TestLoginGate:
    @pytest.mark.asyncio
    async def test_login_blocked_for_inactive_user(self, client):
        """Login for unconfirmed user returns 403 'Email not confirmed'."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "inactive@example.com", "password": "Pass123!"
            })
        resp = await client.post("/api/auth/login", json={
            "email": "inactive@example.com", "password": "Pass123!"
        })
        assert resp.status_code == 403
        detail = resp.json()["detail"].lower()
        assert "confirm" in detail or "active" in detail or "confirmed" in detail

    @pytest.mark.asyncio
    async def test_login_works_for_active_user(self, client):
        """Login for confirmed user returns token."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "active@example.com", "password": "Pass123!"
            })
        # Manually activate
        async with async_session() as db:
            result = await db.execute(select(User).where(User.email == "active@example.com"))
            user = result.scalar_one()
            user.is_active = True
            await db.commit()
        resp = await client.post("/api/auth/login", json={
            "email": "active@example.com", "password": "Pass123!"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()


# ── 3. Email confirmation ──────────────────────────────────────────────────────


class TestConfirmEmail:
    @pytest.mark.asyncio
    async def test_confirm_email_activates_user(self, client):
        """Valid confirmation token activates user → login works."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock) as mock_send:
            await client.post("/api/auth/register", json={
                "email": "confirm@example.com", "password": "Pass123!"
            })
            token = extract_token_from_email_body(mock_send)
        resp = await client.get(f"/api/auth/confirm/{token}")
        assert resp.status_code == 200
        # User is now active
        async with async_session() as db:
            result = await db.execute(select(User).where(User.email == "confirm@example.com"))
            user = result.scalar_one()
            assert user.is_active is True
        # Login works
        resp = await client.post("/api/auth/login", json={
            "email": "confirm@example.com", "password": "Pass123!"
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_confirm_invalid_token_returns_400(self, client):
        resp = await client.get("/api/auth/confirm/invalid-token-xyz")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_confirm_expired_token_returns_400(self, client):
        """Expired token returns 400."""
        from datetime import datetime, timedelta, timezone
        import hashlib
        raw_token = "expired-token-abc"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        async with async_session() as db:
            user = User(email="expired@example.com", hashed_password="hash", is_active=False)
            db.add(user)
            await db.flush()
            expired = EmailToken(
                user_id=user.id,
                token_hash=token_hash,
                token_type="confirm",
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
            db.add(expired)
            await db.commit()
        resp = await client.get(f"/api/auth/confirm/{raw_token}")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_confirm_used_token_returns_400(self, client):
        """Already-used token returns 400."""
        from datetime import datetime, timedelta, timezone
        import hashlib
        raw_token = "used-token-xyz"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        async with async_session() as db:
            user = User(email="used@example.com", hashed_password="hash", is_active=True)
            db.add(user)
            await db.flush()
            used_token = EmailToken(
                user_id=user.id,
                token_hash=token_hash,
                token_type="confirm",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                used_at=datetime.now(timezone.utc),
            )
            db.add(used_token)
            await db.commit()
        resp = await client.get(f"/api/auth/confirm/{raw_token}")
        assert resp.status_code == 400


# ── 4. Forgot password ────────────────────────────────────────────────────────


class TestForgotPassword:
    @pytest.mark.asyncio
    async def test_forgot_password_existing_user_sends_email(self, client):
        """Forgot-password for existing user sends reset email."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "reset@example.com", "password": "Pass123!"
            })
        # Activate
        async with async_session() as db:
            result = await db.execute(select(User).where(User.email == "reset@example.com"))
            user = result.scalar_one()
            user.is_active = True
            await db.commit()
        with patch("app.routers.auth.send_email", new_callable=AsyncMock) as mock_send:
            resp = await client.post("/api/auth/forgot-password", json={
                "email": "reset@example.com"
            })
            assert resp.status_code == 200
            mock_send.assert_called_once()
            token = extract_token_from_email_body(mock_send)
            assert "/reset-password?token=" in mock_send.call_args.args[2] or \
                   "/reset-password?token=" in mock_send.call_args.kwargs.get("body", "")

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_user_returns_404(self, client):
        """Forgot-password for nonexistent email returns 404 (per requirements — tell user)."""
        resp = await client.post("/api/auth/forgot-password", json={
            "email": "nonexistent@example.com"
        })
        assert resp.status_code == 404


# ── 5. Password reset ──────────────────────────────────────────────────────────


class TestResetPassword:
    @pytest.mark.asyncio
    async def test_reset_password_valid_token_updates_password(self, client):
        """Valid reset token + new password → can login with new password."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "reset-ok@example.com", "password": "OldPass123!"
            })
        # Activate
        async with async_session() as db:
            result = await db.execute(select(User).where(User.email == "reset-ok@example.com"))
            user = result.scalar_one()
            user.is_active = True
            await db.commit()
        # Request reset
        with patch("app.routers.auth.send_email", new_callable=AsyncMock) as mock_send:
            await client.post("/api/auth/forgot-password", json={
                "email": "reset-ok@example.com"
            })
            token = extract_token_from_email_body(mock_send)
        # Reset password
        resp = await client.post("/api/auth/reset-password/confirm", json={
            "token": token,
            "new_password": "NewPass456!"
        })
        assert resp.status_code == 200
        # Login with new password
        resp = await client.post("/api/auth/login", json={
            "email": "reset-ok@example.com", "password": "NewPass456!"
        })
        assert resp.status_code == 200
        # Old password fails
        resp = await client.post("/api/auth/login", json={
            "email": "reset-ok@example.com", "password": "OldPass123!"
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token_returns_400(self, client):
        resp = await client.post("/api/auth/reset-password/confirm", json={
            "token": "invalid-reset-token",
            "new_password": "NewPass456!"
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_used_token_returns_400(self, client):
        """After using a reset token, it can't be used again."""
        from datetime import datetime, timedelta, timezone
        import hashlib
        raw_token = "used-reset-token"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        async with async_session() as db:
            user = User(email="reuse@example.com", hashed_password="hash", is_active=True)
            db.add(user)
            await db.flush()
            used_reset = EmailToken(
                user_id=user.id,
                token_hash=token_hash,
                token_type="reset",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                used_at=datetime.now(timezone.utc),
            )
            db.add(used_reset)
            await db.commit()
        resp = await client.post("/api/auth/reset-password/confirm", json={
            "token": raw_token,
            "new_password": "NewPass456!"
        })
        assert resp.status_code == 400


# ── 6. Resend confirmation ──────────────────────────────────────────────────────


class TestResendConfirmation:
    @pytest.mark.asyncio
    async def test_resend_confirmation_sends_new_email(self, client):
        """Resend-confirmation for inactive user sends a new confirmation email."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "resend@example.com", "password": "Pass123!"
            })
        with patch("app.routers.auth.send_email", new_callable=AsyncMock) as mock_send:
            resp = await client.post("/api/auth/resend-confirmation", json={
                "email": "resend@example.com"
            })
            assert resp.status_code == 200
            mock_send.assert_called_once()
            token = extract_token_from_email_body(mock_send)
            assert "/confirm-email?token=" in mock_send.call_args.args[2] or \
                   "/confirm-email?token=" in mock_send.call_args.kwargs.get("body", "")

    @pytest.mark.asyncio
    async def test_resend_confirmation_for_active_user_returns_400(self, client):
        """Resend for already-active user returns 400."""
        with patch("app.routers.auth.send_email", new_callable=AsyncMock):
            await client.post("/api/auth/register", json={
                "email": "already@example.com", "password": "Pass123!"
            })
        async with async_session() as db:
            result = await db.execute(select(User).where(User.email == "already@example.com"))
            user = result.scalar_one()
            user.is_active = True
            await db.commit()
        resp = await client.post("/api/auth/resend-confirmation", json={
            "email": "already@example.com"
        })
        assert resp.status_code == 400