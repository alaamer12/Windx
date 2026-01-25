<template>
  <Card>
    <template #title>
      <div class="flex justify-between items-center">
        <span>{{ title }}</span>
        <Button 
          v-if="hasPendingChanges"
          label="Save All Changes"
          icon="pi pi-check"
          @click="$emit('commit')"
          :loading="loading"
          severity="success"
        />
      </div>
    </template>
    <template #content>
      <DataTable
        :value="data"
        editMode="row"
        dataKey="id"
        @row-edit-save="onRowEditSave"
        :loading="loading"
        paginator
        :rows="10"
        class="p-datatable-sm"
        v-model:editingRows="editingRows"
      >
        <Column 
          v-for="header in headers" 
          :key="header"
          :field="header"
          :header="header"
        >
          <template #editor="{ data, field }">
            <InputText v-model="data[field]" class="w-full" />
          </template>
        </Column>

        <Column :rowEditor="true" style="width:10%; min-width:8rem" />
        
        <Column style="width:5%">
          <template #body="slotProps">
            <Button 
              icon="pi pi-trash" 
              @click="$emit('delete', slotProps.data)"
              severity="danger"
              text
              rounded
            />
          </template>
        </Column>

        <template #empty>
          <div class="text-center py-4 text-gray-500">
            No entries found. Create one using the form above.
          </div>
        </template>
      </DataTable>
    </template>
  </Card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const props = defineProps<{
  data: any[]
  headers: string[]
  loading: boolean
  hasPendingChanges: boolean
  title?: string
}>()

const emit = defineEmits<{
  (e: 'row-save', event: any): void
  (e: 'delete', data: any): void
  (e: 'commit'): void
}>()

const editingRows = ref([])

function onRowEditSave(event: any) {
  emit('row-save', event)
}
</script>
