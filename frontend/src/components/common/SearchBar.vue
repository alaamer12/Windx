<template>
  <div class="search-bar">
    <!-- Main Search Input -->
    <div class="flex items-center gap-2 mb-3">
      <div class="flex-1 relative">
        <IconField iconPosition="left">
          <InputIcon class="pi pi-search" />
          <InputText
            v-model="searchQuery"
            placeholder="Search across all columns..."
            class="w-full"
            @input="onSearchInput"
            @keyup.escape="clearSearch"
          />
        </IconField>
        <Button
          v-if="searchQuery"
          icon="pi pi-times"
          class="absolute right-2 top-1/2 transform -translate-y-1/2"
          text
          rounded
          size="small"
          @click="clearSearch"
          v-tooltip.top="'Clear search'"
        />
      </div>
      
      <Button
        :icon="showAdvancedSearch ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
        :label="showAdvancedSearch ? 'Hide Filters' : 'Show Filters'"
        @click="toggleAdvancedSearch"
        outlined
        size="small"
      />
      
      <Button
        v-if="isSearchActive"
        icon="pi pi-download"
        label="Export"
        @click="exportResults"
        severity="secondary"
        outlined
        size="small"
        v-tooltip.top="'Export filtered results'"
      />
    </div>

    <!-- Search Stats -->
    <div v-if="isSearchActive" class="flex items-center justify-between mb-3 text-sm">
      <div class="flex items-center gap-4">
        <span class="text-gray-600">
          Showing {{ searchStats.filteredRecords }} of {{ searchStats.totalRecords }} records
        </span>
        <Badge
          v-if="searchStats.hiddenRecords > 0"
          :value="`${searchStats.hiddenRecords} hidden`"
          severity="secondary"
        />
      </div>
      
      <div class="flex items-center gap-2">
        <Button
          label="Clear All"
          icon="pi pi-times"
          @click="clearAll"
          text
          size="small"
          severity="secondary"
        />
      </div>
    </div>

    <!-- Advanced Search Panel -->
    <div v-if="showAdvancedSearch" class="advanced-search-panel">
      <Divider align="left">
        <span class="text-sm font-medium text-gray-600">Column Filters</span>
      </Divider>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="header in headers"
          :key="header"
          class="flex flex-col gap-1"
        >
          <label class="text-xs font-medium text-gray-600">{{ header }}</label>
          <div class="relative">
            <InputText
              :modelValue="columnFilters[header] || ''"
              @update:modelValue="(value) => setColumnFilter(header, value)"
              :placeholder="`Filter ${header}...`"
              class="w-full text-sm"
              size="small"
            />
            <Button
              v-if="columnFilters[header]"
              icon="pi pi-times"
              class="absolute right-1 top-1/2 transform -translate-y-1/2"
              text
              rounded
              size="small"
              @click="setColumnFilter(header, '')"
            />
          </div>
        </div>
      </div>
      
      <div v-if="searchStats.activeFiltersCount > 0" class="mt-3 flex items-center gap-2">
        <span class="text-xs text-gray-500">Active filters:</span>
        <div class="flex flex-wrap gap-1">
          <Chip
            v-for="[header, value] in activeFilters"
            :key="header"
            :label="`${header}: ${value}`"
            removable
            @remove="setColumnFilter(header, '')"
            class="text-xs"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import Badge from 'primevue/badge'
import Divider from 'primevue/divider'
import Chip from 'primevue/chip'
import type { SearchStats } from '@/composables/useTableSearch'

interface Props {
  searchQuery: string
  columnFilters: Record<string, string>
  showAdvancedSearch: boolean
  headers: string[]
  searchStats: SearchStats
  isSearchActive: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:searchQuery': [value: string]
  'update:columnFilters': [filters: Record<string, string>]
  'update:showAdvancedSearch': [show: boolean]
  'export': []
  'clear-search': []
  'clear-all': []
}>()

const searchQuery = computed({
  get: () => props.searchQuery,
  set: (value) => emit('update:searchQuery', value)
})

const columnFilters = computed({
  get: () => props.columnFilters,
  set: (value) => emit('update:columnFilters', value)
})

const showAdvancedSearch = computed({
  get: () => props.showAdvancedSearch,
  set: (value) => emit('update:showAdvancedSearch', value)
})

const activeFilters = computed(() => {
  return Object.entries(props.columnFilters).filter(([_, value]) => value && value.trim())
})

function onSearchInput(event: Event) {
  const target = event.target as HTMLInputElement
  searchQuery.value = target.value
}

function setColumnFilter(header: string, value: string) {
  const newFilters = { ...props.columnFilters }
  if (value && value.trim()) {
    newFilters[header] = value
  } else {
    delete newFilters[header]
  }
  emit('update:columnFilters', newFilters)
}

function toggleAdvancedSearch() {
  showAdvancedSearch.value = !showAdvancedSearch.value
}

function clearSearch() {
  emit('clear-search')
}

function clearAll() {
  emit('clear-all')
}

function exportResults() {
  emit('export')
}
</script>

<style scoped>
.search-bar {
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.advanced-search-panel {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #f3f4f6;
}

/* Search term highlighting */
:deep(.search-term-highlight) {
  background-color: #fef3c7;
  color: #92400e;
  padding: 0 0.25rem;
  border-radius: 0.25rem;
  font-weight: 500;
}

/* Row highlighting animation */
@keyframes searchHighlight {
  0% {
    background-color: rgba(251, 191, 36, 0.3);
  }
  100% {
    background-color: transparent;
  }
}

:deep(.search-highlight) {
  background-color: rgba(254, 243, 199, 0.5) !important;
  animation: searchHighlight 0.6s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Utility classes */
.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-between {
  justify-content: space-between;
}

.gap-2 {
  gap: 0.5rem;
}

.gap-3 {
  gap: 0.75rem;
}

.gap-4 {
  gap: 1rem;
}

.mb-3 {
  margin-bottom: 0.75rem;
}

.mt-3 {
  margin-top: 0.75rem;
}

.mt-4 {
  margin-top: 1rem;
}

.flex-1 {
  flex: 1 1 0%;
}

.flex-wrap {
  flex-wrap: wrap;
}

.relative {
  position: relative;
}

.absolute {
  position: absolute;
}

.right-1 {
  right: 0.25rem;
}

.right-2 {
  right: 0.5rem;
}

.top-1\/2 {
  top: 50%;
}

.transform {
  transform: var(--tw-transform);
}

.-translate-y-1\/2 {
  --tw-translate-y: -50%;
  transform: translate(var(--tw-translate-x), var(--tw-translate-y)) rotate(var(--tw-rotate)) skewX(var(--tw-skew-x)) skewY(var(--tw-skew-y)) scaleX(var(--tw-scale-x)) scaleY(var(--tw-scale-y));
}

.w-full {
  width: 100%;
}

.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.text-xs {
  font-size: 0.75rem;
  line-height: 1rem;
}

.font-medium {
  font-weight: 500;
}

.text-gray-600 {
  color: #4b5563;
}

.text-gray-500 {
  color: #6b7280;
}

.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

@media (min-width: 768px) {
  .md\:grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .lg\:grid-cols-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.flex-col {
  flex-direction: column;
}

.gap-1 {
  gap: 0.25rem;
}
</style>