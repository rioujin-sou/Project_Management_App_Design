from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.comment import Comment
from app.models.task import Task
from app.schemas.comment import Comment as CommentSchema, CommentCreate
from app.api.deps.auth import require_tdl_or_tpm
from app.services.audit_service import log_audit

router = APIRouter()


@router.get("/{task_id}/comments", response_model=List[CommentSchema])
def get_task_comments(
    task_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Get all comments for a task. Accessible by TDL and TPM.
    """
    # Check if task exists
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    comments = db.query(Comment).options(joinedload(Comment.user)).filter(
        Comment.task_id == task_id
    ).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
    
    return comments


@router.post("/{task_id}/comments", response_model=CommentSchema, status_code=status.HTTP_201_CREATED)
def create_comment(
    task_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Add a comment to a task. Both TDL and TPM can add comments.
    """
    # Check if task exists
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Ensure task_id matches
    comment_data.task_id = task_id
    
    # Create comment
    comment = Comment(
        task_id=task_id,
        user_id=current_user.id,
        text=comment_data.text
    )
    db.add(comment)
    db.flush()
    
    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Comment",
        entity_id=comment.id,
        changes={
            "task_id": task_id,
            "text": comment_data.text[:100]  # Truncate for audit log
        }
    )
    
    db.commit()
    db.refresh(comment)

    # Reload with user relationship for response
    comment = db.query(Comment).options(joinedload(Comment.user)).filter(Comment.id == comment.id).first()

    return comment