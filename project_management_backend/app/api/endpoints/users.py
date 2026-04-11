from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import User as UserSchema, UserRoleUpdate
from app.schemas.auth import MessageResponse
from app.api.deps.auth import get_current_user, require_tdl
from datetime import datetime

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    """
    return current_user


@router.put("/{user_id}/role", response_model=UserSchema)
def assign_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl)
):
    """
    Assign role to a user. Only TDL can perform this action.
    Cannot assign 'pending' role.
    """
    # Validate role
    if role_update.role == UserRole.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign 'pending' role. Use 'tdl', 'tpm', 'pm', or 'sa'."
        )
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update role
    user.role = role_update.role
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl)
):
    """
    Delete a user. Only TDL can perform this action.
    Cannot delete your own account or the last TDL.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent deleting the last TDL
    if user.role == UserRole.tdl:
        tdl_count = db.query(User).filter(User.role == UserRole.tdl).count()
        if tdl_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last TDL user."
            )

    db.delete(user)
    db.commit()

    return MessageResponse(message=f"User {user.email} deleted successfully")


@router.get("/", response_model=list[UserSchema])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tdl)
):
    """
    List all users. Only TDL can perform this action.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users