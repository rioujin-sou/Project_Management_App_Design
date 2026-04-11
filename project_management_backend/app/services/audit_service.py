from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from typing import Any, Dict, Optional


def log_audit(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: int,
    changes: Dict[str, Any]
) -> AuditLog:
    """
    Create an audit log entry.
    
    Args:
        db: Database session
        user_id: ID of the user performing the action (can be None for system actions)
        action: Action type (CREATE, UPDATE, DELETE)
        entity_type: Type of entity (User, Project, Task, Comment)
        entity_id: ID of the entity
        changes: Dictionary containing the changes (before/after values, or context)
    
    Returns:
        AuditLog: The created audit log entry
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes_json=changes
    )
    
    db.add(audit_log)
    db.flush()  # Flush to get the ID, but don't commit yet
    
    return audit_log
