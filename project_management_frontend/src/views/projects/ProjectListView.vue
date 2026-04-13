<template>
  <div class="project-list-view">
    <div class="page-header">
      <h1>Projects</h1>
      <Button
        v-if="authStore.isTDL"
        icon="pi pi-upload"
        label="Upload Excel"
        @click="showUploadDialog = true"
      />
    </div>

    <div class="card data-table-container">
      <DataTable
        :value="projectsStore.projects"
        :loading="projectsStore.loading"
        :paginator="true"
        :rows="10"
        :rowsPerPageOptions="[10, 25, 50]"
        dataKey="id"
        stripedRows
        sortField="created_at"
        :sortOrder="-1"
        emptyMessage="No projects found"
      >
        <Column field="opp_id" header="Opp ID" sortable style="width: 15%" />
        <Column field="name" header="Project Name" sortable style="width: 30%" />
        <Column field="version" header="Version" sortable style="width: 10%" />
        <Column header="Created" sortable sortField="created_at" style="width: 20%">
          <template #body="{ data }">
            {{ formatDate(data.created_at) }}
          </template>
        </Column>
        <Column header="Tasks" style="width: 10%">
          <template #body="{ data }">
            <span class="task-count">{{ data.task_count || 0 }}</span>
          </template>
        </Column>
        <Column header="Actions" style="width: 15%">
          <template #body="{ data }">
            <div class="btn-group">
              <Button
                icon="pi pi-eye"
                severity="info"
                text
                rounded
                @click.stop="viewProject(data)"
                v-tooltip.top="'View'"
              />
              <Button
                icon="pi pi-th-large"
                severity="secondary"
                text
                rounded
                @click.stop="goToKanban(data)"
                v-tooltip.top="'Kanban'"
              />
              <Button
                icon="pi pi-chart-bar"
                severity="secondary"
                text
                rounded
                @click.stop="goToGantt(data)"
                v-tooltip.top="'Gantt'"
              />
              <Button
                v-if="authStore.isTDL"
                icon="pi pi-users"
                severity="secondary"
                text
                rounded
                @click.stop="openVisibilityDialog(data)"
                v-tooltip.top="'Project Visibility'"
              />
              <span v-if="authStore.isTDL" @click.stop.prevent="confirmDelete(data)">
                <Button
                  icon="pi pi-trash"
                  severity="danger"
                  text
                  rounded
                  v-tooltip.top="'Delete'"
                />
              </span>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Empty state -->
    <div v-if="!projectsStore.loading && projectsStore.projects.length === 0" class="empty-state">
      <i class="pi pi-folder-open"></i>
      <h3>No Projects Yet</h3>
      <p v-if="authStore.isTDL">Upload an Excel file to create your first project</p>
      <p v-else>No projects are available at this time</p>
    </div>

    <!-- Upload Dialog -->
    <Dialog
      v-model:visible="showUploadDialog"
      header="Upload Excel File"
      :modal="true"
      :style="{ width: '500px' }"
    >
      <div class="upload-content">
        <FileUpload
          ref="fileUploadRef"
          mode="advanced"
          name="file"
          accept=".xlsx,.xls"
          :maxFileSize="10000000"
          :auto="false"
          :customUpload="true"
          @uploader="handleUpload"
          @select="onFileSelect"
          @clear="onFileClear"
        >
          <template #empty>
            <div class="upload-empty">
              <i class="pi pi-cloud-upload"></i>
              <p>Drag and drop Excel file here or click to browse</p>
              <small>Supported formats: .xlsx, .xls (Max 10MB)</small>
            </div>
          </template>
        </FileUpload>

        <Message v-if="uploadError" severity="error" :closable="false" class="mt-3">
          {{ uploadError }}
        </Message>

        <ProgressBar 
          v-if="uploading" 
          :value="projectsStore.uploadProgress" 
          class="mt-3"
        />
      </div>
    </Dialog>

    <!-- Visibility Dialog -->
    <Dialog
      v-model:visible="showVisibilityDialog"
      header="Project Visibility"
      :modal="true"
      :style="{ width: '480px' }"
    >
      <div v-if="visibilityProject" class="visibility-content">
        <p class="visibility-description">
          Select which users can see and access <strong>{{ visibilityProject.name }}</strong>.
          TDL users always have access.
        </p>
        <div class="visibility-user-list">
          <div
            v-for="user in nonTdlUsers"
            :key="user.id"
            class="visibility-user-item"
          >
            <Checkbox
              v-model="selectedUserIds"
              :value="user.id"
              :inputId="`vis-user-${user.id}`"
            />
            <label :for="`vis-user-${user.id}`" class="visibility-user-label">
              <span class="visibility-user-email">{{ user.email }}</span>
              <span class="status-badge" :class="user.role">{{ user.role.toUpperCase() }}</span>
            </label>
          </div>
          <div v-if="nonTdlUsers.length === 0" class="no-users">
            No non-TDL users found.
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="showVisibilityDialog = false" />
        <Button label="Save" icon="pi pi-check" :loading="savingVisibility" @click="saveVisibility" />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog
      v-model:visible="showDeleteDialog"
      header="Delete Confirmation"
      :modal="true"
      :style="{ width: '400px' }"
      :closable="!deleting"
    >
      <div style="display: flex; align-items: center; gap: 12px;">
        <i class="pi pi-exclamation-triangle" style="font-size: 24px; color: var(--red-500);" />
        <span>Are you sure you want to delete project <strong>{{ projectToDelete?.name }}</strong>? This action cannot be undone.</span>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text :disabled="deleting" @click="showDeleteDialog = false" />
        <Button label="Delete" severity="danger" icon="pi pi-trash" :loading="deleting" @click="executeDelete" />
      </template>
    </Dialog>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectsStore } from '@/stores/projects'
import { useUsersStore } from '@/stores/users'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Dialog from 'primevue/dialog'
import FileUpload from 'primevue/fileupload'
import Message from 'primevue/message'
import ProgressBar from 'primevue/progressbar'
import Tooltip from 'primevue/tooltip'

const vTooltip = Tooltip

const router = useRouter()
const authStore = useAuthStore()
const projectsStore = useProjectsStore()
const usersStore = useUsersStore()
const toast = useToast()

const showDeleteDialog = ref(false)
const projectToDelete = ref(null)
const deleting = ref(false)

const showUploadDialog = ref(false)
const fileUploadRef = ref(null)
const selectedFile = ref(null)
const uploadError = ref('')
const uploading = ref(false)

// Visibility dialog state
const showVisibilityDialog = ref(false)
const visibilityProject = ref(null)
const selectedUserIds = ref([])
const savingVisibility = ref(false)

const nonTdlUsers = computed(() =>
  usersStore.users.filter(u => u.role !== 'tdl' && u.role !== 'pending')
)

onMounted(async () => {
  await projectsStore.fetchProjects()
})

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const viewProject = (project) => {
  router.push(`/projects/${project.id}`)
}

const goToKanban = (project) => {
  router.push(`/projects/${project.id}/kanban`)
}

const goToGantt = (project) => {
  router.push(`/projects/${project.id}/gantt`)
}

const onFileSelect = (event) => {
  selectedFile.value = event.files[0]
  uploadError.value = ''
}

const onFileClear = () => {
  selectedFile.value = null
  uploadError.value = ''
}

const handleUpload = async (event) => {
  const file = event.files[0]
  if (!file) return

  uploading.value = true
  uploadError.value = ''

  const result = await projectsStore.uploadExcel(file)

  uploading.value = false

  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Project uploaded successfully',
      life: 3000,
    })
    showUploadDialog.value = false
    fileUploadRef.value?.clear()
  } else {
    uploadError.value = result.error
  }
}

const openVisibilityDialog = async (project) => {
  visibilityProject.value = project
  await usersStore.fetchUsers()
  selectedUserIds.value = project.visible_user_ids
    ? [...project.visible_user_ids]
    : []
  showVisibilityDialog.value = true
}

const saveVisibility = async () => {
  if (!visibilityProject.value) return
  savingVisibility.value = true
  const result = await projectsStore.updateVisibility(
    visibilityProject.value.id,
    selectedUserIds.value
  )
  savingVisibility.value = false
  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Saved',
      detail: 'Project visibility updated',
      life: 3000,
    })
    showVisibilityDialog.value = false
  } else {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: result.error,
      life: 5000,
    })
  }
}

const confirmDelete = (project) => {
  if (showDeleteDialog.value || deleting.value) return
  projectToDelete.value = project
  showDeleteDialog.value = true
}

const executeDelete = async () => {
  if (!projectToDelete.value) return
  deleting.value = true
  const result = await projectsStore.deleteProject(projectToDelete.value.id)
  deleting.value = false
  showDeleteDialog.value = false
  projectToDelete.value = null
  if (result.success) {
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Project deleted successfully', life: 3000 })
  } else {
    toast.add({ severity: 'error', summary: 'Error', detail: result.error, life: 5000 })
  }
}
</script>

<style scoped>
.task-count {
  background: var(--surface-ground);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.visibility-content {
  padding: 8px 0;
}

.visibility-description {
  margin-bottom: 16px;
  color: var(--text-color);
  font-size: 14px;
}

.visibility-user-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 320px;
  overflow-y: auto;
}

.visibility-user-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.visibility-user-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex: 1;
}

.visibility-user-email {
  font-size: 14px;
  color: var(--text-color);
}

.no-users {
  color: var(--text-secondary);
  font-size: 14px;
  padding: 16px 0;
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