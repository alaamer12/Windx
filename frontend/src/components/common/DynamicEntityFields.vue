<template>
  <div class="dynamic-entity-fields">
    <!-- Core Entity Fields -->
    <div class="core-fields space-y-6">
      <!-- Name Field -->
      <FormFieldRenderer 
        :field="{ 
          name: getFieldName('name'), 
          label: 'Name', 
          type: 'text',
          required: true
        }"
        :model-value="getFieldValue('name')"
        @update:model-value="updateField('name', $event)"
      />

      <!-- Description Field -->
      <FormFieldRenderer 
        :field="{ 
          name: getFieldName('description'), 
          label: 'Description', 
          type: 'textarea'
        }"
        :model-value="getFieldValue('description')"
        @update:model-value="updateField('description', $event)"
      />

      <!-- Image Field -->
      <FormFieldRenderer 
        :field="{ 
          name: getFieldName('image_url'), 
          label: 'Image', 
          ui_component: 'picture-input'
        }"
        :model-value="getFieldValue('image_url')"
        @update:model-value="updateField('image_url', $event)"
      />

      <!-- Price Impact Field -->
      <FormFieldRenderer 
        :field="{ 
          name: getFieldName('price_impact_value'), 
          label: 'Price Impact', 
          ui_component: 'currency'
        }"
        :model-value="getFieldValue('price_impact_value')"
        @update:model-value="updateField('price_impact_value', $event)"
      />
    </div>

    <!-- Dynamic Validation Rules Fields -->
    <div v-if="hasValidationRules" class="validation-fields border-t border-slate-200 pt-8 mt-8">
      <h4 class="text-lg font-bold text-slate-800 mb-6">Technical Specifications</h4>
      <div class="validation-fields-content space-y-6">
        <div 
          v-for="(value, ruleKey) in entity.validation_rules" 
          :key="ruleKey"
          class="validation-field"
        >
          <FormFieldRenderer 
            :field="getValidationRuleField(String(ruleKey), value)"
            :model-value="getValidationRuleValue(String(ruleKey))"
            @update:model-value="updateValidationRule(String(ruleKey), $event)"
          />
        </div>
      </div>
    </div>

    <!-- Dynamic Metadata Fields -->
    <div v-if="hasMetadata" class="metadata-fields border-t border-slate-200 pt-8 mt-8">
      <h4 class="text-lg font-bold text-slate-800 mb-6">Additional Properties</h4>
      <div class="metadata-fields-content space-y-6">
        <div 
          v-for="(value, metaKey) in entity.metadata_" 
          :key="metaKey"
          class="metadata-field"
        >
          <FormFieldRenderer 
            :field="getMetadataField(String(metaKey), value)"
            :model-value="getMetadataValue(String(metaKey))"
            @update:model-value="updateMetadata(String(metaKey), $event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import FormFieldRenderer from '@/components/common/FormFieldRenderer.vue'

// Props
interface Props {
  entity: any
  entityType: string
  modelValue: Record<string, any>
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
}>()

// Computed
const hasValidationRules = computed(() => {
  return props.entity.validation_rules && Object.keys(props.entity.validation_rules).length > 0
})

const hasMetadata = computed(() => {
  return props.entity.metadata_ && Object.keys(props.entity.metadata_).length > 0
})

// Methods
function getFieldName(fieldName: string): string {
  return `${props.entityType}_${fieldName}`
}

function getFieldValue(fieldName: string): any {
  return props.modelValue[getFieldName(fieldName)] || props.entity[fieldName]
}

function updateField(fieldName: string, value: any): void {
  const fullFieldName = getFieldName(fieldName)
  emit('update:modelValue', {
    ...props.modelValue,
    [fullFieldName]: value
  })
}

function getValidationRuleField(ruleKey: string, value: any): any {
  const fieldName = getFieldName(`validation_${ruleKey}`)
  
  // Determine field type based on rule key and value
  let fieldType = 'text'
  let uiComponent = undefined
  
  if (typeof value === 'number') {
    fieldType = 'number'
    uiComponent = 'number'
  } else if (typeof value === 'boolean') {
    fieldType = 'boolean'
    uiComponent = 'checkbox'
  } else if (ruleKey.includes('price') || ruleKey.includes('cost')) {
    uiComponent = 'currency'
  } else if (ruleKey.includes('description') || ruleKey.includes('characteristics')) {
    fieldType = 'textarea'
  }
  
  return {
    name: fieldName,
    label: formatLabel(ruleKey),
    type: fieldType,
    ui_component: uiComponent
  }
}

function getValidationRuleValue(ruleKey: string): any {
  const fieldName = getFieldName(`validation_${ruleKey}`)
  return props.modelValue[fieldName] || props.entity.validation_rules?.[ruleKey]
}

function updateValidationRule(ruleKey: string, value: any): void {
  const fieldName = getFieldName(`validation_${ruleKey}`)
  emit('update:modelValue', {
    ...props.modelValue,
    [fieldName]: value
  })
}

function getMetadataField(metaKey: string, value: any): any {
  const fieldName = getFieldName(`metadata_${metaKey}`)
  
  // Determine field type based on metadata key and value
  let fieldType = 'text'
  let uiComponent = undefined
  
  if (typeof value === 'number') {
    fieldType = 'number'
    uiComponent = 'number'
  } else if (typeof value === 'boolean') {
    fieldType = 'boolean'
    uiComponent = 'checkbox'
  } else if (Array.isArray(value)) {
    fieldType = 'text'
    // Convert array to comma-separated string for editing
  } else if (typeof value === 'object') {
    fieldType = 'textarea'
    // Convert object to JSON string for editing
  }
  
  return {
    name: fieldName,
    label: formatLabel(metaKey),
    type: fieldType,
    ui_component: uiComponent
  }
}

function getMetadataValue(metaKey: string): any {
  const fieldName = getFieldName(`metadata_${metaKey}`)
  const currentValue = props.modelValue[fieldName]
  
  if (currentValue !== undefined) {
    return currentValue
  }
  
  const originalValue = props.entity.metadata_?.[metaKey]
  
  // Convert complex types to editable strings
  if (Array.isArray(originalValue)) {
    return originalValue.join(', ')
  } else if (typeof originalValue === 'object' && originalValue !== null) {
    return JSON.stringify(originalValue, null, 2)
  }
  
  return originalValue
}

function updateMetadata(metaKey: string, value: any): void {
  const fieldName = getFieldName(`metadata_${metaKey}`)
  
  // Convert string values back to appropriate types if needed
  let processedValue = value
  const originalValue = props.entity.metadata_?.[metaKey]
  
  if (Array.isArray(originalValue) && typeof value === 'string') {
    processedValue = value.split(',').map(item => item.trim()).filter(item => item)
  } else if (typeof originalValue === 'object' && originalValue !== null && typeof value === 'string') {
    try {
      processedValue = JSON.parse(value)
    } catch (e) {
      // Keep as string if JSON parsing fails
      processedValue = value
    }
  }
  
  emit('update:modelValue', {
    ...props.modelValue,
    [fieldName]: processedValue
  })
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
    .replace(/Id$/, 'ID')
    .replace(/Url$/, 'URL')
}
</script>

<style scoped>
.dynamic-entity-fields {
  /* Component-specific styles if needed */
}

.core-fields {
  /* Core fields styling */
}

.validation-fields,
.metadata-fields {
  /* Dynamic fields styling */
}

.validation-field,
.metadata-field {
  /* Individual field styling */
}
</style>