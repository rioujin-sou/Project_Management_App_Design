import { defineStore } from 'pinia'
import { precedenceAPI } from '@/services/api'

export const usePrecedencesStore = defineStore('precedences', {
  state: () => ({
    taskPrecedences: [],     // precedences for the task currently open in the dialog
    projectPrecedences: [],  // all precedences for the project (used by Gantt for link arrows)
    loading: false,
    error: null,
  }),

  actions: {
    async fetchTaskPrecedences(taskId) {
      this.loading = true
      this.error = null
      try {
        const response = await precedenceAPI.list(taskId)
        this.taskPrecedences = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch precedences'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async fetchProjectPrecedences(projectId) {
      this.error = null
      try {
        const response = await precedenceAPI.listByProject(projectId)
        this.projectPrecedences = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch project precedences'
        return { success: false, error: this.error }
      }
    },

    async addPrecedences(taskId, items, projectId) {
      this.loading = true
      this.error = null
      try {
        await precedenceAPI.add(taskId, items)
        await this.fetchTaskPrecedences(taskId)
        if (projectId) await this.fetchProjectPrecedences(projectId)
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to add precedences'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async removePrecedence(taskId, precedenceId, projectId) {
      this.loading = true
      this.error = null
      try {
        await precedenceAPI.remove(taskId, precedenceId)
        this.taskPrecedences = this.taskPrecedences.filter(p => p.id !== precedenceId)
        this.projectPrecedences = this.projectPrecedences.filter(p => p.id !== precedenceId)
        if (projectId) await this.fetchProjectPrecedences(projectId)
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to remove precedence'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    clearTaskPrecedences() {
      this.taskPrecedences = []
    },
  },
})
