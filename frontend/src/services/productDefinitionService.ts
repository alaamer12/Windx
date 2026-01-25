import { apiClient } from '@/services/api'

export const productDefinitionService = {
    // Generic Entity Operations
    async getEntities(type: string) {
        const response = await apiClient.get(`/api/v1/admin/relations/entities/${type}`)
        return response.data
    },

    async createEntity(data: any) {
        const response = await apiClient.post('/api/v1/admin/relations/entities', data)
        return response.data
    },

    async updateEntity(id: number, type: string, data: any) {
        const response = await apiClient.put(`/api/v1/admin/relations/entities/${id}`, { ...data, entity_type: type })
        return response.data
    },

    async deleteEntity(id: number, type: string) {
        const response = await apiClient.delete(`/api/v1/admin/relations/entities/${id}`, { params: { type } })
        return response.data
    },

    // Path/Chain Operations
    async getPaths() {
        const response = await apiClient.get('/api/v1/admin/relations/paths')
        return response.data.paths || []
    },

    async createPath(data: any) {
        const response = await apiClient.post('/api/v1/admin/relations/paths', data)
        return response.data
    },

    async deletePath(data: { ltree_path: string }) {
        const response = await apiClient.delete('/api/v1/admin/relations/paths', { data })
        return response.data
    },

    // Image Upload (Re-using generic endpoint from legacy code context)
    async uploadImage(file: File) {
        const formData = new FormData()
        formData.append('file', file)
        const response = await apiClient.post('/api/v1/admin/entry/upload-image', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        return response.data
    }
}
