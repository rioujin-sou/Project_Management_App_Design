<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="auth-title">Welcome Back</h1>
      <p class="auth-subtitle">Sign in to your account</p>

      <form @submit.prevent="handleLogin">
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
            placeholder="Enter your password"
            :feedback="false"
            toggleMask
            :class="{ 'p-invalid': errors.password }"
          />
          <small v-if="errors.password" class="form-error">{{ errors.password }}</small>
        </div>

        <Message v-if="authStore.error" severity="error" :closable="false">
          {{ authStore.error }}
        </Message>

        <Button
          type="submit"
          label="Sign In"
          :loading="authStore.loading"
          class="w-full mt-3"
        />
      </form>

      <div class="mt-4 text-center">
        <router-link to="/forgot-password" class="text-primary">
          Forgot your password?
        </router-link>
      </div>

      <Divider />

      <div class="text-center">
        <span class="text-secondary">Don't have an account? </span>
        <router-link to="/register" class="text-primary font-semibold">
          Sign up
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
const errors = reactive({
  email: null,
  password: null,
})

const validate = () => {
  errors.email = null
  errors.password = null
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
  }

  return isValid
}

const handleLogin = async () => {
  if (!validate()) return
  await authStore.login(email.value, password.value)
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

.mt-4 {
  margin-top: 1.5rem;
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
