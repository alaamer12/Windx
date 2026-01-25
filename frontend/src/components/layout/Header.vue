<template>
  <Toolbar class="border-b border-slate-200 bg-white !p-3 !rounded-none">
    <template #start>
      <Button 
        icon="pi pi-bars" 
        @click="emit('toggle-sidebar')"
        text
        rounded
        class="text-slate-600"
      />
      <span class="ml-4 font-semibold text-lg text-slate-800">{{ pageTitle }}</span>
    </template>

    <template #end>
      <div class="flex items-center gap-3">
        <span v-if="authStore.user" class="text-sm font-medium text-slate-600">
          {{ authStore.user.full_name || authStore.user.username }}
        </span>
        <Avatar 
          icon="pi pi-user" 
          shape="circle" 
          class="bg-blue-600 text-white"
        />
      </div>
    </template>
  </Toolbar>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'
import Avatar from 'primevue/avatar'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const route = useRoute()
const authStore = useAuthStore()

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/profile-entry': 'Profile Entry'
  }
  return titles[route.path] || 'Windx'
})
</script>
