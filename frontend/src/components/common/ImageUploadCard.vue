<template>
  <Card class="shadow-sm border border-slate-100">
    <template #title>
      <span class="text-sm font-bold uppercase text-slate-500">{{ title }}</span>
    </template>
    <template #content>
      <div 
        class="w-full aspect-square border-2 border-dashed border-slate-300 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors relative overflow-hidden group"
        @click="triggerImageUpload"
        @dragover.prevent
        @drop.prevent="handleDrop"
      >
        <input type="file" ref="fileInput" class="hidden" accept="image/*" @change="handleFileSelect" />
        
        <div v-if="previewUrl" class="absolute inset-0">
          <img :src="previewUrl" class="w-full h-full object-cover" />
          <div class="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <span class="text-white text-sm font-medium">Change Image</span>
          </div>
        </div>
        
        <div v-else class="text-center p-4">
          <i class="pi pi-image text-3xl text-slate-300 mb-2"></i>
          <p class="text-xs text-slate-500">Drag image here or click to upload</p>
        </div>
      </div>
      <Button v-if="previewUrl" label="Remove Image" severity="danger" text size="small" class="w-full mt-2" @click="clearImage" />
    </template>
  </Card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Card from 'primevue/card'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'

const props = defineProps<{
  modelValue: File | null
  previewUrl: string | null
  title?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: File | null): void
  (e: 'update:previewUrl', value: string | null): void
}>()

const toast = useToast()
const fileInput = ref<HTMLInputElement | null>(null)

function triggerImageUpload() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) processFile(file)
}

function handleDrop(event: DragEvent) {
  const file = event.dataTransfer?.files[0]
  if (file) processFile(file)
}

function processFile(file: File) {
  if (!file.type.startsWith('image/')) {
    toast.add({ severity: 'warn', summary: 'Invalid File', detail: 'Please upload an image', life: 3000 })
    return
  }
  
  emit('update:modelValue', file)
  
  const reader = new FileReader()
  reader.onload = (e) => {
    emit('update:previewUrl', e.target?.result as string)
  }
  reader.readAsDataURL(file)
}

function clearImage() {
  emit('update:modelValue', null)
  emit('update:previewUrl', null)
  if (fileInput.value) fileInput.value.value = ''
}
</script>
