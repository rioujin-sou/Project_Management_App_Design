<template>
  <div class="audit-logs-view">
    <div class="page-header">
      <h1>Audit Logs</h1>
    </div>

    <!-- Filters -->
    <div class="card filters-card">
      <div class="filters-row">
        <div class="filter-item">
          <label>User</label>
          <Dropdown
            v-model="filters.user_id"
            :options="userOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="All Users"
            showClear
            style="width: 200px"
          />
        </div>

        <div class="filter-item">
          <label>Entity Type</label>
          <Dropdown
            v-model="filters.entity_type"
            :options="entityTypeOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="All Types"
            showClear
            style="width: 180px"
          />
        </div>

        <div class="filter-item">
          <label>Start Date</label>
          <DatePicker
            v-model="filters.start_date"
            dateFormat="yy-mm-dd"
            placeholder="Start Date"
            showIcon
          />
        </div>

        <div class="filter-item">
          <label>End Date</label>
          <DatePicker
            v-model="filters.end_date"
            dateFormat="yy-mm-dd"
            placeholder="End Date"
            showIcon
          />
        </div>

        <div class="filter-item filter-actions">
          <Button
            label="Apply"
            icon="pi pi-search"
            @click="applyFilters"
          />
          <Button
            label="Clear"
            severity="secondary"
            text
            @click="clearFilters"
          />
        </div>
      </div>
    </div>

    <!-- Logs Table -->
    <div class="card data-table-container">
      <DataTable
        :value="auditLogsStore.logs"
        :loading="auditLogsStore.loading"
        :paginator="true"
        :rows="20"
        :rowsPerPageOptions="[20, 50, 100]"
        dataKey="id"
        stripedRows
        sortField="created_at"
        :sortOrder="-1"
        :expandedRows="expandedRows"
        @update:expandedRows="val => expandedRows = val"
        emptyMessage="No audit logs found"
      >
        <Column :expander="true" style="width: 3rem" />
        
        <Column header="Timestamp" sortable sortField="created_at" style="width: 15%">
          <template #body="{ data }">
            {{ formatDateTime(data.created_at) }}
          </template>
        </Column>

        <Column header="User" style="width: 15%">
          <template #body="{ data }">
            {{ data.user?.email || 'System' }}
          </template>
        </Column>

        <Column field="action" header="Action" style="width: 12%">
          <template #body="{ data }">
            <Tag :value="data.action" :severity="getActionSeverity(data.action)" />
          </template>
        </Column>

        <Column field="entity_type" header="Entity Type" style="width: 12%" />
        <Column field="entity_id" header="Entity ID" style="width: 10%" />

        <Column header="Summary" style="width: 36%">
          <template #body="{ data }">
            <span class="change-summary">{{ getChangeSummary(data) }}</span>
          </template>
        </Column>

        <template #expansion="{ data }">
          <div class="log-details">
            <div v-if="data.changes_json?.old || data.changes_json?.new" class="changes-comparison">
              <div v-if="data.changes_json?.old" class="change-section">
                <h4>Before</h4>
                <pre>{{ formatJSON(data.changes_json.old) }}</pre>
              </div>
              <div v-if="data.changes_json?.new" class="change-section">
                <h4>After</h4>
                <pre>{{ formatJSON(data.changes_json.new) }}</pre>
              </div>
            </div>
            <div v-else class="no-details">
              No additional details available
            </div>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuditLogsStore } from '@/stores/auditLogs'
import { useUsersStore } from '@/stores/users'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import DatePicker from 'primevue/datepicker'
import Tag from 'primevue/tag'

const auditLogsStore = useAuditLogsStore()
const usersStore = useUsersStore()

const expandedRows = ref({})
const filters = reactive({
  user_id: null,
  entity_type: null,
  start_date: null,
  end_date: null,
})

const entityTypeOptions = [
  { label: 'Project', value: 'Project' },
  { label: 'Task', value: 'Task' },
  { label: 'Comment', value: 'Comment' },
  { label: 'User', value: 'User' },
]

const userOptions = computed(() => {
  const options = [{ label: 'All Users', value: null }]
  usersStore.users.forEach(user => {
    options.push({ label: user.email, value: user.id })
  })
  return options
})

onMounted(async () => {
  await Promise.all([
    auditLogsStore.fetchAuditLogs(),
    usersStore.fetchUsers(),
  ])
})

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const getActionSeverity = (action) => {
  switch (action?.toLowerCase()) {
    case 'create':
      return 'success'
    case 'update':
      return 'info'
    case 'delete':
      return 'danger'
    default:
      return 'secondary'
  }
}

const getChangeSummary = (log) => {
  if (log.action === 'create') {
    return `Created ${log.entity_type} #${log.entity_id}`
  }
  if (log.action === 'delete') {
    return `Deleted ${log.entity_type} #${log.entity_id}`
  }
  if (log.action === 'UPDATE' && log.changes_json?.new) {
    try {
      const after = log.changes_json.new
      const fields = Object.keys(after).slice(0, 3)
      return `Updated ${fields.join(', ')}${Object.keys(after).length > 3 ? '...' : ''}`
    } catch {
      return `Updated ${log.entity_type}`
    }
  }
  return `${log.action} ${log.entity_type}`
}

const formatJSON = (data) => {
  try {
    const parsed = typeof data === 'string' ? JSON.parse(data) : data
    return JSON.stringify(parsed, null, 2)
  } catch {
    return data
  }
}

const applyFilters = () => {
  const filterParams = { ...filters }
  
  if (filterParams.start_date) {
    filterParams.start_date = filterParams.start_date.toISOString().split('T')[0]
  }
  if (filterParams.end_date) {
    filterParams.end_date = filterParams.end_date.toISOString().split('T')[0]
  }
  
  auditLogsStore.setFilters(filterParams)
  auditLogsStore.fetchAuditLogs()
}

const clearFilters = () => {
  filters.user_id = null
  filters.entity_type = null
  filters.start_date = null
  filters.end_date = null
  auditLogsStore.clearFilters()
  auditLogsStore.fetchAuditLogs()
}
</script>

<style scoped>
.filters-card {
  margin-bottom: 16px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.change-summary {
  font-size: 13px;
  color: var(--text-secondary);
}

.log-details {
  padding: 16px;
  background: var(--surface-ground);
}

.changes-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.change-section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
}

.change-section pre {
  background: var(--surface-card);
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
  margin: 0;
  max-height: 300px;
  overflow-y: auto;
}

.no-details {
  color: var(--text-secondary);
  font-style: italic;
}
</style>