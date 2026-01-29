import { watch, nextTick, type Ref } from 'vue'

export interface UseAutoSelectOptions {
  options: Ref<any[]>
  modelValue: Ref<any>
  optionValue?: Ref<string | undefined>
  autoSelectSingle?: Ref<boolean>
  disabled?: Ref<boolean>
  isMultiSelect?: boolean
}

interface UseAutoSelectReturn {
  // No return values needed, just side effects
}

/**
 * Composable for auto-selecting single options in dropdown components
 * 
 * @param options - Configuration object with reactive references
 * @param emit - Emit function from the component
 */
export function useAutoSelect(
  options: UseAutoSelectOptions,
  emit: (event: 'update:modelValue' | 'auto-selected', value: any) => void
): UseAutoSelectReturn {

  const {
    options: optionsRef,
    modelValue,
    optionValue,
    autoSelectSingle,
    disabled,
    isMultiSelect = false
  } = options

  // Auto-select single option when there's only one choice
  watch([optionsRef, modelValue], async ([newOptions, currentValue]) => {
    // Early returns for invalid states
    if (!autoSelectSingle?.value) return
    if (!newOptions || !Array.isArray(newOptions)) return
    if (disabled?.value) return
    if (newOptions.length !== 1) return

    // Check if there's no current selection
    const hasNoSelection = isMultiSelect 
      ? !currentValue || (Array.isArray(currentValue) && currentValue.length === 0)
      : !currentValue

    if (!hasNoSelection) return

    // Wait for next tick to ensure DOM is updated
    await nextTick()

    const singleOption = newOptions[0]
    let valueToSelect: any

    // Extract the value based on optionValue prop
    if (optionValue?.value && typeof singleOption === 'object') {
      valueToSelect = singleOption[optionValue.value]
    } else {
      valueToSelect = singleOption
    }

    // For multi-select, wrap in array
    const finalValue = isMultiSelect ? [valueToSelect] : valueToSelect

    // Emit the updates
    emit('update:modelValue', finalValue)
    emit('auto-selected', finalValue)
  }, { immediate: true })

  return {}
}