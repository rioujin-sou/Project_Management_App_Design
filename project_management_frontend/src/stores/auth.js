import { defineStore } from 'pinia'
import { authAPI } from '@/services/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('access_token') || null,
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.user?.role || null,
    isTDL: (state) => state.user?.role === 'tdl',
    isTPM: (state) => state.user?.role === 'tpm',
    isPending: (state) => state.user?.role === 'pending',
  },

  actions: {
    async login(email, password) {
      this.loading = true
      this.error = null
      try {
        const response = await authAPI.login(email, password)
        console.log('[Auth] Login response:', response.data)
        
        const { access_token, user } = response.data
        
        this.token = access_token
        localStorage.setItem('access_token', access_token)
        
        // If login response includes user data, use it
        if (user) {
          console.log('[Auth] User from login response:', user, 'Role:', user.role)
          this.user = user
          localStorage.setItem('user', JSON.stringify(user))
        }
        
        // Always fetch fresh user data from /users/me to ensure we have the role
        try {
          const meResponse = await authAPI.me()
          console.log('[Auth] /users/me response:', meResponse.data)
          this.user = meResponse.data
          localStorage.setItem('user', JSON.stringify(meResponse.data))
          console.log('[Auth] Final user state:', this.user, 'Role:', this.user?.role, 'isTDL:', this.user?.role === 'tdl')
        } catch (meError) {
          console.warn('[Auth] Failed to fetch /users/me, using login response user data:', meError)
        }
        
        router.push('/projects')
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Login failed'
        console.error('[Auth] Login error:', this.error)
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async register(email, password) {
      this.loading = true
      this.error = null
      try {
        await authAPI.register(email, password)
        return { success: true, message: 'Registration successful. Please wait for admin approval.' }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Registration failed'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async forgotPassword(email) {
      this.loading = true
      this.error = null
      try {
        await authAPI.forgotPassword(email)
        return { success: true, message: 'Password reset instructions sent to your email' }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to send reset email'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async resetPassword(token, newPassword) {
      this.loading = true
      this.error = null
      try {
        await authAPI.resetPassword(token, newPassword)
        return { success: true, message: 'Password reset successful. Please login.' }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to reset password'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async checkAuth() {
      if (!this.token) {
        console.log('[Auth] checkAuth: No token found')
        return false
      }
      
      try {
        const response = await authAPI.me()
        console.log('[Auth] checkAuth /users/me response:', response.data)
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
        console.log('[Auth] checkAuth updated user:', this.user, 'Role:', this.user?.role)
        return true
      } catch (error) {
        console.error('[Auth] checkAuth failed:', error)
        this.logout()
        return false
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      router.push('/login')
    },
  },
})
