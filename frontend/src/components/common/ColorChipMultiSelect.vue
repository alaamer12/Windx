<template>
  <MultiSelect 
    v-model="model"
    :options="options"
    :optionLabel="optionLabel"
    :optionValue="optionValue"
    :placeholder="placeholder"
    class="w-full professional-chip-multiselect"
    display="chip"
    v-bind="$attrs"
  >
    <template #chip="slotProps">
      <div 
        class="color-chip"
        :style="getChipStyle(slotProps.value)"
      >
        <span class="color-chip-label">{{ getColorName(slotProps.value) }}</span>
        <button 
          type="button"
          class="color-chip-remove"
          @click.stop="(e) => slotProps.removeCallback(e, slotProps.value)"
          aria-label="Remove color"
        >
          <i class="pi pi-times"></i>
        </button>
      </div>
    </template>
  </MultiSelect>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import MultiSelect from 'primevue/multiselect'
import { useAutoSelect } from '@/composables/useAutoSelect'
import { getColorStyle } from '@/utils/colorUtils'

const props = withDefaults(defineProps<{
  modelValue: any[]
  options: any[]
  optionLabel?: string
  optionValue?: string
  placeholder?: string
  autoSelectSingle?: boolean
}>(), {
  autoSelectSingle: true
})

const emit = defineEmits<{
  'update:modelValue': [value: any[]]
  'auto-selected': [value: any[]]
}>()

const model = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Use the auto-select composable
useAutoSelect({
  options: toRef(props, 'options'),
  modelValue: toRef(props, 'modelValue'),
  optionValue: toRef(props, 'optionValue'),
  autoSelectSingle: toRef(props, 'autoSelectSingle'),
  disabled: computed(() => false), // ColorChipMultiSelect doesn't have disabled prop
  isMultiSelect: true
}, emit)

// Helper to resolve the display label for an option
function getOptionLabel(option: any): string {
  if (option === null || option === undefined) return ''
  if (typeof option !== 'object') return String(option)
  if (props.optionLabel && option[props.optionLabel] !== undefined) return option[props.optionLabel]
  if (option.name !== undefined) return option.name
  if (option.label !== undefined) return option.label
  return String(option)
}

// Helper to resolve the value for comparison
function getOptionValue(option: any): any {
  if (option === null || option === undefined) return null
  if (typeof option !== 'object') return option
  if (props.optionValue && option[props.optionValue] !== undefined) return option[props.optionValue]
  if (option.id !== undefined) return option.id
  if (option.value !== undefined) return option.value
  return option
}

// Find the full option object from a selected value
function findOption(value: any) {
  return props.options.find(opt => getOptionValue(opt) === value)
}

function getColorName(value: any): string {
  const option = findOption(value)
  if (option) return getOptionLabel(option)
  return String(value)
}

function getChipStyle(value: any): { backgroundColor: string; color: string; borderColor: string } {
  const colorName = getColorName(value)
  // Use the reusable color utility following SRP
  return getColorStyle(colorName)
}
</script>

<style scoped>
/* Keep default PrimeVue input padding - don't override */
:deep(.professional-chip-multiselect .p-chip) {
  margin: 0;
  padding: 0;
  background: transparent !important;
  border: none !important;
}

/* Main Color Chip Container - Modern Minimal Design */
.color-chip {
  /* Layout */
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  
  /* Spacing - Compact modern look */
  padding: 0.375rem 0.625rem;
  padding-right: 0.5rem;
  
  /* Visual - Clean minimal border */
  border-radius: 0.375rem;
  border-width: 1px;
  border-style: solid;
  
  /* No shadow - flat modern design */
  box-shadow: none;
  
  /* Typography */
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.25rem;
  
  /* Smooth transition */
  transition: all 0.2s ease;
  
  /* Interaction */
  cursor: default;
  user-select: none;
}

.color-chip:hover {
  /* Subtle opacity change on hover */
  opacity: 0.9;
}

/* Chip Label */
.color-chip-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
  
  /* Smooth text */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Remove Button - Minimal Circle with × */
.color-chip-remove {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  /* Size - small and minimal */
  width: 1rem;
  height: 1rem;
  
  /* Visual - transparent background */
  border-radius: 50%;
  background: transparent;
  border: none;
  padding: 0;
  
  /* Interaction */
  cursor: pointer;
  transition: all 0.2s ease;
  
  /* Icon */
  font-size: 0.75rem;
  opacity: 0.6;
}

.color-chip-remove:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.1);
}

.color-chip-remove:active {
  transform: scale(0.9);
}

.color-chip-remove i {
  pointer-events: none;
  line-height: 1;
}

/* Light background adjustment for remove button */
.color-chip[style*="color: rgb(31, 41, 55)"] .color-chip-remove:hover,
.color-chip[style*="color: #1F2937"] .color-chip-remove:hover {
  background: rgba(0, 0, 0, 0.08);
}

/* Dark background adjustment for remove button */
.color-chip[style*="color: rgb(255, 255, 255)"] .color-chip-remove:hover,
.color-chip[style*="color: #FFFFFF"] .color-chip-remove:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Ensure proper spacing in the multiselect */
:deep(.professional-chip-multiselect .p-multiselect-chip-item) {
  margin: 0.125rem;
}

/* Focus states for accessibility */
.color-chip-remove:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 2px;
  border-radius: 50%;
}
</style>
