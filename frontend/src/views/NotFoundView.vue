<template>
  <div class="flex flex-col items-center justify-center min-h-screen bg-slate-50 text-center p-8">
    <div class="mb-4 text-blue-600">
      <i class="pi pi-exclamation-triangle text-8xl animate-bounce"></i>
    </div>
    <h1 class="text-6xl font-bold text-slate-800 mb-4">404</h1>
    <p class="text-xl text-slate-600 mb-8">Oops! The page you're looking for doesn't exist.</p>
    <router-link to="/dashboard" class="no-underline">
      <Button label="Go to Dashboard" icon="pi pi-home" size="large" />
    </router-link>
  </div>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
</script>
