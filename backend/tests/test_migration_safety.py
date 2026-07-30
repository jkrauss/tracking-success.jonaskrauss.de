"""Tests for metric migration safety — existing users must not be touched."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from sqlalchemy import select

from app.main import app
from app.database import engine, Base, async_session
from app.models.user import User
from app.models.metric import MetricConfig


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


async def _create_active_user(email: str, password: str) -> int:
    """Create and activate a user, return user_id."""
    async with async_session() as db:
        from app.services.auth import get_password_hash
        user = User(email=email, hashed_password=get_password_hash(password), is_active=True)
        db.add(user)
        await db.flush()
        user_id = user.id
        await db.commit()
    return user_id


async def _get_token(client: AsyncClient, email: str, password: str) -> str:
    """Login and return access token."""
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


async def _create_old_metric(user_id: int, slug: str, name: str):
    """Simulate an old-style metric for an existing user."""
    async with async_session() as db:
        config = MetricConfig(
            user_id=user_id,
            name=name,
            slug=slug,
            metric_type="bool",
            has_goal=True,
            goal_type="bool",
            order=0,
        )
        db.add(config)
        await db.commit()


class TestInitDefaultsSafety:
    """init-defaults must never touch existing metrics."""

    @pytest.mark.asyncio
    async def test_new_user_gets_new_defaults(self, client):
        """New user without metrics gets the new default set."""
        user_id = await _create_active_user("new@example.com", "Pass123!")
        token = await _get_token(client, "new@example.com", "Pass123!")

        resp = await client.post(
            "/api/yaml/init-defaults",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        assert resp.json()["count"] == 11

        # Verify the new defaults are English
        async with async_session() as db:
            result = await db.execute(
                select(MetricConfig).where(MetricConfig.user_id == user_id)
            )
            configs = result.scalars().all()
            names = {c.name for c in configs}
            assert "Sleep" in names
            assert "Meditation" in names
            assert "Mindset" in names
            assert "Diet" in names
            assert "Exercise" in names
            assert "Work Duration" in names
            assert "Mood" in names
            assert "Output" in names
            assert "Focus" in names
            assert "Reading" in names
            assert "PlanTT" in names

    @pytest.mark.asyncio
    async def test_existing_user_keeps_old_metrics(self, client):
        """User with existing metrics keeps them — init-defaults returns early."""
        user_id = await _create_active_user("existing@example.com", "Pass123!")
        token = await _get_token(client, "existing@example.com", "Pass123!")

        # Create old-style metric
        await _create_old_metric(user_id, "schlaf", "Schlaf")

        resp = await client.post(
            "/api/yaml/init-defaults",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is False  # Already has metrics

        # Verify old metric is untouched
        async with async_session() as db:
            result = await db.execute(
                select(MetricConfig).where(MetricConfig.user_id == user_id)
            )
            configs = result.scalars().all()
            assert len(configs) == 1
            assert configs[0].name == "Schlaf"
            assert configs[0].slug == "schlaf"

    @pytest.mark.asyncio
    async def test_init_defaults_idempotent(self, client):
        """Calling init-defaults twice for same user is safe."""
        user_id = await _create_active_user("idempotent@example.com", "Pass123!")
        token = await _get_token(client, "idempotent@example.com", "Pass123!")

        # First call succeeds
        resp1 = await client.post(
            "/api/yaml/init-defaults",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.json()["ok"] is True

        # Second call is a no-op
        resp2 = await client.post(
            "/api/yaml/init-defaults",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.json()["ok"] is False

        # Still exactly 11 metrics
        async with async_session() as db:
            result = await db.execute(
                select(MetricConfig).where(MetricConfig.user_id == user_id)
            )
            assert len(result.scalars().all()) == 11
