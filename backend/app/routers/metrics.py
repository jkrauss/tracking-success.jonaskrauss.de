from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.metric import MetricConfig, MetricEntry
from app.models.user import User
from app.schemas.metric import (
    MetricConfigCreate, MetricConfigResponse,
    MetricEntryCreate, MetricEntryResponse, MetricHistory
)
from app.services.metrics import compute_success, get_streak

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


from app.routers.auth import get_current_user_id


@router.get("/configs", response_model=list[MetricConfigResponse])
async def get_configs(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MetricConfig)
        .where(MetricConfig.user_id == user_id)
        .order_by(MetricConfig.order)
    )
    return result.scalars().all()


@router.post("/configs", response_model=MetricConfigResponse)
async def create_config(
    data: MetricConfigCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    config = MetricConfig(user_id=user_id, **data.model_dump())
    db.add(config)
    await db.flush()
    return config


@router.put("/configs/{config_id}", response_model=MetricConfigResponse)
async def update_config(
    config_id: int,
    data: MetricConfigCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MetricConfig).where(
            and_(MetricConfig.id == config_id, MetricConfig.user_id == user_id)
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    for key, value in data.model_dump().items():
        setattr(config, key, value)
    return config


@router.delete("/configs/{config_id}")
async def delete_config(
    config_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MetricConfig).where(
            and_(MetricConfig.id == config_id, MetricConfig.user_id == user_id)
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    await db.delete(config)
    return {"ok": True}


@router.post("/entries", response_model=MetricEntryResponse)
async def create_or_update_entry(
    config_id: int,
    data: MetricEntryCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Get config
    result = await db.execute(
        select(MetricConfig).where(
            and_(MetricConfig.id == config_id, MetricConfig.user_id == user_id)
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    # Compute derived values
    computed, success = await compute_success(config, data, db, user_id)

    # Upsert entry
    result = await db.execute(
        select(MetricEntry).where(
            and_(
                MetricEntry.config_id == config_id,
                MetricEntry.user_id == user_id,
                MetricEntry.entry_date == data.entry_date,
            )
        )
    )
    entry = result.scalar_one_or_none()

    if entry:
        entry.value_bool = data.value_bool
        entry.value_float = data.value_float
        entry.value_time_1 = data.value_time_1
        entry.value_time_2 = data.value_time_2
        entry.computed_value = computed
        entry.success = success
    else:
        entry = MetricEntry(
            config_id=config_id,
            user_id=user_id,
            entry_date=data.entry_date,
            value_bool=data.value_bool,
            value_float=data.value_float,
            value_time_1=data.value_time_1,
            value_time_2=data.value_time_2,
            computed_value=computed,
            success=success,
        )
        db.add(entry)

    await db.flush()
    return entry


@router.get("/entries/{config_id}", response_model=MetricHistory)
async def get_entries(
    config_id: int,
    days: int = Query(default=7, ge=1, le=365),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta

    start_date = date.today() - timedelta(days=days)

    result = await db.execute(
        select(MetricEntry)
        .where(
            and_(
                MetricEntry.config_id == config_id,
                MetricEntry.user_id == user_id,
                MetricEntry.entry_date >= start_date,
            )
        )
        .order_by(MetricEntry.entry_date)
    )
    entries = result.scalars().all()

    streak = await get_streak(db, config_id, user_id)

    return MetricHistory(entries=entries, current_streak=streak)


@router.get("/summary/today")
async def get_today_summary(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get summary of today's entries: count of successes and failures."""
    today = date.today()

    result = await db.execute(
        select(MetricEntry)
        .where(
            and_(
                MetricEntry.user_id == user_id,
                MetricEntry.entry_date == today,
            )
        )
    )
    entries = result.scalars().all()

    success_count = sum(1 for e in entries if e.success is True)
    fail_count = sum(1 for e in entries if e.success is False)
    total = len(entries)

    return {
        "date": today,
        "success": success_count,
        "fail": fail_count,
        "total": total,
        "entries": [
            {
                "config_id": e.config_id,
                "success": e.success,
                "computed_value": e.computed_value,
            }
            for e in entries
        ],
    }


@router.get("/summary/history")
async def get_summary_history(
    days: int = Query(default=7, ge=1, le=365),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get historical summary of successes/failures per day."""
    from datetime import timedelta
    
    start_date = date.today() - timedelta(days=days - 1)
    
    # Get all entries in the date range
    result = await db.execute(
        select(MetricEntry)
        .where(
            and_(
                MetricEntry.user_id == user_id,
                MetricEntry.entry_date >= start_date,
            )
        )
        .order_by(MetricEntry.entry_date)
    )
    entries = result.scalars().all()
    
    # Get total number of goal-based configs
    config_result = await db.execute(
        select(func.count(MetricConfig.id))
        .where(
            and_(
                MetricConfig.user_id == user_id,
                MetricConfig.has_goal == True,  # noqa: E712
            )
        )
    )
    total_configs = config_result.scalar() or 0
    
    # Group by date
    daily_data = {}
    current = start_date
    for _ in range(days):
        daily_data[current] = {"success": 0, "fail": 0}
        current += timedelta(days=1)
    
    for entry in entries:
        if entry.entry_date in daily_data:
            if entry.success is True:
                daily_data[entry.entry_date]["success"] += 1
            elif entry.success is False:
                daily_data[entry.entry_date]["fail"] += 1
    
    return {
        "days": days,
        "total_configs": total_configs,
        "history": [
            {
                "date": d.isoformat(),
                "success": data["success"],
                "fail": data["fail"],
                "total_configs": total_configs,
            }
            for d, data in sorted(daily_data.items())
        ],
    }
