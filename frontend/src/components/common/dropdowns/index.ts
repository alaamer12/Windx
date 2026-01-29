// Reusable dropdown components with auto-selection functionality
import type { Ref } from 'vue'

export { default as SmartSelect } from '../SmartSelect.vue'
export { default as SmartMultiSelect } from '../SmartMultiSelect.vue'
export { default as ColorChipMultiSelect } from '../ColorChipMultiSelect.vue'

// Auto-selection composable
export { useAutoSelect } from '../../composables/useAutoSelect'

// Type definitions for dropdown components
export interface DropdownOption {
  id?: any
  value?: any
  name?: string
  label?: string
  [key: string]: any
}

export interface SmartSelectProps {
  id?: string
  modelValue?: any
  options: DropdownOption[]
  optionLabel?: string
  optionValue?: string
  placeholder?: string
  class?: string
  showClear?: boolean
  disabled?: boolean
  loading?: boolean
  autoSelectSingle?: boolean
}

export interface SmartMultiSelectProps {
  id?: string
  modelValue?: any[]
  options: DropdownOption[]
  optionLabel?: string
  optionValue?: string
  placeholder?: string
  class?: string
  disabled?: boolean
  loading?: boolean
  autoSelectSingle?: boolean
}

export interface UseAutoSelectOptions {
  options: Ref<any[]>
  modelValue: Ref<any>
  optionValue?: Ref<string | undefined>
  autoSelectSingle?: Ref<boolean>
  disabled?: Ref<boolean>
  isMultiSelect?: boolean
}