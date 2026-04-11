import axios from 'axios'
import router from '@/router'
import { getActivePinia } from 'pinia'

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor - add JWT token and check expiry proactively
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      // Check if token is already expired before sending the request
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        if (payload.exp && payload.exp * 1000 < Date.now()) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          try {
            const pinia = getActivePinia()
            if (pinia) {
              const authStore = pinia._s.get('auth')
              if (authStore) {
                authStore.token = null
                authStore.user = null
              }
            }
          } catch (e) {}
          if (router.currentRoute.value.path !== '/login') {
            router.push('/login')
          }
          return Promise.reject(new Error('Token expired'))
        }
      } catch (e) {
        // If we can't decode the token, let the request proceed and handle 401 response
      }
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error
    
    if (response) {
      switch (response.status) {
        case 401:
          // Clear localStorage
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          // Clear Pinia auth store state to keep it in sync
          try {
            const pinia = getActivePinia()
            if (pinia) {
              const authStore = pinia._s.get('auth')
              if (authStore) {
                authStore.token = null
                authStore.user = null
              }
            }
          } catch (e) {
            console.warn('[Auth] Could not clear auth store state:', e)
          }
          if (router.currentRoute.value.path !== '/login') {
            router.push('/login')
          }
          break
        case 403:
          // Forbidden - show error message
          console.error('Access forbidden:', response.data?.detail || 'You do not have permission')
          break
        case 500:
          console.error('Server error:', response.data?.detail || 'Internal server error')
          break
      }
    } else if (error.request) {
      console.error('Network error: No response received')
    } else {
      console.error('Error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (email, password) => 
    api.post('/api/v1/auth/login', { email, password }),
  
  register: (email, password) => 
    api.post('/api/v1/auth/register', { email, password }),
  
  forgotPassword: (email) => 
    api.post('/api/v1/auth/forgot-password', { email }),
  
  resetPassword: (token, newPassword) => 
    api.post('/api/v1/auth/reset-password', { token, new_password: newPassword }),
  
  me: () => 
    api.get('/api/v1/auth/me'),
}

// Projects API
export const projectsAPI = {
  getAll: () => 
    api.get('/api/v1/projects'),
  
  getById: (id) => 
    api.get(`/api/v1/projects/${id}`),
  
  uploadExcel: (formData) => 
    api.post('/api/v1/projects/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  delete: (id) => 
    api.delete(`/api/v1/projects/${id}`),
  
  updateBaseline: (id) => 
    api.post(`/api/v1/projects/${id}/update-baseline`),

  updateVisibility: (id, userIds) =>
    api.put(`/api/v1/projects/${id}/visibility`, { user_ids: userIds }),

  exportExcel: (id) =>
    api.get(`/api/v1/projects/${id}/export`, { responseType: 'blob' }),
}

// Tasks API
export const tasksAPI = {
  getByProject: (projectId) => 
    api.get(`/api/v1/tasks/project/${projectId}`),
  
  getById: (taskId) => 
    api.get(`/api/v1/tasks/${taskId}`),
  
  create: (taskData) => 
    api.post('/api/v1/tasks', taskData),
  
  update: (taskId, taskData) => 
    api.put(`/api/v1/tasks/${taskId}`, taskData),
  
  updateCompletion: (taskId, completionPct) => 
    api.patch(`/api/v1/tasks/${taskId}/completion`, { completion_pct: completionPct }),
  
  delete: (taskId) => 
    api.delete(`/api/v1/tasks/${taskId}`),
}

// Comments API
export const commentsAPI = {
  getByTask: (taskId) => 
    api.get(`/api/v1/comments/${taskId}/comments`),
  
  create: (taskId, content) => 
    api.post(`/api/v1/comments/${taskId}/comments`, { text: content, task_id: taskId }),
  
  delete: (commentId) => 
    api.delete(`/api/v1/comments/${commentId}`),
}

// Audit Logs API
export const auditLogsAPI = {
  getAll: (params = {}) => 
    api.get('/api/v1/audit-logs', { params }),
}

// Users API
export const usersAPI = {
  getAll: () => 
    api.get('/api/v1/users'),
  
  assignRole: (userId, role) => 
    api.put(`/api/v1/users/${userId}/role`, { role }),

  delete: (userId) =>
    api.delete(`/api/v1/users/${userId}`),
}

export default api