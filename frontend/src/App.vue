<template>
  <div id="app">
    <div v-if="!authStore.isInitialized" class="global-loading">
      <div class="loading-content">
        <i class="pi pi-spin pi-spinner text-primary text-4xl mb-3"></i>
        <p class="text-gray-600 font-medium">Loading...</p>
        <p class="text-gray-400 text-sm mt-2">Connecting to server...</p>
      </div>
    </div>
    <RouterView v-else />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
}

.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #ffffff;
  z-index: 9999;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}
</style>
