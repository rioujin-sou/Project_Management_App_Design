# Project Management Backend API

A comprehensive FastAPI backend for project management with role-based access control, Excel import, and audit logging.

## Features

- 🔐 **JWT Authentication** with role-based access control
- 📊 **Excel Import** for project creation from standardized templates
- 👥 **Role Management**: TDL (Technical Delivery Lead) and TPM (Technical Project Manager)
- 📝 **Task Management** with granular permissions
- 💬 **Comments System** for task collaboration
- 📋 **Audit Logging** for all actions
- 🐳 **Docker Compose** for easy deployment
- 📚 **OpenAPI Documentation** (Swagger UI)

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Excel Parsing**: openpyxl, pandas
- **Server**: Uvicorn

## Project Structure

```
project_management_backend/
├── app/
│   ├── api/
│   │   ├── deps/
│   │   │   └── auth.py          # Authentication dependencies
│   │   └── endpoints/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── users.py         # User management
│   │       ├── projects.py      # Project CRUD + Excel upload
│   │       ├── tasks.py         # Task management
│   │       ├── comments.py      # Comments system
│   │       └── audit.py         # Audit logs
│   ├── core/
│   │   ├── config.py            # Settings management
│   │   └── security.py          # Password hashing, JWT
│   ├── db/
│   │   └── session.py           # Database session
│   ├── models/
│   │   ├── user.py              # User model
│   │   ├── project.py           # Project model
│   │   ├── task.py              # Task model
│   │   ├── comment.py           # Comment model
│   │   └── audit_log.py         # AuditLog model
│   ├── schemas/
│   │   ├── auth.py              # Auth schemas
│   │   ├── user.py              # User schemas
│   │   ├── project.py           # Project schemas
│   │   ├── task.py              # Task schemas
│   │   ├── comment.py           # Comment schemas
│   │   └── audit_log.py         # AuditLog schemas
│   ├── services/
│   │   ├── excel_parser.py      # Excel file parser
│   │   └── audit_service.py     # Audit logging service
│   └── main.py                  # FastAPI application
├── alembic/
│   ├── versions/
│   │   └── 001_initial_schema.py
│   └── env.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Setup Instructions

### Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.11+ and PostgreSQL 15

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   cd /home/ubuntu/project_management_backend
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and update SECRET_KEY and other settings
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Check the logs**
   ```bash
   docker-compose logs -f backend
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

### Option 2: Local Setup

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL**
   ```bash
   # Create database
   psql -U postgres
   CREATE DATABASE project_management;
   \\q
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and update DATABASE_URL, SECRET_KEY, etc.
   ```

5. **Run migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/project_management` |
| `SECRET_KEY` | JWT secret key (change in production!) | - |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `30` |
| `API_V1_STR` | API version prefix | `/api/v1` |
| `PROJECT_NAME` | Project name | `Project Management API` |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins (JSON array) | `[\"http://localhost:3000\"]` |
| `EMAIL_ENABLED` | Enable email notifications | `false` |

## User Roles

### Pending
- Default role for new registrations
- Cannot access any endpoints until role is assigned by TDL

### TDL (Technical Delivery Lead)
- Full permissions on all resources
- Can upload/delete projects
- Can create/update/delete tasks (all fields)
- Can assign roles to users
- Can view audit logs
- Can add comments

### TPM (Technical Project Manager)
- Limited permissions
- Can view projects and tasks
- Can create/delete tasks
- Can update tasks (only: `start_date`, `end_date`, `completion_pct`)
- Can add comments
- Cannot delete projects
- Cannot view audit logs
- Cannot assign roles

## API Endpoints

### Authentication

#### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### Forgot Password
```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```
*Note: Reset token is currently logged to console (mock email)*

#### Reset Password
```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "reset_token_here",
  "new_password": "newpassword123"
}
```

### Users

#### Get Current User
```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

#### Assign Role (TDL only)
```http
PUT /api/v1/users/{user_id}/role
Authorization: Bearer <token>
Content-Type: application/json

{
  "role": "tdl"  // or "tpm"
}
```

#### List All Users (TDL only)
```http
GET /api/v1/users/
Authorization: Bearer <token>
```

### Projects

#### List Projects
```http
GET /api/v1/projects/
Authorization: Bearer <token>
```

#### Get Project with Tasks
```http
GET /api/v1/projects/{project_id}
Authorization: Bearer <token>
```

#### Upload Excel (TDL only)
```http
POST /api/v1/projects/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <excel_file>
```

**Excel File Requirements:**
- Filename pattern: `SCD PP DU APJ_{opp_id}_{name}_EE_v{version}.xlsx`
- Must contain sheet: `EffortEstimation`
- Required columns: Site, Category, Product, WP, WP-ID, Unit, Effort, Comment, Tuning Factor, Qty, Total, Role, Resource Category, Support Type, SPC, Resource Name, Start Date, End Date
- Optional columns: Rate, Cost

#### Delete Project (TDL only)
```http
DELETE /api/v1/projects/{project_id}
Authorization: Bearer <token>
```

### Tasks

#### List Tasks
```http
GET /api/v1/tasks/{project_id}/tasks
Authorization: Bearer <token>
```

#### Create Task
```http
POST /api/v1/tasks/{project_id}/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "site": "Solution",
  "category": "DES",
  "product": "Solution",
  "wp": "HLD",
  "wp_id": "WP001",
  "unit": "days",
  "effort": 5.0,
  "comment": "Task description",
  "tuning_factor": 1.0,
  "qty": 1,
  "total": 5.0,
  "role": "SA",
  "resource_category": "Internal",
  "support_type": "Onsite",
  "spc": "SPC001",
  "resource_name": "John Doe",
  "start_date": "2026-03-01",
  "end_date": "2026-03-05",
  "completion_pct": 0
}
```

#### Update Task
```http
PUT /api/v1/tasks/{task_id}
Authorization: Bearer <token>
Content-Type: application/json

// TDL can update all fields
// TPM can only update: start_date, end_date, completion_pct
{
  "start_date": "2026-03-02",
  "end_date": "2026-03-06",
  "completion_pct": 50
}
```

**Task Status (computed from completion_pct):**
- `0%` → "To Do"
- `1-99%` → "In Progress"
- `100%` → "Done"

#### Delete Task
```http
DELETE /api/v1/tasks/{task_id}
Authorization: Bearer <token>
```

### Comments

#### Get Task Comments
```http
GET /api/v1/comments/{task_id}/comments
Authorization: Bearer <token>
```

#### Add Comment
```http
POST /api/v1/comments/{task_id}/comments
Authorization: Bearer <token>
Content-Type: application/json

{
  "text": "This is a comment"
}
```

### Audit Logs

#### Get Audit Logs (TDL only)
```http
GET /api/v1/audit-logs/?user_id=1&entity_type=Task&start_date=2026-03-01&end_date=2026-03-31
Authorization: Bearer <token>
```

**Query Parameters:**
- `user_id` (optional): Filter by user ID
- `entity_type` (optional): Filter by entity type (User, Project, Task, Comment)
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Pagination limit (default: 100)

## Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend

# Restart backend
docker-compose restart backend

# Rebuild and start
docker-compose up -d --build

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v

# Access database
docker-compose exec db psql -U postgres -d project_management

# Run migrations manually
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Testing

### Manual Testing with curl

1. **Register a user**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \\
     -H "Content-Type: application/json" \\
     -d '{"email":"tdl@example.com","password":"password123"}'
   ```

2. **Assign TDL role** (requires existing TDL or manual DB update)
   ```sql
   -- Connect to database
   docker-compose exec db psql -U postgres -d project_management
   
   -- Update user role
   UPDATE users SET role = 'tdl' WHERE email = 'tdl@example.com';
   ```

3. **Login**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \\
     -H "Content-Type: application/json" \\
     -d '{"email":"tdl@example.com","password":"password123"}'
   ```

4. **Upload Excel file**
   ```bash
   TOKEN="your_jwt_token_here"
   curl -X POST http://localhost:8000/api/v1/projects/upload \\
     -H "Authorization: Bearer $TOKEN" \\
     -F "file=@/path/to/your/file.xlsx"
   ```

## Deployment Fixes & Notes

### bcrypt Dependency (requirements.txt)

`passlib[bcrypt]` declares bcrypt as an *extra* dependency but does not pin a
specific version.  In some environments (Docker / Alpine), an incompatible
bcrypt version may be pulled, leading to `"hash could not be identified"` errors
at login time.  **Fix:** `bcrypt==4.0.1` is now explicitly listed in
`requirements.txt` alongside `passlib[bcrypt]`.

### Docker Compose Version Field (docker-compose.yml)

Docker Compose **v2+** no longer requires the top-level `version:` key. Keeping
it produces a deprecation warning. The field has been removed; existing
deployments using Compose v1 should upgrade to v2.

### CORS Configuration (app/core/config.py)

`BACKEND_CORS_ORIGINS` previously only accepted a list of valid HTTP URLs.  In
development it is common to set `["*"]` to allow all origins.  The validator now
accepts both formats:

| Value | Environment |
|-------|-------------|
| `["http://localhost:3000"]` | Development with specific origins |
| `["*"]` | Development / testing (allow all) |
| `["https://app.example.com"]` | Production (locked down) |

> ⚠️ **Security warning:** Never use `["*"]` in production — it disables CORS
> origin checking entirely and exposes the API to cross-site attacks.

---

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check PostgreSQL logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Migration Issues
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d

# Or manually drop and recreate
docker-compose exec db psql -U postgres -c "DROP DATABASE project_management;"
docker-compose exec db psql -U postgres -c "CREATE DATABASE project_management;"
docker-compose exec backend alembic upgrade head
```

### Import Errors
```bash
# Rebuild backend container
docker-compose up -d --build backend
```

## Security Considerations

⚠️ **IMPORTANT**: Before deploying to production:

1. **Change SECRET_KEY**: Generate a secure random key
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use environment-specific .env files**
   - Never commit `.env` to version control
   - Use different keys for dev/staging/production

3. **Configure CORS**: Update `BACKEND_CORS_ORIGINS` with your frontend URL

4. **Enable HTTPS**: Use reverse proxy (nginx/traefik) with SSL certificates

5. **Database Security**:
   - Change default PostgreSQL password
   - Use strong passwords
   - Restrict network access

6. **Email Configuration**: Configure SMTP settings for password reset emails

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.
