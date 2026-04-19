from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import tempfile
import os
import logging
import traceback
from datetime import datetime
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.project import Project, project_visibility
from app.models.task import Task
from app.schemas.project import Project as ProjectSchema, ProjectWithTasks, VisibilityUpdate
from app.schemas.auth import MessageResponse
from app.api.deps.auth import require_tdl, require_tdl_or_tpm, get_current_user
from app.services.excel_parser import parse_excel_file, parse_tasks_only, ExcelParserError, serialize_for_json
from app.services.excel_exporter import export_tasks_to_excel
from app.services.audit_service import log_audit

logger = logging.getLogger(__name__)

router = APIRouter()


def _attach_project_meta(project: Project, db: Session) -> Project:
    """Attach task_count and visible_user_ids to a project instance."""
    project.task_count = db.query(Task).filter(Task.project_id == project.id).count()
    project.visible_user_ids = [u.id for u in project.visible_to]
    return project


@router.get("", response_model=List[ProjectSchema])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    List projects visible to the current user.
    TDL sees all projects; other roles only see projects they are in visible_to.
    """
    if current_user.role == UserRole.tdl:
        projects = db.query(Project).offset(skip).limit(limit).all()
    else:
        projects = (
            db.query(Project)
            .join(project_visibility, Project.id == project_visibility.c.project_id)
            .filter(project_visibility.c.user_id == current_user.id)
            .offset(skip).limit(limit).all()
        )
    for project in projects:
        _attach_project_meta(project, db)
    return projects


@router.get("/{project_id}", response_model=ProjectWithTasks)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Get project details with all tasks. Accessible by TDL and TPM.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    # Non-TDL users can only access projects they have visibility to
    if current_user.role != UserRole.tdl:
        visible_ids = [u.id for u in project.visible_to]
        if current_user.id not in visible_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project"
            )
    _attach_project_meta(project, db)
    return project


@router.post("/upload", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
async def upload_project_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl)
):
    """
    Upload Excel file to create a project. Only TDL can upload.
    If project with same opp_id exists, delete all existing tasks and replace.
    """
    logger.info(f"Upload started - filename: {file.filename}, user: {current_user.id}")
    
    # Validate file extension
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are supported"
        )
    
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    logger.info(f"File saved to temp path: {tmp_file_path}, size: {len(content)} bytes")
    
    try:
        # Parse Excel file
        try:
            parsed_data = parse_excel_file(tmp_file_path, file.filename)
            logger.info(f"Excel parsed successfully. Tasks found: {len(parsed_data['tasks'])}")
        except ExcelParserError as e:
            logger.error(f"Excel parsing error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error during Excel parsing: {e}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error parsing Excel file: {str(e)}"
            )
        
        project_data = parsed_data['project']
        tasks_data = parsed_data['tasks']
        
        logger.info(f"Project data: opp_id={project_data['opp_id']}, name={project_data['name']}, version={project_data['version']}")
        logger.info(f"Number of tasks to create: {len(tasks_data)}")
        
        # Check if project with same opp_id exists
        existing_project = db.query(Project).filter(
            Project.opp_id == project_data['opp_id']
        ).first()
        
        if existing_project:
            logger.info(f"Existing project found (id={existing_project.id}), updating...")
            # Delete all existing tasks
            deleted_count = db.query(Task).filter(Task.project_id == existing_project.id).delete()
            logger.info(f"Deleted {deleted_count} existing tasks")
            
            # Update project
            existing_project.name = project_data['name']
            existing_project.version = project_data['version']
            existing_project.baseline_json = project_data['baseline_json']
            existing_project.created_by = current_user.id
            
            project = existing_project
            action = "UPDATE"
            
            log_audit(
                db=db,
                user_id=current_user.id,
                action=action,
                entity_type="Project",
                entity_id=project.id,
                changes={
                    "message": f"Project re-uploaded with {len(tasks_data)} tasks",
                    "version": project_data['version']
                }
            )
        else:
            logger.info("No existing project, creating new...")
            # Create new project
            project = Project(
                opp_id=project_data['opp_id'],
                name=project_data['name'],
                version=project_data['version'],
                baseline_json=project_data['baseline_json'],
                created_by=current_user.id
            )
            db.add(project)
            db.flush()  # Get project.id
            logger.info(f"New project created with id={project.id}")
            action = "CREATE"
            
            log_audit(
                db=db,
                user_id=current_user.id,
                action=action,
                entity_type="Project",
                entity_id=project.id,
                changes={
                    "message": f"Project created with {len(tasks_data)} tasks",
                    "opp_id": project_data['opp_id']
                }
            )
        
        # Create tasks
        logger.info(f"Creating {len(tasks_data)} tasks for project_id={project.id}")
        created_count = 0
        for i, task_data in enumerate(tasks_data):
            try:
                task = Task(
                    project_id=project.id,
                    **task_data
                )
                db.add(task)
                created_count += 1
            except Exception as e:
                logger.error(f"Error creating task {i+1}: {e}\nTask data: {task_data}\n{traceback.format_exc()}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating task {i+1}: {str(e)}"
                )
        
        logger.info(f"Added {created_count} tasks to session, committing...")

        try:
            db.commit()
            logger.info("Database commit successful")
        except Exception as e:
            logger.error(f"Database commit failed: {e}\n{traceback.format_exc()}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error while saving tasks: {str(e)}"
            )

        db.refresh(project)

        # Inject DB-assigned task IDs into baseline_json.tasks so the frontend
        # can use `id` as the unique comparison key (wp_id is not unique across sites).
        tasks_in_db = db.query(Task).filter(Task.project_id == project.id).order_by(Task.id).all()
        baseline_tasks = project.baseline_json.get('tasks', [])
        if len(tasks_in_db) == len(baseline_tasks):
            import copy
            updated_baseline = copy.deepcopy(project.baseline_json)
            for i, db_task in enumerate(tasks_in_db):
                updated_baseline['tasks'][i]['id'] = db_task.id
            project.baseline_json = updated_baseline
            db.commit()
            db.refresh(project)
            logger.info(f"Injected task IDs into baseline_json for project_id={project.id}")

        # Grant visibility to all TDL users automatically
        tdl_users = db.query(User).filter(User.role == UserRole.tdl).all()
        for tdl_user in tdl_users:
            if tdl_user not in project.visible_to:
                project.visible_to.append(tdl_user)
        db.commit()
        db.refresh(project)
        
        # Verify tasks were created
        task_count = db.query(Task).filter(Task.project_id == project.id).count()
        logger.info(f"Verification: {task_count} tasks in database for project_id={project.id}")
        
        if task_count == 0:
            logger.error("WARNING: Zero tasks in database after commit!")
        
        _attach_project_meta(project, db)
        return project
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Unexpected error in upload_project_excel: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
    finally:
        # Clean up temp file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.post("/{project_id}/import-tasks", response_model=ProjectSchema)
async def import_tasks_excel(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl)
):
    """
    Append tasks from an Excel file to an existing project. Only TDL can import.
    Existing tasks are kept; only the new tasks from the file are added.
    Project metadata and baseline are not modified.
    """
    logger.info(f"import_tasks called for project_id={project_id}, filename={file.filename}, user={current_user.id}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xlsx files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        try:
            tasks_data = parse_tasks_only(tmp_file_path)
            logger.info(f"Excel parsed successfully. Tasks found: {len(tasks_data)}")
        except ExcelParserError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error during Excel parsing: {e}\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error parsing Excel file: {str(e)}"
            )

        for i, task_data in enumerate(tasks_data):
            try:
                task = Task(project_id=project.id, **task_data)
                db.add(task)
            except Exception as e:
                logger.error(f"Error creating task {i+1}: {e}\n{traceback.format_exc()}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error creating task {i+1}: {str(e)}"
                )

        log_audit(
            db=db,
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Project",
            entity_id=project.id,
            changes={"message": f"Imported {len(tasks_data)} tasks from Excel"}
        )

        db.commit()
        db.refresh(project)
        _attach_project_meta(project, db)

        logger.info(f"Imported {len(tasks_data)} tasks into project_id={project_id}")
        return project

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in import_tasks_excel: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")
    finally:
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.post("/{project_id}/update-baseline", response_model=ProjectSchema)
def update_project_baseline(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl)
):
    """
    Snapshot current tasks as the new baseline for a project. Only TDL can update.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    tasks = db.query(Task).filter(Task.project_id == project_id).all()

    # Build task snapshot — same fields the excel parser stores, plus `id` for unique comparison
    task_snapshots = []
    for t in tasks:
        snapshot = {
            'id': t.id,
            'site': t.site,
            'category': t.category,
            'product': t.product,
            'wp': t.wp,
            'wp_id': t.wp_id,
            'unit': t.unit,
            'effort': t.effort,
            'comment': t.comment,
            'tuning_factor': t.tuning_factor,
            'qty': t.qty,
            'total': t.total,
            'role': t.role,
            'resource_category': t.resource_category,
            'support_type': t.support_type,
            'spc': t.spc,
            'resource_name': t.resource_name,
            'start_date': t.start_date,
            'end_date': t.end_date,
            'rate': float(t.rate) if t.rate is not None else None,
            'cost': float(t.cost) if t.cost is not None else None,
        }
        task_snapshots.append(snapshot)

    serialized_tasks = serialize_for_json(task_snapshots)

    project.baseline_json = {
        'opp_id': project.opp_id,
        'name': project.name,
        'version': project.version,
        'imported_at': datetime.utcnow().isoformat(),
        'task_count': len(serialized_tasks),
        'tasks': serialized_tasks,
    }

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="Project",
        entity_id=project.id,
        changes={"message": f"Baseline updated with {len(serialized_tasks)} tasks"}
    )

    db.commit()
    db.refresh(project)
    _attach_project_meta(project, db)

    logger.info(f"Baseline updated for project_id={project_id} with {len(serialized_tasks)} tasks")
    return project


@router.get("/{project_id}/export")
def export_project_excel(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl_or_tpm)
):
    """
    Export all tasks for a project as an Excel file matching the import format.
    Accessible by TDL and TPM.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Non-TDL users can only export projects they have visibility to
    if current_user.role != UserRole.tdl:
        visible_ids = [u.id for u in project.visible_to]
        if current_user.id not in visible_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project"
            )

    tasks = db.query(Task).filter(Task.project_id == project_id).all()

    stream = export_tasks_to_excel(tasks)

    from datetime import datetime
    current_date = datetime.utcnow().strftime('%Y%m%d')
    filename = f"SCD PP DU APJ_{project.opp_id}_{project.name}_EE_v{project.version}_{current_date}.xlsx"

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )


@router.put("/{project_id}/visibility", response_model=ProjectSchema)
def update_project_visibility(
    project_id: int,
    visibility: VisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl)
):
    """
    Set which users can see a project. Only TDL can perform this action.
    TDL users are always kept in the visible list regardless of the payload.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Fetch requested users
    users = db.query(User).filter(User.id.in_(visibility.user_ids)).all()

    # Always include all TDL users
    tdl_users = db.query(User).filter(User.role == UserRole.tdl).all()
    tdl_ids = {u.id for u in tdl_users}
    merged = {u.id: u for u in users}
    for u in tdl_users:
        merged[u.id] = u

    project.visible_to = list(merged.values())
    db.commit()
    db.refresh(project)
    _attach_project_meta(project, db)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="Project",
        entity_id=project.id,
        changes={"visibility": [u.id for u in project.visible_to]}
    )

    return project


@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl)
):
    """
    Delete a project and all its tasks. Only TDL can delete.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    log_audit(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        entity_type="Project",
        entity_id=project.id,
        changes={
            "opp_id": project.opp_id,
            "name": project.name
        }
    )
    
    db.delete(project)
    db.commit()
    
    return MessageResponse(message="Project deleted successfully")