from pydantic import BaseModel
from datetime import datetime
from typing import Any


class AuditLogBase(BaseModel):
    action: str
    entity_type: str
    entity_id: int
    changes_json: dict[str, Any]


class AuditLogCreate(AuditLogBase):
    user_id: int | None


class AuditLog(AuditLogBase):
    id: int
    user_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True
