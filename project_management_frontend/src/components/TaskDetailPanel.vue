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
            <div class="field-value">{{ isEditing && isInternalPartTime ? editForm.qty : (task.qty ?? '-') }}</div>
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
            label="Precedence"
            icon="pi pi-sitemap"
            severity="secondary"
            outlined
            @click="openPrecedenceDialog"
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

      <!-- Precedence Dialog -->
      <Dialog
        v-model:visible="showPrecedenceDialog"
        modal
        :style="{ width: '960px' }"
        :closable="true"
        @hide="onPrecedenceDialogHide"
      >
        <template #header>
          <div class="prec-dialog-header">
            <span class="prec-dialog-title">Predecessors</span>
            <div class="prec-dialog-meta">
              <span class="prec-meta-item">
                <span class="prec-meta-label">WP-ID</span>
                <span class="prec-meta-value">{{ task?.wp_id || '-' }}</span>
              </span>
              <span class="prec-meta-sep">|</span>
              <span class="prec-meta-item">
                <span class="prec-meta-label">Task</span>
                <span class="prec-meta-value" :title="task?.wp">{{ task?.wp || '-' }}</span>
              </span>
              <span class="prec-meta-sep">|</span>
              <span class="prec-meta-item">
                <span class="prec-meta-label">Resource Category</span>
                <span class="prec-meta-value">{{ task?.resource_category || '-' }}</span>
              </span>
              <span class="prec-meta-sep">|</span>
              <span class="prec-meta-item">
                <span class="prec-meta-label">Comment</span>
                <span class="prec-meta-value" :title="task?.comment">{{ task?.comment || '-' }}</span>
              </span>
            </div>
          </div>
        </template>
        <div class="precedence-dialog-body">
          <!-- Type selector -->
          <div class="prec-type-row">
            <label class="prec-label">Precedence Type</label>
            <Dropdown
              v-model="precedenceType"
              :options="precedenceTypeOptions"
              optionLabel="label"
              optionValue="value"
              style="width: 220px"
              @change="onPrecedenceTypeChange"
            />
          </div>

          <!-- Existing predecessors -->
          <div class="prec-existing-section">
            <div class="prec-section-title">Existing Predecessors</div>
            <div v-if="precedencesStore.loading" class="prec-loading">
              <ProgressSpinner style="width: 24px; height: 24px" />
            </div>
            <div v-else-if="precedencesStore.taskPrecedences.length === 0" class="prec-empty">
              No predecessors configured yet.
            </div>
            <div v-else class="prec-chips">
              <span
                v-for="p in precedencesStore.taskPrecedences"
                :key="p.id"
                class="prec-chip"
              >
                <span class="prec-chip-id">{{ p.predecessor_wp_id || `#${p.predecessor_task_id}` }}</span>
                <span :class="['prec-chip-type', p.precedence_type === 'FS' ? 'type-fs' : 'type-ss']">
                  {{ p.precedence_type === 'FS' ? 'Finish to Start' : 'Start to Start' }}
                </span>
                <button
                  class="prec-chip-remove"
                  :disabled="precedencesStore.loading"
                  @click="removeExistingPrecedence(p)"
                  title="Remove"
                >×</button>
              </span>
            </div>
          </div>

          <!-- Candidate task list -->
          <div class="prec-candidates-section">
            <div class="prec-section-title">
              Available Tasks
              <span class="prec-candidate-hint">
                {{ precedenceType === 'FS' ? '(end date ≤ current task start date)' : '(same start date as current task)' }}
              </span>
            </div>

            <div v-if="candidateTasks.length === 0" class="prec-empty">
              No tasks match this precedence type for the current task's dates.
            </div>

            <div v-else class="prec-table-wrapper">
              <table class="prec-table">
                <thead>
                  <tr>
                    <th class="col-check"></th>
                    <th class="col-site">Site</th>
                    <th class="col-task">Task</th>
                    <th class="col-rc">Resource Category</th>
                    <th class="col-date">Start Date</th>
                    <th class="col-date">End Date</th>
                    <th class="col-role">Role</th>
                    <th class="col-comment">Comment</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="t in candidateTasks"
                    :key="t.id"
                    :class="{ selected: isPredecessorSelected(t.id) }"
                    @click="togglePredecessor(t.id)"
                  >
                    <td class="col-check">
                      <input
                        type="checkbox"
                        :checked="isPredecessorSelected(t.id)"
                        @click.stop
                        @change="togglePredecessor(t.id)"
                      />
                    </td>
                    <td class="col-site">{{ t.site || '-' }}</td>
                    <td class="col-task" :title="t.wp">{{ t.wp || '-' }}</td>
                    <td class="col-rc">{{ t.resource_category || '-' }}</td>
                    <td class="col-date">{{ t.start_date || '-' }}</td>
                    <td class="col-date">{{ t.end_date || '-' }}</td>
                    <td class="col-role">{{ t.role || '-' }}</td>
                    <td class="col-comment" :title="t.comment">{{ t.comment || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="prec-footer">
            <span v-if="selectedPredecessorIds.length > 0" class="prec-selection-count">
              {{ selectedPredecessorIds.length }} task(s) selected
            </span>
            <Button label="Cancel" severity="secondary" @click="showPrecedenceDialog = false" />
            <Button
              label="Add Selected"
              icon="pi pi-plus"
              :loading="precedenceSaving"
              :disabled="selectedPredecessorIds.length === 0"
              @click="addSelectedPrecedences"
            />
          </div>
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
import { usePrecedencesStore } from '@/stores/precedences'
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
const precedencesStore = usePrecedencesStore()
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

// Precedence dialog state
const showPrecedenceDialog = ref(false)
const precedenceType = ref('FS')
const selectedPredecessorIds = ref([])
const precedenceSaving = ref(false)

const precedenceTypeOptions = [
  { label: 'Finish to Start', value: 'FS' },
  { label: 'Start to Start', value: 'SS' },
]

const editForm = reactive({
  start_date: null,
  end_date: null,
  completion_pct: 0,
  resource_name: '',
  total: 0,
  qty: 0,
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

// Precedence: IDs of tasks already set as predecessors (any type)
const existingPredecessorIds = computed(() =>
  new Set(precedencesStore.taskPrecedences.map(p => p.predecessor_task_id))
)

// Candidate tasks filtered by precedence type, excluding current task and existing predecessors
const candidateTasks = computed(() => {
  if (!props.task) return []
  const currentId = props.task.id
  const currentStart = props.task.start_date   // "YYYY-MM-DD"
  const currentEnd = props.task.end_date

  return tasksStore.tasks.filter(t => {
    if (t.id === currentId) return false
    if (existingPredecessorIds.value.has(t.id)) return false
    if (precedenceType.value === 'FS') {
      // Predecessor must finish on or before current task's start date
      return t.end_date && currentStart && t.end_date <= currentStart
    } else {
      // SS: same start date
      return t.start_date && currentStart && t.start_date === currentStart
    }
  })
})

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
      precedencesStore.clearTaskPrecedences()
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
const isInternalPartTime = computed(() => isInternal.value && (props.task?.effort ?? 1) < 1)

// Prevent the start_date watcher from triggering the end_date watcher
let suppressEndDateWatch = false

watch(() => editForm.start_date, async (newVal, oldVal) => {
  if (!isEditing.value || !newVal) return

  if (isInternal.value) {
    const effort = props.task?.effort ?? 1
    if (effort < 1) {
      // Preserve the workday span — same logic as External
      if (!oldVal || !editForm.end_date) return
      const workdays = countWorkdays(oldVal, editForm.end_date)
      suppressEndDateWatch = true
      editForm.end_date = addWorkdays(newVal, workdays - 1)
      await nextTick()
      suppressEndDateWatch = false
    } else {
      // Derive end_date from total effort
      const durationDays = Math.round(editForm.total) - 1
      if (durationDays < 0) return
      suppressEndDateWatch = true
      editForm.end_date = addWorkdays(newVal, durationDays)
      await nextTick()
      suppressEndDateWatch = false
    }
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
  if (effort < 1) {
    editForm.qty = workdays
    editForm.total = workdays * effort
  } else {
    editForm.total = workdays
  }
})

const resetForm = () => {
  if (props.task) {
    editForm.start_date = props.task.start_date ? new Date(props.task.start_date) : null
    editForm.end_date = props.task.end_date ? new Date(props.task.end_date) : null
    editForm.completion_pct = props.task.completion_pct || 0
    editForm.resource_name = props.task.resource_name || ''
    editForm.total = props.task.total ?? 0
    editForm.qty = props.task.qty ?? 0
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
      if (isInternalPartTime.value) {
        updateData.qty = editForm.qty
      }
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

// ── Precedence dialog ────────────────────────────────────────────────────────

const openPrecedenceDialog = async () => {
  precedenceType.value = 'FS'
  selectedPredecessorIds.value = []
  showPrecedenceDialog.value = true
  await precedencesStore.fetchTaskPrecedences(props.task.id)
}

const onPrecedenceDialogHide = () => {
  selectedPredecessorIds.value = []
}

const onPrecedenceTypeChange = () => {
  // Reset selection when the candidate list changes
  selectedPredecessorIds.value = []
}

const isPredecessorSelected = (id) => selectedPredecessorIds.value.includes(id)

const togglePredecessor = (id) => {
  const idx = selectedPredecessorIds.value.indexOf(id)
  if (idx === -1) {
    selectedPredecessorIds.value.push(id)
  } else {
    selectedPredecessorIds.value.splice(idx, 1)
  }
}

const addSelectedPrecedences = async () => {
  if (selectedPredecessorIds.value.length === 0) return

  precedenceSaving.value = true
  const items = selectedPredecessorIds.value.map(id => ({
    predecessor_task_id: id,
    precedence_type: precedenceType.value,
  }))

  const result = await precedencesStore.addPrecedences(
    props.task.id,
    items,
    props.task.project_id,
  )

  precedenceSaving.value = false

  if (result.success) {
    selectedPredecessorIds.value = []
    toast.add({ severity: 'success', summary: 'Success', detail: 'Predecessor(s) added', life: 3000 })
  } else {
    toast.add({ severity: 'error', summary: 'Error', detail: result.error, life: 5000 })
  }
}

const removeExistingPrecedence = async (precedence) => {
  const result = await precedencesStore.removePrecedence(
    props.task.id,
    precedence.id,
    props.task.project_id,
  )
  if (!result.success) {
    toast.add({ severity: 'error', summary: 'Error', detail: result.error, life: 5000 })
  }
}

// ── Comments ─────────────────────────────────────────────────────────────────

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

/* ── Precedence dialog ─────────────────────────────────────────────────────── */

.prec-dialog-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.prec-dialog-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-color);
}

.prec-dialog-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 12px;
}

.prec-meta-sep {
  color: var(--surface-border);
  user-select: none;
}

.prec-meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.prec-meta-label {
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-size: 10px;
  letter-spacing: 0.03em;
}

.prec-meta-value {
  color: var(--text-color);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.precedence-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.prec-type-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.prec-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  white-space: nowrap;
}

.prec-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.prec-candidate-hint {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-secondary);
  text-transform: none;
}

.prec-existing-section,
.prec-candidates-section {
  border-top: 1px solid var(--surface-border);
  padding-top: 16px;
}

.prec-loading {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.prec-empty {
  color: var(--text-secondary);
  font-size: 13px;
  padding: 4px 0;
}

/* Predecessor chips */
.prec-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.prec-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--surface-100);
  border: 1px solid var(--surface-border);
  border-radius: 20px;
  padding: 4px 10px;
  font-size: 13px;
}

.prec-chip-id {
  font-weight: 600;
  color: var(--text-color);
}

.prec-chip-type {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.type-fs {
  background: #dbeafe;
  color: #1d4ed8;
}

.type-ss {
  background: #d1fae5;
  color: #065f46;
}

.prec-chip-remove {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1;
  padding: 0 2px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.prec-chip-remove:hover:not(:disabled) {
  background: var(--surface-200);
  color: var(--text-color);
}

.prec-chip-remove:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Candidate task table */
.prec-table-wrapper {
  max-height: 320px;
  overflow-y: auto;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
}

.prec-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.prec-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--surface-100);
}

.prec-table th {
  padding: 8px 10px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  border-bottom: 1px solid var(--surface-border);
  white-space: nowrap;
}

.prec-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--surface-50);
  color: var(--text-color);
  vertical-align: middle;
}

.prec-table tbody tr {
  cursor: pointer;
  transition: background 0.1s;
}

.prec-table tbody tr:hover {
  background: var(--surface-50);
}

.prec-table tbody tr.selected {
  background: #eff6ff;
}

.prec-table tbody tr:last-child td {
  border-bottom: none;
}

/* Column widths */
.col-check  { width: 36px; text-align: center; }
.col-site   { width: 80px; }
.col-task   { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.col-rc     { width: 130px; }
.col-date   { width: 100px; white-space: nowrap; }
.col-role   { width: 100px; }
.col-comment { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Dialog footer */
.prec-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
  width: 100%;
}

.prec-selection-count {
  margin-right: auto;
  font-size: 13px;
  color: var(--primary-color);
  font-weight: 600;
}

/* ── Comments ─────────────────────────────────────────────────────────────── */

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
