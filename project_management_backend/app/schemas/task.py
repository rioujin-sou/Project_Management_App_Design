from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


class TaskBase(BaseModel):
    site: str
    category: str
    product: str
    wp: str
    wp_id: str
    unit: str
    effort: float
    comment: Optional[str] = None
    tuning_factor: float
    qty: int
    total: float
    role: str
    resource_category: str
    support_type: str
    spc: str
    resource_name: str
    start_date: date
    end_date: date
    rate: Optional[Decimal] = None
    cost: Optional[Decimal] = None


class TaskCreate(TaskBase):
    project_id: int
    completion_pct: int = Field(default=0, ge=0, le=100, multiple_of=10)


class TaskUpdate(BaseModel):
    site: Optional[str] = None
    category: Optional[str] = None
    product: Optional[str] = None
    wp: Optional[str] = None
    wp_id: Optional[str] = None
    unit: Optional[str] = None
    effort: Optional[float] = None
    comment: Optional[str] = None
    tuning_factor: Optional[float] = None
    qty: Optional[int] = None
    total: Optional[float] = None
    role: Optional[str] = None
    resource_category: Optional[str] = None
    support_type: Optional[str] = None
    spc: Optional[str] = None
    resource_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rate: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    completion_pct: Optional[int] = Field(None, ge=0, le=100, multiple_of=10)


class TaskUpdateTPM(BaseModel):
    """Limited update fields for TPM role"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    completion_pct: Optional[int] = Field(None, ge=0, le=100, multiple_of=10)


class Task(TaskBase):
    id: int
    project_id: int
    completion_pct: int
    status: str  # Computed from completion_pct
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
