import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import get_password_hash
from app.api.endpoints import auth, users, projects, tasks, comments, audit
from app.db.session import engine, SessionLocal
from app.models import base
from app.models.user import User, UserRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_first_superuser() -> None:
    """Create the initial TDL admin user if no TDL users exist."""
    db = SessionLocal()
    try:
        tdl_exists = db.query(User).filter(User.role == UserRole.tdl).first()
        if tdl_exists:
            return
        admin = User(
            email=settings.FIRST_SUPERUSER_EMAIL,
            password_hash=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            role=UserRole.tdl,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info(f"[Startup] Created first superuser: {settings.FIRST_SUPERUSER_EMAIL}")
    except Exception as e:
        db.rollback()
        logger.error(f"[Startup] Failed to create first superuser: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_first_superuser()
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    redirect_slashes=False,
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    # Convert AnyHttpUrl to strings and remove trailing slashes
    origins = [str(origin).rstrip('/') for origin in settings.BACKEND_CORS_ORIGINS]
    print(f"[CORS] Allowed origins: {origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # In development, allow all origins
    print("[CORS] No origins specified, allowing all origins for development")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["tasks"])
app.include_router(comments.router, prefix=f"{settings.API_V1_STR}/comments", tags=["comments"])
app.include_router(audit.router, prefix=f"{settings.API_V1_STR}/audit-logs", tags=["audit-logs"])


@app.get("/")
def root():
    return {
        "message": "Project Management API",
        "docs": f"{settings.API_V1_STR}/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
