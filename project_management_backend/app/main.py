import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import auth, users, projects, tasks, comments, audit
from app.db.session import engine
from app.models import base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create tables (in production, use Alembic migrations)
# base.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
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
