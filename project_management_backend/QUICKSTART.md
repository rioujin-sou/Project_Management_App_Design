# Quick Start Guide

This guide will help you quickly set up and test the Project Management API.

## 1. Start the Application

```bash
cd /home/ubuntu/project_management_backend
docker-compose up -d
```

Wait for the services to start (about 30 seconds).

## 2. Check if it's running

```bash
# Check service status
docker-compose ps

# Check backend logs
docker-compose logs -f backend
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Press `Ctrl+C` to exit logs.

## 3. Access the API Documentation

Open your browser and go to:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## 4. Create Your First User (TDL)

### Step 1: Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123456"
  }'
```

### Step 2: Assign TDL Role
Since the first user needs TDL role, update it directly in the database:

```bash
docker-compose exec db psql -U postgres -d project_management -c \
  "UPDATE users SET role = 'tdl' WHERE email = 'admin@example.com';"
```

### Step 3: Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123456"
  }'
```

Copy the `access_token` from the response. You'll need it for authenticated requests.

## 5. Upload a Project from Excel

```bash
# Replace YOUR_TOKEN with the access_token from step 4
TOKEN="YOUR_TOKEN"

curl -X POST http://localhost:8000/api/v1/projects/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/home/ubuntu/Uploads/SCD PP DU APJ_25.JP.415810_Project-Example_EE_v01.xlsx"
```

You should see a response with the created project details, including 26 tasks.

## 6. List Projects

```bash
curl -X GET http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer $TOKEN"
```

## 7. Get Project with Tasks

```bash
# Replace 1 with your project_id
curl -X GET http://localhost:8000/api/v1/projects/1 \
  -H "Authorization: Bearer $TOKEN"
```

## 8. Update a Task (Change Completion)

```bash
# Replace 1 with your task_id
curl -X PUT http://localhost:8000/api/v1/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "completion_pct": 50
  }'
```

## 9. Add a Comment to a Task

```bash
# Replace 1 with your task_id
curl -X POST http://localhost:8000/api/v1/comments/1/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Work in progress, halfway done!"
  }'
```

## 10. View Audit Logs

```bash
curl -X GET http://localhost:8000/api/v1/audit-logs/ \
  -H "Authorization: Bearer $TOKEN"
```

## Testing TPM Role

### Create a TPM user
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "tpm@example.com",
    "password": "tpm123456"
  }'

# Assign TPM role (use TDL token)
curl -X PUT http://localhost:8000/api/v1/users/2/role \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "tpm"
  }'

# Login as TPM
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "tpm@example.com",
    "password": "tpm123456"
  }'

# Use TPM token to update task (limited fields only)
TPM_TOKEN="tpm_access_token_here"
curl -X PUT http://localhost:8000/api/v1/tasks/1 \
  -H "Authorization: Bearer $TPM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "completion_pct": 75,
    "end_date": "2026-04-30"
  }'
```

## Useful Commands

### Stop the application
```bash
docker-compose down
```

### View all logs
```bash
docker-compose logs -f
```

### Reset everything (WARNING: deletes all data)
```bash
docker-compose down -v
docker-compose up -d
```

### Access database directly
```bash
docker-compose exec db psql -U postgres -d project_management

# Useful SQL queries
\dt                          # List tables
SELECT * FROM users;        # View users
SELECT * FROM projects;     # View projects
SELECT * FROM tasks LIMIT 5; # View first 5 tasks
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10; # Recent audit logs
\q                          # Exit
```

## Troubleshooting

### Services not starting
```bash
# Check Docker logs
docker-compose logs

# Rebuild containers
docker-compose up -d --build
```

### Database connection errors
```bash
# Restart database
docker-compose restart db

# Wait a few seconds, then restart backend
docker-compose restart backend
```

### Excel upload errors
- Ensure filename matches pattern: `SCD PP DU APJ_{opp_id}_{name}_EE_v{version}.xlsx`
- Check that `EffortEstimation` sheet exists
- Verify all required columns are present

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore the API using Swagger UI at http://localhost:8000/api/v1/docs
3. Test password reset functionality
4. Try creating, updating, and deleting tasks with different roles
5. Review audit logs to see all tracked actions

## API Testing Tools

Besides curl, you can use:
- **Swagger UI**: http://localhost:8000/api/v1/docs (built-in, interactive)
- **Postman**: Import OpenAPI spec from http://localhost:8000/api/v1/openapi.json
- **HTTPie**: `http POST localhost:8000/api/v1/auth/login email=admin@example.com password=admin123456`
