import { ref, watch, type Ref } from 'vue'
import type { SchemaWithDependencies, DependencyAction, DependencyRule } from '@/types/dependencies'

const MAX_RECURSION_DEPTH = 20

export function useDependencyEngine(
    schema: Ref<SchemaWithDependencies | null>,
    form: Ref<Record<string, any>>,
    findField: (name: string) => any
) {
    const disabledFields = ref<Record<string, boolean>>({})

    // Process a single action
    function processAction(action: DependencyAction, triggerValue: any, sourceOption: any, depth = 0) {
        if (depth > MAX_RECURSION_DEPTH) {
            throw new Error(
                `[DependencyEngine] Maximum recursion depth of ${MAX_RECURSION_DEPTH} exceeded for target field "${action.target_field}". ` +
                'Internal dependency chain is too deep or contains a circular reference.'
            )
        }

        console.log('[DependencyEngine] Processing action:', action.type, action.target_field, `(depth: ${depth})`)

        switch (action.type) {
            case 'autofill': {
                let valueToSet: any = null

                if (action.source_property) {
                    console.log(`[DependencyEngine] Resolving "${action.source_property}" in option:`, sourceOption)
                    // Dot notation access (e.g. metadata_.opening_system_id)
                    valueToSet = action.source_property.split('.').reduce((obj, key) => obj && obj[key], sourceOption)
                    console.log(`[DependencyEngine] Resolved value:`, valueToSet)
                } else {
                    // Direct value from trigger if no source property specified
                    valueToSet = triggerValue
                }

                if (valueToSet !== undefined && valueToSet !== null) {
                    // If lookup_source is provided, resolve ID to Name from those options
                    if (action.lookup_source) {
                        const lookupField = findField(action.lookup_source)
                        if (lookupField) {
                            const options = lookupField.options_data || lookupField.options || []
                            const lookupKey = action.lookup_key || 'id'
                            console.log(`[DependencyEngine] Performing ID-to-Name lookup in "${action.lookup_source}" for ID:`, valueToSet)
                            const found = options.find((o: any) => String(o[lookupKey]) === String(valueToSet))
                            if (found) {
                                console.log(`[DependencyEngine] Resolved ID ${valueToSet} to Name "${found.name}"`)
                                valueToSet = found.name
                            } else {
                                console.warn(`[DependencyEngine] Could not find option with ${lookupKey}=${valueToSet} in ${action.lookup_source}`)
                            }
                        }
                    }

                    form.value[action.target_field] = valueToSet
                    console.log(`[DependencyEngine] Successfully set ${action.target_field} to`, valueToSet)
                } else {
                    console.warn(`[DependencyEngine] Failed to resolve value for ${action.target_field} using ${action.source_property}`)
                }

                if (action.disable_target) {
                    disabledFields.value[action.target_field] = true
                }

                // Chain processing
                if (action.chain) {
                    // Use the original valueToSet (the ID) for the next lookup if it was replaced by name
                    // But wait, the chain might want the name or ID. Usually it wants the NAME of the source.

                    // IF we used a lookup_source for the CURRENT action, we likely wanted the name.
                    // BUT for the chain, we might still have the sourceOption from which we derived the value.

                    if (action.chain.lookup_source) {
                        const lookupField = findField(action.chain.lookup_source)
                        if (lookupField) {
                            const options = lookupField.options_data || lookupField.options || []
                            const lookupKey = action.chain.lookup_key || 'id'

                            // Find the option in lookup source using the value we just set (or its ID)
                            // Usually chains trigger off the PREVIOUS target_field's value.
                            const currentVal = form.value[action.target_field]
                            console.log(`[DependencyEngine] Chained lookup for "${action.chain.lookup_source}" using key "${lookupKey}" and value:`, currentVal)
                            const nextSourceOption = options.find((o: any) => String(o[lookupKey]) === String(currentVal))

                            if (nextSourceOption) {
                                console.log('[DependencyEngine] Chaining next lookup found:', nextSourceOption.name)
                                processAction(action.chain, currentVal, nextSourceOption, depth + 1)
                            } else {
                                console.warn('[DependencyEngine] Chained lookup failed for', action.chain.lookup_source)
                            }
                        }
                    } else {
                        // Direct chain without lookup
                        console.log('[DependencyEngine] Processing direct chain for:', action.chain.target_field)
                        processAction(action.chain, valueToSet, sourceOption, depth + 1)
                    }
                }
                break
            }

            case 'disable':
                disabledFields.value[action.target_field] = true
                break

            default:
                console.warn(`[DependencyEngine] Unknown action type: ${action.type}`)
        }
    }

    // Reset a chain of actions (recursive)
    function resetAction(action: DependencyAction, depth = 0) {
        if (depth > MAX_RECURSION_DEPTH) {
            throw new Error(
                `[DependencyEngine] Maximum recursion depth of ${MAX_RECURSION_DEPTH} exceeded during reset for field "${action.target_field}".`
            )
        }

        disabledFields.value[action.target_field] = false
        if (action.chain) {
            resetAction(action.chain, depth + 1)
        }
    }

    // Set up watchers based on schema
    watch(() => schema.value, (newSchema) => {
        if (!newSchema || !newSchema.dependencies) return

        newSchema.dependencies.forEach((rule: DependencyRule) => {
            watch(() => form.value[rule.trigger_field], (newVal) => {
                // If value is cleared, recursively enable the targets.
                if (!newVal) {
                    rule.actions.forEach(action => {
                        resetAction(action)
                    })
                    return
                }

                // Find the selected option for the trigger field
                const field = findField(rule.trigger_field)
                if (!field) return

                const options = field.options_data || field.options || []

                // Try matching by name or id
                const selectedOption = options.find((o: any) => o.name === newVal || o.id === newVal)

                if (selectedOption) {
                    rule.actions.forEach(action => {
                        processAction(action, newVal, selectedOption)
                    })
                }
            })
        })
    }, { immediate: true })

    return {
        disabledFields
    }
}
