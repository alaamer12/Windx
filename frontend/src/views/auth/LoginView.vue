<template>
  <div class="flex items-center justify-center min-h-screen bg-slate-100">
    <Card class="w-full max-w-md p-4 shadow-xl rounded-xl">
      <template #title>
        <div class="text-center mb-6">
          <h1 class="text-2xl font-bold text-slate-800">Windx Configurator</h1>
          <p class="text-slate-500 mt-2">Sign in to your account</p>
        </div>
      </template>
      <template #content>
        <form @submit.prevent="handleLogin" class="flex flex-col gap-5">
          <div class="flex flex-col gap-2">
            <label for="username" class="font-medium text-slate-700">Username</label>
            <InputText
              id="username"
              v-model="username"
              class="w-full"
              required
              autocomplete="username"
              placeholder="Enter your username"
            />
          </div>

          <div class="flex flex-col gap-2">
            <label for="password" class="font-medium text-slate-700">Password</label>
            <Password
              id="password"
              v-model="password"
              :feedback="false"
              toggleMask
              class="w-full"
              inputClass="w-full"
              required
              autocomplete="current-password"
              placeholder="Enter your password"
            />
          </div>

          <Message v-if="error" severity="error" :closable="false">
            {{ error }}
          </Message>

          <Button 
            type="submit" 
            label="Sign in" 
            icon="pi pi-sign-in" 
            :loading="isLoading" 
            class="w-full mt-2"
          />
        </form>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const isLoading = ref(false)

async function handleLogin() {
  error.value = ''
  isLoading.value = true

  try {
    const result = await authStore.login(username.value, password.value)
    
    if (result.success) {
      const redirect = route.query.redirect as string || '/dashboard'
      router.push(redirect)
    } else {
      error.value = result.error || 'Login failed'
    }
  } catch (err: any) {
    error.value = err.message || 'An error occurred'
  } finally {
    isLoading.value = false
  }
}
</script>
