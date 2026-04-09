import { productDefinitionServiceFactory } from '@/services/productDefinition'
import { parseApiError } from '@/utils/errorHandler'

// Types for schema definition
export interface FieldDefinition {
    name: string
    label: string
    type: 'text' | 'number' | 'boolean' | 'textarea' | 'checkbox' // Enhanced types
    required?: boolean
    options?: { label: string; value: any }[]
    hidden?: boolean
    metadata_?: { placeholder?: string }
}

export interface EntityTypeDefinition {
    value: string
    label: string
    icon: string
    fields: FieldDefinition[]
    hasImage?: boolean
    isLinker?: boolean
    specialUi?: {
        type: string
        config: Record<string, any>
    }
}

export interface ChainNodeDefinition {
    key: string
    label: string
    icon: string
    entityType: string
}

export interface DefinitionSchema {
    title: string
    entityTypes: EntityTypeDefinition[]
    chainStructure: ChainNodeDefinition[]
}

// Dynamic Schema Builder
export async function fetchAndBuildSchemas(): Promise<Record<string, DefinitionSchema>> {
    try {
        const availableScopes = productDefinitionServiceFactory.getAvailableScopes()
        const schemas: Record<string, DefinitionSchema> = {}

        for (const scope of availableScopes) {
            try {
                const service = productDefinitionServiceFactory.getService(scope)
                const metadata = await service.getScopeMetadata()

                if (!metadata) continue

                // Map backend metadata to frontend DefinitionSchema
                const entityTypes: EntityTypeDefinition[] = []

                if (metadata.entities) {
                    Object.keys(metadata.entities).forEach(type => {
                        const def = metadata.entities[type]
                        entityTypes.push({
                            value: type,
                            label: def.label || type,
                            icon: def.icon || 'pi pi-tag',
                            hasImage: true,
                            isLinker: type === 'system_series', // Special case for profile linker
                            fields: (def.metadata_fields || []).map((f: any) => ({
                                name: f.name,
                                label: f.label || f.name,
                                type: f.type || 'text',
                                required: f.required || false,
                                metadata_: {
                                    placeholder: f.placeholder
                                }
                            })),
                            specialUi: def.special_ui
                        })
                    })
                }

                // Map hierarchy to chainStructure
                const chainStructure: ChainNodeDefinition[] = []
                if (metadata.hierarchy) {
                    const sortedLevels = Object.keys(metadata.hierarchy).sort((a, b) => parseInt(a) - parseInt(b))
                    sortedLevels.forEach(level => {
                        const entityType = metadata.hierarchy[level]
                        const entityDef = metadata.entities?.[entityType]
                        chainStructure.push({
                            key: entityType,
                            entityType: entityType,
                            label: entityDef?.label || entityType,
                            icon: entityDef?.icon || 'pi pi-tag'
                        })
                    })
                }

                schemas[scope] = {
                    title: metadata.label || scope,
                    entityTypes,
                    chainStructure
                }
            } catch (err) {
                console.warn(`Failed to build schema for scope ${scope}:`, err)
                // Fallback or skip
            }
        }

        return schemas
    } catch (error) {
        console.error('Error fetching schemas:', error)
        const errorMessage = parseApiError(error)
        throw new Error(`Failed to load definition schemas: ${errorMessage}`)
    }
}
