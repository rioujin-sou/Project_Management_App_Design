<template>
  <div class="kanban-view">
    <div class="page-header">
      <div>
        <h2>{{ project?.name || 'Kanban Board' }}</h2>
        <p v-if="project" class="project-meta">
          <span>Opp ID: {{ project.opp_id }}</span>
          <span class="separator">•</span>
          <span>Version: {{ project.version }}</span>
          <span class="separator">•</span>
          <span>Created: {{ formatDate(project.created_at) }}</span>
        </p>
      </div>
      <div class="btn-group">
        <Button
          icon="pi pi-arrow-left"
          label="Back to Project"
          severity="secondary"
          text
          @click="router.push(`/projects/${projectId}`)"
        />
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <ProgressSpinner />
    </div>

    <template v-else>
      <!-- Site Tabs -->
      <TabView v-model:activeIndex="activeTabIndex" class="site-tabs">
        <TabPanel v-for="site in sites" :key="site" :header="site || 'Unassigned'">
          <div class="kanban-board">
            <!-- To Do Column -->
            <div class="kanban-column">
              <div class="kanban-column-header todo">
                <span>To Do</span>
                <span class="task-count-badge">{{ getTasksByStatus(site, 'todo').length }}</span>
              </div>
              <draggable
                :list="getTasksByStatus(site, 'todo')"
                group="tasks"
                item-key="id"
                class="kanban-tasks"
                @add="(e) => onDragAdd(e, site, 'todo')"
              >
                <template #item="{ element }">
                  <div class="kanban-task-card" @click="openTaskDetail(element)">
                    <div class="task-wp-id">{{ element.wp_id }}</div>
                    <div class="task-name">{{ element.wp }}</div>
                    <div class="task-product">{{ element.product }}</div>
                    <div v-if="element.comment" class="task-comment">
                      <i class="pi pi-comment"></i>
                      {{ element.comment }}
                    </div>
                    <div class="task-resource">
                      <i class="pi pi-user"></i>
                      {{ element.resource_name || 'Unassigned' }}
                    </div>
                    <div class="task-dates">
                      <span>{{ formatDate(element.start_date, true) }}</span>
                      <span>{{ formatDate(element.end_date, true) }}</span>
                    </div>
                    <div class="task-completion">
                      <ProgressBar :value="element.completion_pct || 0" :showValue="false" />
                    </div>
                  </div>
                </template>
              </draggable>
            </div>

            <!-- In Progress Column -->
            <div class="kanban-column">
              <div class="kanban-column-header in-progress">
                <span>In Progress</span>
                <span class="task-count-badge">{{ getTasksByStatus(site, 'inProgress').length }}</span>
              </div>
              <draggable
                :list="getTasksByStatus(site, 'inProgress')"
                group="tasks"
                item-key="id"
                class="kanban-tasks"
                @add="(e) => onDragAdd(e, site, 'inProgress')"
              >
                <template #item="{ element }">
                  <div class="kanban-task-card" @click="openTaskDetail(element)">
                    <div class="task-wp-id">{{ element.wp_id }}</div>
                    <div class="task-name">{{ element.wp }}</div>
                    <div class="task-product">{{ element.product }}</div>
                    <div v-if="element.comment" class="task-comment">
                      <i class="pi pi-comment"></i>
                      {{ element.comment }}
                    </div>
                    <div class="task-resource">
                      <i class="pi pi-user"></i>
                      {{ element.resource_name || 'Unassigned' }}
                    </div>
                    <div class="task-dates">
                      <span>{{ formatDate(element.start_date, true) }}</span>
                      <span>{{ formatDate(element.end_date, true) }}</span>
                    </div>
                    <div class="task-completion">
                      <ProgressBar :value="element.completion_pct || 0" :showValue="false" />
                      <small>{{ element.completion_pct }}%</small>
                    </div>
                  </div>
                </template>
              </draggable>
            </div>

            <!-- Done Column -->
            <div class="kanban-column">
              <div class="kanban-column-header done">
                <span>Done</span>
                <span class="task-count-badge">{{ getTasksByStatus(site, 'done').length }}</span>
              </div>
              <draggable
                :list="getTasksByStatus(site, 'done')"
                group="tasks"
                item-key="id"
                class="kanban-tasks"
                @add="(e) => onDragAdd(e, site, 'done')"
              >
                <template #item="{ element }">
                  <div class="kanban-task-card" @click="openTaskDetail(element)">
                    <div class="task-wp-id">{{ element.wp_id }}</div>
                    <div class="task-name">{{ element.wp }}</div>
                    <div class="task-product">{{ element.product }}</div>
                    <div v-if="element.comment" class="task-comment">
                      <i class="pi pi-comment"></i>
                      {{ element.comment }}
                    </div>
                    <div class="task-resource">
                      <i class="pi pi-user"></i>
                      {{ element.resource_name || 'Unassigned' }}
                    </div>
                    <div class="task-dates">
                      <span>{{ formatDate(element.start_date, true) }}</span>
                      <span>{{ formatDate(element.end_date, true) }}</span>
                    </div>
                    <div class="task-completion">
                      <ProgressBar :value="100" :showValue="false" />
                      <small>100%</small>
                    </div>
                  </div>
                </template>
              </draggable>
            </div>
          </div>
        </TabPanel>
      </TabView>

      <!-- Empty state when no tasks -->
      <div v-if="tasksStore.tasks.length === 0" class="empty-state">
        <i class="pi pi-inbox"></i>
        <h3>No Tasks</h3>
        <p>This project has no tasks yet</p>
      </div>
    </template>

    <!-- Status Change Dialog -->
    <Dialog
      v-model:visible="showStatusDialog"
      :header="statusDialogTitle"
      :modal="true"
      :style="{ width: '440px' }"
    >
      <div class="status-dialog-content">
        <!-- Completion selector — only shown for In Progress -->
        <div v-if="pendingStatus === 'inProgress'" class="dialog-field">
          <label>Completion Percentage</label>
          <Dropdown
            v-model="selectedCompletion"
            :options="completionOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select completion %"
            class="w-full"
          />
        </div>

        <!-- Auto-completion info for To Do / Done -->
        <div v-else class="dialog-info">
          <i class="pi pi-info-circle"></i>
          <span>Completion will be set to <strong>{{ pendingStatus === 'done' ? '100%' : '0%' }}</strong> automatically.</span>
        </div>

        <!-- Comment field — always shown -->
        <div class="dialog-field">
          <label>Add a Comment <span class="optional">(optional)</span></label>
          <Textarea
            v-model="statusComment"
            placeholder="Write a comment about this status change..."
            :autoResize="true"
            rows="3"
            class="w-full"
          />
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="cancelStatusDialog" />
        <Button
          label="Confirm"
          icon="pi pi-check"
          :loading="submittingStatus"
          @click="confirmStatusChange"
        />
      </template>
    </Dialog>

    <!-- Task Detail Sidebar -->
    <TaskDetailPanel
      v-model:visible="showTaskPanel"
      :task="selectedTask"
      @updated="handleTaskUpdated"
      @deleted="handleTaskDeleted"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { useCommentsStore } from '@/stores/comments'
import { useToast } from 'primevue/usetoast'
import draggable from 'vuedraggable'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'
import ProgressSpinner from 'primevue/progressspinner'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import TaskDetailPanel from '@/components/TaskDetailPanel.vue'

const route = useRoute()
const router = useRouter()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()
const commentsStore = useCommentsStore()

const project = computed(() => projectsStore.currentProject)
const toast = useToast()

const projectId = computed(() => route.params.id)
const loading = ref(true)
const activeTabIndex = ref(0)
const showTaskPanel = ref(false)
const selectedTask = ref(null)

// Status change dialog
const showStatusDialog = ref(false)
const pendingTask = ref(null)
const pendingStatus = ref(null)
const selectedCompletion = ref(50)
const statusComment = ref('')
const submittingStatus = ref(false)

const statusDialogTitle = computed(() => {
  switch (pendingStatus.value) {
    case 'todo': return 'Move to To Do'
    case 'inProgress': return 'Move to In Progress'
    case 'done': return 'Move to Done'
    default: return 'Update Status'
  }
})

const completionOptions = [
  { label: '10%', value: 10 },
  { label: '20%', value: 20 },
  { label: '30%', value: 30 },
  { label: '40%', value: 40 },
  { label: '50%', value: 50 },
  { label: '60%', value: 60 },
  { label: '70%', value: 70 },
  { label: '80%', value: 80 },
  { label: '90%', value: 90 },
]

const sites = computed(() => {
  return tasksStore.uniqueSites.length > 0 ? tasksStore.uniqueSites : ['All']
})

onMounted(async () => {
  // Fetch project only if not already cached for this ID (fire-and-forget — no await)
  const currentId = Number(projectId.value)
  if (!projectsStore.currentProject || projectsStore.currentProject.id !== currentId) {
    projectsStore.fetchProjectById(projectId.value)
  }
  await tasksStore.fetchTasks(projectId.value)
  loading.value = false
})

const getTasksByStatus = (site, status) => {
  const siteTasks = site === 'All'
    ? tasksStore.tasks
    : tasksStore.tasks.filter(t => t.site === site)

  switch (status) {
    case 'todo':
      return siteTasks.filter(t => !t.completion_pct || t.completion_pct === 0)
    case 'inProgress':
      return siteTasks.filter(t => t.completion_pct > 0 && t.completion_pct < 100)
    case 'done':
      return siteTasks.filter(t => t.completion_pct === 100)
    default:
      return []
  }
}

const formatDate = (dateString, short = false) => {
  if (!dateString) return '-'
  if (short) {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const onDragAdd = async (event, site, targetStatus) => {
  const taskElement = event.item.__draggable_context?.element
  if (!taskElement) return

  // Immediately reset vuedraggable's local mutation — real update happens on confirm
  await tasksStore.fetchTasks(projectId.value)

  pendingTask.value = taskElement
  pendingStatus.value = targetStatus
  statusComment.value = ''
  selectedCompletion.value = taskElement.completion_pct > 0 && taskElement.completion_pct < 100
    ? taskElement.completion_pct
    : 50
  showStatusDialog.value = true
}

const confirmStatusChange = async () => {
  if (!pendingTask.value) return
  submittingStatus.value = true

  let newCompletion
  switch (pendingStatus.value) {
    case 'todo': newCompletion = 0; break
    case 'inProgress': newCompletion = selectedCompletion.value; break
    case 'done': newCompletion = 100; break
  }

  await updateTaskCompletion(pendingTask.value.id, newCompletion)

  if (statusComment.value.trim()) {
    await commentsStore.addComment(pendingTask.value.id, statusComment.value.trim())
  }

  submittingStatus.value = false
  showStatusDialog.value = false
  pendingTask.value = null
  pendingStatus.value = null
  statusComment.value = ''
}

const cancelStatusDialog = () => {
  showStatusDialog.value = false
  pendingTask.value = null
  pendingStatus.value = null
  statusComment.value = ''
}

const updateTaskCompletion = async (taskId, completion) => {
  const result = await tasksStore.updateTaskCompletion(taskId, completion)
  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Updated',
      detail: `Task completion updated to ${completion}%`,
      life: 2000,
    })
  } else {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: result.error,
      life: 5000,
    })
    await tasksStore.fetchTasks(projectId.value)
  }
}

const openTaskDetail = (task) => {
  selectedTask.value = task
  showTaskPanel.value = true
}

const handleTaskUpdated = async () => {
  await tasksStore.fetchTasks(projectId.value)
  if (selectedTask.value) {
    const refreshed = tasksStore.tasks.find(t => t.id === selectedTask.value.id)
    if (refreshed) selectedTask.value = refreshed
  }
}

const handleTaskDeleted = async () => {
  showTaskPanel.value = false
  selectedTask.value = null
  await tasksStore.fetchTasks(projectId.value)
}
</script>

<style scoped>
.project-meta {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 4px;
}

.separator {
  margin: 0 8px;
}

.task-count-badge {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.task-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 2px;
  line-height: 1.3;
}

.task-comment {
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: flex-start;
  gap: 5px;
  line-height: 1.3;
}

.task-comment i {
  font-size: 11px;
  margin-top: 2px;
  flex-shrink: 0;
}

.completion-dialog-content {
  padding: 16px 0;
}

.completion-dialog-content p {
  margin-bottom: 16px;
  color: var(--text-color);
}

.status-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0;
}

.dialog-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dialog-field label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.optional {
  font-weight: normal;
  text-transform: none;
  font-size: 12px;
}

.dialog-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--surface-ground);
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-color);
}

.dialog-info i {
  color: var(--primary-color);
  font-size: 16px;
  flex-shrink: 0;
}

.w-full {
  width: 100%;
}

:deep(.p-tabview-panels) {
  padding: 0;
}
</style>