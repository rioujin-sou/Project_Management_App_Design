import { defineStore } from 'pinia'
import { commentsAPI } from '@/services/api'

export const useCommentsStore = defineStore('comments', {
  state: () => ({
    comments: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchComments(taskId) {
      this.loading = true
      this.error = null
      try {
        const response = await commentsAPI.getByTask(taskId)
        this.comments = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch comments'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async addComment(taskId, content) {
      this.loading = true
      this.error = null
      try {
        const response = await commentsAPI.create(taskId, content)
        this.comments.push(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to add comment'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async deleteComment(commentId) {
      this.loading = true
      this.error = null
      try {
        await commentsAPI.delete(commentId)
        this.comments = this.comments.filter(c => c.id !== commentId)
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to delete comment'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    clearComments() {
      this.comments = []
    },
  },
})
