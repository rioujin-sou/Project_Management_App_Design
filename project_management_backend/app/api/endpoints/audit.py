from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date
from app.db.session import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLog as AuditLogSchema
from app.api.deps.auth import require_tdl

router = APIRouter()


@router.get("", response_model=List[AuditLogSchema])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (User, Project, Task, Comment)"),
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl)
):
    """
    Get audit logs with optional filtering. Only TDL can access.
    """
    query = db.query(AuditLog)
    
    # Apply filters
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(AuditLog.created_at >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(AuditLog.created_at <= end_datetime)
    
    # Order by most recent first
    audit_logs = (
        query
        .options(joinedload(AuditLog.user))
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return audit_logs