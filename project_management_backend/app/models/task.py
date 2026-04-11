from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Numeric, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, column_property
from sqlalchemy import case
from app.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # Excel columns (18 required + 2 optional)
    site = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    product = Column(String(255), nullable=False)
    wp = Column(String(500), nullable=False)
    wp_id = Column(String(100), nullable=False)
    unit = Column(String(255), nullable=False)
    effort = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    tuning_factor = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)
    role = Column(String(100), nullable=False)
    resource_category = Column(String(100), nullable=False)
    support_type = Column(String(100), nullable=False)
    spc = Column(String(50), nullable=False)
    resource_name = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Optional columns
    rate = Column(Numeric(10, 2), nullable=True)
    cost = Column(Numeric(10, 2), nullable=True)
    
    # Additional fields
    completion_pct = Column(Integer, default=0, nullable=False)  # 0, 10, 20, ..., 100
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    
    # Computed status property (not a database column, computed in Python)
    @property
    def status(self) -> str:
        """Compute status from completion_pct"""
        if self.completion_pct == 0:
            return "To Do"
        elif self.completion_pct == 100:
            return "Done"
        else:
            return "In Progress"
