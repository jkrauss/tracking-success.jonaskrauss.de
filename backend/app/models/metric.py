from datetime import date, time, datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, Time, DateTime, ForeignKey,
    UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from app.database import Base


class MetricConfig(Base):
    __tablename__ = "metric_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    metric_type = Column(String(20), nullable=False)  # bool, float, sleep, weight, fasting
    unit = Column(String(50), nullable=True)
    has_goal = Column(Boolean, default=False)
    goal_type = Column(String(20), nullable=True)  # min, max, bool
    goal_value = Column(Float, nullable=True)
    calculation = Column(String(50), nullable=True)  # sleep_duration, weight_loss, fasting_duration
    input_fields = Column(String(500), nullable=True)  # JSON array of field definitions
    order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    entries = relationship("MetricEntry", back_populates="config", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="uq_user_metric_slug"),
    )


class MetricEntry(Base):
    __tablename__ = "metric_entries"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("metric_configs.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entry_date = Column(Date, nullable=False, index=True)

    # Raw input values
    value_bool = Column(Boolean, nullable=True)
    value_float = Column(Float, nullable=True)
    value_time_1 = Column(Time, nullable=True)  # bedtime or breakfast
    value_time_2 = Column(Time, nullable=True)  # wake time or dinner

    # Computed values
    computed_value = Column(Float, nullable=True)
    success = Column(Boolean, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    config = relationship("MetricConfig", back_populates="entries")

    __table_args__ = (
        UniqueConstraint("config_id", "entry_date", name="uq_config_date"),
    )
