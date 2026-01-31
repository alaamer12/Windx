<template>
  <MultiSelect
    :id="id"
    :modelValue="modelValue"
    @update:modelValue="handleUpdate"
    :options="options"
    :optionLabel="optionLabel"
    :optionValue="optionValue"
    :placeholder="placeholder"
    :class="class"
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
  </MultiSelect>
</template>

<script setup lang="ts">
import { toRef } from 'vue'
import MultiSelect from 'primevue/multiselect'
import { useAutoSelect } from '@/composables/useAutoSelect'

interface Props {
  id?: string
  modelValue?: any[]
  options: any[]
  optionLabel?: string
  optionValue?: string
  placeholder?: string
  class?: string
  disabled?: boolean
  loading?: boolean
  autoSelectSingle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoSelectSingle: true,
  placeholder: 'Select items...'
})

const emit = defineEmits<{
  'update:modelValue': [value: any[]]
  'change': [event: any]
  'focus': [event: any]
  'blur': [event: any]
  'auto-selected': [value: any[]]
}>()

// Use the auto-select composable
const composableEmit = (event: 'update:modelValue' | 'auto-selected', value: any) => {
  if (event === 'update:modelValue') {
    emit('update:modelValue', value)
  } else if (event === 'auto-selected') {
    emit('auto-selected', value)
  }
}

useAutoSelect({
  options: toRef(props, 'options'),
  modelValue: toRef(props, 'modelValue'),
  optionValue: toRef(props, 'optionValue'),
  autoSelectSingle: toRef(props, 'autoSelectSingle'),
  disabled: toRef(props, 'disabled'),
  isMultiSelect: true
}, composableEmit)

function handleUpdate(value: any[]) {
  emit('update:modelValue', value || [])
}
</script>