from pydantic import BaseModel
from datetime import datetime
from typing import Any, List, Optional


class ProjectBase(BaseModel):
    opp_id: str
    name: str
    version: str


class ProjectCreate(ProjectBase):
    baseline_json: dict[str, Any]


class Project(ProjectBase):
    id: int
    baseline_json: dict[str, Any]
    created_by: int
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    visible_user_ids: List[int] = []

    class Config:
        from_attributes = True


class ProjectWithTasks(Project):
    tasks: List['Task'] = []

    class Config:
        from_attributes = True


class VisibilityUpdate(BaseModel):
    user_ids: List[int]


# Import here to avoid circular imports
from app.schemas.task import Task
ProjectWithTasks.model_rebuild()