<template>
  <PrimeSidebar 
    v-model:visible="isVisible"
    :showCloseIcon="false"
    class="w-[260px] !border-none"
  >
    <template #header>
      <div class="flex items-center p-4">
        <i class="pi pi-th-large text-2xl text-blue-600"></i>
        <span class="font-bold text-xl ml-2 text-slate-800">Windx</span>
      </div>
    </template>

    <PanelMenu :model="menuItems" class="w-full border-none" />

    <template #footer>
      <div class="p-4 border-t border-slate-200">
        <div class="flex items-center p-3 mb-2 bg-slate-50 rounded-lg">
          <i class="pi pi-user text-slate-600"></i>
          <span class="ml-2 text-sm font-medium text-slate-700 truncate">
            {{ authStore.user?.username }}
          </span>
        </div>
        <Button 
          label="Logout" 
          icon="pi pi-sign-out" 
          @click="handleLogout"
          text
          class="w-full justify-start text-slate-600 hover:text-red-600"
        />
      </div>
    </template>
  </PrimeSidebar>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import PrimeSidebar from 'primevue/sidebar'
import PanelMenu from 'primevue/panelmenu'
import Button from 'primevue/button'
import { useAuthStore } from '@/stores/auth'
import { useDebugLogger } from '@/composables/useDebugLogger'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

const router = useRouter()
const authStore = useAuthStore()
const logger = useDebugLogger('Sidebar')

const isVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const menuItems = ref([
  {
    label: 'Dashboard',
    icon: 'pi pi-home',
    command: () => router.push('/dashboard')
  },
  {
    label: 'Profile Entry',
    icon: 'pi pi-file-edit',
    command: () => router.push('/profile-entry')
  }
])

function handleLogout() {
  logger.info('User logging out')
  authStore.logout()
  router.push('/login')
}
</script>
