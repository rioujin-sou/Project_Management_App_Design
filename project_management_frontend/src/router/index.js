import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Auth pages
import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'
import ForgotPasswordView from '@/views/auth/ForgotPasswordView.vue'
import ResetPasswordView from '@/views/auth/ResetPasswordView.vue'

// Main layout
import AppLayout from '@/components/AppLayout.vue'

const routes = [
  // Public routes
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false, public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: { requiresAuth: false, public: true },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPasswordView,
    meta: { requiresAuth: false, public: true },
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: ResetPasswordView,
    meta: { requiresAuth: false, public: true },
  },

  // Protected routes with layout
  {
    path: '/',
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/projects',
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/projects/ProjectListView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/projects/ProjectDetailView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'projects/:id/kanban',
        name: 'ProjectKanban',
        component: () => import('@/views/projects/KanbanView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'projects/:id/gantt',
        name: 'ProjectGantt',
        component: () => import('@/views/projects/GanttView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'projects/:id/baseline-diff',
        name: 'BaselineDiff',
        component: () => import('@/views/projects/BaselineDiffView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'audit-logs',
        name: 'AuditLogs',
        component: () => import('@/views/AuditLogsView.vue'),
        meta: { requiresAuth: true, requiresTDL: true },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/UserManagementView.vue'),
        meta: { requiresAuth: true, requiresTDL: true },
      },
    ],
  },

  // Catch all - 404
  {
    path: '/:pathMatch(.*)*',
    redirect: '/projects',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  console.log('[Router] Navigation to:', to.path, 'Token exists:', !!authStore.token, 'User:', authStore.user)

  // Public routes
  if (to.meta.public) {
    if (authStore.isAuthenticated && !authStore.isPending) {
      return next('/projects')
    }
    return next()
  }

  // Protected routes - check auth
  if (to.meta.requiresAuth) {
    if (!authStore.token) {
      console.log('[Router] No token, redirecting to login')
      return next('/login')
    }
    
    // If we have a token but no user data (or missing role), fetch it
    if (!authStore.user || !authStore.user.role) {
      console.log('[Router] Token exists but user data incomplete, calling checkAuth')
      const authValid = await authStore.checkAuth()
      if (!authValid) {
        console.log('[Router] checkAuth failed, redirecting to login')
        return next('/login')
      }
    }
    
    console.log('[Router] After auth check - User:', authStore.user, 'Role:', authStore.userRole, 'isTDL:', authStore.isTDL)
  }

  // Check if user has pending role
  if (authStore.isAuthenticated && authStore.isPending && to.path !== '/login') {
    console.log('[Router] User has pending role, logging out')
    authStore.logout()
    return next('/login')
  }

  // TDL-only routes
  if (to.meta.requiresTDL && authStore.userRole !== 'tdl') {
    console.log('[Router] TDL route access denied for role:', authStore.userRole)
    return next('/projects')
  }

  next()
})

export default router
