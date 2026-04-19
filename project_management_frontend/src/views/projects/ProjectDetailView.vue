<template>
  <div class="project-detail-view">
    <div v-if="projectsStore.loading" class="loading-container">
      <ProgressSpinner />
    </div>

    <template v-else-if="project">
      <div class="page-header">
        <div>
          <h1>{{ project.name }}</h1>
          <p class="project-meta">
            <span>Opp ID: {{ project.opp_id }}</span>
            <span class="separator">•</span>
            <span>Version: {{ project.version }}</span>
            <span class="separator">•</span>
            <span>Created: {{ formatDate(project.created_at) }}</span>
          </p>
        </div>
        <div class="btn-group">
          <Button
            icon="pi pi-download"
            label="Export Excel"
            severity="secondary"
            :loading="exporting"
            @click="handleExportExcel"
          />
          <Button
            v-if="authStore.isTDL"
            icon="pi pi-upload"
            label="Import Tasks"
            severity="secondary"
            @click="showImportDialog = true"
          />
          <Button
            v-if="authStore.isTDL"
            icon="pi pi-refresh"
            label="Update Baseline"
            severity="secondary"
            @click="handleUpdateBaseline"
          />
        </div>
      </div>

      <div class="quick-actions">
        <div class="action-card" @click="goToKanban">
          <i class="pi pi-th-large"></i>
          <h3>Kanban Board</h3>
          <p>Visualize tasks in columns</p>
        </div>
        <div class="action-card" @click="goToGantt">
          <i class="pi pi-chart-bar"></i>
          <h3>Gantt Chart</h3>
          <p>Timeline view of tasks</p>
        </div>
        <div class="action-card" @click="goToBaselineDiff">
          <i class="pi pi-sliders-h"></i>
          <h3>Baseline Diff</h3>
          <p>Compare with baseline</p>
        </div>
      </div>

      <div class="card">
        <h2>Project Tasks</h2>
        <DataTable
          :value="tasksStore.tasks"
          :loading="tasksStore.loading"
          :paginator="true"
          :rows="10"
          :rowsPerPageOptions="[10, 25, 50]"
          dataKey="id"
          stripedRows
          filterDisplay="menu"
          :globalFilterFields="['wp_id', 'product', 'resource_name', 'site']"
          emptyMessage="No tasks found"
        >
          <template #header>
            <div class="table-header">
              <IconField>
                <InputIcon class="pi pi-search" />
                <InputText v-model="globalFilter" placeholder="Search tasks..." />
              </IconField>
            </div>
          </template>
          <Column field="wp_id" header="WP-ID" sortable style="width: 10%" />
          <Column field="site" header="Site" sortable style="width: 10%" />
          <Column field="product" header="Product" sortable style="width: 15%" />
          <Column field="resource_name" header="Resource" sortable style="width: 15%" />
          <Column header="Duration" style="width: 15%">
            <template #body="{ data }">
              {{ formatDate(data.start_date, true) }} - {{ formatDate(data.end_date, true) }}
            </template>
          </Column>
          <Column header="Completion" style="width: 15%">
            <template #body="{ data }">
              <div class="completion-cell">
                <ProgressBar :value="data.completion_pct || 0" :showValue="false" style="height: 8px" />
                <span>{{ data.completion_pct || 0 }}%</span>
              </div>
            </template>
          </Column>
          <Column header="Actions" style="width: 10%">
            <template #body="{ data }">
              <Button
                icon="pi pi-eye"
                severity="info"
                text
                rounded
                @click="openTaskDetail(data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </template>

    <div v-else class="empty-state">
      <i class="pi pi-exclamation-circle"></i>
      <h3>Project Not Found</h3>
      <p>The project you're looking for doesn't exist</p>
      <Button label="Back to Projects" @click="router.push('/projects')" />
    </div>

    <!-- Import Tasks Dialog -->
    <Dialog
      v-model:visible="showImportDialog"
      header="Import Tasks from Excel"
      :modal="true"
      :style="{ width: '500px' }"
      @hide="onImportDialogHide"
    >
      <div class="upload-content">
        <FileUpload
          ref="importFileRef"
          mode="advanced"
          name="file"
          accept=".xlsx,.xls"
          :maxFileSize="10000000"
          :auto="false"
          :customUpload="true"
          @uploader="handleImport"
          @select="onImportFileSelect"
          @clear="onImportFileClear"
        >
          <template #empty>
            <div class="upload-empty">
              <i class="pi pi-cloud-upload"></i>
              <p>Drag and drop Excel file here or click to browse</p>
              <small>Supported formats: .xlsx, .xls (Max 10MB)</small>
            </div>
          </template>
        </FileUpload>
        <Message v-if="importError" severity="error" :closable="false" class="mt-3">
          {{ importError }}
        </Message>
      </div>
    </Dialog>

    <!-- Task Detail Sidebar -->
    <TaskDetailPanel
      v-model:visible="showTaskPanel"
      :task="selectedTask"
      @updated="handleTaskUpdated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { useToast } from 'primevue/usetoast'
import { projectsAPI } from '@/services/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import FileUpload from 'primevue/fileupload'
import Message from 'primevue/message'
import ProgressBar from 'primevue/progressbar'
import ProgressSpinner from 'primevue/progressspinner'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import TaskDetailPanel from '@/components/TaskDetailPanel.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()
const toast = useToast()

const globalFilter = ref('')
const showTaskPanel = ref(false)
const selectedTask = ref(null)
const exporting = ref(false)
const showImportDialog = ref(false)
const importFileRef = ref(null)
const importError = ref('')

const project = computed(() => projectsStore.currentProject)
const projectId = computed(() => route.params.id)

onMounted(async () => {
  await projectsStore.fetchProjectById(projectId.value)
  await tasksStore.fetchTasks(projectId.value)
})

const formatDate = (dateString, short = false) => {
  if (!dateString) return '-'
  const options = short
    ? { month: 'short', day: 'numeric' }
    : { year: 'numeric', month: 'short', day: 'numeric' }
  return new Date(dateString).toLocaleDateString('en-US', options)
}

const goToKanban = () => {
  router.push(`/projects/${projectId.value}/kanban`)
}

const goToGantt = () => {
  router.push(`/projects/${projectId.value}/gantt`)
}

const goToBaselineDiff = () => {
  router.push(`/projects/${projectId.value}/baseline-diff`)
}

const handleUpdateBaseline = async () => {
  const result = await projectsStore.updateBaseline(projectId.value)
  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Baseline updated successfully',
      life: 3000,
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

const openTaskDetail = (task) => {
  selectedTask.value = task
  showTaskPanel.value = true
}

const handleExportExcel = async () => {
  exporting.value = true
  try {
    const response = await projectsAPI.exportExcel(projectId.value)
    const url = URL.createObjectURL(new Blob([response.data]))
    const a = document.createElement('a')
    const p = project.value
    const date = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Tokyo' }).replace(/-/g, '')
    a.href = url
    a.download = `SCD PP DU APJ_${p.opp_id}_${p.name}_EE_v${p.version}_${date}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Export Failed',
      detail: error.response?.data?.detail || 'Failed to export Excel file',
      life: 5000,
    })
  } finally {
    exporting.value = false
  }
}

const onImportFileSelect = () => {
  importError.value = ''
}

const onImportFileClear = () => {
  importError.value = ''
}

const onImportDialogHide = () => {
  importError.value = ''
  importFileRef.value?.clear()
}

const handleImport = async (event) => {
  const file = event.files[0]
  if (!file) return

  importError.value = ''
  const result = await projectsStore.importTasks(projectId.value, file)

  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Tasks imported successfully',
      life: 3000,
    })
    showImportDialog.value = false
    importFileRef.value?.clear()
    await tasksStore.fetchTasks(projectId.value)
  } else {
    importError.value = result.error
  }
}

const handleTaskUpdated = async () => {
  await tasksStore.fetchTasks(projectId.value)
}
</script>

<style scoped>
.project-meta {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 8px;
}

.separator {
  margin: 0 8px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.action-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.action-card i {
  font-size: 32px;
  color: var(--primary-color);
  margin-bottom: 12px;
}

.action-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.action-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.table-header {
  display: flex;
  justify-content: flex-end;
}

.completion-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.completion-cell .p-progressbar {
  flex: 1;
}

.completion-cell span {
  font-size: 12px;
  min-width: 35px;
  text-align: right;
}

.upload-content {
  padding: 16px 0;
}

.upload-empty {
  text-align: center;
  padding: 40px 20px;
}

.upload-empty i {
  font-size: 48px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.upload-empty p {
  margin: 8px 0;
  color: var(--text-color);
}

.upload-empty small {
  color: var(--text-secondary);
}

.mt-3 {
  margin-top: 1rem;
}
</style>
