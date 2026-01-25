<template>
  <Card class="mb-4">
    <template #title>Configuration Form</template>
    <template #content>
      <div v-if="loading" class="space-y-4">
        <Skeleton height="60px" v-for="i in 5" :key="i" />
      </div>

      <div v-else-if="schema" class="space-y-6">
        <div v-for="section in schema.sections" :key="section.name" class="form-section">
          <h3 class="text-lg font-semibold mb-3">{{ section.label }}</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div 
              v-for="field in section.fields" 
              :key="field.name"
              v-show="fieldVisibility[field.name] !== false"
              class="field-item"
            >
              <label :for="field.name" class="block font-medium mb-2">
                {{ field.label }}
                <span v-if="field.required" class="text-red-500">*</span>
              </label>

              <!-- Text Input -->
              <InputText
                v-if="field.ui_component === 'text'"
                :id="field.name"
                v-model="model[field.name]"
                :placeholder="field.description"
                class="w-full"
                @blur="validateField(field.name)"
              />

              <!-- Number Input -->
              <InputNumber
                v-else-if="field.ui_component === 'number'"
                :id="field.name"
                v-model="model[field.name]"
                class="w-full"
                @blur="validateField(field.name)"
              />

              <!-- Dropdown -->
              <Dropdown
                v-else-if="field.ui_component === 'dropdown'"
                :id="field.name"
                v-model="model[field.name]"
                :options="field.options || []"
                :placeholder="`Select ${field.label}`"
                class="w-full"
                @change="validateField(field.name)"
              />

              <!-- Checkbox -->
              <Checkbox
                v-else-if="field.ui_component === 'checkbox'"
                :id="field.name"
                v-model="model[field.name]"
                :binary="true"
                @change="validateField(field.name)"
              />

              <!-- Error Message -->
              <small v-if="fieldErrors[field.name]" class="text-red-500">
                {{ fieldErrors[field.name] }}
              </small>
            </div>
          </div>
        </div>

        <div class="flex gap-2">
          <Button 
            label="Save Configuration" 
            icon="pi pi-save"
            @click="handleSubmit"
            :loading="saving"
            :disabled="!isValid"
          />
          <Button 
            label="Clear Form" 
            icon="pi pi-times"
            @click="handleClear"
            severity="secondary"
            outlined
          />
        </div>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import Skeleton from 'primevue/skeleton'
import { useFormValidation } from '@/composables/useFormValidation'

const props = defineProps({
  schema: {
    type: Object as PropType<any>,
    default: null
  },
  modelValue: {
    type: Object as PropType<Record<string, any>>,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  saving: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'clear'])

const model = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Setup validation using the composable
const schemaRef = computed(() => props.schema)
const { fieldErrors, fieldVisibility, isValid, validateField, validateAll, clearErrors } = 
  useFormValidation(schemaRef, model)

function handleSubmit() {
  if (validateAll()) {
    emit('submit', model.value)
  }
}

function handleClear() {
  clearErrors()
  emit('clear')
}
</script>

<style scoped>
.form-section {
  padding: 1rem;
  background: #f8fafc;
  border-radius: 0.5rem;
}

.field-item {
  margin-bottom: 0;
}
</style>
