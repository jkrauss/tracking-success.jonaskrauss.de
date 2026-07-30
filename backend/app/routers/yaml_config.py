from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import yaml

from app.database import get_db
from app.models.metric import MetricConfig
from app.schemas.metric import MetricConfigCreate
from app.routers.auth import get_current_user_id

router = APIRouter(prefix="/api/yaml", tags=["yaml"])

DEFAULT_METRICS = [
    {
        "name": "Sleep",
        "slug": "sleep",
        "metric_type": "sleep",
        "unit": "hours",
        "has_goal": True,
        "goal_type": "min",
        "goal_value": 7.0,
        "calculation": "sleep_duration",
        "input_fields": '[{"name":"bedtime","type":"time","label":"Bedtime"},{"name":"waketime","type":"time","label":"Wake time"}]',
        "order": 0,
    },
    {
        "name": "Meditation",
        "slug": "meditation",
        "metric_type": "meditation",
        "unit": "hours",
        "has_goal": True,
        "goal_type": "min",
        "goal_value": 10 / 60,
        "calculation": "same_day_duration",
        "input_fields": '[{"name":"start","type":"time","label":"Start"},{"name":"end","type":"time","label":"End"}]',
        "order": 1,
    },
    {
        "name": "Mindset",
        "slug": "mindset",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Done?"}]',
        "order": 2,
    },
    {
        "name": "Diet",
        "slug": "diet",
        "metric_type": "float",
        "unit": "%",
        "has_goal": True,
        "goal_type": "min",
        "goal_value": 80.0,
        "calculation": None,
        "input_fields": '[{"name":"value","type":"percent","label":"Diet"}]',
        "order": 3,
    },
    {
        "name": "Exercise",
        "slug": "exercise",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Done?"}]',
        "order": 4,
    },
    {
        "name": "Work Duration",
        "slug": "work-duration",
        "metric_type": "work",
        "unit": "hours",
        "has_goal": False,
        "calculation": "same_day_duration",
        "input_fields": '[{"name":"start","type":"time","label":"Start"},{"name":"end","type":"time","label":"End"}]',
        "order": 5,
    },
    {
        "name": "Mood",
        "slug": "mood",
        "metric_type": "float",
        "unit": "%",
        "has_goal": False,
        "calculation": None,
        "input_fields": '[{"name":"value","type":"percent","label":"Mood"}]',
        "order": 6,
    },
    {
        "name": "Output",
        "slug": "output",
        "metric_type": "float",
        "unit": "%",
        "has_goal": False,
        "calculation": None,
        "input_fields": '[{"name":"value","type":"percent","label":"Output"}]',
        "order": 7,
    },
    {
        "name": "Focus",
        "slug": "focus",
        "metric_type": "float",
        "unit": "%",
        "has_goal": False,
        "calculation": None,
        "input_fields": '[{"name":"value","type":"percent","label":"Focus"}]',
        "order": 8,
    },
    {
        "name": "Reading",
        "slug": "reading",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Done?"}]',
        "order": 9,
    },
    {
        "name": "PlanTT",
        "slug": "plan-tt",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Done?"}]',
        "order": 10,
    },
]


@router.get("/export")
async def export_yaml(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MetricConfig)
        .where(MetricConfig.user_id == user_id)
        .order_by(MetricConfig.order)
    )
    configs = result.scalars().all()

    metrics = []
    for c in configs:
        metrics.append({
            "name": c.name,
            "slug": c.slug,
            "metric_type": c.metric_type,
            "unit": c.unit,
            "has_goal": c.has_goal,
            "goal_type": c.goal_type,
            "goal_value": c.goal_value,
            "calculation": c.calculation,
            "input_fields": c.input_fields,
            "order": c.order,
        })

    return {"yaml": yaml.dump({"metrics": metrics}, default_flow_style=False, allow_unicode=True)}


@router.post("/import")
async def import_yaml(
    yaml_content: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    if "metrics" not in data:
        raise HTTPException(status_code=400, detail="YAML must contain 'metrics' key")

    # Delete existing configs
    result = await db.execute(
        select(MetricConfig).where(MetricConfig.user_id == user_id)
    )
    for config in result.scalars().all():
        await db.delete(config)

    # Create new configs
    for item in data["metrics"]:
        config = MetricConfig(user_id=user_id, **item)
        db.add(config)

    await db.flush()
    return {"ok": True, "count": len(data["metrics"])}


@router.post("/init-defaults")
async def init_defaults(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Initialize default metrics for a new user."""
    result = await db.execute(
        select(MetricConfig).where(MetricConfig.user_id == user_id)
    )
    if result.scalars().first():
        return {"ok": False, "detail": "User already has metrics configured"}

    for item in DEFAULT_METRICS:
        config = MetricConfig(user_id=user_id, **item)
        db.add(config)

    await db.flush()
    return {"ok": True, "count": len(DEFAULT_METRICS)}
