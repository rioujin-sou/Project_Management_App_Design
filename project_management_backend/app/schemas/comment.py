from pydantic import BaseModel
from datetime import datetime


class CommentUser(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    text: str


class CommentCreate(CommentBase):
    task_id: int


class Comment(CommentBase):
    id: int
    task_id: int
    user_id: int
    user: CommentUser
    created_at: datetime

    class Config:
        from_attributes = True