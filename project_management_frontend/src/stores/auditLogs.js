import { defineStore } from 'pinia'
import { auditLogsAPI } from '@/services/api'

export const useAuditLogsStore = defineStore('auditLogs', {
  state: () => ({
    logs: [],
    loading: false,
    error: null,
    filters: {
      user_id: null,
      entity_type: null,
      start_date: null,
      end_date: null,
    },
    pagination: {
      page: 1,
      limit: 20,
      total: 0,
    },
  }),

  actions: {
    async fetchAuditLogs(filters = {}) {
      this.loading = true
      this.error = null
      
      const params = {
        ...this.filters,
        ...filters,
        skip: (this.pagination.page - 1) * this.pagination.limit,
        limit: this.pagination.limit,
      }
      
      // Remove null/undefined values
      Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === undefined || params[key] === '') {
          delete params[key]
        }
      })
      
      try {
        const response = await auditLogsAPI.getAll(params)
        this.logs = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch audit logs'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
      this.pagination.page = 1
    },

    setPage(page) {
      this.pagination.page = page
    },

    clearFilters() {
      this.filters = {
        user_id: null,
        entity_type: null,
        start_date: null,
        end_date: null,
      }
      this.pagination.page = 1
    },
  },
})
