<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="auth-title">Forgot Password</h1>
      <p class="auth-subtitle">Enter your email to reset your password</p>

      <form @submit.prevent="handleForgotPassword">
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

        <Message v-if="authStore.error" severity="error" :closable="false">
          {{ authStore.error }}
        </Message>

        <Message v-if="successMessage" severity="success" :closable="false">
          {{ successMessage }}
        </Message>

        <Button
          type="submit"
          label="Send Reset Link"
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
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Divider from 'primevue/divider'

const authStore = useAuthStore()

const email = ref('')
const successMessage = ref('')
const errors = reactive({
  email: null,
})

const validate = () => {
  errors.email = null

  if (!email.value) {
    errors.email = 'Email is required'
    return false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    errors.email = 'Invalid email format'
    return false
  }

  return true
}

const handleForgotPassword = async () => {
  if (!validate()) return
  
  successMessage.value = ''
  const result = await authStore.forgotPassword(email.value)
  
  if (result.success) {
    successMessage.value = result.message
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
</style>
