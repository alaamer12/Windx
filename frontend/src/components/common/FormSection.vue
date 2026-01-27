<template>
  <div :class="containerClasses">
    <div v-if="title" class="mb-4 flex justify-between items-center">
      <div>
        <h3 :class="titleClasses">
          <i v-if="icon" :class="[icon, 'mr-2 opacity-75']"></i>
          {{ title }}
        </h3>
        <p v-if="subtitle" class="text-sm text-slate-500 mt-1">{{ subtitle }}</p>
      </div>
      <slot name="actions"></slot>
    </div>
    <div :class="contentClasses">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title?: string
  subtitle?: string
  icon?: string
  variant?: 'default' | 'inline' | 'card' | 'transparent'
}>(), {
  variant: 'default'
})

const containerClasses = computed(() => {
  switch (props.variant) {
    case 'card':
      return 'bg-white border border-slate-200 rounded-xl p-6 shadow-sm' 
    case 'default':
      // Standard gray background block (used in DynamicForm)
      return 'p-4 bg-slate-50 rounded-lg border border-slate-100'
    case 'inline':
      // Separator style (used definitions)
      return 'border-t border-slate-200 pt-4 mt-4'
    case 'transparent':
      return ''
    default:
      return ''
  }
})

const titleClasses = computed(() => {
  switch (props.variant) {
    case 'inline':
      return 'text-sm font-bold text-slate-500 uppercase tracking-wide'
    default:
      return 'text-lg font-semibold text-slate-800'
  }
})

const contentClasses = computed(() => {
  // Add specific layout classes here if needed, or leave to parent
  return ''
})
</script>
