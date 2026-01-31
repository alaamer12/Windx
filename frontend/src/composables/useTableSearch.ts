import { ref, computed, watch, nextTick } from 'vue'
import type { Ref } from 'vue'

export interface SearchState {
  searchQuery: string
  columnFilters: Record<string, string>
  showAdvancedSearch: boolean
  searchResults: {
    total: number
    filtered: number
  }
}

export interface SearchStats {
  totalRecords: number
  filteredRecords: number
  hiddenRecords: number
  searchActive: boolean
  globalSearchActive: boolean
  columnFiltersActive: boolean
  activeFiltersCount: number
}

/**
 * Composable for advanced table search and filtering functionality
 * Based on the legacy SearchEngine.js with modern Vue 3 improvements
 */
export function useTableSearch<T extends Record<string, any>>(
  data: Ref<T[]>,
  headers?: Ref<string[]>
) {
  // Search state
  const searchQuery = ref('')
  const columnFilters = ref<Record<string, string>>({})
  const showAdvancedSearch = ref(false)
  const highlightedRows = ref<Set<string>>(new Set())
  
  // Search results
  const searchResults = ref({
    total: 0,
    filtered: 0
  })

  // Computed filtered data
  const filteredData = computed(() => {
    let filtered = [...data.value]
    
    // Update total count
    searchResults.value.total = data.value.length

    // Apply global search query
    if (searchQuery.value && searchQuery.value.trim()) {
      filtered = applyGlobalSearch(filtered, searchQuery.value.trim())
    }

    // Apply column-specific filters
    if (Object.keys(columnFilters.value).length > 0) {
      filtered = applyColumnFilters(filtered)
    }

    // Update filtered count
    searchResults.value.filtered = filtered.length

    return filtered
  })

  // Check if any search is active
  const isSearchActive = computed(() => {
    return !!(searchQuery.value && searchQuery.value.trim()) || 
           Object.values(columnFilters.value).some(filter => filter && filter.trim())
  })

  // Search statistics
  const searchStats = computed<SearchStats>(() => ({
    totalRecords: searchResults.value.total,
    filteredRecords: searchResults.value.filtered,
    hiddenRecords: searchResults.value.total - searchResults.value.filtered,
    searchActive: isSearchActive.value,
    globalSearchActive: !!(searchQuery.value && searchQuery.value.trim()),
    columnFiltersActive: Object.values(columnFilters.value).some(filter => filter && filter.trim()),
    activeFiltersCount: Object.values(columnFilters.value).filter(filter => filter && filter.trim()).length
  }))

  // Current search state
  const searchState = computed<SearchState>(() => ({
    searchQuery: searchQuery.value,
    columnFilters: { ...columnFilters.value },
    showAdvancedSearch: showAdvancedSearch.value,
    searchResults: { ...searchResults.value }
  }))

  /**
   * Apply global search across all columns
   */
  function applyGlobalSearch(items: T[], query: string): T[] {
    const searchTerms = query.toLowerCase().split(/\s+/).filter(term => term.length > 0)
    
    return items.filter(item => {
      // Search across all fields in the item
      const searchableText = Object.values(item)
        .map(value => {
          if (value === null || value === undefined) return ''
          return String(value).toLowerCase()
        })
        .join(' ')

      // Check if all search terms are found
      return searchTerms.every(term => searchableText.includes(term))
    })
  }

  /**
   * Apply column-specific filters
   */
  function applyColumnFilters(items: T[]): T[] {
    return items.filter(item => {
      return Object.entries(columnFilters.value).every(([header, filterValue]) => {
        if (!filterValue || !filterValue.trim()) return true

        const itemValue = item[header]
        if (itemValue === null || itemValue === undefined) return false

        const itemText = String(itemValue).toLowerCase()
        const filterText = filterValue.toLowerCase().trim()

        return itemText.includes(filterText)
      })
    })
  }

  /**
   * Highlight search terms in text
   */
  function highlightSearchTerm(text: string | number | null | undefined, header?: string): string {
    if (!text || text === 'N/A') return String(text || '')

    let highlightedText = String(text)
    const termsToHighlight = new Set<string>()

    // Add global search terms
    if (searchQuery.value && searchQuery.value.trim()) {
      const searchTerms = searchQuery.value.toLowerCase().split(/\s+/).filter(term => term.length > 0)
      searchTerms.forEach(term => termsToHighlight.add(term))
    }

    // Add column-specific filter terms
    if (header && columnFilters.value[header] && columnFilters.value[header].trim()) {
      const filterTerms = columnFilters.value[header].toLowerCase().split(/\s+/).filter(term => term.length > 0)
      filterTerms.forEach(term => termsToHighlight.add(term))
    }

    // Apply highlighting
    termsToHighlight.forEach(term => {
      const regex = new RegExp(`(${escapeRegExp(term)})`, 'gi')
      highlightedText = highlightedText.replace(regex, '<span class="search-term-highlight">$1</span>')
    })

    return highlightedText
  }

  /**
   * Check if a row should be highlighted
   */
  function isRowHighlighted(row: T): boolean {
    if (!isSearchActive.value) return false

    // Check if any field contains search terms
    const searchableText = Object.values(row)
      .map(value => {
        if (value === null || value === undefined) return ''
        return String(value).toLowerCase()
      })
      .join(' ')

    // Check global search
    if (searchQuery.value && searchQuery.value.trim()) {
      const searchTerms = searchQuery.value.toLowerCase().split(/\s+/).filter(term => term.length > 0)
      if (searchTerms.some(term => searchableText.includes(term))) {
        return true
      }
    }

    // Check column filters
    return Object.entries(columnFilters.value).some(([header, filterValue]) => {
      if (!filterValue || !filterValue.trim()) return false

      const itemValue = row[header]
      if (itemValue === null || itemValue === undefined) return false
      
      const itemText = String(itemValue).toLowerCase()
      const filterText = filterValue.toLowerCase().trim()
      
      return itemText.includes(filterText)
    })
  }

  /**
   * Set search query
   */
  function setSearchQuery(query: string) {
    searchQuery.value = query || ''
  }

  /**
   * Set column filter
   */
  function setColumnFilter(header: string, value: string) {
    if (value && value.trim()) {
      columnFilters.value[header] = value
    } else {
      delete columnFilters.value[header]
    }
  }

  /**
   * Clear global search
   */
  function clearSearch() {
    searchQuery.value = ''
  }

  /**
   * Clear all column filters
   */
  function clearAllFilters() {
    columnFilters.value = {}
  }

  /**
   * Clear all search and filters
   */
  function clearAll() {
    searchQuery.value = ''
    columnFilters.value = {}
  }

  /**
   * Toggle advanced search panel
   */
  function toggleAdvancedSearch() {
    showAdvancedSearch.value = !showAdvancedSearch.value
  }

  /**
   * Export filtered results to CSV
   */
  function exportSearchResults(filename?: string) {
    if (filteredData.value.length === 0) {
      throw new Error('No results to export')
    }

    const csvContent = generateCSV(filteredData.value, headers?.value || [])
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', filename || `search_results_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }
  }

  /**
   * Generate CSV content
   */
  function generateCSV(items: T[], headerList: string[]): string {
    if (!headerList.length) {
      headerList = items.length > 0 && items[0] ? Object.keys(items[0]) : []
    }

    // Create CSV header row
    const csvHeaders = headerList.map(header => `"${header.replace(/"/g, '""')}"`)
    const csvRows = [csvHeaders.join(',')]

    // Create CSV data rows
    items.forEach(item => {
      const row = headerList.map(header => {
        let value = item[header]
        
        if (value === null || value === undefined) {
          value = 'N/A'
        } else if (typeof value === 'object') {
          value = JSON.stringify(value)
        } else {
          value = String(value)
        }
        
        // Escape quotes and wrap in quotes
        return `"${value.replace(/"/g, '""')}"`
      })
      csvRows.push(row.join(','))
    })

    return csvRows.join('\n')
  }

  /**
   * Escape special regex characters
   */
  function escapeRegExp(string: string): string {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }

  /**
   * Highlight a row temporarily
   */
  async function highlightRow(rowId: string, duration = 2000) {
    highlightedRows.value.add(rowId)
    await nextTick()
    
    setTimeout(() => {
      highlightedRows.value.delete(rowId)
    }, duration)
  }

  // Watch for data changes to update search results
  watch(data, () => {
    searchResults.value.total = data.value.length
  }, { immediate: true })

  return {
    // State
    searchQuery,
    columnFilters,
    showAdvancedSearch,
    highlightedRows,
    
    // Computed
    filteredData,
    searchStats,
    isSearchActive,
    searchState,
    
    // Methods
    setSearchQuery,
    setColumnFilter,
    clearSearch,
    clearAllFilters,
    clearAll,
    toggleAdvancedSearch,
    highlightSearchTerm,
    isRowHighlighted,
    exportSearchResults,
    highlightRow
  }
}