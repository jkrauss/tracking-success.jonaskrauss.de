from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import yaml

from app.database import get_db
from app.models.metric import MetricConfig
from app.models.user import User
from app.schemas.metric import MetricConfigCreate
from app.routers.auth import get_current_user_id

router = APIRouter(prefix="/api/yaml", tags=["yaml"])

DEFAULT_METRICS = [
    {
        "name": "Schlaf",
        "slug": "sleep",
        "metric_type": "sleep",
        "unit": "hours",
        "has_goal": True,
        "goal_type": "min",
        "goal_value": 7.0,
        "calculation": "sleep_duration",
        "input_fields": '[{"name":"bedtime","type":"time","label":"Bettzeit"},{"name":"waketime","type":"time","label":"Aufstehzeit"}]',
        "order": 0,
    },
    {
        "name": "Einstellarbeit",
        "slug": "setup-work",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Erledigt?"}]',
        "order": 1,
    },
    {
        "name": "Morgenrunde",
        "slug": "morning-routine",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Erledigt?"}]',
        "order": 2,
    },
    {
        "name": "Sport",
        "slug": "sport",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Erledigt?"}]',
        "order": 3,
    },
    {
        "name": "Zwei Stunden Fokus",
        "slug": "focus-2h",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Erledigt?"}]',
        "order": 4,
    },
    {
        "name": "Plan für Morgen",
        "slug": "plan-tomorrow",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Erledigt?"}]',
        "order": 5,
    },
    {
        "name": "Kein Youtube",
        "slug": "no-youtube",
        "metric_type": "bool",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": None,
        "input_fields": '[{"name":"done","type":"bool","label":"Erledigt?"}]',
        "order": 6,
    },
    {
        "name": "Stimmung",
        "slug": "mood",
        "metric_type": "float",
        "unit": "%",
        "has_goal": False,
        "calculation": None,
        "input_fields": '[{"name":"value","type":"percent","label":"Stimmung"}]',
        "order": 7,
    },
    {
        "name": "Fokus",
        "slug": "focus",
        "metric_type": "float",
        "unit": "%",
        "has_goal": False,
        "calculation": None,
        "input_fields": '[{"name":"value","type":"percent","label":"Fokus"}]',
        "order": 8,
    },
    {
        "name": "Gewicht",
        "slug": "weight",
        "metric_type": "weight",
        "unit": "kg",
        "has_goal": True,
        "goal_type": "bool",
        "calculation": "weight_loss",
        "input_fields": '[{"name":"value","type":"float","label":"Gewicht (kg)"}]',
        "order": 9,
    },
    {
        "name": "Fastenzeit",
        "slug": "fasting",
        "metric_type": "fasting",
        "unit": "hours",
        "has_goal": True,
        "goal_type": "min",
        "goal_value": 15.0,
        "calculation": "fasting_duration",
        "input_fields": '[{"name":"breakfast","type":"time","label":"Frühstück"},{"name":"dinner","type":"time","label":"Abendessen"}]',
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
