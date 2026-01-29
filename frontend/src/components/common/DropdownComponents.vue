<template>
  <div>
    <!-- This file exports all reusable dropdown components -->
  </div>
</template>

<script setup lang="ts">
// This component serves as a barrel export for all dropdown components
// Import and re-export all dropdown-related components here
</script>

<script lang="ts">
// Export components for use in other files
export { default as SmartSelect } from './SmartSelect.vue'
export { default as SmartMultiSelect } from './SmartMultiSelect.vue'
export { default as ColorChipMultiSelect } from './ColorChipMultiSelect.vue'
</script>