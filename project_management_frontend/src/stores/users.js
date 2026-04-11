import { defineStore } from 'pinia'
import { usersAPI } from '@/services/api'

export const useUsersStore = defineStore('users', {
  state: () => ({
    users: [],
    loading: false,
    error: null,
  }),

  getters: {
    pendingUsers: (state) => state.users.filter(u => u.role === 'pending'),
    activeUsers: (state) => state.users.filter(u => u.role !== 'pending'),
  },

  actions: {
    async fetchUsers() {
      this.loading = true
      this.error = null
      try {
        const response = await usersAPI.getAll()
        this.users = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch users'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async deleteUser(userId) {
      this.loading = true
      this.error = null
      try {
        await usersAPI.delete(userId)
        this.users = this.users.filter(u => u.id !== userId)
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to delete user'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async assignRole(userId, role) {
      this.loading = true
      this.error = null
      try {
        const response = await usersAPI.assignRole(userId, role)
        const index = this.users.findIndex(u => u.id === userId)
        if (index !== -1) {
          this.users[index] = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to assign role'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },
  },
})