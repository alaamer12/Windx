<template>
  <div class="dashboard">
    <h1>Dashboard</h1>
    <p>Welcome to Windx Configurator</p>
    
    <div class="stats-grid">
      <div class="stat-card">
        <h3>Total Configurations</h3>
        <p class="stat-value">{{ stats.total_configurations || 0 }}</p>
      </div>
      <div class="stat-card">
        <h3>Active Quotes</h3>
        <p class="stat-value">{{ stats.active_quotes || 0 }}</p>
      </div>
      <div class="stat-card">
        <h3>Pending Orders</h3>
        <p class="stat-value">{{ stats.pending_orders || 0 }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient } from '@/services/api'

const stats = ref({
  total_configurations: 0,
  active_quotes: 0,
  pending_orders: 0
})

onMounted(async () => {
  try {
    const response = await apiClient.get('/api/v1/dashboard/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load dashboard stats:', error)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 2rem;
}

h1 {
  font-size: 1.875rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 0.75rem;
  border: 1px solid var(--border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-card h3 {
  font-size: 0.875rem;
  color: var(--text-light);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary);
}
</style>
