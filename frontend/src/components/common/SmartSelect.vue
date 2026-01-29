<template>
  <Select
    :id="id"
    :modelValue="modelValue"
    @update:modelValue="handleUpdate"
    :options="options"
    :optionLabel="optionLabel"
    :optionValue="optionValue"
    :placeholder="placeholder"
    :class="class"
    :showClear="showClear"
    :disabled="disabled"
    :loading="loading"
    v-bind="$attrs"
    @change="$emit('change', $event)"
    @focus="$emit('focus', $event)"
    @blur="$emit('blur', $event)"
  >
    <template v-for="(_, slot) in $slots" v-slot:[slot]="scope">
      <slot :name="slot" v-bind="scope" />
    </template>
  </Select>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import Select from 'primevue/select'
import { useAutoSelect } from '@/composables/useAutoSelect'

interface Props {
  id?: string
  modelValue?: any
  options: any[]
  optionLabel?: string
  optionValue?: string
  placeholder?: string
  class?: string
  showClear?: boolean
  disabled?: boolean
  loading?: boolean
  autoSelectSingle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showClear: true,
  autoSelectSingle: true,
  placeholder: 'Select...'
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
  'change': [event: any]
  'focus': [event: any]
  'blur': [event: any]
  'auto-selected': [value: any]
}>()

// Computed to get the actual value from options based on optionValue
const resolvedOptions = computed(() => {
  if (!Array.isArray(props.options)) return []
  return props.options
})

// Use the auto-select composable
useAutoSelect({
  options: toRef(props, 'options'),
  modelValue: toRef(props, 'modelValue'),
  optionValue: toRef(props, 'optionValue'),
  autoSelectSingle: toRef(props, 'autoSelectSingle'),
  disabled: toRef(props, 'disabled'),
  isMultiSelect: false
}, emit)

function handleUpdate(value: any) {
  emit('update:modelValue', value)
}
</script>