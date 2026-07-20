from datetime import date, time
from typing import Optional
from pydantic import BaseModel


class MetricConfigCreate(BaseModel):
    name: str
    slug: str
    metric_type: str  # bool, float, sleep, weight, fasting
    unit: Optional[str] = None
    has_goal: bool = False
    goal_type: Optional[str] = None  # min, max, bool
    goal_value: Optional[float] = None
    calculation: Optional[str] = None
    input_fields: Optional[str] = None  # JSON string
    order: int = 0


class MetricConfigResponse(BaseModel):
    id: int
    name: str
    slug: str
    metric_type: str
    unit: Optional[str]
    has_goal: bool
    goal_type: Optional[str]
    goal_value: Optional[float]
    calculation: Optional[str]
    input_fields: Optional[str]
    order: int

    class Config:
        from_attributes = True


class MetricEntryCreate(BaseModel):
    entry_date: date
    value_bool: Optional[bool] = None
    value_float: Optional[float] = None
    value_time_1: Optional[time] = None
    value_time_2: Optional[time] = None


class MetricEntryResponse(BaseModel):
    id: int
    config_id: int
    entry_date: date
    value_bool: Optional[bool]
    value_float: Optional[float]
    value_time_1: Optional[time]
    value_time_2: Optional[time]
    computed_value: Optional[float]
    success: Optional[bool]

    class Config:
        from_attributes = True


class MetricHistory(BaseModel):
    entries: list[MetricEntryResponse]
    current_streak: int = 0
