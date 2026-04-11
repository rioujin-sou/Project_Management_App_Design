<template>
  <div class="user-management-view">
    <div class="page-header">
      <h1>User Management</h1>
    </div>

    <!-- Pending Users Section -->
    <div v-if="pendingUsers.length > 0" class="card pending-users-section">
      <h2>
        <i class="pi pi-clock"></i>
        Pending Users
        <Tag :value="pendingUsers.length" severity="warning" class="ml-2" />
      </h2>
      <p class="section-description">
        These users have registered and are waiting for role assignment.
      </p>

      <DataTable
        :value="pendingUsers"
        dataKey="id"
        stripedRows
      >
        <Column field="email" header="Email" style="width: 40%" />
        <Column header="Registered" style="width: 20%">
          <template #body="{ data }">
            {{ formatDate(data.created_at) }}
          </template>
        </Column>
        <Column header="Assign Role" style="width: 25%">
          <template #body="{ data }">
            <Dropdown
              v-model="pendingRoles[data.id]"
              :options="roleOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select Role"
              style="width: 150px"
            />
          </template>
        </Column>
        <Column header="Action" style="width: 15%">
          <template #body="{ data }">
            <Button
              label="Assign"
              :disabled="!pendingRoles[data.id]"
              :loading="assigningRole === data.id"
              @click="assignRole(data.id)"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- All Users Section -->
    <div class="card">
      <h2>
        <i class="pi pi-users"></i>
        All Users
      </h2>

      <DataTable
        :value="usersStore.users"
        :loading="usersStore.loading"
        :paginator="usersStore.users.length > 10"
        :rows="10"
        :rowsPerPageOptions="[10, 25, 50]"
        dataKey="id"
        stripedRows
        sortField="created_at"
        :sortOrder="-1"
        emptyMessage="No users found"
      >
        <Column field="email" header="Email" sortable style="width: 40%" />
        <Column header="Role" sortable sortField="role" style="width: 15%">
          <template #body="{ data }">
            <span class="status-badge" :class="data.role">
              {{ data.role?.toUpperCase() }}
            </span>
          </template>
        </Column>
        <Column header="Registered" sortable sortField="created_at" style="width: 20%">
          <template #body="{ data }">
            {{ formatDate(data.created_at) }}
          </template>
        </Column>
        <Column header="Status" style="width: 10%">
          <template #body="{ data }">
            <Tag
              :value="data.is_active ? 'Active' : 'Inactive'"
              :severity="data.is_active ? 'success' : 'danger'"
            />
          </template>
        </Column>
        <Column header="Actions" style="width: 15%">
          <template #body="{ data }">
            <div v-if="data.role !== 'pending'" class="btn-group">
              <Button
                icon="pi pi-pencil"
                severity="secondary"
                text
                rounded
                @click="openEditDialog(data)"
                v-tooltip.top="'Change Role'"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                :disabled="data.id === authStore.user?.id"
                @click="confirmDeleteUser(data)"
                v-tooltip.top="data.id === authStore.user?.id ? 'Cannot delete your own account' : 'Delete User'"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Edit Role Dialog -->
    <Dialog
      v-model:visible="showEditDialog"
      header="Change User Role"
      :modal="true"
      :style="{ width: '400px' }"
    >
      <div v-if="selectedUser" class="edit-dialog-content">
        <div class="user-info-display">
          <i class="pi pi-user"></i>
          <span>{{ selectedUser.email }}</span>
        </div>

        <div class="form-group">
          <label>New Role</label>
          <Dropdown
            v-model="newRole"
            :options="roleOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Select Role"
            class="w-full"
          />
        </div>
      </div>

      <template #footer>
        <Button
          label="Cancel"
          severity="secondary"
          text
          @click="showEditDialog = false"
        />
        <Button
          label="Update Role"
          :loading="assigningRole === selectedUser?.id"
          :disabled="!newRole"
          @click="updateRole"
        />
      </template>
    </Dialog>

    <!-- Delete User Confirmation Dialog -->
    <Dialog
      v-model:visible="showDeleteDialog"
      header="Delete User"
      :modal="true"
      :style="{ width: '420px' }"
    >
      <div v-if="userToDelete" class="delete-dialog-content">
        <i class="pi pi-exclamation-triangle delete-warning-icon"></i>
        <p>Are you sure you want to delete user <strong>{{ userToDelete.email }}</strong>?</p>
        <p class="delete-warning-text">This action cannot be undone. All associated data will be permanently removed.</p>
      </div>
      <template #footer>
        <Button label="Cancel" severity="secondary" text @click="showDeleteDialog = false" />
        <Button
          label="Delete"
          severity="danger"
          icon="pi pi-trash"
          :loading="deletingUser"
          @click="executeDeleteUser"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUsersStore } from '@/stores/users'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import Tooltip from 'primevue/tooltip'

const vTooltip = Tooltip

const usersStore = useUsersStore()
const authStore = useAuthStore()
const toast = useToast()

const pendingRoles = reactive({})
const assigningRole = ref(null)
const showEditDialog = ref(false)
const selectedUser = ref(null)
const newRole = ref(null)
const showDeleteDialog = ref(false)
const userToDelete = ref(null)
const deletingUser = ref(false)

const roleOptions = [
  { label: 'TDL (Admin)', value: 'tdl' },
  { label: 'TPM (Project Manager)', value: 'tpm' },
  { label: 'PM (Project Manager)', value: 'pm' },
  { label: 'SA (Solution Architect)', value: 'sa' },
]

const pendingUsers = computed(() => usersStore.pendingUsers)

onMounted(async () => {
  await usersStore.fetchUsers()
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

const assignRole = async (userId) => {
  const role = pendingRoles[userId]
  if (!role) return

  assigningRole.value = userId

  const result = await usersStore.assignRole(userId, role)

  assigningRole.value = null

  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Role assigned successfully',
      life: 3000,
    })
    delete pendingRoles[userId]
  } else {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: result.error,
      life: 5000,
    })
  }
}

const confirmDeleteUser = (user) => {
  userToDelete.value = user
  showDeleteDialog.value = true
}

const executeDeleteUser = async () => {
  if (!userToDelete.value) return
  deletingUser.value = true
  const result = await usersStore.deleteUser(userToDelete.value.id)
  deletingUser.value = false
  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Deleted',
      detail: `User ${userToDelete.value.email} deleted successfully`,
      life: 3000,
    })
    showDeleteDialog.value = false
    userToDelete.value = null
  } else {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: result.error,
      life: 5000,
    })
  }
}

const openEditDialog = (user) => {
  selectedUser.value = user
  newRole.value = user.role
  showEditDialog.value = true
}

const updateRole = async () => {
  if (!selectedUser.value || !newRole.value) return

  assigningRole.value = selectedUser.value.id

  const result = await usersStore.assignRole(selectedUser.value.id, newRole.value)

  assigningRole.value = null

  if (result.success) {
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Role updated successfully',
      life: 3000,
    })
    showEditDialog.value = false
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
.pending-users-section {
  border-left: 4px solid var(--warning-color);
  margin-bottom: 24px;
}

.pending-users-section h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px;
  font-size: 18px;
}

.pending-users-section h2 i {
  color: var(--warning-color);
}

.section-description {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0 0 16px;
}

.card h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px;
  font-size: 18px;
}

.card h2 i {
  color: var(--primary-color);
}

.ml-2 {
  margin-left: 8px;
}

.edit-dialog-content {
  padding: 16px 0;
}

.user-info-display {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--surface-ground);
  border-radius: 8px;
  margin-bottom: 20px;
}

.user-info-display i {
  font-size: 24px;
  color: var(--text-secondary);
}

.w-full {
  width: 100%;
}

.delete-dialog-content {
  padding: 16px 0;
  text-align: center;
}

.delete-warning-icon {
  font-size: 48px;
  color: var(--red-500);
  margin-bottom: 16px;
  display: block;
}

.delete-warning-text {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 8px;
}
</style>