import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.models.task_precedence import TaskPrecedence
from app.schemas.task_precedence import PrecedenceCreate, PrecedenceResponse
from app.schemas.auth import MessageResponse
from app.api.deps.auth import require_tdl_or_tpm

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/project/{project_id}/precedences", response_model=List[PrecedenceResponse])
def list_project_precedences(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    task_ids = [row.id for row in db.query(Task.id).filter(Task.project_id == project_id).all()]
    if not task_ids:
        return []

    rows = (
        db.query(TaskPrecedence)
        .options(joinedload(TaskPrecedence.predecessor))
        .filter(TaskPrecedence.successor_task_id.in_(task_ids))
        .all()
    )
    return [_to_response(r) for r in rows]


@router.get("/{task_id}/precedences", response_model=List[PrecedenceResponse])
def list_task_precedences(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm),
):
    _get_task_or_404(task_id, db)
    rows = (
        db.query(TaskPrecedence)
        .options(joinedload(TaskPrecedence.predecessor))
        .filter(TaskPrecedence.successor_task_id == task_id)
        .all()
    )
    return [_to_response(r) for r in rows]


@router.post("/{task_id}/precedences", response_model=List[PrecedenceResponse], status_code=status.HTTP_201_CREATED)
def add_precedences(
    task_id: int,
    items: List[PrecedenceCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm),
):
    _get_task_or_404(task_id, db)
    created = []
    for item in items:
        if item.predecessor_task_id == task_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A task cannot be its own predecessor",
            )
        _get_task_or_404(item.predecessor_task_id, db)

        existing = (
            db.query(TaskPrecedence)
            .filter(
                TaskPrecedence.predecessor_task_id == item.predecessor_task_id,
                TaskPrecedence.successor_task_id == task_id,
            )
            .first()
        )
        if existing:
            continue

        row = TaskPrecedence(
            predecessor_task_id=item.predecessor_task_id,
            successor_task_id=task_id,
            precedence_type=item.precedence_type,
        )
        db.add(row)
        db.flush()
        created.append(row)

    db.commit()
    for row in created:
        db.refresh(row)

    # Re-query with predecessor loaded for response serialization
    ids = [r.id for r in created]
    if not ids:
        return []
    rows = (
        db.query(TaskPrecedence)
        .options(joinedload(TaskPrecedence.predecessor))
        .filter(TaskPrecedence.id.in_(ids))
        .all()
    )
    return [_to_response(r) for r in rows]


@router.delete("/{task_id}/precedences/{precedence_id}", response_model=MessageResponse)
def remove_precedence(
    task_id: int,
    precedence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm),
):
    _get_task_or_404(task_id, db)
    row = (
        db.query(TaskPrecedence)
        .filter(
            TaskPrecedence.id == precedence_id,
            TaskPrecedence.successor_task_id == task_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Precedence not found")

    db.delete(row)
    db.commit()
    logger.info(f"Removed precedence {precedence_id} from task {task_id}")
    return MessageResponse(message="Precedence removed")


def _get_task_or_404(task_id: int, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")
    return task


def _to_response(row: TaskPrecedence) -> PrecedenceResponse:
    return PrecedenceResponse(
        id=row.id,
        predecessor_task_id=row.predecessor_task_id,
        successor_task_id=row.successor_task_id,
        precedence_type=row.precedence_type,
        predecessor_wp_id=row.predecessor.wp_id if row.predecessor else None,
        predecessor_wp=row.predecessor.wp if row.predecessor else None,
        created_at=row.created_at,
    )
