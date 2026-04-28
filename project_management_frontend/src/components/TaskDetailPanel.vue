<template>
  <Sidebar
    v-model:visible="isVisible"
    position="right"
    :style="{ width: '500px' }"
    class="task-detail-panel"
  >
    <template #header>
      <div class="panel-title">
        <span>Task Details</span>
        <span v-if="task" class="wp-id">{{ task.wp_id }}</span>
      </div>
    </template>

    <div v-if="loading" class="loading-container">
      <ProgressSpinner />
    </div>

    <div v-else-if="task" class="panel-body">
      <div class="task-fields">
        <!-- Read-only fields -->
        <div class="field-group">
          <label>WP-ID</label>
          <div class="field-value">{{ task.wp_id }}</div>
        </div>

        <div class="field-group">
          <label>Task</label>
          <div class="field-value">{{ task.wp || '-' }}</div>
        </div>

        <div class="field-group">
          <label>Site</label>
          <div class="field-value">{{ task.site || '-' }}</div>
        </div>

        <div class="field-group">
          <label>Role</label>
          <div class="field-value">{{ task.role || '-' }}</div>
        </div>

        <div class="field-group">
          <label>Resource Name</label>
          <div v-if="!isEditing || !canEditAllFields" class="field-value">{{ task.resource_name || '-' }}</div>
          <InputText v-else v-model="editForm.resource_name" class="w-full" />
        </div>

        <div class="field-row">
          <div class="field-group">
            <label>Total Effort (MWDs)</label>
            <div class="field-value">
              {{ isEditing && isInternal ? editForm.total : (task.total ?? '-') }}
            </div>
          </div>
          <div class="field-group">
            <label>Qty</label>
            <div class="field-value">{{ task.qty ?? '-' }}</div>
          </div>
        </div>

        <div class="field-group">
          <label>Comment</label>
          <div class="field-value">{{ task.comment || '-' }}</div>
        </div>

        <!-- Editable fields -->
        <div class="field-row">
          <div class="field-group">
            <label>Start Date</label>
            <div v-if="!isEditing" class="field-value">{{ formatDate(task.start_date) }}</div>
            <DatePicker v-else v-model="editForm.start_date" dateFormat="yy-mm-dd" class="w-full" />
          </div>
          <div class="field-group">
            <label>End Date</label>
            <div v-if="!isEditing" class="field-value">{{ formatDate(task.end_date) }}</div>
            <DatePicker v-else v-model="editForm.end_date" dateFormat="yy-mm-dd" class="w-full" />
          </div>
        </div>

        <div class="field-group">
          <label>Completion %</label>
          <div v-if="!isEditing" class="field-value">
            <ProgressBar :value="task.completion_pct || 0" :showValue="true" style="height: 20px" />
          </div>
          <Dropdown
            v-else
            v-model="editForm.completion_pct"
            :options="completionOptions"
            optionLabel="label"
            optionValue="value"
            class="w-full"
          />
        </div>
      </div>

      <!-- Action buttons -->
      <div class="action-buttons">
        <template v-if="!isEditing">
          <Button
            v-if="canEditAllFields"
            label="Delete"
            icon="pi pi-trash"
            severity="danger"
            outlined
            @click="confirmDelete"
          />
          <Button
            label="Edit"
            icon="pi pi-pencil"
            @click="startEditing"
          />
        </template>
        <template v-else>
          <Button
            label="Cancel"
            severity="secondary"
            @click="cancelEditing"
          />
          <Button
            label="Save"
            icon="pi pi-check"
            :loading="saving"
            @click="saveChanges"
          />
        </template>
      </div>

      <!-- Delete Confirmation Dialog -->
      <Dialog
        v-model:visible="showDeleteDialog"
        modal
        header="Confirm Delete"
        :style="{ width: '400px' }"
      >
        <p>Are you sure you want to delete task <strong>{{ task?.wp_id }}</strong>? This action cannot be undone.</p>
        <template #footer>
          <Button
            label="Cancel"
            severity="secondary"
            @click="showDeleteDialog = false"
          />
          <Button
            label="Delete"
            icon="pi pi-trash"
            severity="danger"
            :loading="deleting"
            @click="executeDelete"
          />
        </template>
      </Dialog>

      <!-- Comments Section -->
      <div class="comments-section">
        <h3>
          <i class="pi pi-comments"></i>
          Comments
          <span class="comment-count">({{ comments.length }})</span>
        </h3>

        <div class="comments-list">
          <div v-if="commentsLoading" class="loading-container small">
            <ProgressSpinner style="width: 30px; height: 30px" />
          </div>

          <div v-else-if="comments.length === 0" class="no-comments">
            <i class="pi pi-comment"></i>
            <p>No comments yet</p>
          </div>

          <div v-else>
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <div class="comment-header">
                <span class="comment-user">{{ comment.user?.email || 'Unknown' }}</span>
                <span class="comment-date">{{ formatDateTime(comment.created_at) }}</span>
              </div>
              <div class="comment-text">{{ comment.text }}</div>
            </div>
          </div>
        </div>

        <div class="add-comment">
          <Textarea
            v-model="newComment"
            placeholder="Write a comment..."
            :autoResize="true"
            rows="2"
            class="w-full"
          />
          <Button
            label="Add Comment"
            icon="pi pi-send"
            :loading="addingComment"
            :disabled="!newComment.trim()"
            @click="addComment"
          />
        </div>
      </div>
    </div>
  </Sidebar>
</template>

<script setup>
import { ref, computed, watch, reactive, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTasksStore } from '@/stores/tasks'
import { useCommentsStore } from '@/stores/comments'
import { useToast } from 'primevue/usetoast'
import Sidebar from 'primevue/sidebar'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import DatePicker from 'primevue/datepicker'
import Textarea from 'primevue/textarea'
import ProgressBar from 'primevue/progressbar'
import ProgressSpinner from 'primevue/progressspinner'

const props = defineProps({
  visible: Boolean,
  task: Object,
})

const emit = defineEmits(['update:visible', 'updated', 'deleted'])

const authStore = useAuthStore()
const tasksStore = useTasksStore()
const commentsStore = useCommentsStore()
const toast = useToast()

const isVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const isEditing = ref(false)
const commentsLoading = ref(false)
const addingComment = ref(false)
const newComment = ref('')
const showDeleteDialog = ref(false)

const editForm = reactive({
  start_date: null,
  end_date: null,
  completion_pct: 0,
  resource_name: '',
  total: 0,
})

const comments = computed(() => commentsStore.comments)

const canEditAllFields = computed(() => authStore.isTDL)

const completionOptions = [
  { label: '0%', value: 0 },
  { label: '10%', value: 10 },
  { label: '20%', value: 20 },
  { label: '30%', value: 30 },
  { label: '40%', value: 40 },
  { label: '50%', value: 50 },
  { label: '60%', value: 60 },
  { label: '70%', value: 70 },
  { label: '80%', value: 80 },
  { label: '90%', value: 90 },
  { label: '100%', value: 100 },
]

watch(
  () => props.task,
  async (newTask) => {
    if (newTask) {
      resetForm()
      commentsLoading.value = true
      await commentsStore.fetchComments(newTask.id)
      commentsLoading.value = false
    } else {
      commentsStore.clearComments()
    }
  },
  { immediate: true }
)

// Workday helpers (weekends only, no holidays)
const addWorkdays = (date, n) => {
  const result = new Date(date)
  let remaining = Math.round(n)
  while (remaining > 0) {
    result.setDate(result.getDate() + 1)
    if (result.getDay() !== 0 && result.getDay() !== 6) remaining--
  }
  return result
}

const countWorkdays = (start, end) => {
  const d = new Date(start)
  const endDate = new Date(end)
  d.setHours(0, 0, 0, 0)
  endDate.setHours(0, 0, 0, 0)
  let count = 0
  while (d <= endDate) {
    if (d.getDay() !== 0 && d.getDay() !== 6) count++
    d.setDate(d.getDate() + 1)
  }
  return count
}

const isInternal = computed(() => props.task?.resource_category === 'Internal')
const isExternal = computed(() => props.task?.resource_category === 'External')

// Prevent the start_date watcher from triggering the end_date watcher
let suppressEndDateWatch = false

watch(() => editForm.start_date, async (newVal, oldVal) => {
  if (!isEditing.value || !newVal) return

  if (isInternal.value) {
    const effort = props.task?.effort ?? 1
    let durationDays
    if (effort < 1) {
      durationDays = Math.round(editForm.total / effort) - 1
    } else {
      durationDays = Math.round(editForm.total) - 1
    }
    if (durationDays < 0) return
    suppressEndDateWatch = true
    editForm.end_date = addWorkdays(newVal, durationDays)
    await nextTick()
    suppressEndDateWatch = false
  } else if (isExternal.value && oldVal && editForm.end_date) {
    const workdays = countWorkdays(oldVal, editForm.end_date)
    suppressEndDateWatch = true
    editForm.end_date = addWorkdays(newVal, workdays - 1)
    await nextTick()
    suppressEndDateWatch = false
  }
})

watch(() => editForm.end_date, (newVal) => {
  if (suppressEndDateWatch || !isEditing.value || !newVal || !editForm.start_date) return
  if (!isInternal.value) return
  const workdays = countWorkdays(editForm.start_date, newVal)
  const effort = props.task?.effort ?? 1
  editForm.total = effort < 1 ? workdays * effort : workdays
})

const resetForm = () => {
  if (props.task) {
    editForm.start_date = props.task.start_date ? new Date(props.task.start_date) : null
    editForm.end_date = props.task.end_date ? new Date(props.task.end_date) : null
    editForm.completion_pct = props.task.completion_pct || 0
    editForm.resource_name = props.task.resource_name || ''
    editForm.total = props.task.total ?? 0
  }
  isEditing.value = false
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const startEditing = () => {
  resetForm()
  isEditing.value = true
}

const cancelEditing = () => {
  resetForm()
}

const saveChanges = async () => {
  saving.value = true

  const updateData = {
    start_date: editForm.start_date ? formatDateForAPI(editForm.start_date) : null,
    end_date: editForm.end_date ? formatDateForAPI(editForm.end_date) : null,
    completion_pct: editForm.completion_pct,
  }

  if (canEditAllFields.value) {
    updateData.resource_name = editForm.resource_name
    if (isInternal.value) {
      updateData.total = editForm.total
    }
  }

  const result = await tasksStore.updateTask(props.task.id, updateData)

  saving.value = false

  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Task updated successfully',
      life: 3000,
    })
    isEditing.value = false
    emit('updated')
  } else {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: result.error,
      life: 5000,
    })
  }
}

const formatDateForAPI = (date) => {
  if (!date) return null
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const confirmDelete = () => {
  showDeleteDialog.value = true
}

const executeDelete = async () => {
  deleting.value = true
  const result = await tasksStore.deleteTask(props.task.id)
  deleting.value = false
  showDeleteDialog.value = false

  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Deleted',
      detail: 'Task deleted successfully',
      life: 3000,
    })
    emit('update:visible', false)
    emit('deleted')
  } else {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: result.error || 'Failed to delete task',
      life: 5000,
    })
  }
}

const addComment = async () => {
  if (!newComment.value.trim()) return

  addingComment.value = true

  const result = await commentsStore.addComment(props.task.id, newComment.value)

  addingComment.value = false

  if (result.success) {
    newComment.value = ''
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Comment added',
      life: 2000,
    })
  } else {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: result.error,
      life: 5000,
    })
  }
}
</script>

<style scoped>
.panel-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-title .wp-id {
  background: var(--primary-color);
  color: white;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.panel-body {
  padding: 20px;
}

.task-fields {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.field-value {
  color: var(--text-color);
  font-size: 14px;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--surface-border);
}

.comments-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
}

.comment-count {
  color: var(--text-secondary);
  font-weight: normal;
}

.comments-list {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.loading-container.small {
  min-height: 60px;
}

.no-comments {
  text-align: center;
  padding: 24px;
  color: var(--text-secondary);
}

.no-comments i {
  font-size: 24px;
  margin-bottom: 8px;
}

.no-comments p {
  margin: 0;
}

.add-comment {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.add-comment .p-button {
  align-self: flex-end;
}

.w-full {
  width: 100%;
}
</style>