<template>
  <AppLayout>
    <div class="max-w-[1200px] mx-auto">
      <!-- Header -->
      <div class="mb-6 flex justify-between items-center">
        <div class="flex items-center gap-4">
          <Button 
            icon="pi pi-arrow-left" 
            text 
            rounded 
            @click="goBack"
            v-tooltip.bottom="'Back to Definitions'"
          />
          <div>
            <h1 class="text-3xl font-bold text-slate-800">Edit Configuration</h1>
            <p class="text-slate-500 mt-1">{{ pathData?.ltree_path || 'Loading...' }}</p>
          </div>
        </div>
        <div class="flex gap-2">
          <Button 
            label="Cancel" 
            severity="secondary" 
            text 
            @click="goBack" 
          />
          <Button 
            label="Save Changes" 
            icon="pi pi-save" 
            @click="saveChanges" 
            :loading="isSaving"
            :disabled="!hasChanges"
          />
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="space-y-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="space-y-4">
            <Skeleton height="2rem" width="8rem" />
            <Skeleton height="3rem" />
            <Skeleton height="3rem" />
            <Skeleton height="6rem" />
          </div>
          <div class="space-y-4">
            <Skeleton height="2rem" width="8rem" />
            <Skeleton height="3rem" />
            <Skeleton height="3rem" />
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="loadError" class="p-8 text-center">
        <div class="bg-red-50 border border-red-200 rounded-lg p-6">
          <i class="pi pi-exclamation-triangle text-red-500 text-3xl mb-4"></i>
          <h3 class="text-lg font-semibold text-red-800 mb-2">Failed to Load Configuration</h3>
          <p class="text-red-600 mb-4">{{ loadError }}</p>
          <div class="flex gap-2 justify-center">
            <Button 
              label="Retry" 
              icon="pi pi-refresh" 
              @click="loadData" 
              :loading="isLoading"
            />
            <Button 
              label="Go Back" 
              severity="secondary" 
              @click="goBack" 
            />
          </div>
        </div>
      </div>

      <!-- Edit Form -->
      <div v-else-if="pathData" class="space-y-8">
        <!-- Basic Information Section -->
        <FormSection 
          title="Basic Information" 
          icon="pi pi-info-circle"
          variant="card"
        >
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <FormFieldRenderer 
              :field="{ 
                name: 'id', 
                label: 'ID', 
                type: 'text',
                disabled: true
              }"
              :modelValue="pathData.id"
              :disabled="true"
            />
            <FormFieldRenderer 
              :field="{ 
                name: 'ltree_path', 
                label: 'Path', 
                type: 'text',
                disabled: true
              }"
              :modelValue="pathData.ltree_path"
              :disabled="true"
            />
            <FormFieldRenderer 
              :field="{ 
                name: 'display_path', 
                label: 'Display Name', 
                type: 'text'
              }"
              v-model="formData.display_path"
            />
            <FormFieldRenderer 
              :field="{ 
                name: 'created_at', 
                label: 'Created', 
                type: 'text',
                disabled: true
              }"
              :modelValue="formatDate(pathData.created_at)"
              :disabled="true"
            />
          </div>
        </FormSection>

        <!-- Entity Components Section -->
        <FormSection 
          title="Configuration Components" 
          icon="pi pi-sitemap"
          subtitle="Individual entities that make up this configuration path"
          variant="card"
        >
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Company -->
            <div v-if="entityData.company" class="space-y-4">
              <h4 class="font-semibold text-slate-700 flex items-center gap-2">
                <i class="pi pi-building text-blue-500"></i>
                Company
              </h4>
              <div class="bg-slate-50 p-4 rounded-lg space-y-3">
                <FormFieldRenderer 
                  :field="{ name: 'company_name', label: 'Name', type: 'text' }"
                  v-model="formData.company_name"
                />
                <FormFieldRenderer 
                  :field="{ name: 'company_description', label: 'Description', type: 'textarea' }"
                  v-model="formData.company_description"
                />
                <FormFieldRenderer 
                  :field="{ name: 'company_price', label: 'Base Price', ui_component: 'currency' }"
                  v-model="formData.company_price"
                />
              </div>
            </div>

            <!-- Material -->
            <div v-if="entityData.material" class="space-y-4">
              <h4 class="font-semibold text-slate-700 flex items-center gap-2">
                <i class="pi pi-box text-green-500"></i>
                Material
              </h4>
              <div class="bg-slate-50 p-4 rounded-lg space-y-3">
                <FormFieldRenderer 
                  :field="{ name: 'material_name', label: 'Name', type: 'text' }"
                  v-model="formData.material_name"
                />
                <FormFieldRenderer 
                  :field="{ name: 'material_description', label: 'Description', type: 'textarea' }"
                  v-model="formData.material_description"
                />
                <FormFieldRenderer 
                  :field="{ name: 'material_price', label: 'Base Price', ui_component: 'currency' }"
                  v-model="formData.material_price"
                />
                <!-- Material-specific metadata -->
                <FormFieldRenderer 
                  v-if="entityData.material.validation_rules?.density"
                  :field="{ name: 'material_density', label: 'Density (kg/m³)', type: 'number' }"
                  v-model="formData.material_density"
                />
              </div>
            </div>

            <!-- Opening System -->
            <div v-if="entityData.opening_system" class="space-y-4">
              <h4 class="font-semibold text-slate-700 flex items-center gap-2">
                <i class="pi pi-cog text-orange-500"></i>
                Opening System
              </h4>
              <div class="bg-slate-50 p-4 rounded-lg space-y-3">
                <FormFieldRenderer 
                  :field="{ name: 'opening_system_name', label: 'Name', type: 'text' }"
                  v-model="formData.opening_system_name"
                />
                <FormFieldRenderer 
                  :field="{ name: 'opening_system_description', label: 'Description', type: 'textarea' }"
                  v-model="formData.opening_system_description"
                />
                <FormFieldRenderer 
                  :field="{ name: 'opening_system_price', label: 'Base Price', ui_component: 'currency' }"
                  v-model="formData.opening_system_price"
                />
              </div>
            </div>

            <!-- System Series -->
            <div v-if="entityData.system_series" class="space-y-4">
              <h4 class="font-semibold text-slate-700 flex items-center gap-2">
                <i class="pi pi-sitemap text-purple-500"></i>
                System Series
              </h4>
              <div class="bg-slate-50 p-4 rounded-lg space-y-3">
                <FormFieldRenderer 
                  :field="{ name: 'system_series_name', label: 'Name', type: 'text' }"
                  v-model="formData.system_series_name"
                />
                <FormFieldRenderer 
                  :field="{ name: 'system_series_description', label: 'Description', type: 'textarea' }"
                  v-model="formData.system_series_description"
                />
                <FormFieldRenderer 
                  :field="{ name: 'system_series_price', label: 'Base Price', ui_component: 'currency' }"
                  v-model="formData.system_series_price"
                />
                <!-- System Series specific metadata -->
                <div class="grid grid-cols-2 gap-3">
                  <FormFieldRenderer 
                    v-if="entityData.system_series.validation_rules?.width"
                    :field="{ name: 'system_series_width', label: 'Width (mm)', type: 'number' }"
                    v-model="formData.system_series_width"
                  />
                  <FormFieldRenderer 
                    v-if="entityData.system_series.validation_rules?.number_of_chambers"
                    :field="{ name: 'system_series_chambers', label: 'Chambers', type: 'number' }"
                    v-model="formData.system_series_chambers"
                  />
                  <FormFieldRenderer 
                    v-if="entityData.system_series.validation_rules?.u_value"
                    :field="{ name: 'system_series_u_value', label: 'U-Value', type: 'number' }"
                    v-model="formData.system_series_u_value"
                  />
                  <FormFieldRenderer 
                    v-if="entityData.system_series.validation_rules?.number_of_seals"
                    :field="{ name: 'system_series_seals', label: 'Seals', type: 'number' }"
                    v-model="formData.system_series_seals"
                  />
                </div>
                <FormFieldRenderer 
                  v-if="entityData.system_series.validation_rules?.characteristics"
                  :field="{ name: 'system_series_characteristics', label: 'Characteristics', type: 'textarea' }"
                  v-model="formData.system_series_characteristics"
                />
              </div>
            </div>

            <!-- Colors -->
            <div v-if="entityData.colors && entityData.colors.length > 0" class="space-y-4 lg:col-span-2">
              <h4 class="font-semibold text-slate-700 flex items-center gap-2">
                <i class="pi pi-palette text-pink-500"></i>
                Colors ({{ entityData.colors.length }})
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div 
                  v-for="(color, index) in entityData.colors" 
                  :key="color.id"
                  class="bg-slate-50 p-4 rounded-lg space-y-3"
                >
                  <div class="flex items-center gap-2">
                    <div 
                      class="w-4 h-4 rounded-full border border-slate-300"
                      :style="{ backgroundColor: getColorValue(color) }"
                    ></div>
                    <span class="font-medium">{{ color.name }}</span>
                  </div>
                  <FormFieldRenderer 
                    :field="{ name: `color_${index}_name`, label: 'Name', type: 'text' }"
                    v-model="formData[`color_${index}_name`]"
                  />
                  <FormFieldRenderer 
                    :field="{ name: `color_${index}_price`, label: 'Price Impact', ui_component: 'currency' }"
                    v-model="formData[`color_${index}_price`]"
                  />
                  <FormFieldRenderer 
                    v-if="color.validation_rules?.code"
                    :field="{ name: `color_${index}_code`, label: 'Color Code', type: 'text' }"
                    v-model="formData[`color_${index}_code`]"
                  />
                  <FormFieldRenderer 
                    v-if="color.validation_rules?.has_lamination !== undefined"
                    :field="{ name: `color_${index}_lamination`, label: 'Has Lamination', type: 'boolean' }"
                    v-model="formData[`color_${index}_lamination`]"
                  />
                </div>
              </div>
            </div>
          </div>
        </FormSection>

        <!-- Technical Information Section -->
        <FormSection 
          title="Technical Information" 
          icon="pi pi-cog"
          subtitle="Technical specifications and metadata"
          variant="card"
        >
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <FormFieldRenderer 
              :field="{ name: 'total_price', label: 'Total Price', ui_component: 'currency', disabled: true }"
              :modelValue="calculateTotalPrice()"
              :disabled="true"
            />
            <FormFieldRenderer 
              :field="{ name: 'total_weight', label: 'Total Weight (kg)', type: 'number', disabled: true }"
              :modelValue="calculateTotalWeight()"
              :disabled="true"
            />
          </div>
        </FormSection>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { productDefinitionService } from '@/services/productDefinitionService'
import { parseApiError } from '@/utils/errorHandler'

// Components
import AppLayout from '@/components/layout/AppLayout.vue'
import FormSection from '@/components/common/FormSection.vue'
import FormFieldRenderer from '@/components/common/FormFieldRenderer.vue'
import Button from 'primevue/button'
import Skeleton from 'primevue/skeleton'

const route = useRoute()
const router = useRouter()
const toast = useToast()

// State
const isLoading = ref(true)
const isSaving = ref(false)
const loadError = ref<string | null>(null)
const pathData = ref<any>(null)
const entityData = ref<any>({})
const formData = ref<Record<string, any>>({})
const originalData = ref<Record<string, any>>({})

// Computed
const hasChanges = computed(() => {
  return JSON.stringify(formData.value) !== JSON.stringify(originalData.value)
})

// Methods
async function loadData() {
  isLoading.value = true
  loadError.value = null
  
  try {
    const scope = route.params.scope as string
    const pathId = route.params.pathId as string
    
    if (!pathId) {
      throw new Error('Path ID is required')
    }
    
    // Load path data and related entities
    const response = await productDefinitionService.getPathDetails(parseInt(pathId))
    
    if (!response.success) {
      throw new Error('Failed to load path details')
    }
    
    pathData.value = response.path
    entityData.value = response.path.entities || {}
    
    // Initialize form data
    initializeFormData()
    
  } catch (error) {
    const apiError = parseApiError(error)
    loadError.value = apiError.message
    console.error('Failed to load path data:', error)
  } finally {
    isLoading.value = false
  }
}

function initializeFormData() {
  const data: Record<string, any> = {}
  
  // Basic information
  data.display_path = pathData.value?.display_path || ''
  
  // Entity data
  if (entityData.value.company) {
    data.company_name = entityData.value.company.name
    data.company_description = entityData.value.company.description
    data.company_price = parseFloat(entityData.value.company.price_impact_value || '0')
  }
  
  if (entityData.value.material) {
    data.material_name = entityData.value.material.name
    data.material_description = entityData.value.material.description
    data.material_price = parseFloat(entityData.value.material.price_impact_value || '0')
    data.material_density = entityData.value.material.validation_rules?.density
  }
  
  if (entityData.value.opening_system) {
    data.opening_system_name = entityData.value.opening_system.name
    data.opening_system_description = entityData.value.opening_system.description
    data.opening_system_price = parseFloat(entityData.value.opening_system.price_impact_value || '0')
  }
  
  if (entityData.value.system_series) {
    const series = entityData.value.system_series
    data.system_series_name = series.name
    data.system_series_description = series.description
    data.system_series_price = parseFloat(series.price_impact_value || '0')
    data.system_series_width = series.validation_rules?.width
    data.system_series_chambers = series.validation_rules?.number_of_chambers
    data.system_series_u_value = series.validation_rules?.u_value
    data.system_series_seals = series.validation_rules?.number_of_seals
    data.system_series_characteristics = series.validation_rules?.characteristics
  }
  
  if (entityData.value.colors) {
    entityData.value.colors.forEach((color: any, index: number) => {
      data[`color_${index}_name`] = color.name
      data[`color_${index}_price`] = parseFloat(color.price_impact_value || '0')
      data[`color_${index}_code`] = color.validation_rules?.code
      data[`color_${index}_lamination`] = color.validation_rules?.has_lamination
    })
  }
  
  formData.value = data
  originalData.value = { ...data }
}

function calculateTotalPrice(): number {
  let total = 0
  total += formData.value.company_price || 0
  total += formData.value.material_price || 0
  total += formData.value.opening_system_price || 0
  total += formData.value.system_series_price || 0
  
  // Add color prices
  if (entityData.value.colors) {
    entityData.value.colors.forEach((_: any, index: number) => {
      total += formData.value[`color_${index}_price`] || 0
    })
  }
  
  return total
}

function calculateTotalWeight(): number {
  // This would be calculated based on actual weight formulas
  return 45.2 // Placeholder
}

function getColorValue(color: any): string {
  // Simple color mapping - in real app, you'd have proper color values
  const colorMap: Record<string, string> = {
    'White': '#FFFFFF',
    'Black': '#000000',
    'Brown': '#8B4513',
    'Grey': '#808080',
    'Blue': '#0000FF'
  }
  return colorMap[color.name] || '#CCCCCC'
}

function formatDate(dateString: string): string {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString()
}

async function saveChanges() {
  isSaving.value = true
  
  try {
    // Here you would implement the actual save logic
    // This would involve updating multiple entities through the API
    
    // Simulate save delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Configuration updated successfully',
      life: 3000
    })
    
    // Update original data to reflect saved state
    originalData.value = { ...formData.value }
    
  } catch (error) {
    const apiError = parseApiError(error)
    toast.add({
      severity: 'error',
      summary: 'Save Error',
      detail: apiError.message,
      life: 5000
    })
  } finally {
    isSaving.value = false
  }
}

function goBack() {
  const scope = route.params.scope as string
  router.push({
    name: 'ProfileDefinitions',
    params: { scope }
  })
}

// Lifecycle
onMounted(loadData)
</script>

<style scoped>
/* Custom styles if needed */
</style>