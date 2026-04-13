<template>
  <div class="gantt-view">
    <div class="page-header">
      <div>
        <h2>{{ project?.name || 'Gantt Chart' }}</h2>
        <p v-if="project" class="project-meta">
          <span>Opp ID: {{ project.opp_id }}</span>
          <span class="separator">•</span>
          <span>Version: {{ project.version }}</span>
          <span class="separator">•</span>
          <span>Created: {{ formatProjectDate(project.created_at) }}</span>
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
      <!-- Filters and Column Toggle -->
      <div class="gantt-controls card">
        <div class="filters-row">
          <div class="filter-item">
            <label>Site Filter</label>
            <Dropdown
              v-model="selectedSite"
              :options="siteOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="All Sites"
              style="width: 200px"
              @change="filterTasks"
            />
          </div>
          <div class="filter-item">
            <label>Product Filter</label>
            <Dropdown
              v-model="selectedProduct"
              :options="productOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="All Products"
              style="width: 200px"
              @change="filterTasks"
            />
          </div>
          <div class="filter-item">
            <label>Resource Category Filter</label>
            <Dropdown
              v-model="selectedResourceCategory"
              :options="resourceCategoryOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="All Categories"
              style="width: 200px"
              @change="filterTasks"
            />
          </div>
        </div>

        <div class="column-toggles">
          <label>Show Additional Columns:</label>
          <div class="checkbox-group">
            <div v-for="col in optionalColumns" :key="col.name" class="checkbox-item">
              <Checkbox
                v-model="visibleOptionalColumns"
                :value="col.name"
                :inputId="col.name"
                @change="updateColumns"
              />
              <label :for="col.name">{{ col.label }}</label>
            </div>
          </div>
        </div>
      </div>

      <!-- Gantt Chart -->
      <div ref="ganttContainer" class="gantt-container"></div>

      <!-- Empty state -->
      <div v-if="filteredTasks.length === 0" class="empty-state">
        <i class="pi pi-chart-bar"></i>
        <h3>No Tasks to Display</h3>
        <p>No tasks match the current filter</p>
      </div>
    </template>

    <!-- Task Detail Sidebar -->
    <TaskDetailPanel
      v-model:visible="showTaskPanel"
      :task="selectedTask"
      @updated="handleTaskUpdated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { gantt } from 'dhtmlx-gantt'
import 'dhtmlx-gantt/codebase/dhtmlxgantt.css'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Checkbox from 'primevue/checkbox'
import ProgressSpinner from 'primevue/progressspinner'
import TaskDetailPanel from '@/components/TaskDetailPanel.vue'

const route = useRoute()
const router = useRouter()
const projectsStore = useProjectsStore()
const tasksStore = useTasksStore()

const project = computed(() => projectsStore.currentProject)

const projectId = computed(() => route.params.id)
const loading = ref(true)
const ganttContainer = ref(null)
const showTaskPanel = ref(false)
const selectedTask = ref(null)
const selectedSite = ref(null)
const selectedProduct = ref(null)
const selectedResourceCategory = ref(null)
const visibleOptionalColumns = ref([])

const siteOptions = computed(() => {
  const sites = [{ label: 'All Sites', value: null }]
  tasksStore.uniqueSites.forEach(site => {
    sites.push({ label: site, value: site })
  })
  return sites
})

const productOptions = computed(() => {
  const products = [...new Set(tasksStore.tasks.map(t => t.product).filter(Boolean))].sort()
  return [{ label: 'All Products', value: null }, ...products.map(p => ({ label: p, value: p }))]
})

const resourceCategoryOptions = computed(() => {
  const cats = [...new Set(tasksStore.tasks.map(t => t.resource_category).filter(Boolean))].sort()
  return [{ label: 'All Categories', value: null }, ...cats.map(c => ({ label: c, value: c }))]
})

// Mandatory columns (always visible, frozen on the left)
const mandatoryColumns = [
  { name: 'site', label: 'Site', width: 80 },
  { name: 'text', label: 'Task', width: 270, tree: false },
  { name: 'wp_id', label: 'WP-ID', width: 120, align: 'left' },
  { name: 'product', label: 'Product', width: 80, align: 'left' },
  { name: 'resource_category', label: 'Resource\nCategory', width: 80, align: 'left' },
  { name: 'start_date', label: 'Start', width: 95, align: 'center' },
  { name: 'end_date', label: 'End', width: 95, align: 'center' },
  { name: 'completion_pct', label: 'Progress', width: 80, align: 'center' },
]

// Optional columns (can be toggled, scrollable)
const optionalColumns = [
  { name: 'category', label: 'Category', width: 110 },
  { name: 'role', label: 'Role', width: 90 },
  { name: 'resource_name', label: 'Resource', width: 130 },
  { name: 'effort', label: 'Effort', width: 70 },
  { name: 'total_effort', label: 'Total Effort', width: 90 },
  { name: 'comment', label: 'Comment', width: 200 },
]

const filteredTasks = computed(() => {
  let tasks = tasksStore.tasks
  if (selectedSite.value) {
    tasks = tasks.filter(t => t.site === selectedSite.value)
  }
  if (selectedProduct.value) {
    tasks = tasks.filter(t => t.product === selectedProduct.value)
  }
  if (selectedResourceCategory.value) {
    tasks = tasks.filter(t => t.resource_category === selectedResourceCategory.value)
  }
  // Sort by start_date ascending
  return [...tasks].sort((a, b) => {
    const dateA = a.start_date ? new Date(a.start_date) : new Date('9999-12-31')
    const dateB = b.start_date ? new Date(b.start_date) : new Date('9999-12-31')
    return dateA - dateB
  })
})

const formatProjectDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

onMounted(async () => {
  // Fetch project only if not already cached for this ID (fire-and-forget — no await)
  const currentId = Number(projectId.value)
  if (!projectsStore.currentProject || projectsStore.currentProject.id !== currentId) {
    projectsStore.fetchProjectById(projectId.value)
  }
  await tasksStore.fetchTasks(projectId.value)
  loading.value = false
  await nextTick()
  initGantt()
})

onUnmounted(() => {
  gantt.clearAll()
})

const calculateDateRange = (tasks) => {
  const validDates = []
  tasks.forEach(t => {
    if (t.start_date) {
      const d = new Date(t.start_date)
      if (!isNaN(d.getTime())) validDates.push(d)
    }
    if (t.end_date) {
      const d = new Date(t.end_date)
      if (!isNaN(d.getTime())) validDates.push(d)
    }
  })

  if (validDates.length === 0) {
    // Default to current month if no valid dates
    const now = new Date()
    const startDate = new Date(now.getFullYear(), now.getMonth(), 1)
    const endDate = new Date(now.getFullYear(), now.getMonth() + 2, 0)
    return { startDate, endDate }
  }

  const minDate = new Date(Math.min(...validDates))
  const maxDate = new Date(Math.max(...validDates))

  // Add 1 month padding before and after
  const startDate = new Date(minDate)
  startDate.setMonth(startDate.getMonth() - 1)
  startDate.setDate(1) // Snap to start of month

  const endDate = new Date(maxDate)
  endDate.setMonth(endDate.getMonth() + 2)
  endDate.setDate(0) // Snap to end of month

  // Safety: ensure start < end
  if (startDate >= endDate) {
    endDate.setMonth(startDate.getMonth() + 2)
  }

  return { startDate, endDate }
}

const initGantt = () => {
  if (!ganttContainer.value) return

  // Configure Gantt
  gantt.config.date_format = '%Y-%m-%d'
  gantt.config.scale_height = 50
  gantt.config.row_height = 35
  gantt.config.readonly = true
  gantt.config.drag_move = false
  gantt.config.drag_resize = false
  gantt.config.drag_progress = false

  // Two-level timeline: months on top, weeks on bottom
  gantt.config.scales = [
    { unit: "month", step: 1, format: "%F %Y" },
    { unit: "week", step: 1, format: "Wk%W" }
  ]
  gantt.config.min_column_width = 50

  // Bound the timeline to the task date range
  const { startDate, endDate } = calculateDateRange(filteredTasks.value)
  gantt.config.start_date = startDate
  gantt.config.end_date = endDate

  gantt.config.fit_tasks = false
  gantt.config.show_tasks_outside_timescale = false
  gantt.config.auto_scheduling = false
  gantt.config.autosize = false

  // Decouple grid and timeline scrollbars completely.
  // The grid has NO horizontal scrollbar (gridScroll height=0, no group).
  // Only the timeline gets a real horizontal scrollbar (scrollHor).
  // Both share a single vertical scrollbar (scrollVer).
  gantt.config.layout = {
    css: 'gantt_container',
    rows: [
      {
        cols: [
          { view: 'grid', id: 'grid', scrollX: 'gridScroll', scrollY: 'scrollVer' },
          { resizer: true, width: 1 },
          { view: 'timeline', id: 'timeline', scrollX: 'scrollHor', scrollY: 'scrollVer' },
          { view: 'scrollbar', id: 'scrollVer' },
        ]
      },
      { view: 'scrollbar', id: 'scrollHor' },
      { view: 'scrollbar', id: 'gridScroll', height: 0, visible: false },
    ]
  }

  // Set columns
  updateColumns()

  // Remove text labels from task bars in the timeline
  gantt.templates.task_text = () => ''

  // Enable markers plugin and today marker
  gantt.plugins({ marker: true })
  gantt.config.show_markers = true

  // Initialize gantt
  gantt.init(ganttContainer.value)

  // Click handler
  gantt.attachEvent('onTaskClick', (id) => {
    const task = tasksStore.tasks.find(t => t.id === parseInt(id))
    if (task) {
      selectedTask.value = task
      showTaskPanel.value = true
    }
    return true
  })

  // Load data
  loadGanttData()
}

const loadGanttData = () => {
  const data = filteredTasks.value.map(task => ({
    id: task.id,
    text: task.wp || task.wp_id || `Task ${task.id}`,
    start_date: task.start_date || new Date().toISOString().split('T')[0],
    end_date: task.end_date,
    duration: calculateDuration(task.start_date, task.end_date),
    progress: (task.completion_pct || 0) / 100,
    wp: task.wp,
    wp_id: task.wp_id,
    category: task.category,
    product: task.product,
    role: task.role,
    resource_name: task.resource_name,
    site: task.site,
    effort: task.effort,
    total_effort: task.total,
    completion_pct: task.completion_pct,
    comment: task.comment,
    resource_category: task.resource_category,
  }))

  // Recalculate date range for current data set
  const { startDate, endDate } = calculateDateRange(filteredTasks.value)
  gantt.config.start_date = startDate
  gantt.config.end_date = endDate

  gantt.clearAll()
  gantt.parse({ data, links: [] })

  // Add today marker after parse (clearAll wipes markers)
  const todayTokyo = new Date(new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Tokyo' }))
  gantt.addMarker({
    start_date: todayTokyo,
    css: 'today-marker',
    text: 'Today',
    title: todayTokyo.toLocaleDateString('en-CA'),
  })
}

const calculateDuration = (startDate, endDate) => {
  if (!startDate || !endDate) return 1
  const start = new Date(startDate)
  const end = new Date(endDate)
  const diff = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
  return Math.max(diff, 1)
}

const buildColumnConfig = (col) => {
  const config = {
    name: col.name,
    label: col.label,
    width: col.width,
    align: col.align || 'left',
  }

  if (col.tree !== undefined) {
    config.tree = col.tree
  }

  // Custom template for specific columns
  if (col.name === 'completion_pct') {
    config.template = (task) => `${task.completion_pct || 0}%`
  } else if (col.name === 'start_date' || col.name === 'end_date') {
    config.template = (task) => {
      const val = task[col.name]
      if (!val) return '-'
      try {
        return new Date(val).toLocaleDateString('en-CA') // YYYY-MM-DD format
      } catch {
        return val
      }
    }
  } else if (col.name !== 'text') {
    config.template = (task) => task[col.name] || '-'
  }

  // Show full text on hover for truncated columns
  if (['text', 'comment', 'resource_name'].includes(col.name)) {
    const inner = config.template || ((task) => task[col.name] || '')
    config.template = (task) => {
      const value = (col.name === 'text' ? task.text : task[col.name]) || ''
      const escaped = value.toString().replace(/"/g, '&quot;')
      return `<span title="${escaped}">${inner(task)}</span>`
    }
  }

  return config
}

const MANDATORY_GRID_WIDTH = mandatoryColumns.reduce((sum, col) => sum + col.width, 0)

const updateColumns = () => {
  const allCols = mandatoryColumns.map(buildColumnConfig)

  const scrollCols = visibleOptionalColumns.value
    .map(colName => optionalColumns.find(c => c.name === colName))
    .filter(Boolean)
    .map(buildColumnConfig)

  allCols.push(...scrollCols)

  const optionalWidth = scrollCols.reduce((sum, col) => sum + col.width, 0)

  // Grid width is fixed to its columns — only the timeline panel scrolls horizontally
  gantt.config.grid_width = MANDATORY_GRID_WIDTH + optionalWidth + 2
  gantt.config.grid_resize = true
  gantt.config.columns = allCols

  if (ganttContainer.value && gantt.$container) {
    gantt.clearAll()
    gantt.init(ganttContainer.value)
    loadGanttData()
  }
}

const filterTasks = () => {
  loadGanttData()
}

const handleTaskUpdated = async () => {
  await tasksStore.fetchTasks(projectId.value)
  loadGanttData()
  // Refresh the selected task object so TaskDetailPanel re-renders with updated data
  if (selectedTask.value) {
    const refreshed = tasksStore.tasks.find(t => t.id === selectedTask.value.id)
    if (refreshed) selectedTask.value = refreshed
  }
}

watch(filteredTasks, () => {
  if (!loading.value && ganttContainer.value) {
    loadGanttData()
  }
})
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

.gantt-controls {
  margin-bottom: 16px;
}

/* Prevent the view wrapper from expanding wider than its parent */
.gantt-view {
  min-width: 0;
  width: 100%;
}

.column-toggles {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--surface-border);
}

.column-toggles > label {
  font-weight: 600;
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  display: block;
  margin-bottom: 12px;
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox-item label {
  font-size: 14px;
  cursor: pointer;
}

:deep(.gantt_task_progress) {
  background: var(--primary-color);
}

:deep(.gantt_task_line) {
  background: #93c5fd;
  border-color: var(--primary-color);
}

:deep(.gantt_grid_scale .gantt_grid_head_cell) {
  font-weight: 600;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: pre-line;
  line-height: 1.3;
  display: table-cell;
  vertical-align: middle;
}

:deep(.gantt_cell) {
  font-size: 13px;
}

/* Lock the grid panel — it must never grow wider than its columns */
:deep(.gantt_grid) {
  overflow: hidden !important;
  flex-shrink: 0 !important;
  flex-grow: 0 !important;
}

/* The dummy grid scrollbar must take zero space */
:deep(#gridScroll),
:deep(.gantt_grid_scroll_cell) {
  height: 0 !important;
  min-height: 0 !important;
  overflow: hidden !important;
  visibility: hidden !important;
}

/* The timeline panel scrolls horizontally via its own scrollbar only */
:deep(.gantt_task) {
  overflow: hidden !important;
}

/* Full-width layout */
:deep(.gantt_container) {
  width: 100% !important;
}

/* Today marker */
:deep(.today-marker) {
  background: #ef4444;
  width: 2px;
  opacity: 0.85;
}

:deep(.today-marker .gantt_marker_content) {
  background: #ef4444;
  color: white;
  font-size: 11px;
  padding: 2px 5px;
  border-radius: 3px;
}
</style>