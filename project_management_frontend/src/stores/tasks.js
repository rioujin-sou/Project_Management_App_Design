import { defineStore } from 'pinia'
import { tasksAPI } from '@/services/api'

export const useTasksStore = defineStore('tasks', {
  state: () => ({
    tasks: [],
    currentTask: null,
    loading: false,
    error: null,
  }),

  getters: {
    // Get unique sites from tasks
    uniqueSites: (state) => {
      const sites = [...new Set(state.tasks.map(t => t.site).filter(Boolean))]
      return sites.sort()
    },

    // Get tasks grouped by site
    tasksBySite: (state) => (site) => {
      return state.tasks.filter(t => t.site === site)
    },

    // Get tasks grouped by status (completion)
    tasksByStatus: (state) => (site) => {
      const siteTasks = site ? state.tasks.filter(t => t.site === site) : state.tasks
      return {
        todo: siteTasks.filter(t => t.completion_pct === 0 || t.completion_pct === null),
        inProgress: siteTasks.filter(t => t.completion_pct > 0 && t.completion_pct < 100),
        done: siteTasks.filter(t => t.completion_pct === 100),
      }
    },

    getTaskById: (state) => (id) => {
      return state.tasks.find(t => t.id === parseInt(id))
    },
  },

  actions: {
    async fetchTasks(projectId) {
      this.loading = true
      this.error = null
      try {
        const response = await tasksAPI.getByProject(projectId)
        this.tasks = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch tasks'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async fetchTaskById(taskId) {
      this.loading = true
      this.error = null
      try {
        const response = await tasksAPI.getById(taskId)
        this.currentTask = response.data
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch task'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async createTask(taskData) {
      this.loading = true
      this.error = null
      try {
        const response = await tasksAPI.create(taskData)
        this.tasks.push(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to create task'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async updateTask(taskId, taskData) {
      this.loading = true
      this.error = null
      try {
        const response = await tasksAPI.update(taskId, taskData)
        const index = this.tasks.findIndex(t => t.id === taskId)
        if (index !== -1) {
          this.tasks[index] = response.data
        }
        if (this.currentTask?.id === taskId) {
          this.currentTask = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to update task'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async updateTaskCompletion(taskId, completionPct) {
      this.error = null
      try {
        const response = await tasksAPI.updateCompletion(taskId, completionPct)
        const index = this.tasks.findIndex(t => t.id === taskId)
        if (index !== -1) {
          this.tasks[index] = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to update task completion'
        return { success: false, error: this.error }
      }
    },

    async deleteTask(taskId) {
      this.loading = true
      this.error = null
      try {
        await tasksAPI.delete(taskId)
        this.tasks = this.tasks.filter(t => t.id !== taskId)
        if (this.currentTask?.id === taskId) {
          this.currentTask = null
        }
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to delete task'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    setCurrentTask(task) {
      this.currentTask = task
    },

    clearTasks() {
      this.tasks = []
      this.currentTask = null
    },
  },
})
