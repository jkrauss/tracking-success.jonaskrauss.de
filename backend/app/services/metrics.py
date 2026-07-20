from datetime import date, time, timedelta
from typing import Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric import MetricConfig, MetricEntry
from app.schemas.metric import MetricEntryCreate
from app.calculations import compute_sleep, compute_fasting


async def compute_success(
    config: MetricConfig,
    entry_data: MetricEntryCreate,
    db: AsyncSession,
    user_id: int,
) -> tuple[Optional[float], Optional[bool]]:
    """Compute derived values and success flag."""
    computed = None
    success = None

    if config.calculation == "sleep_duration":
        if entry_data.value_time_1 and entry_data.value_time_2:
            computed = compute_sleep(entry_data.value_time_1, entry_data.value_time_2)
            if config.has_goal and config.goal_value:
                success = computed >= config.goal_value

    elif config.calculation == "fasting_duration":
        if entry_data.value_time_1 and entry_data.value_time_2:
            computed = compute_fasting(entry_data.value_time_1, entry_data.value_time_2)
            if config.has_goal and config.goal_value:
                success = computed >= config.goal_value

    elif config.calculation == "weight_loss":
        if entry_data.value_float is not None:
            computed = entry_data.value_float
            # Get yesterday's entry
            yesterday = entry_data.entry_date - timedelta(days=1)
            result = await db.execute(
                select(MetricEntry).where(
                    and_(
                        MetricEntry.config_id == config.id,
                        MetricEntry.user_id == user_id,
                        MetricEntry.entry_date == yesterday,
                    )
                )
            )
            prev = result.scalar_one_or_none()
            if prev and prev.computed_value is not None:
                success = entry_data.value_float < prev.computed_value

    elif config.metric_type == "bool":
        success = entry_data.value_bool if config.has_goal else None

    elif config.metric_type == "float":
        computed = entry_data.value_float
        if config.has_goal and config.goal_value and entry_data.value_float is not None:
            if config.goal_type == "min":
                success = entry_data.value_float >= config.goal_value
            elif config.goal_type == "max":
                success = entry_data.value_float <= config.goal_value

    return computed, success


async def get_streak(db: AsyncSession, config_id: int, user_id: int) -> int:
    """Calculate current streak of consecutive successful days."""
    result = await db.execute(
        select(MetricEntry)
        .where(
            and_(
                MetricEntry.config_id == config_id,
                MetricEntry.user_id == user_id,
                MetricEntry.success == True,  # noqa: E712
            )
        )
        .order_by(MetricEntry.entry_date.desc())
    )
    entries = result.scalars().all()

    if not entries:
        return 0

    streak = 0
    expected_date = date.today()

    for entry in entries:
        if entry.entry_date == expected_date:
            streak += 1
            expected_date -= timedelta(days=1)
        elif entry.entry_date < expected_date:
            break

    return streak
