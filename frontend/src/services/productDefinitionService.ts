import { apiClient } from '@/services/api'
import { useDebugLogger } from '@/composables/useDebugLogger'

// Create logger instance for the service
const logger = useDebugLogger('ProductDefinitionService')

// Interfaces aligned with Backend Pydantic Schemas (app.api.v1.endpoints.admin_relations)

export interface EntityCreateRequest {
    entity_type: string
    name: string
    image_url?: string | null
    price_from?: number | null
    description?: string | null
    metadata?: Record<string, any>
}

export interface EntityUpdateRequest {
    name?: string
    image_url?: string | null
    price_from?: number | null
    description?: string | null
    metadata?: Record<string, any>
}

export interface PathCreateRequest {
    company_id: number
    material_id: number
    opening_system_id: number
    system_series_id: number
    color_id: number
}

export interface PathDeleteRequest {
    ltree_path: string
}

export interface RelationEntity {
    id: number
    name: string
    node_type: string
    image_url: string | null
    price_impact_value: string | null
    description: string | null
    validation_rules: Record<string, any>
    metadata_?: Record<string, any>  // UI metadata from backend
}

export interface GetEntitiesResponse {
    success: boolean
    entities: RelationEntity[]
    type_metadata?: Record<string, any>  // Type-level UI metadata
}

export const productDefinitionService = {
    // Generic Entity Operations
    async getEntities(type: string, scope?: string) {
        logger.debug('Getting entities', { type, scope })
        try {
            const response = await apiClient.get(`/api/v1/admin/relations/entities/${type}`, {
                params: scope ? { scope } : {}
            })
            logger.info('Successfully retrieved entities', { type, scope, count: response.data?.entities?.length })
            return response.data
        } catch (error) {
            logger.error('Failed to get entities', { type, scope, error })
            throw error
        }
    },

    async createEntity(data: EntityCreateRequest) {
        logger.debug('Creating entity', { entityType: data.entity_type, name: data.name })
        try {
            const response = await apiClient.post('/api/v1/admin/relations/entities', data)
            logger.info('Successfully created entity', { entityId: response.data?.entity?.id, name: data.name })
            return response.data
        } catch (error) {
            logger.error('Failed to create entity', { data, error })
            throw error
        }
    },

    async updateEntity(id: number, data: EntityUpdateRequest) {
        logger.debug('Updating entity', { entityId: id, changes: Object.keys(data) })
        
        try {
            // Prepare the update data to match backend expectations
            const updatePayload: any = {}
            
            if (data.name !== undefined) updatePayload.name = data.name
            if (data.description !== undefined) updatePayload.description = data.description
            if (data.image_url !== undefined) updatePayload.image_url = data.image_url
            if (data.price_from !== undefined) updatePayload.price_from = data.price_from
            
            // Handle metadata - merge validation_rules and other metadata
            if (data.metadata !== undefined) {
                updatePayload.metadata = data.metadata
            }
            
            // Remove undefined fields
            Object.keys(updatePayload).forEach(key => {
                if (updatePayload[key] === undefined) {
                    delete updatePayload[key]
                }
            })
            
            // Only include metadata if it has content
            if (updatePayload.metadata && Object.keys(updatePayload.metadata).length === 0) {
                delete updatePayload.metadata
            }
            
            logger.debug('Prepared update payload', { entityId: id, payload: updatePayload })
            
            const response = await apiClient.put(`/api/v1/admin/relations/entities/${id}`, updatePayload)
            
            logger.info('Successfully updated entity', { 
                entityId: id, 
                updatedFields: Object.keys(updatePayload),
                entityName: response.data?.entity?.name 
            })
            
            return response.data
        } catch (error) {
            logger.error('Failed to update entity', { entityId: id, data, error })
            throw error
        }
    },

    async deleteEntity(id: number) {
        logger.debug('Deleting entity', { entityId: id })
        try {
            const response = await apiClient.delete(`/api/v1/admin/relations/entities/${id}`)
            logger.info('Successfully deleted entity', { entityId: id })
            return response.data
        } catch (error) {
            logger.error('Failed to delete entity', { entityId: id, error })
            throw error
        }
    },

    // Path/Chain Operations
    async getPaths() {
        logger.debug('Getting all paths')
        try {
            const response = await apiClient.get('/api/v1/admin/relations/paths')
            const paths = response.data.paths || []
            logger.info('Successfully retrieved paths', { count: paths.length })
            return paths
        } catch (error) {
            logger.error('Failed to get paths', { error })
            throw error
        }
    },

    async getPathDetails(pathId: number) {
        logger.debug('Getting path details', { pathId })
        try {
            const response = await apiClient.get(`/api/v1/admin/relations/paths/${pathId}`)
            const entityCount = response.data?.path?.entities ? Object.keys(response.data.path.entities).length : 0
            logger.info('Successfully retrieved path details', { 
                pathId, 
                entityCount,
                ltreePath: response.data?.path?.ltree_path 
            })
            return response.data
        } catch (error) {
            logger.error('Failed to get path details', { pathId, error })
            throw error
        }
    },

    async createPath(data: PathCreateRequest) {
        logger.debug('Creating path', { data })
        try {
            const response = await apiClient.post('/api/v1/admin/relations/paths', data)
            logger.info('Successfully created path', { 
                pathId: response.data?.path?.id,
                ltreePath: response.data?.path?.ltree_path 
            })
            return response.data
        } catch (error) {
            logger.error('Failed to create path', { data, error })
            throw error
        }
    },

    async deletePath(data: PathDeleteRequest) {
        logger.debug('Deleting path', { ltreePath: data.ltree_path })
        try {
            const response = await apiClient.delete('/api/v1/admin/relations/paths', { data })
            logger.info('Successfully deleted path', { ltreePath: data.ltree_path })
            return response.data
        } catch (error) {
            logger.error('Failed to delete path', { data, error })
            throw error
        }
    },

    // Scope Operations
    async getScopes() {
        logger.debug('Getting scopes')
        try {
            const response = await apiClient.get('/api/v1/admin/relations/scopes')
            logger.info('Successfully retrieved scopes', { count: Object.keys(response.data || {}).length })
            return response.data
        } catch (error) {
            logger.error('Failed to get scopes', { error })
            throw error
        }
    },

    // Image Upload (Re-using generic endpoint from legacy code context)
    async uploadImage(file: File) {
        logger.debug('Uploading image', { fileName: file.name, fileSize: file.size })
        try {
            const formData = new FormData()
            formData.append('file', file)
            const response = await apiClient.post('/api/v1/admin/entry/upload-image', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            logger.info('Successfully uploaded image', { 
                fileName: file.name, 
                imageUrl: response.data?.image_url 
            })
            return response.data
        } catch (error) {
            logger.error('Failed to upload image', { fileName: file.name, error })
            throw error
        }
    }
}
