import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.task import Task
from app.models.project import Project
from app.schemas.task import Task as TaskSchema, TaskCreate, TaskUpdate, TaskUpdateTPM
from app.schemas.auth import MessageResponse
from app.api.deps.auth import require_tdl, require_tdl_or_tpm, get_current_user
from app.services.audit_service import log_audit

logger = logging.getLogger(__name__)

router = APIRouter()


# ========================
# LIST TASKS FOR A PROJECT
# ========================
# Frontend calls: GET /api/v1/tasks/project/{projectId}
@router.get("/project/{project_id}", response_model=List[TaskSchema])
def list_tasks(
    project_id: int,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Get all tasks for a project. Accessible by TDL and TPM.
    """
    logger.info(f"list_tasks called for project_id={project_id}, skip={skip}, limit={limit}, user={current_user.id}")

    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        logger.warning(f"Project {project_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    tasks = db.query(Task).filter(
        Task.project_id == project_id
    ).order_by(Task.id).offset(skip).limit(limit).all()

    logger.info(f"Returning {len(tasks)} tasks for project_id={project_id}")
    if tasks:
        logger.info(f"Sample task: id={tasks[0].id}, site={tasks[0].site}, wp_id={tasks[0].wp_id}")

    return tasks


# Also keep the old route for backward compatibility
# Backend originally had: GET /{project_id}/tasks
@router.get("/{project_id}/tasks", response_model=List[TaskSchema])
def list_tasks_compat(
    project_id: int,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Get all tasks for a project (backward-compatible route).
    """
    logger.info(f"list_tasks_compat called for project_id={project_id}")
    return list_tasks(project_id, skip, limit, db, current_user)


# ========================
# DEBUG ENDPOINT
# ========================
@router.get("/project/{project_id}/debug")
def debug_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Debug endpoint to check tasks directly in the database.
    Returns raw task data and count.
    """
    logger.info(f"debug_tasks called for project_id={project_id}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "Project not found", "project_id": project_id}

    task_count = db.query(Task).filter(Task.project_id == project_id).count()
    tasks = db.query(Task).filter(Task.project_id == project_id).limit(5).all()

    sample_tasks = []
    for t in tasks:
        sample_tasks.append({
            "id": t.id,
            "project_id": t.project_id,
            "site": t.site,
            "category": t.category,
            "product": t.product,
            "wp_id": t.wp_id,
            "start_date": str(t.start_date),
            "end_date": str(t.end_date),
            "completion_pct": t.completion_pct,
            "status": t.status,
        })

    return {
        "project_id": project_id,
        "project_name": project.name,
        "project_opp_id": project.opp_id,
        "total_task_count": task_count,
        "sample_tasks": sample_tasks,
        "tasks_relationship_count": len(project.tasks) if project.tasks else 0,
    }


# ========================
# GET SINGLE TASK
# ========================
# Frontend calls: GET /api/v1/tasks/{taskId}
@router.get("/{task_id}", response_model=TaskSchema)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Get a single task by ID. Accessible by TDL and TPM.
    """
    logger.info(f"get_task called for task_id={task_id}")
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


# ========================
# CREATE TASK
# ========================
# Frontend calls: POST /api/v1/tasks (with project_id in body)
@router.post("/", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Create a new task. Both TDL and TPM can create tasks.
    project_id is included in the request body.
    """
    logger.info(f"create_task called with project_id={task_data.project_id}")

    # Check if project exists
    project = db.query(Project).filter(Project.id == task_data.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Validate dates
    if task_data.start_date > task_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )

    # Create task
    task = Task(**task_data.model_dump())
    db.add(task)
    db.flush()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Task",
        entity_id=task.id,
        changes={
            "project_id": task_data.project_id,
            "site": task.site,
            "wp": task.wp
        }
    )

    db.commit()
    db.refresh(task)

    logger.info(f"Task created: id={task.id}, project_id={task.project_id}")
    return task


# Also keep the old route for backward compatibility
@router.post("/{project_id}/tasks", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_task_compat(
    project_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Create a new task (backward-compatible route).
    """
    task_data.project_id = project_id
    return create_task(task_data, db, current_user)


# ========================
# UPDATE TASK COMPLETION (PATCH)
# ========================
# Frontend calls: PATCH /api/v1/tasks/{taskId}/completion
@router.patch("/{task_id}/completion", response_model=TaskSchema)
def update_task_completion(
    task_id: int,
    completion_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Update just the completion percentage of a task.
    Body: { "completion_pct": <int> }
    """
    logger.info(f"update_task_completion called for task_id={task_id}, data={completion_data}")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    completion_pct = completion_data.get("completion_pct")
    if completion_pct is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="completion_pct is required"
        )

    if not (0 <= completion_pct <= 100) or completion_pct % 10 != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="completion_pct must be a multiple of 10 between 0 and 100"
        )

    old_pct = task.completion_pct
    task.completion_pct = completion_pct
    task.updated_at = datetime.utcnow()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="Task",
        entity_id=task.id,
        changes={
            "old": {"completion_pct": old_pct},
            "new": {"completion_pct": completion_pct}
        }
    )

    db.commit()
    db.refresh(task)

    logger.info(f"Task {task_id} completion updated: {old_pct} -> {completion_pct}")
    return task


# ========================
# UPDATE TASK (PUT)
# ========================
# Frontend calls: PUT /api/v1/tasks/{taskId}
@router.put("/{task_id}", response_model=TaskSchema)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a task.
    - TDL: Can update all fields
    - TPM: Can only update start_date, end_date, completion_pct
    """
    logger.info(f"update_task called for task_id={task_id}, user_role={current_user.role}")

    # Find task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Get all fields being updated
    update_data = task_update.model_dump(exclude_unset=True)

    # Determine allowed fields based on role
    if current_user.role in (UserRole.tpm, UserRole.pm, UserRole.sa):
        # TPM can only update specific fields
        allowed_fields = {'start_date', 'end_date', 'completion_pct'}
        forbidden_fields = set(update_data.keys()) - allowed_fields
        if forbidden_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"TPM can only update: start_date, end_date, completion_pct"
            )
    elif current_user.role == UserRole.tdl:
        pass  # TDL can update all fields
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Capture old values for exactly the fields being updated
    old_values = {k: str(getattr(task, k)) for k in update_data.keys()}

    # Validate dates if both are being updated
    new_start = update_data.get('start_date', task.start_date)
    new_end = update_data.get('end_date', task.end_date)
    if new_start > new_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )

    # Update task
    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()

    # Log audit
    new_values = {k: str(getattr(task, k)) for k in update_data.keys()}
    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="Task",
        entity_id=task.id,
        changes={
            "old": old_values,
            "new": new_values
        }
    )

    db.commit()
    db.refresh(task)

    logger.info(f"Task {task_id} updated: fields={list(update_data.keys())}")
    return task


# ========================
# DELETE TASK
# ========================
@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Delete a task. Both TDL and TPM can delete tasks.
    """
    logger.info(f"delete_task called for task_id={task_id}")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    log_audit(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        entity_type="Task",
        entity_id=task.id,
        changes={
            "project_id": task.project_id,
            "site": task.site,
            "wp": task.wp
        }
    )

    db.delete(task)
    db.commit()

    logger.info(f"Task {task_id} deleted")
    return MessageResponse(message="Task deleted successfully")