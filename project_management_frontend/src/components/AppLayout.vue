<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-header">
        <div class="logo">
          <i class="pi pi-briefcase"></i>
          <span>Project Manager</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/projects" class="nav-item" @click="closeSidebar">
          <i class="pi pi-folder"></i>
          <span>Projects</span>
        </router-link>

        <template v-if="currentProjectId">
          <div class="nav-section-title">Current Project</div>
          
          <router-link 
            :to="`/projects/${currentProjectId}/kanban`" 
            class="nav-item"
            @click="closeSidebar"
          >
            <i class="pi pi-th-large"></i>
            <span>Kanban Board</span>
          </router-link>

          <router-link 
            :to="`/projects/${currentProjectId}/gantt`" 
            class="nav-item"
            @click="closeSidebar"
          >
            <i class="pi pi-chart-bar"></i>
            <span>Gantt Chart</span>
          </router-link>

          <router-link 
            :to="`/projects/${currentProjectId}/baseline-diff`" 
            class="nav-item"
            @click="closeSidebar"
          >
            <i class="pi pi-sliders-h"></i>
            <span>Baseline Diff</span>
          </router-link>
        </template>

        <div class="nav-section-title">Administration</div>

        <router-link 
          v-if="authStore.isTDL"
          to="/audit-logs" 
          class="nav-item"
          @click="closeSidebar"
        >
          <i class="pi pi-history"></i>
          <span>Audit Logs</span>
        </router-link>

        <router-link 
          v-if="authStore.isTDL"
          to="/users" 
          class="nav-item"
          @click="closeSidebar"
        >
          <i class="pi pi-users"></i>
          <span>User Management</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">
            <i class="pi pi-user"></i>
          </div>
          <div class="user-details">
            <div class="user-email">{{ authStore.user?.email }}</div>
            <div class="user-role">
              <span class="status-badge" :class="authStore.userRole">
                {{ authStore.userRole?.toUpperCase() }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div class="main-content">
      <!-- Header -->
      <header class="header">
        <div class="header-left">
          <Button
            icon="pi pi-bars"
            class="menu-toggle"
            text
            @click="toggleSidebar"
          />
          <Breadcrumb :model="breadcrumbs" v-if="breadcrumbs.length" />
        </div>

        <div class="header-right">
          <Button
            icon="pi pi-sign-out"
            label="Logout"
            text
            severity="secondary"
            @click="handleLogout"
          />
        </div>
      </header>

      <!-- Page content -->
      <main class="page-content">
        <router-view />
      </main>
    </div>

    <!-- Mobile overlay -->
    <div 
      v-if="sidebarOpen" 
      class="sidebar-overlay" 
      @click="closeSidebar"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Button from 'primevue/button'
import Breadcrumb from 'primevue/breadcrumb'

const route = useRoute()
const authStore = useAuthStore()

const sidebarOpen = ref(false)

// Debug role visibility
onMounted(() => {
  console.log('[AppLayout] Mounted - User:', authStore.user, 'Role:', authStore.userRole, 'isTDL:', authStore.isTDL, 'isTPM:', authStore.isTPM)
})

watch(() => authStore.user, (newUser) => {
  console.log('[AppLayout] User changed:', newUser, 'Role:', newUser?.role, 'isTDL:', authStore.isTDL)
}, { deep: true })

const currentProjectId = computed(() => {
  return route.params.id || null
})

const breadcrumbs = computed(() => {
  const items = []
  const path = route.path

  if (path.includes('/projects')) {
    items.push({ label: 'Projects', to: '/projects' })
    
    if (route.params.id) {
      if (path.includes('/kanban')) {
        items.push({ label: 'Kanban Board' })
      } else if (path.includes('/gantt')) {
        items.push({ label: 'Gantt Chart' })
      } else if (path.includes('/baseline-diff')) {
        items.push({ label: 'Baseline Diff' })
      } else {
        items.push({ label: 'Project Detail' })
      }
    }
  } else if (path.includes('/audit-logs')) {
    items.push({ label: 'Audit Logs' })
  } else if (path.includes('/users')) {
    items.push({ label: 'User Management' })
  }

  return items
})

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const closeSidebar = () => {
  sidebarOpen.value = false
}

const handleLogout = () => {
  authStore.logout()
}

// Close sidebar on route change (mobile)
watch(() => route.path, () => {
  closeSidebar()
})
</script>

<style scoped>
.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--surface-border);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color);
}

.logo i {
  font-size: 24px;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
}

.nav-section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-secondary);
  padding: 16px 12px 8px;
  letter-spacing: 0.5px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: var(--text-color);
  text-decoration: none;
  transition: all 0.2s ease;
  margin-bottom: 4px;
}

.nav-item:hover {
  background: var(--surface-hover);
}

.nav-item.router-link-active {
  background: var(--primary-color);
  color: white;
}

.nav-item i {
  font-size: 16px;
  width: 20px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--surface-border);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--surface-ground);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.user-details {
  flex: 1;
  min-width: 0;
}

.user-email {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  margin-top: 4px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-toggle {
  display: none;
}

.sidebar-overlay {
  display: none;
}

@media (max-width: 768px) {
  .menu-toggle {
    display: flex;
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
  }
}
</style>
