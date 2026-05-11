from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Literal


class PrecedenceCreate(BaseModel):
    predecessor_task_id: int
    precedence_type: Literal["FS", "SS"]


class PrecedenceResponse(BaseModel):
    id: int
    predecessor_task_id: int
    successor_task_id: int
    precedence_type: str
    predecessor_wp_id: Optional[str] = None
    predecessor_wp: Optional[str] = None
    predecessor_comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
