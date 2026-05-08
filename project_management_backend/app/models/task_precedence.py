from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class TaskPrecedence(Base):
    __tablename__ = "task_precedence"
    __table_args__ = (
        UniqueConstraint('predecessor_task_id', 'successor_task_id', name='uq_task_precedence_pair'),
    )

    id = Column(Integer, primary_key=True, index=True)
    predecessor_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    successor_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    precedence_type = Column(String(2), nullable=False)  # "FS" or "SS"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    predecessor = relationship("Task", foreign_keys=[predecessor_task_id], back_populates="precedences_as_predecessor")
    successor = relationship("Task", foreign_keys=[successor_task_id], back_populates="precedences_as_successor")
