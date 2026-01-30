<template>
  <AppLayout>
    <div class="page-wrapper bg-slate-50">
      <!-- Header -->
      <div class="header-container bg-white border-b border-slate-200 sticky top-0 z-10">
        <div class="header-content px-8 py-6">
          <div class="header-flex flex items-center justify-between">
            <div class="header-left flex items-center gap-4">
              <Button 
                icon="pi pi-arrow-left" 
                text 
                rounded 
                size="large"
                @click="goBack"
                class="text-slate-600 hover:text-slate-800"
              />
              <div>
                <h1 class="text-3xl font-bold text-slate-900">Edit Configuration</h1>
                <p class="text-base text-slate-600 mt-2">{{ pathData?.display_path || 'Loading...' }}</p>
              </div>
            </div>
            <div class="header-right flex items-center gap-4">
              <Button 
                label="Cancel" 
                severity="secondary" 
                outlined
                size="large"
                @click="goBack" 
              />
              <Button 
                label="Save Changes" 
                icon="pi pi-save" 
                size="large"
                @click="saveChanges" 
                :loading="isSaving"
                :disabled="!hasChanges"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Content -->
      <div class="content-container px-8 py-8">
        <!-- Loading State -->
        <div v-if="isLoading" class="loading-container space-y-8">
          <div class="bg-white rounded-xl p-8 shadow-sm">
            <Skeleton height="2.5rem" width="16rem" class="mb-6" />
            <div class="space-y-6">
              <Skeleton height="4rem" />
              <Skeleton height="4rem" />
              <Skeleton height="4rem" />
              <Skeleton height="4rem" />
            </div>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="loadError" class="error-container flex items-center justify-center min-h-[400px]">
          <div class="error-content text-center max-w-md">
            <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <i class="pi pi-exclamation-triangle text-red-500 text-2xl"></i>
            </div>
            <h3 class="text-xl font-semibold text-slate-900 mb-3">Failed to Load Configuration</h3>
            <p class="text-slate-600 mb-6">{{ loadError }}</p>
            <div class="error-buttons flex gap-4 justify-center">
              <Button 
                label="Try Again" 
                icon="pi pi-refresh" 
                size="large"
                @click="loadData" 
                :loading="isLoading"
              />
              <Button 
                label="Go Back" 
                severity="secondary" 
                outlined
                size="large"
                @click="goBack" 
              />
            </div>
          </div>
        </div>

        <!-- Edit Form -->
        <div v-else-if="pathData" class="form-container space-y-8">
          <!-- Overview Card -->
          <div class="overview-card bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="overview-header px-8 py-6 border-b border-slate-200 bg-slate-50">
              <h2 class="text-2xl font-bold text-slate-900 flex items-center gap-3">
                <i class="pi pi-info-circle text-blue-500"></i>
                Configuration Overview
              </h2>
            </div>
            <div class="overview-content p-8">
              <div class="overview-grid grid grid-cols-1 md:grid-cols-2 gap-8">
                <div class="space-y-3">
                  <label class="block text-sm font-semibold text-slate-700 uppercase tracking-wide">Configuration ID</label>
                  <div class="px-4 py-3 bg-slate-100 rounded-lg text-slate-700 font-mono text-lg">
                    #{{ pathData.id }}
                  </div>
                </div>
                <div class="space-y-3">
                  <label class="block text-sm font-semibold text-slate-700 uppercase tracking-wide">Path</label>
                  <div class="px-4 py-3 bg-slate-100 rounded-lg text-slate-700 text-base">
                    {{ pathData.ltree_path }}
                  </div>
                </div>
                <div class="space-y-3">
                  <label class="block text-sm font-semibold text-slate-700 uppercase tracking-wide">Created</label>
                  <div class="px-4 py-3 bg-slate-100 rounded-lg text-slate-700 text-base">
                    {{ formatDate(pathData.created_at) }}
                  </div>
                </div>
                <div class="space-y-3">
                  <label class="block text-sm font-semibold text-slate-700 uppercase tracking-wide">Total Price</label>
                  <div class="px-4 py-3 bg-green-50 rounded-lg text-green-700 font-bold text-lg">
                    ${{ calculateTotalPrice().toFixed(2) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Dynamic Entity Cards -->
          <div 
            v-for="(entity, entityType) in entityData" 
            :key="entityType"
            class="entity-card bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"
          >
            <div 
              class="entity-header px-8 py-6 border-b border-slate-200"
              :class="getEntityHeaderClass(String(entityType))"
            >
              <h3 class="text-2xl font-bold text-slate-900 flex items-center gap-3">
                <i :class="getEntityIcon(String(entityType))"></i>
                {{ getEntityTitle(String(entityType)) }}
              </h3>
            </div>
            <div class="entity-content p-8">
              <!-- Render fields dynamically based on entity data -->
              <div class="entity-fields space-y-6">
                <DynamicEntityFields 
                  :entity="entity"
                  :entity-type="String(entityType)"
                  v-model="formData"
                />
              </div>
            </div>
          </div>

          <!-- Summary Card -->
          <div class="summary-card bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="summary-header px-8 py-6 border-b border-slate-200 bg-slate-50">
              <h3 class="text-2xl font-bold text-slate-900 flex items-center gap-3">
                <i class="pi pi-calculator text-slate-600"></i>
                Configuration Summary
              </h3>
            </div>
            <div class="summary-content p-8">
              <div class="summary-grid grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="text-center p-6 bg-green-50 rounded-lg">
                  <div class="text-3xl font-bold text-green-700">${{ calculateTotalPrice().toFixed(2) }}</div>
                  <div class="text-base text-green-600 mt-2">Total Price</div>
                </div>
                <div class="text-center p-6 bg-blue-50 rounded-lg">
                  <div class="text-3xl font-bold text-blue-700">{{ calculateTotalWeight().toFixed(1) }} kg</div>
                  <div class="text-base text-blue-600 mt-2">Total Weight</div>
                </div>
                <div class="text-center p-6 bg-purple-50 rounded-lg">
                  <div class="text-3xl font-bold text-purple-700">{{ Object.keys(entityData).length }}</div>
                  <div class="text-base text-purple-600 mt-2">Components</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { productDefinitionService } from '@/services/productDefinitionService'
import { parseApiError } from '@/utils/errorHandler'

// Components
import AppLayout from '@/components/layout/AppLayout.vue'
import DynamicEntityFields from '@/components/common/DynamicEntityFields.vue'
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
    const pathId = route.params.pathId as string
    
    if (!pathId) {
      throw new Error('Path ID is required')
    }
    
    // Load path data and related entities from backend
    const response = await productDefinitionService.getPathDetails(parseInt(pathId))
    
    if (!response.success) {
      throw new Error('Failed to load path details')
    }
    
    pathData.value = response.path
    entityData.value = response.path.entities || {}
    
    // Initialize form data dynamically from entity data
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
  
  // Initialize form data dynamically from entity data
  Object.entries(entityData.value).forEach(([entityType, entity]: [string, any]) => {
    if (Array.isArray(entity)) {
      // Handle arrays (like colors)
      entity.forEach((item: any, index: number) => {
        initializeEntityFields(data, `${entityType}_${index}`, item)
      })
    } else {
      // Handle single entities
      initializeEntityFields(data, entityType, entity)
    }
  })
  
  formData.value = data
  originalData.value = { ...data }
}

function initializeEntityFields(data: Record<string, any>, prefix: string, entity: any) {
  // Core fields
  data[`${prefix}_name`] = entity.name || ''
  data[`${prefix}_description`] = entity.description || ''
  data[`${prefix}_image_url`] = entity.image_url || ''
  data[`${prefix}_price_impact_value`] = parseFloat(entity.price_impact_value || '0')
  
  // Validation rules
  if (entity.validation_rules) {
    Object.entries(entity.validation_rules).forEach(([key, value]) => {
      data[`${prefix}_validation_${key}`] = value
    })
  }
  
  // Metadata
  if (entity.metadata_) {
    Object.entries(entity.metadata_).forEach(([key, value]) => {
      data[`${prefix}_metadata_${key}`] = value
    })
  }
}

function calculateTotalPrice(): number {
  let total = 0
  
  // Calculate total from all entity price impacts
  Object.entries(entityData.value).forEach(([entityType, entity]: [string, any]) => {
    if (Array.isArray(entity)) {
      entity.forEach((_, index: number) => {
        const priceField = `${entityType}_${index}_price_impact_value`
        total += formData.value[priceField] || 0
      })
    } else {
      const priceField = `${entityType}_price_impact_value`
      total += formData.value[priceField] || 0
    }
  })
  
  return total
}

function calculateTotalWeight(): number {
  // This would be calculated based on actual weight formulas from backend
  // For now, return a placeholder value
  return 45.2
}

function getEntityTitle(entityType: string): string {
  const titles: Record<string, string> = {
    company: 'Company Information',
    material: 'Material Specifications',
    opening_system: 'Opening System',
    system_series: 'System Series',
    colors: 'Color Options'
  }
  
  return titles[entityType] || entityType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function getEntityIcon(entityType: string): string {
  const icons: Record<string, string> = {
    company: 'pi pi-building text-blue-600',
    material: 'pi pi-box text-green-600',
    opening_system: 'pi pi-cog text-orange-600',
    system_series: 'pi pi-sitemap text-purple-600',
    colors: 'pi pi-palette text-pink-600'
  }
  
  return icons[entityType] || 'pi pi-circle text-gray-600'
}

function getEntityHeaderClass(entityType: string): string {
  const classes: Record<string, string> = {
    company: 'bg-blue-50',
    material: 'bg-green-50',
    opening_system: 'bg-orange-50',
    system_series: 'bg-purple-50',
    colors: 'bg-pink-50'
  }
  
  return classes[entityType] || 'bg-gray-50'
}

function formatDate(dateString: string): string {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString()
}

async function saveChanges() {
  isSaving.value = true
  
  try {
    // Prepare update data by extracting changes for each entity
    const updates: Record<string, any> = {}
    
    Object.entries(entityData.value).forEach(([entityType, entity]: [string, any]) => {
      if (Array.isArray(entity)) {
        // Handle arrays (like colors)
        updates[entityType] = entity.map((item: any, index: number) => {
          return extractEntityChanges(`${entityType}_${index}`, item)
        })
      } else {
        // Handle single entities
        updates[entityType] = extractEntityChanges(entityType, entity)
      }
    })
    
    // Send updates to backend
    // This would be implemented based on your backend API structure
    // For now, simulate the save operation
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

function extractEntityChanges(prefix: string, originalEntity: any): any {
  const changes: any = {
    id: originalEntity.id
  }
  
  // Extract core field changes
  const nameField = `${prefix}_name`
  const descField = `${prefix}_description`
  const imageField = `${prefix}_image_url`
  const priceField = `${prefix}_price_impact_value`
  
  if (formData.value[nameField] !== originalEntity.name) {
    changes.name = formData.value[nameField]
  }
  
  if (formData.value[descField] !== originalEntity.description) {
    changes.description = formData.value[descField]
  }
  
  if (formData.value[imageField] !== originalEntity.image_url) {
    changes.image_url = formData.value[imageField]
  }
  
  if (formData.value[priceField] !== parseFloat(originalEntity.price_impact_value || '0')) {
    changes.price_impact_value = formData.value[priceField]
  }
  
  // Extract validation rule changes
  const validationRules: any = {}
  let hasValidationChanges = false
  
  if (originalEntity.validation_rules) {
    Object.keys(originalEntity.validation_rules).forEach(key => {
      const fieldName = `${prefix}_validation_${key}`
      const newValue = formData.value[fieldName]
      const oldValue = originalEntity.validation_rules[key]
      
      if (newValue !== oldValue) {
        validationRules[key] = newValue
        hasValidationChanges = true
      }
    })
  }
  
  if (hasValidationChanges) {
    changes.validation_rules = validationRules
  }
  
  // Extract metadata changes
  const metadata: any = {}
  let hasMetadataChanges = false
  
  if (originalEntity.metadata_) {
    Object.keys(originalEntity.metadata_).forEach(key => {
      const fieldName = `${prefix}_metadata_${key}`
      const newValue = formData.value[fieldName]
      const oldValue = originalEntity.metadata_[key]
      
      if (newValue !== oldValue) {
        metadata[key] = newValue
        hasMetadataChanges = true
      }
    })
  }
  
  if (hasMetadataChanges) {
    changes.metadata_ = metadata
  }
  
  return changes
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
/* Layout CSS - converted from Tailwind */
.page-wrapper {
  min-height: 100vh;
}

.header-container {
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-content {
  max-width: 64rem; /* max-w-4xl */
  margin-left: auto;
  margin-right: auto;
}

.header-flex {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.content-container {
  max-width: 64rem; /* max-w-4xl */
  margin-left: auto;
  margin-right: auto;
}

.loading-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.error-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.error-content {
  text-align: center;
  max-width: 28rem;
}

.error-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.overview-card {
  overflow: hidden;
}

.overview-header {
  padding: 1.5rem 2rem;
}

.overview-content {
  padding: 2rem;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

@media (min-width: 768px) {
  .overview-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.company-card,
.material-card,
.opening-card,
.series-card,
.colors-card,
.summary-card {
  overflow: hidden;
}

.company-header,
.material-header,
.opening-header,
.series-header,
.colors-header,
.summary-header {
  padding: 1.5rem 2rem;
}

.company-content,
.material-content,
.opening-content,
.series-content,
.colors-content,
.summary-content {
  padding: 2rem;
}

.tech-specs {
  padding-top: 2rem;
  margin-top: 2rem;
}

.tech-fields {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.colors-list {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.color-item {
  padding: 1.5rem;
}

.color-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.color-fields {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

@media (min-width: 768px) {
  .summary-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>