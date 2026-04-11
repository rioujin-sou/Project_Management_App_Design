# Project Management Frontend

A Vue 3 frontend application for project management with Kanban board, Gantt chart, and baseline tracking features.

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **Vite** - Fast build tool and dev server
- **Pinia** - State management
- **Vue Router** - Client-side routing
- **PrimeVue** - UI component library
- **DHTMLX Gantt** - Gantt chart visualization
- **vuedraggable** - Drag-and-drop for Kanban board
- **Axios** - HTTP client

## Features

### Authentication
- User login/logout
- User registration (pending approval)
- Password reset flow
- JWT-based authentication
- Role-based access control (TDL, TPM)

### Project Management
- Project list with search and sort
- Excel file upload for project creation
- Project deletion (TDL only)

### Kanban Board
- Dynamic site-based tabs
- Three columns: To Do, In Progress, Done
- Drag-and-drop task management
- Automatic completion % updates
- Task detail panel with comments

### Gantt Chart
- Timeline visualization of tasks
- Toggleable columns
- Site filtering
- Zoom levels (Day, Week, Month)
- Click-to-view task details

### Baseline Comparison
- Compare current tasks with baseline
- View added, removed, and modified tasks
- Field-by-field change highlighting

### Audit Logs (TDL Only)
- Complete activity history
- Filterable by user, entity type, date
- Expandable rows for detailed changes

### User Management (TDL Only)
- View all users
- Assign roles to pending users
- Update user roles

## Getting Started

### Prerequisites

- **Node.js 22.0.0 or higher** (Required for Vite 7.x)
- npm 10+ or yarn 1.22+

> ✅ **Note**: This project uses **Vite 7.x** which requires **Node.js 22+**. The `crypto.hash` API used by Vite 7 is only available in Node.js 21.7.0+, but we recommend Node.js 22+ for the best performance and stability.

#### Benefits of Node.js 22+ with Vite 7.x
- **Faster builds**: Native ES module support and improved V8 performance
- **Better security**: Latest security patches and features
- **Modern APIs**: Access to native `crypto.hash` and other modern Node.js APIs
- **Long-term support**: Node.js 22 becomes LTS in October 2024

### Installation

```bash
# Clone the repository
cd project_management_frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.development
```

### Development

```bash
# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
# Build the application
npm run build

# Preview production build
npm run preview
```

## Docker Deployment

### Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services

- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_NAME=project_management

# Backend
SECRET_KEY=your-secret-key-change-in-production
```

## Project Structure

```
src/
├── assets/
│   └── styles/
│       └── main.css        # Global styles
├── components/
│   ├── AppLayout.vue       # Main app layout
│   └── TaskDetailPanel.vue # Task detail sidebar
├── router/
│   └── index.js            # Vue Router configuration
├── services/
│   └── api.js              # Axios API service
├── stores/
│   ├── auth.js             # Authentication store
│   ├── projects.js         # Projects store
│   ├── tasks.js            # Tasks store
│   ├── comments.js         # Comments store
│   ├── auditLogs.js        # Audit logs store
│   └── users.js            # Users store
├── views/
│   ├── auth/
│   │   ├── LoginView.vue
│   │   ├── RegisterView.vue
│   │   ├── ForgotPasswordView.vue
│   │   └── ResetPasswordView.vue
│   ├── projects/
│   │   ├── ProjectListView.vue
│   │   ├── ProjectDetailView.vue
│   │   ├── KanbanView.vue
│   │   ├── GanttView.vue
│   │   └── BaselineDiffView.vue
│   ├── users/
│   │   └── UserManagementView.vue
│   └── AuditLogsView.vue
├── App.vue
└── main.js
```

## API Integration

The frontend communicates with the FastAPI backend at `/api/v1`. Key endpoints:

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects/upload` - Upload Excel file
- `GET /api/v1/tasks/project/:id` - Get project tasks
- `PATCH /api/v1/tasks/:id/completion` - Update task completion
- `GET /api/v1/comments/task/:id` - Get task comments
- `GET /api/v1/audit-logs` - Get audit logs

## Role Permissions

### TDL (Team Delivery Lead)
- Full access to all features
- Upload and delete projects
- Edit all task fields
- View audit logs
- Manage users

### TPM (Technical Project Manager)
- View projects and tasks
- Edit limited task fields (start_date, end_date, completion_pct)
- Add comments
- Cannot access audit logs or user management

## Troubleshooting

### Build Error: `crypto.hash is not a function`

This error occurs when using Vite 7.x with Node.js versions below 21.7.0.

**Solution**: Upgrade Node.js to version 22+
```bash
# Using nvm (recommended)
nvm install 22
nvm use 22
node --version  # Should show v22.x.x

# Clean install and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build
```

> ⚠️ **Important**: Vite 7.x requires Node.js 22+. If you cannot upgrade Node.js, you'll need to downgrade Vite to version 5.x.

### Node.js Version Check

To verify your Node.js version meets the requirements:
```bash
node --version
# Must be v22.0.0 or higher
```

### Other Common Issues

- **Module not found errors**: Delete `node_modules` and `package-lock.json`, then run `npm install`
- **Port already in use**: Change the port in `vite.config.js` or stop the conflicting process
- **API connection errors**: Ensure the backend is running and `.env` has the correct API URL
- **Deprecated packages warning**: Some packages may show deprecation warnings but will still work

## License

MIT
