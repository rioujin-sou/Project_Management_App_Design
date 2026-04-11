from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    create_password_reset_token,
    verify_password_reset_token,
)
from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    Token,
    TokenWithUser,
    LoginRequest,
    RegisterRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
)
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user with 'pending' role.
    Admin (TDL) must assign role later.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with pending role
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=UserRole.pending,
        is_active=True,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return MessageResponse(
        message="Registration successful. Please wait for admin to assign your role."
    )


@router.post("/login", response_model=TokenWithUser)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login and get JWT access token with user data.
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )
    
    # Check if user has a role assigned
    if user.role == UserRole.pending:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval. Please contact an administrator."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    
    return TokenWithUser(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role.value,  # Convert enum to string
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user info.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,  # Convert enum to string
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset. Generates reset token and sends email (mocked for now).
    """
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success to prevent email enumeration
    if not user:
        return MessageResponse(
            message="If the email exists, a password reset link has been sent."
        )
    
    # Generate reset token
    reset_token = create_password_reset_token(user.email)
    
    # Store token and expiry in database
    user.reset_token = reset_token
    user.reset_token_expires_at = datetime.utcnow() + timedelta(
        hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    )
    db.commit()
    
    # Mock email sending (log to console)
    print(f"\\n{'='*60}")
    print(f"PASSWORD RESET EMAIL (MOCK)")
    print(f"{'='*60}")
    print(f"To: {user.email}")
    print(f"Subject: Password Reset Request")
    print(f"\\nReset Token: {reset_token}")
    print(f"\\nUse this token with the /auth/reset-password endpoint")
    print(f"Token expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours")
    print(f"{'='*60}\\n")
    
    return MessageResponse(
        message="If the email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using the reset token.
    """
    # Verify token
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if token matches and is not expired
    if user.reset_token != request.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    if user.reset_token_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Update password
    user.password_hash = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return MessageResponse(message="Password successfully reset")
