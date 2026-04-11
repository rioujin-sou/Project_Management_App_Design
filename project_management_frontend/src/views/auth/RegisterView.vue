<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="auth-title">Create Account</h1>
      <p class="auth-subtitle">Sign up to get started</p>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="email">Email</label>
          <InputText
            id="email"
            v-model="email"
            type="email"
            placeholder="Enter your email"
            :class="{ 'p-invalid': errors.email }"
          />
          <small v-if="errors.email" class="form-error">{{ errors.email }}</small>
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <Password
            id="password"
            v-model="password"
            placeholder="Create a password"
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
            placeholder="Confirm your password"
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
          label="Sign Up"
          :loading="authStore.loading"
          class="w-full mt-3"
        />
      </form>

      <Divider />

      <div class="text-center">
        <span class="text-secondary">Already have an account? </span>
        <router-link to="/login" class="text-primary font-semibold">
          Sign in
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Divider from 'primevue/divider'

const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const successMessage = ref('')
const errors = reactive({
  email: null,
  password: null,
  confirmPassword: null,
})

const validate = () => {
  errors.email = null
  errors.password = null
  errors.confirmPassword = null
  let isValid = true

  if (!email.value) {
    errors.email = 'Email is required'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    errors.email = 'Invalid email format'
    isValid = false
  }

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

const handleRegister = async () => {
  if (!validate()) return
  
  successMessage.value = ''
  const result = await authStore.register(email.value, password.value)
  
  if (result.success) {
    successMessage.value = result.message
    email.value = ''
    password.value = ''
    confirmPassword.value = ''
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

.text-secondary {
  color: var(--text-secondary);
}

.font-semibold {
  font-weight: 600;
}

.w-full {
  width: 100%;
}

.mt-3 {
  margin-top: 1rem;
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
