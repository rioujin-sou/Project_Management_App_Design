<template>
  <div class="baseline-diff-view">
    <div class="page-header">
      <h2>Baseline Comparison</h2>
      <div class="btn-group">
        <Button
          v-if="authStore.isTDL"
          icon="pi pi-refresh"
          label="Update Baseline"
          @click="handleUpdateBaseline"
        />
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
      <!-- Summary Cards -->
      <div class="diff-summary">
        <div class="summary-card added">
          <i class="pi pi-plus-circle"></i>
          <div class="summary-content">
            <div class="summary-number">{{ addedTasks.length }}</div>
            <div class="summary-label">Added Tasks</div>
          </div>
        </div>
        <div class="summary-card removed">
          <i class="pi pi-minus-circle"></i>
          <div class="summary-content">
            <div class="summary-number">{{ removedTasks.length }}</div>
            <div class="summary-label">Removed Tasks</div>
          </div>
        </div>
        <div class="summary-card modified">
          <i class="pi pi-pencil"></i>
          <div class="summary-content">
            <div class="summary-number">{{ modifiedTasks.length }}</div>
            <div class="summary-label">Modified Tasks</div>
          </div>
        </div>
        <div class="summary-card unchanged">
          <i class="pi pi-check-circle"></i>
          <div class="summary-content">
            <div class="summary-number">{{ unchangedTasks.length }}</div>
            <div class="summary-label">Unchanged Tasks</div>
          </div>
        </div>
      </div>

      <!-- No baseline message -->
      <Message v-if="!hasBaseline" severity="info" :closable="false">
        No baseline has been set for this project. Click "Update Baseline" to create one.
      </Message>

      <!-- Diff Tabs -->
      <TabView v-else class="diff-tabs">
        <!-- Added Tasks -->
        <TabPanel header="Added">
          <DataTable
            :value="addedTasks"
            :paginator="addedTasks.length > 10"
            :rows="10"
            emptyMessage="No added tasks"
            stripedRows
          >
            <Column field="wp_id" header="WP-ID" style="width: 8%" />
            <Column field="site" header="Site" style="width: 8%" />
            <Column field="product" header="Product" style="width: 15%" />
            <Column field="wp" header="Task" style="width: 15%" />
            <Column field="resource_name" header="Resource" style="width: 12%" />
            <Column field="resource_category" header="Resource Category" style="width: 12%" />
            <Column header="Duration" style="width: 15%">
              <template #body="{ data }">
                {{ formatDate(data.start_date) }} - {{ formatDate(data.end_date) }}
              </template>
            </Column>
            <Column header="Completion" style="width: 8%">
              <template #body="{ data }">
                {{ data.completion_pct || 0 }}%
              </template>
            </Column>
            <Column field="comment" header="Comment" style="width: 7%" />
          </DataTable>
        </TabPanel>

        <!-- Removed Tasks -->
        <TabPanel header="Removed">
          <DataTable
            :value="removedTasks"
            :paginator="removedTasks.length > 10"
            :rows="10"
            emptyMessage="No removed tasks"
            stripedRows
          >
            <Column field="wp_id" header="WP-ID" style="width: 8%" />
            <Column field="site" header="Site" style="width: 8%" />
            <Column field="product" header="Product" style="width: 15%" />
            <Column field="wp" header="Task" style="width: 15%" />
            <Column field="resource_name" header="Resource" style="width: 12%" />
            <Column field="resource_category" header="Resource Category" style="width: 12%" />
            <Column header="Duration" style="width: 15%">
              <template #body="{ data }">
                {{ formatDate(data.start_date) }} - {{ formatDate(data.end_date) }}
              </template>
            </Column>
            <Column header="Completion" style="width: 8%">
              <template #body="{ data }">
                {{ data.completion_pct || 0 }}%
              </template>
            </Column>
            <Column field="comment" header="Comment" style="width: 7%" />
          </DataTable>
        </TabPanel>

        <!-- Modified Tasks -->
        <TabPanel header="Modified">
          <DataTable
            :value="modifiedTasks"
            :paginator="modifiedTasks.length > 10"
            :rows="10"
            emptyMessage="No modified tasks"
            stripedRows
            :expandedRows="expandedRows"
            @update:expandedRows="val => expandedRows = val"
            dataKey="current.id"
          >
            <Column :expander="true" style="width: 3rem" />
            <Column field="current.wp_id" header="WP-ID" style="width: 8%" />
            <Column field="current.site" header="Site" style="width: 8%" />
            <Column field="current.product" header="Product" style="width: 13%" />
            <Column field="current.wp" header="Task" style="width: 13%" />
            <Column field="current.resource_name" header="Resource" style="width: 10%" />
            <Column field="current.resource_category" header="Resource Category" style="width: 10%" />
            <Column field="current.comment" header="Comment" style="width: 10%" />
            <Column header="Changed Fields" style="width: 25%">
              <template #body="{ data }">
                <div class="changed-fields">
                  <Tag
                    v-for="field in data.changedFields"
                    :key="field"
                    :value="field"
                    severity="warning"
                    class="mr-1"
                  />
                </div>
              </template>
            </Column>

            <template #expansion="{ data }">
              <div class="field-comparison">
                <h4>Field Changes</h4>
                <div class="comparison-table">
                  <div v-for="field in data.changedFields" :key="field" class="comparison-row">
                    <div class="field-name">{{ formatFieldName(field) }}</div>
                    <div class="field-before diff-removed">{{ formatValue(data.baseline[field]) }}</div>
                    <div class="diff-arrow"><i class="pi pi-arrow-right"></i></div>
                    <div class="field-after diff-added">{{ formatValue(data.current[field]) }}</div>
                  </div>
                </div>
              </div>
            </template>
          </DataTable>
        </TabPanel>
      </TabView>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Tag from 'primevue/tag'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()
const toast = useToast()

const projectId = computed(() => route.params.id)
const loading = ref(true)
const expandedRows = ref({})

const project = computed(() => projectsStore.currentProject)
const hasBaseline = computed(() => project.value?.baseline_json != null)

const baselineTasks = computed(() => {
  return project.value?.baseline_json?.tasks ?? []
})

const currentTasks = computed(() => tasksStore.tasks)

// Compare tasks
const comparedFields = ['wp_id', 'site', 'category', 'product', 'wp', 'role', 'resource_name', 'resource_category', 'start_date', 'end_date', 'effort', 'comment']

const addedTasks = computed(() => {
  const baselineIds = new Set(baselineTasks.value.map(t => t.wp_id))
  return currentTasks.value.filter(t => !baselineIds.has(t.wp_id))
})

const removedTasks = computed(() => {
  const currentIds = new Set(currentTasks.value.map(t => t.wp_id))
  return baselineTasks.value.filter(t => !currentIds.has(t.wp_id))
})

const modifiedTasks = computed(() => {
  const modified = []
  const baselineMap = new Map(baselineTasks.value.map(t => [t.wp_id, t]))
  
  currentTasks.value.forEach(current => {
    const baseline = baselineMap.get(current.wp_id)
    if (!baseline) return
    
    const changedFields = []
    comparedFields.forEach(field => {
      const currentVal = normalizeValue(current[field])
      const baselineVal = normalizeValue(baseline[field])
      if (currentVal !== baselineVal) {
        changedFields.push(field)
      }
    })
    
    if (changedFields.length > 0) {
      modified.push({
        current,
        baseline,
        changedFields,
      })
    }
  })
  
  return modified
})

const unchangedTasks = computed(() => {
  const modifiedIds = new Set(modifiedTasks.value.map(t => t.current.wp_id))
  const addedIds = new Set(addedTasks.value.map(t => t.wp_id))
  const baselineIds = new Set(baselineTasks.value.map(t => t.wp_id))
  
  return currentTasks.value.filter(t => 
    !modifiedIds.has(t.wp_id) && 
    !addedIds.has(t.wp_id) &&
    baselineIds.has(t.wp_id)
  )
})

onMounted(async () => {
  await projectsStore.fetchProjectById(projectId.value)
  await tasksStore.fetchTasks(projectId.value)
  loading.value = false
})

const normalizeValue = (val) => {
  if (val === null || val === undefined) return ''
  if (typeof val === 'string') return val.trim()
  return String(val)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

const formatFieldName = (field) => {
  return field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatValue = (val) => {
  if (val === null || val === undefined || val === '') return '(empty)'
  if (typeof val === 'string' && val.match(/^\d{4}-\d{2}-\d{2}/)) {
    return formatDate(val)
  }
  return String(val)
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
</script>

<style scoped>
.diff-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.summary-card i {
  font-size: 32px;
}

.summary-card.added i {
  color: var(--success-color);
}

.summary-card.removed i {
  color: var(--danger-color);
}

.summary-card.modified i {
  color: var(--warning-color);
}

.summary-card.unchanged i {
  color: var(--info-color);
}

.summary-number {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.summary-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.diff-tabs {
  background: var(--surface-card);
  border-radius: var(--border-radius);
  border: 1px solid var(--surface-border);
}

.changed-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.field-comparison {
  padding: 16px;
  background: var(--surface-ground);
}

.field-comparison h4 {
  margin: 0 0 16px;
  font-size: 14px;
  font-weight: 600;
}

.comparison-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comparison-row {
  display: grid;
  grid-template-columns: 150px 1fr 40px 1fr;
  gap: 16px;
  align-items: center;
  padding: 8px 12px;
  background: var(--surface-card);
  border-radius: 4px;
}

.field-name {
  font-weight: 500;
}

.field-before {
  padding: 4px 8px;
  border-radius: 4px;
}

.field-after {
  padding: 4px 8px;
  border-radius: 4px;
}

.diff-arrow {
  text-align: center;
  color: var(--text-secondary);
}

.mr-1 {
  margin-right: 4px;
}
</style>
