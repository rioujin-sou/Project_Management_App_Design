# Frontend Development Guide

This guide explains the architecture, patterns, and best practices used in the Project Management Frontend.

## Architecture Overview

### Component Structure

The application follows a modular component architecture:

1. **Views** - Page-level components that map to routes
2. **Components** - Reusable UI components
3. **Stores** - Pinia stores for state management
4. **Services** - API communication layer

### State Management with Pinia

We use Pinia for state management. Each store follows this pattern:

```javascript
import { defineStore } from 'pinia'

export const useExampleStore = defineStore('example', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
  }),

  getters: {
    filteredItems: (state) => state.items.filter(/* ... */),
  },

  actions: {
    async fetchItems() {
      this.loading = true
      this.error = null
      try {
        const response = await api.getItems()
        this.items = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },
  },
})
```

### API Service Layer

All API calls go through `src/services/api.js` which:

- Creates a configured Axios instance
- Adds JWT token to requests automatically
- Handles 401/403/500 errors globally
- Provides typed API methods

### Adding a New API Endpoint

1. Add the method to `src/services/api.js`:

```javascript
export const newFeatureAPI = {
  getAll: () => api.get('/api/v1/new-feature'),
  create: (data) => api.post('/api/v1/new-feature', data),
  update: (id, data) => api.put(`/api/v1/new-feature/${id}`, data),
  delete: (id) => api.delete(`/api/v1/new-feature/${id}`),
}
```

2. Create a store in `src/stores/`:

```javascript
import { defineStore } from 'pinia'
import { newFeatureAPI } from '@/services/api'

export const useNewFeatureStore = defineStore('newFeature', {
  // ... state, getters, actions
})
```

## Adding a New Page

### 1. Create the View Component

Create a new file in `src/views/`:

```vue
<template>
  <div class="new-page-view">
    <div class="page-header">
      <h1>New Page</h1>
    </div>
    
    <!-- Your content -->
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useNewFeatureStore } from '@/stores/newFeature'

const store = useNewFeatureStore()

onMounted(async () => {
  await store.fetchItems()
})
</script>

<style scoped>
/* Component styles */
</style>
```

### 2. Add the Route

Update `src/router/index.js`:

```javascript
{
  path: 'new-page',
  name: 'NewPage',
  component: () => import('@/views/NewPageView.vue'),
  meta: { requiresAuth: true },
}
```

### 3. Add Navigation Link

Update `src/components/AppLayout.vue` to add a sidebar link.

## PrimeVue Components

We use PrimeVue for UI components. Common imports:

```javascript
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Toast from 'primevue/toast'
```

### Using Toast Notifications

```javascript
import { useToast } from 'primevue/usetoast'

const toast = useToast()

// Success
toast.add({
  severity: 'success',
  summary: 'Success',
  detail: 'Operation completed',
  life: 3000,
})

// Error
toast.add({
  severity: 'error',
  summary: 'Error',
  detail: 'Something went wrong',
  life: 5000,
})
```

### Using Confirmation Dialogs

```javascript
import { useConfirm } from 'primevue/useconfirm'

const confirm = useConfirm()

confirm.require({
  message: 'Are you sure?',
  header: 'Confirm',
  icon: 'pi pi-exclamation-triangle',
  accept: () => {
    // Confirmed action
  },
})
```

## Authentication & Authorization

### Protected Routes

Routes are protected using navigation guards in the router:

```javascript
meta: { requiresAuth: true }  // Requires login
meta: { requiresTDL: true }   // Requires TDL role
```

### Checking User Role in Components

```javascript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Check role
if (authStore.isTDL) {
  // TDL-only action
}

if (authStore.isTPM) {
  // TPM-only action
}
```

### Conditional Rendering

```vue
<Button v-if="authStore.isTDL" label="Admin Action" />
```

## Styling Guidelines

### CSS Variables

Use the defined CSS variables from `main.css`:

```css
.my-component {
  background: var(--surface-card);
  color: var(--text-color);
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
}
```

### Scoped Styles

Always use scoped styles in components:

```vue
<style scoped>
.my-class {
  /* Styles only affect this component */
}
</style>
```

### Deep Selector for PrimeVue

To override PrimeVue component styles:

```css
:deep(.p-datatable) {
  /* Override PrimeVue DataTable styles */
}
```

## Error Handling

### API Error Handling

Errors are handled at multiple levels:

1. **Global** - Axios interceptors handle 401/403
2. **Store** - Actions catch errors and set error state
3. **Component** - Display errors using Toast or Message

### Loading States

```vue
<template>
  <div v-if="store.loading" class="loading-container">
    <ProgressSpinner />
  </div>
  
  <div v-else-if="store.error">
    <Message severity="error">{{ store.error }}</Message>
  </div>
  
  <div v-else>
    <!-- Content -->
  </div>
</template>
```

## Testing

### Running Tests

```bash
# Unit tests
npm run test:unit

# E2E tests
npm run test:e2e
```

### Testing Components

```javascript
import { mount } from '@vue/test-utils'
import MyComponent from '@/components/MyComponent.vue'

describe('MyComponent', () => {
  it('renders correctly', () => {
    const wrapper = mount(MyComponent)
    expect(wrapper.text()).toContain('Expected text')
  })
})
```

## Build & Deployment

### Development Build

```bash
npm run dev
```

### Production Build

```bash
npm run build
```

### Docker Build

```bash
docker build -t pm-frontend .
docker run -p 80:80 pm-frontend
```

## Common Patterns

### Form Validation

```javascript
const errors = reactive({
  email: null,
  password: null,
})

const validate = () => {
  let isValid = true
  
  if (!email.value) {
    errors.email = 'Email is required'
    isValid = false
  }
  
  return isValid
}
```

### Computed Properties for Filtering

```javascript
const filteredItems = computed(() => {
  return items.value.filter(item => {
    if (selectedFilter.value && item.type !== selectedFilter.value) {
      return false
    }
    return true
  })
})
```

### Watch for Route Changes

```javascript
import { watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

watch(() => route.params.id, (newId) => {
  // Fetch new data when route parameter changes
  fetchData(newId)
})
```
