import { defineStore } from 'pinia'
import { projectsAPI } from '@/services/api'

export const useProjectsStore = defineStore('projects', {
  state: () => ({
    projects: [],
    currentProject: null,
    loading: false,
    error: null,
    uploadProgress: 0,
  }),

  getters: {
    getProjectById: (state) => (id) => {
      return state.projects.find(p => p.id === parseInt(id))
    },
  },

  actions: {
    async fetchProjects() {
      this.loading = true
      this.error = null
      try {
        const response = await projectsAPI.getAll()
        this.projects = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch projects'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async fetchProjectById(id) {
      this.loading = true
      this.error = null
      try {
        const response = await projectsAPI.getById(id)
        this.currentProject = response.data
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch project'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async uploadExcel(file) {
      this.loading = true
      this.error = null
      this.uploadProgress = 0
      
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        const response = await projectsAPI.uploadExcel(formData)
        this.uploadProgress = 100
        const fetchResult = await this.fetchProjects()
        if (!fetchResult.success) {
          console.warn('[Projects] Upload succeeded but project list refresh failed:', fetchResult.error)
        }
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to upload Excel file'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async deleteProject(id) {
      this.loading = true
      this.error = null
      try {
        await projectsAPI.delete(id)
        this.projects = this.projects.filter(p => p.id !== id)
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to delete project'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async updateBaseline(id) {
      this.loading = true
      this.error = null
      try {
        const response = await projectsAPI.updateBaseline(id)
        if (this.currentProject && this.currentProject.id === id) {
          this.currentProject = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to update baseline'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async updateVisibility(id, userIds) {
      this.loading = true
      this.error = null
      try {
        const response = await projectsAPI.updateVisibility(id, userIds)
        const index = this.projects.findIndex(p => p.id === id)
        if (index !== -1) {
          this.projects[index] = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to update visibility'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    clearCurrentProject() {
      this.currentProject = null
    },
  },
})