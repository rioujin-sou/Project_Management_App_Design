<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="auth-title">Reset Password</h1>
      <p class="auth-subtitle">Enter your new password</p>

      <form @submit.prevent="handleResetPassword">
        <div class="form-group">
          <label for="password">New Password</label>
          <Password
            id="password"
            v-model="password"
            placeholder="Enter new password"
            toggleMask
            :class="{ 'p-invalid': errors.password }"
          />
          <small v-if="errors.password" class="form-error">{{ errors.password }}</small>
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <Password
            id="confirmPassword"
            v-model="confirmPassword"
            placeholder="Confirm new password"
            :feedback="false"
            toggleMask
            :class="{ 'p-invalid': errors.confirmPassword }"
          />
          <small v-if="errors.confirmPassword" class="form-error">{{ errors.confirmPassword }}</small>
        </div>

        <Message v-if="authStore.error" severity="error" :closable="false">
          {{ authStore.error }}
        </Message>

        <Message v-if="successMessage" severity="success" :closable="false">
          {{ successMessage }}
        </Message>

        <Button
          type="submit"
          label="Reset Password"
          :loading="authStore.loading"
          class="w-full mt-3"
        />
      </form>

      <Divider />

      <div class="text-center">
        <router-link to="/login" class="text-primary">
          <i class="pi pi-arrow-left mr-2"></i>
          Back to Sign In
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Divider from 'primevue/divider'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const password = ref('')
const confirmPassword = ref('')
const token = ref('')
const successMessage = ref('')
const errors = reactive({
  password: null,
  confirmPassword: null,
})

onMounted(() => {
  token.value = route.query.token || ''
  if (!token.value) {
    router.push('/forgot-password')
  }
})

const validate = () => {
  errors.password = null
  errors.confirmPassword = null
  let isValid = true

  if (!password.value) {
    errors.password = 'Password is required'
    isValid = false
  } else if (password.value.length < 8) {
    errors.password = 'Password must be at least 8 characters'
    isValid = false
  }

  if (!confirmPassword.value) {
    errors.confirmPassword = 'Please confirm your password'
    isValid = false
  } else if (password.value !== confirmPassword.value) {
    errors.confirmPassword = 'Passwords do not match'
    isValid = false
  }

  return isValid
}

const handleResetPassword = async () => {
  if (!validate()) return
  
  successMessage.value = ''
  const result = await authStore.resetPassword(token.value, password.value)
  
  if (result.success) {
    successMessage.value = result.message
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  }
}
</script>

<style scoped>
.text-primary {
  color: var(--primary-color);
  text-decoration: none;
}

.text-primary:hover {
  text-decoration: underline;
}

.w-full {
  width: 100%;
}

.mt-3 {
  margin-top: 1rem;
}

.mr-2 {
  margin-right: 0.5rem;
}

.text-center {
  text-align: center;
}

:deep(.p-password) {
  width: 100%;
}

:deep(.p-password-input) {
  width: 100%;
}
</style>
