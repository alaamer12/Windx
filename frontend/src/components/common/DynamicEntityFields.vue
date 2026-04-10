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
        :disabled="readOnly"
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
        :disabled="readOnly"
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
        :disabled="readOnly"
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
        :disabled="readOnly"
        @update:model-value="updateField('price_impact_value', $event)"
      />
    </div>

    <!-- Dynamic Validation Rules Fields -->
    <div v-if="hasMetadataFields" class="validation-fields border-t border-slate-200 pt-8 mt-8">
      <h4 class="text-lg font-bold text-slate-800 mb-6">Technical Specifications</h4>
      <div class="validation-fields-content space-y-6">
        <div 
          v-for="field in definition.metadata_fields" 
          :key="field.name"
          class="validation-field"
        >
          <FormFieldRenderer 
            :field="getMetadataField(field)"
            :model-value="getMetadataFieldValue(field.name)"
            :disabled="readOnly"
            @update:model-value="updateMetadataField(field.name, $event)"
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
  definition: any
  modelValue: Record<string, any>
  readOnly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readOnly: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
}>()

// Computed
const hasMetadataFields = computed(() => {
  return props.definition?.metadata_fields && props.definition.metadata_fields.length > 0
})

// Methods
function getFieldName(fieldName: string): string {
  return `${props.entityType}_${fieldName}`
}

function getFieldValue(fieldName: string): any {
  const fullFieldName = getFieldName(fieldName)
  // Check if the field exists in modelValue (even if it's empty)
  if (fullFieldName in props.modelValue) {
    return props.modelValue[fullFieldName]
  }
  // Only fallback to entity value if the field hasn't been touched yet
  return props.entity[fieldName]
}

function updateField(fieldName: string, value: any): void {
  const fullFieldName = getFieldName(fieldName)
  emit('update:modelValue', {
    ...props.modelValue,
    [fullFieldName]: value
  })
}

function getMetadataField(field: any): any {
  const fieldName = getFieldName(`validation_${field.name}`)
  
  return {
    name: fieldName,
    label: field.label || formatLabel(field.name),
    type: field.type || 'text',
    ui_component: field.type === 'number' ? 'number' : undefined,
    step: field.step
  }
}

function getMetadataFieldValue(fieldName: string): any {
  const fullFieldName = getFieldName(`validation_${fieldName}`)
  // Check if the field exists in modelValue (even if it's empty)
  if (fullFieldName in props.modelValue) {
    return props.modelValue[fullFieldName]
  }
  // Fallback to entity validation rules
  return props.entity.validation_rules?.[fieldName]
}

function updateMetadataField(fieldName: string, value: any): void {
  const fullFieldName = getFieldName(`validation_${fieldName}`)
  emit('update:modelValue', {
    ...props.modelValue,
    [fullFieldName]: value
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
/* Component styles are handled by parent components and Tailwind classes */
</style>