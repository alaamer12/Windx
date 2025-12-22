// Profile Entry Application JavaScript

// JavaScript ConditionEvaluator (from service)
class ConditionEvaluator {
    static OPERATORS = {
        // Comparison operators
        equals: (a, b) => a == b,
        not_equals: (a, b) => a != b,
        greater_than: (a, b) => (a || 0) > (b || 0),
        less_than: (a, b) => (a || 0) < (b || 0),
        greater_equal: (a, b) => (a || 0) >= (b || 0),
        less_equal: (a, b) => (a || 0) <= (b || 0),

        // String operators
        contains: (a, b) => String(a || '').toLowerCase().includes(String(b).toLowerCase()),
        starts_with: (a, b) => String(a || '').toLowerCase().startsWith(String(b).toLowerCase()),
        ends_with: (a, b) => String(a || '').toLowerCase().endsWith(String(b).toLowerCase()),
        matches_pattern: (a, b) => new RegExp(b).test(String(a || '')),

        // Collection operators
        in: (a, b) => (Array.isArray(b) ? b : [b]).includes(a),
        not_in: (a, b) => !(Array.isArray(b) ? b : [b]).includes(a),
        any_of: (a, b) => b.some(item => (Array.isArray(a) ? a : [a]).includes(item)),
        all_of: (a, b) => b.every(item => (Array.isArray(a) ? a : [a]).includes(item)),

        // Existence operators
        exists: (a, b) => a !== null && a !== undefined && a !== '',
        not_exists: (a, b) => a === null || a === undefined || a === '',
        is_empty: (a, b) => !Boolean(a),
        is_not_empty: (a, b) => Boolean(a),
    };

    static evaluateCondition(condition, formData) {
        if (!condition) return true;

        const operator = condition.operator;
        if (!operator) return true;

        // Handle logical operators
        if (operator === 'and') {
            return (condition.conditions || []).every(c =>
                ConditionEvaluator.evaluateCondition(c, formData)
            );
        } else if (operator === 'or') {
            return (condition.conditions || []).some(c =>
                ConditionEvaluator.evaluateCondition(c, formData)
            );
        } else if (operator === 'not') {
            return !ConditionEvaluator.evaluateCondition(condition.condition, formData);
        }

        // Handle field-based operators
        const field = condition.field;
        if (!field) return true;

        const fieldValue = ConditionEvaluator.getFieldValue(field, formData);
        const expectedValue = condition.value;

        const operatorFn = ConditionEvaluator.OPERATORS[operator];
        if (!operatorFn) {
            throw new Error(`Unknown operator: ${operator}`);
        }

        return operatorFn(fieldValue, expectedValue);
    }

    static getFieldValue(fieldPath, formData) {
        if (!fieldPath.includes('.')) {
            return formData[fieldPath];
        }

        // Support nested field access
        let value = formData;
        for (const part of fieldPath.split('.')) {
            if (value && typeof value === 'object') {
                value = value[part];
            } else {
                return undefined;
            }
        }
        return value;
    }
}

// Session storage keys
const SESSION_KEY = 'profile_entry_form_data';
const COMMIT_STATUS_KEY = 'profile_entry_committed';

function profileEntryApp(options = {}) {
    return {
        // State
        manufacturingTypeId: window.INITIAL_MANUFACTURING_TYPE_ID || null,
        manufacturingTypes: [],
        schema: null,
        formData: {},
        fieldVisibility: {},
        fieldErrors: {},
        activeTab: 'input', // Default to input tab
        imagePreviews: {}, // Store object URLs for image previews

        loading: false,
        saving: false,
        error: null,
        hasUnsavedData: false, // Track if session has uncommitted data
        lastSavedData: null,
        autoSaveInterval: null,

        // Inline Editing & Table Preview
        canEdit: options.canEdit || false,
        canDelete: options.canDelete || false,
        savedConfigurations: [],
        editingCell: { rowId: null, field: null, value: null },
        pendingEdits: {}, // Track unsaved edits: { rowId: { field: value } }
        hasUnsavedEdits: false,
        committingChanges: false,


        // Computed
        get isFormValid() {
            if (!this.schema) return false;

            // Check required fields
            for (const section of this.schema.sections) {
                for (const field of section.fields) {
                    if (field.required && this.isFieldVisible(field.name)) {
                        const value = this.formData[field.name];
                        if (!value || value === '') {
                            return false;
                        }
                    }
                }
            }

            // Check for validation errors
            return Object.keys(this.fieldErrors).length === 0;
        },

        // Methods
        switchTab(tabName) {
            this.activeTab = tabName;
            console.log('Switched to tab:', tabName);
        },

        async init() {
            console.log('🦆 [DUCK DEBUG] ========================================');
            console.log('🦆 [DUCK DEBUG] ProfileEntryApp Initialization Started');
            console.log('🦆 [DUCK DEBUG] ========================================');
            console.log('🦆 [INIT] Alpine.js version:', typeof Alpine !== 'undefined' ? 'loaded' : 'NOT LOADED');
            console.log('🦆 [INIT] Window object keys:', Object.keys(window).filter(k => k.includes('INITIAL')));
            console.log('🦆 [INIT] manufacturingTypeId:', this.manufacturingTypeId);
            console.log('🦆 [INIT] Current state:', {
                loading: this.loading,
                schema: this.schema,
                formData: this.formData,
                error: this.error
            });

            // Add event listener for image uploads
            this.$el.addEventListener('image-uploaded', (event) => {
                console.log('🦆 [EVENT DEBUG] Image uploaded event received:', event.detail);
                const { rowId, field, filename, url } = event.detail;
                
                // Update the savedConfigurations data if it exists
                if (this.savedConfigurations && Array.isArray(this.savedConfigurations)) {
                    const row = this.savedConfigurations.find(r => r.id === rowId);
                    if (row) {
                        console.log('🦆 [EVENT DEBUG] Updating row data via event...');
                        console.log('🦆 [EVENT DEBUG] Row before update:', row[field]);
                        
                        // Use URL for display, filename for database
                        row[field] = url || filename;
                        
                        console.log('🦆 [EVENT DEBUG] Row after update:', row[field]);
                        
                        // Force Alpine.js reactivity
                        this.savedConfigurations = [...this.savedConfigurations];
                    }
                }
                
                // Initialize pendingEdits if it doesn't exist
                if (!this.pendingEdits) {
                    this.pendingEdits = {};
                }
                if (!this.pendingEdits[rowId]) {
                    this.pendingEdits[rowId] = {};
                }
                
                // Store the filename for database commit
                this.pendingEdits[rowId][field] = filename;
                this.hasUnsavedEdits = true;
                
                console.log('🦆 [EVENT DEBUG] Updated pendingEdits via event:', this.pendingEdits);
                console.log('🦆 [EVENT DEBUG] hasUnsavedEdits set to:', this.hasUnsavedEdits);
            });

            // Load from session storage first
            this.loadFromSession();

            console.log('🦆 [STEP 1] Loading manufacturing types...');
            await this.loadManufacturingTypes();
            console.log('🦆 [STEP 1] Manufacturing types loaded:', this.manufacturingTypes.length, 'types');

            if (this.manufacturingTypeId) {
                console.log('🦆 [STEP 2] Manufacturing type ID found, loading schema and previews...');
                await Promise.all([
                    this.loadSchema(),
                    this.loadPreviews()
                ]);
                console.log('🦆 [STEP 2] Data loading completed');
            } else {
                console.warn('🦆 [WARNING] No manufacturingTypeId provided - cannot load schema');
            }

            // Setup navigation guards
            this.setupNavigationGuards();


            console.log('🦆 [DUCK DEBUG] ========================================');
            console.log('🦆 [DUCK DEBUG] Initialization Complete');
            console.log('🦆 [DUCK DEBUG] ✨ LOUD DUCK DEBUG - Final state:', {
                loading: this.loading,
                hasSchema: !!this.schema,
                schemaSection: this.schema?.sections?.length || 0,
                error: this.error,
                schemaKeys: Object.keys(this.schema || {}),
                fullSchema: this.schema
            });
            console.log('🦆 [DUCK DEBUG] ✨ LOUD DUCK DEBUG - Form data keys:', Object.keys(this.formData));
            console.log('🦆 [DUCK DEBUG] ✨ LOUD DUCK DEBUG - Field visibility:', this.fieldVisibility);
            console.log('🦆 [DUCK DEBUG] ========================================');
        },

        async loadManufacturingTypes() {
            console.log('🦆 [MFGTYPE] Starting to load manufacturing types...');
            try {
                const url = '/api/v1/manufacturing-types/';
                console.log('🦆 [MFGTYPE] Fetching from:', url);

                const response = await fetch(url, {
                    credentials: 'include'  // Include cookies for admin authentication
                });

                console.log('🦆 [MFGTYPE] Response status:', response.status);
                console.log('🦆 [MFGTYPE] Response ok:', response.ok);

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('🦆 [MFGTYPE ERROR] Failed response:', errorText);
                    throw new Error('Failed to load manufacturing types');
                }

                const data = await response.json();
                console.log('🦆 [MFGTYPE] Response data:', data);
                this.manufacturingTypes = data.items || [];
                console.log('🦆 [MFGTYPE] ✅ Success! Loaded', this.manufacturingTypes.length, 'types');
            } catch (err) {
                console.error('🦆 [MFGTYPE ERROR] ❌ Exception caught:', err);
                console.error('🦆 [MFGTYPE ERROR] Error stack:', err.stack);
                this.error = 'Failed to load manufacturing types';
            }
        },

        async loadSchema() {
            console.log('🦆 [SCHEMA] ========================================');
            console.log('🦆 [SCHEMA] Starting schema load process...');

            if (!this.manufacturingTypeId) {
                console.warn('🦆 [SCHEMA] ⚠️ No manufacturing type ID - aborting');
                this.schema = null;
                this.loading = false;
                return;
            }

            console.log('🦆 [SCHEMA] Manufacturing type ID:', this.manufacturingTypeId);
            console.log('🦆 [SCHEMA] Setting loading state to true...');
            this.loading = true;
            this.error = null;

            try {
                const url = `/api/v1/admin/entry/profile/schema/${this.manufacturingTypeId}`;
                console.log('🦆 [SCHEMA] Constructed URL:', url);
                console.log('🦆 [SCHEMA] Initiating fetch request...');

                const response = await fetch(url, {
                    credentials: 'include'  // Include cookies for admin authentication
                });

                console.log('🦆 [SCHEMA] Response received!');
                console.log('🦆 [SCHEMA] Status:', response.status);
                console.log('🦆 [SCHEMA] Status text:', response.statusText);
                console.log('🦆 [SCHEMA] Headers:', Object.fromEntries(response.headers.entries()));

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('🦆 [SCHEMA ERROR] ❌ Response not OK');
                    console.error('🦆 [SCHEMA ERROR] Status:', response.status);
                    console.error('🦆 [SCHEMA ERROR] Error body:', errorText);
                    throw new Error(`Failed to load schema: ${response.status}`);
                }

                console.log('🦆 [SCHEMA] Parsing JSON response...');
                this.schema = await response.json();
                console.log('🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Schema loaded:', this.schema);
                console.log('🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Schema type:', typeof this.schema);
                console.log('🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Schema keys:', Object.keys(this.schema || {}));
                console.log('🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Has sections?', !!this.schema?.sections);
                console.log('🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Sections length:', this.schema?.sections?.length || 0);
                console.log('🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Sections content:', this.schema?.sections);

                // Ensure schema is properly reactive by forcing Alpine.js to detect the change
                if (this.schema && this.schema.sections) {
                    // Force Alpine.js reactivity by triggering multiple updates
                    const tempSchema = this.schema;
                    this.schema = null;
                    await new Promise(resolve => setTimeout(resolve, 50)); // Longer delay
                    this.schema = tempSchema;
                    
                    // Force another update cycle
                    await new Promise(resolve => setTimeout(resolve, 50));
                    this.schema = { ...tempSchema }; // Create new object reference
                    
                    console.log('🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Forced multiple Alpine reactivity updates');
                }

                // Pre-calculate component types for stable rendering
                if (this.schema && this.schema.sections) {
                    console.log('🦆 [SCHEMA] Pre-calculating component types...');
                    console.log('🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Processing sections:', this.schema.sections.length);
                    this.schema.sections.forEach((section, sectionIndex) => {
                        console.log(`🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Section ${sectionIndex}:`, section.title, 'Fields:', section.fields?.length || 0);
                        section.fields.forEach((field, fieldIndex) => {
                            console.log(`🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Field ${fieldIndex}:`, field.name, 'Type:', field.data_type);
                            field.componentType = this.getUIComponent(field);
                            // Set default value if not in formData
                            if (this.formData[field.name] === undefined) {
                                this.formData[field.name] = null;
                            }
                        });
                    });
                    console.log('🦆 [SCHEMA] ✅ Schema processing complete');
                } else {
                    console.warn('🦆 [SCHEMA] ⚠️ LOUD DUCK DEBUG - Schema has no sections!');
                    console.warn('🦆 [SCHEMA] ⚠️ LOUD DUCK DEBUG - Schema object:', JSON.stringify(this.schema, null, 2));
                }
            } catch (err) {
                console.error('🦆 [SCHEMA ERROR] ❌ Exception caught:', err);
                this.error = 'Failed to load form schema';
            } finally {
                console.log('🦆 [SCHEMA] Setting loading to false');
                this.loading = false;
            }
        },

        async loadPreviews() {
            if (!this.manufacturingTypeId) return;

            try {
                const response = await fetch(`/api/v1/admin/entry/profile/previews/${this.manufacturingTypeId}`, {
                    credentials: 'include'  // Include cookies for admin authentication
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.savedConfigurations = data.rows || [];
                    console.log(`Loaded ${this.savedConfigurations.length} previews`);
                } else if (response.status === 403) {
                    console.warn('🔒 Preview access forbidden - user may not have permission');
                    this.savedConfigurations = [];
                } else {
                    console.warn(`Failed to load previews: ${response.status}`);
                    this.savedConfigurations = [];
                }
            } catch (err) {
                console.error('Failed to load previews:', err);
                this.savedConfigurations = [];
            }
        },

        startEditing(rowId, field, value) {
            console.log('🦆 [EDITING DEBUG] ========================================');
            console.log('🦆 [EDITING DEBUG] startEditing called');
            console.log('🦆 [EDITING DEBUG] rowId:', rowId);
            console.log('🦆 [EDITING DEBUG] field:', field);
            console.log('🦆 [EDITING DEBUG] value:', value);
            console.log('🦆 [EDITING DEBUG] isImageField(field):', this.isImageField(field));
            
            this.editingCell = {
                rowId: rowId,
                field: field,
                value: value === 'N/A' ? '' : value
            };
            
            console.log('🦆 [EDITING DEBUG] editingCell set to:', this.editingCell);
            console.log('🦆 [EDITING DEBUG] ========================================');
        },

        cancelEditing() {
            console.log('🦆 [CANCEL EDITING DEBUG] ========================================');
            console.log('🦆 [CANCEL EDITING DEBUG] cancelEditing called');
            console.log('🦆 [CANCEL EDITING DEBUG] Current editingCell:', this.editingCell);
            
            this.editingCell = { rowId: null, field: null, value: null };
            
            console.log('🦆 [CANCEL EDITING DEBUG] editingCell reset to:', this.editingCell);
            console.log('🦆 [CANCEL EDITING DEBUG] ========================================');
        },

        async saveInlineEdit(rowId, field) {
            const newValue = this.editingCell.value;
            const originalValue = this.savedConfigurations.find(r => r.id === rowId)?.[field];
            
            console.log('Saving inline edit:', rowId, field, newValue, 'Original:', originalValue);

            // If value hasn't changed, just cancel editing
            if (newValue === originalValue || (newValue === '' && originalValue === 'N/A')) {
                this.cancelEditing();
                return;
            }

            // Store the edit in pending edits (don't save to server yet)
            if (!this.pendingEdits[rowId]) {
                this.pendingEdits[rowId] = {};
            }
            this.pendingEdits[rowId][field] = newValue || 'N/A';
            this.hasUnsavedEdits = true;

            // Update local display immediately
            const row = this.savedConfigurations.find(r => r.id === rowId);
            if (row) {
                row[field] = newValue || 'N/A';
            }

            this.cancelEditing();
            console.log('Edit stored locally. Pending edits:', this.pendingEdits);
        },

        async commitTableChanges() {
            if (Object.keys(this.pendingEdits).length === 0) {
                return;
            }

            this.committingChanges = true;
            let successCount = 0;
            let errorCount = 0;
            const totalEdits = Object.values(this.pendingEdits).reduce((sum, edits) => sum + Object.keys(edits).length, 0);

            try {
                // Process each row's edits
                for (const [rowId, edits] of Object.entries(this.pendingEdits)) {
                    for (const [field, value] of Object.entries(edits)) {
                        try {
                            console.log(`🦆 [COMMIT DEBUG] Saving ${field} for row ${rowId} with value:`, value);
                            
                            const response = await fetch(`/api/v1/admin/entry/profile/preview/${rowId}/update-cell`, {
                                method: 'PATCH',
                                headers: { 'Content-Type': 'application/json' },
                                credentials: 'include',
                                body: JSON.stringify({ field: field, value: value })
                            });

                            console.log(`🦆 [COMMIT DEBUG] Response status for ${field}:`, response.status);

                            if (response.ok) {
                                successCount++;
                                console.log(`✅ Successfully saved ${field} for row ${rowId}`);
                            } else {
                                errorCount++;
                                const error = await response.json();
                                console.error(`❌ Failed to save ${field} for row ${rowId}:`, error);
                            }
                        } catch (err) {
                            errorCount++;
                            console.error(`❌ Network error saving ${field} for row ${rowId}:`, err);
                        }
                    }
                }

                // Clear pending edits and show results
                this.pendingEdits = {};
                this.hasUnsavedEdits = false;

                if (errorCount === 0) {
                    showToast(`Successfully committed ${successCount} changes`, 'success');
                } else if (successCount > 0) {
                    showToast(`Committed ${successCount} changes, ${errorCount} failed`, 'warning');
                } else {
                    showToast(`Failed to commit ${errorCount} changes`, 'error');
                }

                // Reload the preview data to ensure consistency
                await this.loadPreviews();

            } catch (err) {
                console.error('Error committing changes:', err);
                showToast('Failed to commit changes', 'error');
            } finally {
                this.committingChanges = false;
            }
        },

        async deleteRow(rowId) {
            if (!confirm('Are you sure you want to delete this configuration?')) return;

            try {
                const response = await fetch(`/api/v1/admin/entry/profile/configuration/${rowId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    this.savedConfigurations = this.savedConfigurations.filter(r => r.id !== rowId);

                    if (window.showToast) {
                        window.showToast('Deleted successfully', 'success');
                    }
                } else {
                    alert('Failed to delete');
                }
            } catch (err) {
                console.error('Delete error:', err);
            }
        },


        initializeFormData() {
            this.formData = {
                manufacturing_type_id: this.manufacturingTypeId,
                name: '',
                type: '',
                upvc_profile_discount: 20.0
            };

            // Initialize all fields with default values
            if (this.schema) {
                for (const section of this.schema.sections) {
                    for (const field of section.fields) {
                        if (!(field.name in this.formData)) {
                            this.formData[field.name] = this.getDefaultValue(field);
                        }
                    }
                }
            }
        },

        getDefaultValue(field) {
            switch (field.data_type) {
                case 'boolean':
                    return false;
                case 'number':
                case 'float':
                    return null;
                case 'array':
                    return [];
                default:
                    return '';
            }
        },

        updateFieldVisibility() {
            if (!this.schema || !this.schema.conditional_logic) return;

            // Evaluate all conditional logic
            for (const [fieldName, condition] of Object.entries(this.schema.conditional_logic)) {
                try {
                    this.fieldVisibility[fieldName] = ConditionEvaluator.evaluateCondition(condition, this.formData);
                } catch (err) {
                    console.error(`Error evaluating condition for ${fieldName}:`, err);
                    this.fieldVisibility[fieldName] = true; // Default to visible
                }
            }
        },

        isFieldVisible(fieldName) {
            // If no conditional logic, field is visible
            if (!this.schema || !this.schema.conditional_logic[fieldName]) {
                return true;
            }

            return this.fieldVisibility[fieldName] !== false;
        },

        getUIComponent(field) {
            // Determine UI component based on field name and data type
            if (field.data_type === 'boolean') return 'checkbox';
            if (field.data_type === 'number' || field.data_type === 'float') return 'number';
            if (field.name.includes('percentage') || field.name.includes('discount')) return 'percentage';
            if (field.name.includes('price') || field.name.includes('cost')) return 'currency';
            if (field.name.includes('description') || field.name.includes('notes')) return 'textarea';

            // Field-specific UI components based on CSV analysis
            const dropdownFields = ['type', 'company', 'material', 'opening_system', 'system_series'];
            const multiSelectFields = [];
            const checkboxFields = ['renovation', 'builtin_flyscreen_track'];

            if (dropdownFields.includes(field.name)) return 'dropdown';
            if (multiSelectFields.includes(field.name)) return 'multi-select';
            if (checkboxFields.includes(field.name)) return 'checkbox';

            return 'text';  // DEFAULT: text input
        },


        getFieldOptions(fieldName) {
            // Return options based on CSV data analysis
            const optionsMap = {
                'type': ['Frame', 'sash', 'Mullion', 'Flying mullion', 'glazing bead', 'Interlock', 'Track', 'auxilary', 'coupling', 'tube'],
                'company': ['kompen', 'choose from database'],
                'material': ['UPVC', 'Choose'],
                'opening_system': ['Casement', 'All'],
                'system_series': ['Kom700', 'Kom701', 'Kom800', 'All'],
                'renovation': ['yes', 'no', 'n.a'],
            };

            return optionsMap[fieldName] || [];
        },

        getFieldUnit(fieldName) {
            // Return appropriate unit based on field name
            const unitMap = {
                'length_of_beam': 'm',
                'width': 'mm',
                'total_width': 'mm',
                'flyscreen_track_height': 'mm',
                'front_height': 'mm',
                'rear_height': 'mm',
                'glazing_height': 'mm',
                'renovation_height': 'mm',
                'glazing_undercut_height': 'mm',
                'sash_overlap': 'mm',
                'flying_mullion_horizontal_clearance': 'mm',
                'flying_mullion_vertical_clearance': 'mm',
                'steel_material_thickness': 'mm',
                'weight_per_meter': 'kg',
                'price_per_meter': '$',
                'price_per_beam': '$',
                'upvc_profile_discount': '%'
            };

            return unitMap[fieldName] || '';
        },

        updateMultiSelectField(fieldName, selectElement) {
            const selectedOptions = Array.from(selectElement.selectedOptions).map(option => option.value);
            this.updateField(fieldName, selectedOptions);
        },

        handleFileChange(fieldName, event) {
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] ========================================');
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] handleFileChange called');
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] fieldName:', fieldName);
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] event:', event);
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] event.target:', event.target);
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] event.target.files:', event.target.files);
            
            const file = event.target.files[0];
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] Selected file:', file);
            
            if (!file) {
                console.log('🦆 [MAIN FORM UPLOAD DEBUG] ❌ No file selected');
                return;
            }
            
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] File details:');
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] - name:', file.name);
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] - size:', file.size);
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] - type:', file.type);

            // Update form data with filename
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] Updating form data with filename:', file.name);
            this.updateField(fieldName, file.name);

            // Create image preview if it's an image
            if (file.type.startsWith('image/')) {
                console.log('🦆 [MAIN FORM UPLOAD DEBUG] Creating image preview...');
                const reader = new FileReader();
                reader.onload = (e) => {
                    console.log('🦆 [MAIN FORM UPLOAD DEBUG] FileReader loaded, creating preview');
                    // Force Alpine.js reactivity using spread
                    this.imagePreviews = {
                        ...this.imagePreviews,
                        [fieldName]: e.target.result
                    };
                    console.log('🦆 [MAIN FORM UPLOAD DEBUG] Image preview created for:', fieldName);
                };
                reader.readAsDataURL(file);
            } else {
                console.log('🦆 [MAIN FORM UPLOAD DEBUG] Not an image file, skipping preview');
            }
            
            console.log('🦆 [MAIN FORM UPLOAD DEBUG] ========================================');
        },

        clearFile(fieldName) {
            this.updateField(fieldName, '');
            // Create a copy and delete to trigger reactivity
            const updatedPreviews = { ...this.imagePreviews };
            delete updatedPreviews[fieldName];
            this.imagePreviews = updatedPreviews;

            // Clear the file input element if it exists
            const input = document.getElementById(fieldName);
            if (input) {
                input.value = '';
            }
        },

        // Image handling methods
        isImageField(fieldName) {
            console.log('🦆 [IMAGE FIELD DEBUG] isImageField called with:', fieldName);
            
            if (!fieldName) {
                console.log('🦆 [IMAGE FIELD DEBUG] ❌ No fieldName provided');
                return false;
            }
            
            const imageFields = ['pic', 'image', 'photo', 'picture', 'img', 'thumbnail', 'avatar', 'logo'];
            const fieldNameLower = fieldName.toLowerCase();
            
            console.log('🦆 [IMAGE FIELD DEBUG] fieldNameLower:', fieldNameLower);
            console.log('🦆 [IMAGE FIELD DEBUG] imageFields:', imageFields);
            
            const isImage = imageFields.some(imgField => {
                const matches = fieldNameLower.includes(imgField);
                console.log(`🦆 [IMAGE FIELD DEBUG] Checking "${imgField}" in "${fieldNameLower}":`, matches);
                return matches;
            });
            
            console.log('🦆 [IMAGE FIELD DEBUG] Final result:', isImage);
            return isImage;
        },

        openImageModal(imageSrc) {
            window.openImageModal(imageSrc);
        },

        handleInlineImageChange(rowId, field, event) {
            window.handleInlineImageChange(rowId, field, event);
        },

        getImageUrl(filename) {
            console.log('🦆 [IMAGE URL DEBUG] getImageUrl called with:', filename);
            
            // Handle both full URLs and relative filenames
            if (!filename || filename === 'N/A') {
                console.log('🦆 [IMAGE URL DEBUG] No filename or N/A, returning empty string');
                return '';
            }
            
            // If it's already a full URL (starts with http), return as-is
            if (filename.startsWith('http')) {
                console.log('🦆 [IMAGE URL DEBUG] Full URL detected, returning as-is:', filename);
                return filename;
            }
            
            // If it starts with a path separator, it's a relative URL
            if (filename.startsWith('/')) {
                console.log('🦆 [IMAGE URL DEBUG] Relative URL detected, adding cache buster');
                // Add cache-busting parameter
                const cacheBuster = `?t=${Date.now()}`;
                const urlWithCache = filename + cacheBuster;
                console.log('🦆 [IMAGE URL DEBUG] URL with cache buster:', urlWithCache);
                return urlWithCache;
            }
            
            // Otherwise, assume it's a filename and construct the URL
            const constructedUrl = `/static/uploads/${filename}?t=${Date.now()}`;
            console.log('🦆 [IMAGE URL DEBUG] Constructed URL with cache buster:', constructedUrl);
            return constructedUrl;
        },

        // Add debugging method to check template conditions
        debugImageField(header, rowValue) {
            console.log('🦆 [TEMPLATE DEBUG] debugImageField called');
            console.log('🦆 [TEMPLATE DEBUG] - header:', header);
            console.log('🦆 [TEMPLATE DEBUG] - rowValue:', rowValue);
            console.log('🦆 [TEMPLATE DEBUG] - header.toLowerCase():', header.toLowerCase());
            console.log('🦆 [TEMPLATE DEBUG] - header.toLowerCase() === "pic":', header.toLowerCase() === 'pic');
            console.log('🦆 [TEMPLATE DEBUG] - rowValue exists:', !!rowValue);
            console.log('🦆 [TEMPLATE DEBUG] - rowValue !== "N/A":', rowValue !== 'N/A');
            console.log('🦆 [TEMPLATE DEBUG] - should show image:', header.toLowerCase() === 'pic' && rowValue && rowValue !== 'N/A');
            return header.toLowerCase() === 'pic' && rowValue && rowValue !== 'N/A';
        },

        updateField(fieldName, value) {
            // Update form data
            this.formData[fieldName] = value;

            // Save to session storage
            sessionStorage.setItem(SESSION_KEY, JSON.stringify(this.formData));
            sessionStorage.setItem(COMMIT_STATUS_KEY, 'false');
            this.hasUnsavedData = true;

            // Clear field error
            delete this.fieldErrors[fieldName];

            // Update field visibility based on new data
            this.updateFieldVisibility();

            // Validate field
            this.validateField(fieldName, value);
        },

        validateField(fieldName, value) {
            if (!this.schema) return;

            // Find field definition
            let field = null;
            for (const section of this.schema.sections) {
                field = section.fields.find(f => f.name === fieldName);
                if (field) break;
            }

            if (!field) return;

            // Skip validation for hidden fields
            if (!this.isFieldVisible(fieldName)) {
                delete this.fieldErrors[fieldName];
                return;
            }

            // Required validation
            if (field.required && (!value || value === '' || (Array.isArray(value) && value.length === 0))) {
                this.fieldErrors[fieldName] = `${field.label} is required`;
                return;
            }

            // Skip further validation if field is empty and not required
            if (!value || value === '') {
                delete this.fieldErrors[fieldName];
                return;
            }

            // Validation rules
            if (field.validation_rules) {
                const rules = field.validation_rules;

                // Range validation for numbers
                if ((rules.min !== undefined || rules.max !== undefined) && !isNaN(value)) {
                    const numValue = parseFloat(value);
                    if (rules.min !== undefined && numValue < rules.min) {
                        this.fieldErrors[fieldName] = `${field.label} must be at least ${rules.min}`;
                        return;
                    }
                    if (rules.max !== undefined && numValue > rules.max) {
                        this.fieldErrors[fieldName] = `${field.label} must be at most ${rules.max}`;
                        return;
                    }
                }

                // Pattern validation for strings
                if (rules.pattern && typeof value === 'string') {
                    try {
                        if (!new RegExp(rules.pattern).test(value)) {
                            this.fieldErrors[fieldName] = rules.message || `${field.label} format is invalid`;
                            return;
                        }
                    } catch (e) {
                        console.warn(`Invalid regex pattern for ${fieldName}:`, rules.pattern);
                    }
                }

                // Length validation for strings
                if (typeof value === 'string') {
                    if (rules.min_length && value.length < rules.min_length) {
                        this.fieldErrors[fieldName] = `${field.label} must be at least ${rules.min_length} characters`;
                        return;
                    }
                    if (rules.max_length && value.length > rules.max_length) {
                        this.fieldErrors[fieldName] = `${field.label} must be at most ${rules.max_length} characters`;
                        return;
                    }
                }

                // Custom validation rules
                if (rules.rule_type) {
                    switch (rules.rule_type) {
                        case 'email':
                            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                            if (!emailRegex.test(value)) {
                                this.fieldErrors[fieldName] = `${field.label} must be a valid email address`;
                                return;
                            }
                            break;
                        case 'positive_number':
                            if (isNaN(value) || parseFloat(value) <= 0) {
                                this.fieldErrors[fieldName] = `${field.label} must be a positive number`;
                                return;
                            }
                            break;
                    }
                }
            }

            // Clear error if validation passes
            delete this.fieldErrors[fieldName];
        },

        validateAllFields() {
            if (!this.schema) return;

            // Clear all errors first
            this.fieldErrors = {};

            // Validate all visible fields
            for (const section of this.schema.sections) {
                for (const field of section.fields) {
                    if (this.isFieldVisible(field.name)) {
                        this.validateField(field.name, this.formData[field.name]);
                    }
                }
            }
        },

        getPreviewValue(header) {
            // Map CSV headers to form field names (exact match with CSV structure)
            const headerMapping = {
                "Name": "name",
                "Type": "type",
                "Company": "company",
                "Material": "material",
                "Opening System": "opening_system",
                "System Series": "system_series",
                "Code": "code",
                "Length of beam": "length_of_beam",
                "Renovation": "renovation",
                "Width": "width",
                "Builtin Flyscreen Track": "builtin_flyscreen_track",
                "Total Width": "total_width",
                "Flyscreen Track Height": "flyscreen_track_height",
                "Front Height": "front_height",
                "Rear Height": "rear_height",
                "Glazing Height": "glazing_height",
                "Renovation Height": "renovation_height",
                "Glazing Undercut Height": "glazing_undercut_height",
                "Pic": "pic",
                "Sash Overlap": "sash_overlap",
                "Flying Mullion Horizontal Clearance": "flying_mullion_horizontal_clearance",
                "Flying Mullion Vertical Clearance": "flying_mullion_vertical_clearance",
                "Steel Material Thickness": "steel_material_thickness",
                "Weight per meter": "weight_per_meter",
                "Reinforcement Steel": "reinforcement_steel",
                "Colours": "colours",
                "Price per meter": "price_per_meter",
                "Price per beam": "price_per_beam",
                "UPVC Profile Discount": "upvc_profile_discount"
            };

            const fieldName = headerMapping[header];
            if (!fieldName) return 'N/A';

            const value = this.formData[fieldName];

            // Handle conditional field visibility - if field is hidden, show N/A
            if (!this.isFieldVisible(fieldName)) {
                return 'N/A';
            }

            if (value === null || value === undefined || value === '') {
                return 'N/A';
            }

            // Format different data types to match CSV format
            if (typeof value === 'boolean') {
                return value ? 'yes' : 'no';
            } else if (Array.isArray(value)) {
                return value.length > 0 ? value.join(', ') : 'N/A';
            } else if (typeof value === 'number') {
                // Format numbers appropriately
                if (fieldName.includes('price')) {
                    return value.toFixed(2);
                } else if (fieldName.includes('percentage') || fieldName.includes('discount')) {
                    return value + '%';
                } else {
                    return String(value);
                }
            } else {
                return String(value);
            }
        },

        // Enhanced preview headers matching exact CSV structure
        get previewHeaders() {
            return [
                "Name", "Type", "Company", "Material", "opening system", "system series",
                "Code", "Length of Beam\nm", "Renovation\nonly for frame", "width",
                "builtin Flyscreen track only for sliding frame", "Total width\nonly for frame with builtin flyscreen",
                "flyscreen track height\nonly for frame with builtin flyscreen", "front Height mm", "Rear heightt",
                "Glazing height", "Renovation height mm\nonly for frame", "Glazing undercut heigth\nonly for glazing bead",
                "Pic", "Sash overlap only for sashs", "flying mullion horizontal clearance",
                "flying mullion vertical clearance", "Steel material thickness\nonly for reinforcement",
                "Weight/m kg", "Reinforcement steel", "Colours", "Price/m", "Price per/beam", "UPVC Profile Discount%"
            ];
        },

        async saveConfiguration() {
            // Validate all fields before saving
            this.validateAllFields();

            if (!this.isFormValid) {
                showToast('Please fix validation errors before saving', 'error');
                // Scroll to first error
                this.scrollToFirstError();
                return;
            }

            this.saving = true;
            this.error = null;

            try {
                // Prepare data for saving (exclude empty/null values for optional fields)
                const saveData = this.prepareSaveData();

                const response = await fetch('/api/v1/admin/entry/profile/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',  // Include cookies for admin authentication
                    body: JSON.stringify(saveData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    if (response.status === 422 && errorData.detail && errorData.detail.field_errors) {
                        // Handle validation errors from server
                        this.fieldErrors = { ...this.fieldErrors, ...errorData.detail.field_errors };
                        showToast('Please fix validation errors', 'error');
                        this.scrollToFirstError();
                    } else if (response.status === 401) {
                        showToast('Authentication required. Please log in again.', 'error');
                        // Redirect to login
                        window.location.href = '/api/v1/admin/login';
                    } else {
                        const message = errorData.detail?.message || errorData.message || 'Failed to save configuration';
                        throw new Error(message);
                    }
                    return;
                }

                const configuration = await response.json();
                showToast('Configuration saved successfully!', 'success');

                // Update UI state
                this.lastSavedData = { ...this.formData };

                // Optionally redirect or update URL
                if (configuration.id) {
                    const url = new URL(window.location);
                    url.searchParams.set('configuration_id', configuration.id);
                    window.history.replaceState({}, '', url);
                }

                console.log('Saved configuration:', configuration);

                // Reload previews to show the new record
                await this.loadPreviews();


            } catch (err) {
                console.error('Error saving configuration:', err);
                this.error = err.message || 'Failed to save configuration';
                showToast(err.message || 'Failed to save configuration', 'error');
            } finally {
                this.saving = false;
            }
        },

        prepareSaveData() {
            const saveData = {
                ...this.formData,
                manufacturing_type_id: this.manufacturingTypeId
            };

            // Remove fields that are not visible (conditional logic)
            if (this.schema) {
                for (const section of this.schema.sections) {
                    for (const field of section.fields) {
                        if (!this.isFieldVisible(field.name)) {
                            delete saveData[field.name];
                        }
                    }
                }
            }

            // Convert empty strings to null for optional fields
            Object.keys(saveData).forEach(key => {
                if (saveData[key] === '') {
                    saveData[key] = null;
                }
            });

            return saveData;
        },

        scrollToFirstError() {
            const firstErrorField = Object.keys(this.fieldErrors)[0];
            console.log('🎯 Scrolling to first error field:', firstErrorField, 'All errors:', this.fieldErrors);
            
            if (firstErrorField) {
                // Switch to input tab if we're not already there
                if (this.activeTab !== 'input') {
                    this.activeTab = 'input';
                    console.log('🔄 Switched to input tab to show error');
                }
                
                // Wait a bit for tab switch to complete, then scroll
                setTimeout(() => {
                    const element = document.getElementById(firstErrorField);
                    console.log('🔍 Found error element:', element);
                    
                    if (element) {
                        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        element.focus();
                        
                        // Add a temporary highlight effect
                        element.classList.add('error-highlight');
                        setTimeout(() => {
                            element.classList.remove('error-highlight');
                        }, 3000);
                        
                        console.log('✅ Scrolled to and focused error field:', firstErrorField);
                    } else {
                        console.warn('⚠️ Could not find element for field:', firstErrorField);
                    }
                }, 100);
            }
        },

        // Auto-save functionality (optional)
        startAutoSave() {
            if (this.autoSaveInterval) {
                clearInterval(this.autoSaveInterval);
            }

            this.autoSaveInterval = setInterval(() => {
                if (this.hasUnsavedChanges() && this.isFormValid) {
                    this.autoSave();
                }
            }, 30000); // Auto-save every 30 seconds
        },

        hasUnsavedChanges() {
            return JSON.stringify(this.formData) !== JSON.stringify(this.lastSavedData || {});
        },

        async autoSave() {
            if (this.saving) return;

            try {
                await this.saveConfiguration();
                console.log('Auto-saved configuration');
            } catch (err) {
                console.warn('Auto-save failed:', err);
            }
        },

        isValueChanged(header) {
            if (!this.lastSavedData) return false;

            const headerMapping = {
                "Name": "name",
                "Type": "type",
                "Company": "company",
                "Material": "material",
                "opening system": "opening_system",
                "system series": "system_series",
                "Code": "code",
                "Length of Beam\nm": "length_of_beam",
                "Renovation\nonly for frame": "renovation",
                "width": "width",
                "builtin Flyscreen track only for sliding frame": "builtin_flyscreen_track",
                "Total width\nonly for frame with builtin flyscreen": "total_width",
                "flyscreen track height\nonly for frame with builtin flyscreen": "flyscreen_track_height",
                "front Height mm": "front_height",
                "Rear heightt": "rear_height",
                "Glazing height": "glazing_height",
                "Renovation height mm\nonly for frame": "renovation_height",
                "Glazing undercut heigth\nonly for glazing bead": "glazing_undercut_height",
                "Pic": "pic",
                "Sash overlap only for sashs": "sash_overlap",
                "flying mullion horizontal clearance": "flying_mullion_horizontal_clearance",
                "flying mullion vertical clearance": "flying_mullion_vertical_clearance",
                "Steel material thickness\nonly for reinforcement": "steel_material_thickness",
                "Weight/m kg": "weight_per_meter",
                "Reinforcement steel": "reinforcement_steel",
                "Colours": "colours",
                "Price/m": "price_per_meter",
                "Price per/beam": "price_per_beam",
                "UPVC Profile Discount%": "upvc_profile_discount"
            };

            const fieldName = headerMapping[header];
            if (!fieldName) return false;

            return this.formData[fieldName] !== this.lastSavedData[fieldName];
        },

        getCompletedFieldsCount() {
            if (!this.schema) return 0;

            let completed = 0;
            for (const section of this.schema.sections) {
                for (const field of section.fields) {
                    if (this.isFieldVisible(field.name)) {
                        const value = this.formData[field.name];
                        if (value !== null && value !== undefined && value !== '' &&
                            !(Array.isArray(value) && value.length === 0)) {
                            completed++;
                        }
                    }
                }
            }
            return completed;
        },

        getTotalFieldsCount() {
            if (!this.schema) return 0;

            let total = 0;
            for (const section of this.schema.sections) {
                for (const field of section.fields) {
                    if (this.isFieldVisible(field.name)) {
                        total++;
                    }
                }
            }
            return total;
        },

        // Session Storage Management
        loadFromSession() {
            const savedData = sessionStorage.getItem(SESSION_KEY);
            const isCommitted = sessionStorage.getItem(COMMIT_STATUS_KEY) === 'true';

            if (savedData) {
                try {
                    const parsedData = JSON.parse(savedData);
                    // Only load if there's meaningful data (not just defaults)
                    const hasActualData = Object.keys(parsedData).some(key => {
                        const value = parsedData[key];
                        return value !== null && value !== undefined && value !== '' &&
                            !(Array.isArray(value) && value.length === 0);
                    });

                    if (hasActualData) {
                        this.formData = { ...this.formData, ...parsedData };
                        // Only show unsaved indicator if data exists AND not committed
                        this.hasUnsavedData = !isCommitted;
                        console.log('Loaded form data from session:', this.formData);
                    }
                } catch (err) {
                    console.error('Failed to load session data:', err);
                }
            }
        },

        async recordConfiguration() {
            this.validateAllFields();
            if (!this.isFormValid) {
                showToast('Please fix validation errors before recording', 'error');
                this.scrollToFirstError();
                return;
            }
            this.saving = true;
            this.error = null;
            
            // Clear previous field errors
            this.fieldErrors = {};
            
            try {
                const saveData = this.prepareSaveData();
                console.log('🔄 Sending data to server:', saveData);
                
                const response = await fetch('/api/v1/admin/entry/profile/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(saveData)
                });
                
                console.log('📡 Server response status:', response.status);
                
                if (!response.ok) {
                    const errorData = await response.json();
                    console.log('❌ Server error data:', errorData);

                    // Specific handling for 422 Validation Errors
                    if (response.status === 422) {
                        if (errorData.detail) {
                            // If detail is an array (standard FastAPI validation error)
                            if (Array.isArray(errorData.detail)) {
                                const fieldErrorsFromServer = {};
                                const messages = errorData.detail.map(e => {
                                    const field = e.loc ? e.loc[e.loc.length - 1] : 'Unknown field';
                                    const msg = e.msg || 'Invalid value';
                                    fieldErrorsFromServer[field] = msg;
                                    return `${field}: ${msg}`;
                                });
                                
                                // Update field errors for UI highlighting
                                this.fieldErrors = { ...this.fieldErrors, ...fieldErrorsFromServer };
                                console.log('🎯 Updated field errors:', this.fieldErrors);
                                
                                // Scroll to first error field
                                this.scrollToFirstError();
                                
                                const errorMessage = `Validation errors found:\n${messages.join('\n')}`;
                                showToast('Please fix the highlighted validation errors', 'error', 8000);
                                return; // Don't throw, just return to show field errors
                            }
                            // If detail is an object with specific field_errors (EntryService custom validation)
                            else if (errorData.detail.field_errors) {
                                // Update field errors for UI highlighting
                                this.fieldErrors = { ...this.fieldErrors, ...errorData.detail.field_errors };
                                console.log('🎯 Updated field errors from server:', this.fieldErrors);

                                // Scroll to first error field
                                this.scrollToFirstError();

                                // Create a readable list of errors for toast
                                const errorList = Object.entries(errorData.detail.field_errors)
                                    .map(([field, msg]) => `• ${field.replace(/_/g, ' ')}: ${msg}`)
                                    .join('\n');

                                showToast('Please fix the highlighted validation errors', 'error', 8000);
                                return; // Don't throw, just return to show field errors
                            }
                            // Generic detail message
                            else {
                                throw new Error(errorData.detail.message || errorData.detail || 'Validation failed');
                            }
                        }
                    } else if (response.status === 401) {
                        showToast('Authentication session expired', 'error');
                        window.location.href = '/api/v1/admin/login';
                        return;
                    } else if (response.status === 500) {
                        throw new Error('Server Error: ' + (errorData.detail?.message || 'Internal server error occurred'));
                    }

                    throw new Error(errorData.message || errorData.detail || `Server returned ${response.status}`);
                }
                
                const configuration = await response.json();
                console.log('✅ Configuration saved successfully:', configuration);
                
                sessionStorage.setItem(COMMIT_STATUS_KEY, 'true');
                this.hasUnsavedData = false;
                showToast('Configuration recorded successfully!', 'success');

                // Refresh previews to show the new record
                await this.loadPreviews();

            } catch (err) {
                console.error('❌ Error recording configuration:', err);
                this.error = err.message;
                showToast(err.message, 'error', 8000);
                this.scrollToFirstError();
            } finally {
                this.saving = false;
            }
        },

        setupNavigationGuards() {
            window.addEventListener('beforeunload', (e) => {
                if (this.hasUnsavedData) {
                    e.preventDefault();
                    e.returnValue = 'You have unsaved data. Are you sure you want to leave?';
                    return e.returnValue;
                }
            });
            document.addEventListener('click', (e) => {
                const link = e.target.closest('a');
                if (link && this.hasUnsavedData && !link.getAttribute('href').startsWith('#')) {
                    if (!confirm('You have unsaved data that has not been recorded to the database. Are you sure you want to leave this page?')) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }
            }, true);
        }
    };
}

// Image handling functions for profile entry
window.openImageModal = function(imageSrc) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50';
    modal.style.zIndex = '9999';
    
    // Create modal content
    modal.innerHTML = `
        <div class="relative max-w-4xl max-h-full p-4">
            <button class="absolute top-2 right-2 text-white text-2xl hover:text-gray-300 z-10" onclick="this.closest('.fixed').remove()">
                ×
            </button>
            <img src="${imageSrc}" alt="Preview" class="max-w-full max-h-full object-contain rounded shadow-lg">
        </div>
    `;
    
    // Close on click outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Close on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            modal.remove();
        }
    }, { once: true });
    
    document.body.appendChild(modal);
};

window.handleInlineImageChange = function(rowId, field, event) {
    console.log('🦆 [UPLOAD DEBUG] ========================================');
    console.log('🦆 [UPLOAD DEBUG] handleInlineImageChange called');
    console.log('🦆 [UPLOAD DEBUG] rowId:', rowId);
    console.log('🦆 [UPLOAD DEBUG] field:', field);
    console.log('🦆 [UPLOAD DEBUG] event:', event);
    console.log('🦆 [UPLOAD DEBUG] event.target:', event.target);
    console.log('🦆 [UPLOAD DEBUG] event.target.files:', event.target.files);
    
    const file = event.target.files[0];
    console.log('🦆 [UPLOAD DEBUG] Selected file:', file);
    
    if (!file) {
        console.log('🦆 [UPLOAD DEBUG] ❌ No file selected');
        return;
    }
    
    console.log('🦆 [UPLOAD DEBUG] File details:');
    console.log('🦆 [UPLOAD DEBUG] - name:', file.name);
    console.log('🦆 [UPLOAD DEBUG] - size:', file.size);
    console.log('🦆 [UPLOAD DEBUG] - type:', file.type);
    console.log('🦆 [UPLOAD DEBUG] - lastModified:', file.lastModified);
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        console.log('🦆 [UPLOAD DEBUG] ❌ Invalid file type:', file.type);
        alert('Please select an image file');
        return;
    }
    console.log('🦆 [UPLOAD DEBUG] ✅ File type validation passed');
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        console.log('🦆 [UPLOAD DEBUG] ❌ File too large:', file.size);
        alert('Image file must be smaller than 5MB');
        return;
    }
    console.log('🦆 [UPLOAD DEBUG] ✅ File size validation passed');
    
    // Create FormData for upload
    console.log('🦆 [UPLOAD DEBUG] Creating FormData...');
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('🦆 [UPLOAD DEBUG] FormData created:');
    console.log('🦆 [UPLOAD DEBUG] - FormData entries:', [...formData.entries()]);
    
    // Show loading state
    const loadingText = 'Uploading...';
    console.log('🦆 [UPLOAD DEBUG] Starting upload...');
    
    // Upload the file with credentials for authentication
    fetch('/api/v1/admin/entry/upload-image', {
        method: 'POST',
        credentials: 'include',  // Include cookies for authentication
        body: formData
    })
    .then(response => {
        console.log('🦆 [UPLOAD DEBUG] Response received:');
        console.log('🦆 [UPLOAD DEBUG] - status:', response.status);
        console.log('🦆 [UPLOAD DEBUG] - statusText:', response.statusText);
        console.log('🦆 [UPLOAD DEBUG] - ok:', response.ok);
        console.log('🦆 [UPLOAD DEBUG] - headers:', Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('🦆 [UPLOAD DEBUG] Response data:', data);
        
        if (data.success) {
            console.log('🦆 [UPLOAD DEBUG] ✅ Upload successful!');
            console.log('🦆 [UPLOAD DEBUG] - filename:', data.filename);
            console.log('🦆 [UPLOAD DEBUG] - url:', data.url);
            console.log('🦆 [UPLOAD DEBUG] - message:', data.message);
            
            // Update the row data with the new filename or URL
            console.log('🦆 [UPLOAD DEBUG] Looking for Alpine app...');
            
            // Try multiple ways to get the Alpine app instance
            let app = null;
            
            // Method 1: Alpine store
            if (window.Alpine && window.Alpine.store) {
                app = window.Alpine.store('profileEntry');
                console.log('🦆 [UPLOAD DEBUG] Method 1 (Alpine.store):', app);
            }
            
            // Method 2: Global window reference
            if (!app && window.profileEntryApp) {
                app = window.profileEntryApp;
                console.log('🦆 [UPLOAD DEBUG] Method 2 (window.profileEntryApp):', app);
            }
            
            // Method 3: Try to find Alpine component in DOM
            if (!app) {
                const profileContainer = document.querySelector('[x-data*="profileEntryApp"]');
                console.log('🦆 [UPLOAD DEBUG] Profile container found:', profileContainer);
                
                if (profileContainer && profileContainer._x_dataStack) {
                    app = profileContainer._x_dataStack[0];
                    console.log('🦆 [UPLOAD DEBUG] Method 3 (DOM search):', app);
                } else if (profileContainer && window.Alpine) {
                    // Try Alpine.$data method
                    try {
                        app = window.Alpine.$data(profileContainer);
                        console.log('🦆 [UPLOAD DEBUG] Method 3b (Alpine.$data):', app);
                    } catch (e) {
                        console.log('🦆 [UPLOAD DEBUG] Alpine.$data failed:', e);
                    }
                }
            }
            
            // Method 4: Try to access Alpine component data directly
            if (!app) {
                const profileContainer = document.querySelector('[x-data*="profileEntryApp"]');
                if (profileContainer && profileContainer.__x) {
                    app = profileContainer.__x.$data;
                    console.log('🦆 [UPLOAD DEBUG] Method 4 (__x.$data):', app);
                }
            }
            
            console.log('🦆 [UPLOAD DEBUG] Final app:', app);
            console.log('🦆 [UPLOAD DEBUG] app type:', typeof app);
            console.log('🦆 [UPLOAD DEBUG] app.savedConfigurations:', app?.savedConfigurations);
            
            // If app is a function, it means we got the factory function, not the instance
            if (typeof app === 'function') {
                console.log('🦆 [UPLOAD DEBUG] App is a function, trying to find the actual instance...');
                
                // Try to find the actual Alpine.js instance in the DOM
                const profileContainer = document.querySelector('[x-data*="profileEntryApp"]');
                if (profileContainer) {
                    console.log('🦆 [UPLOAD DEBUG] Found profile container, checking for Alpine data...');
                    
                    // Try different ways to access Alpine data
                    if (profileContainer._x_dataStack && profileContainer._x_dataStack[0]) {
                        app = profileContainer._x_dataStack[0];
                        console.log('🦆 [UPLOAD DEBUG] Found via _x_dataStack:', app);
                    } else if (profileContainer.__x && profileContainer.__x.$data) {
                        app = profileContainer.__x.$data;
                        console.log('🦆 [UPLOAD DEBUG] Found via __x.$data:', app);
                    } else {
                        console.log('🦆 [UPLOAD DEBUG] Could not find Alpine instance, will use DOM fallback');
                        app = null; // Force DOM fallback
                    }
                }
            }
            
            if (app && app.savedConfigurations) {
                console.log('🦆 [UPLOAD DEBUG] Searching for row with id:', rowId);
                console.log('🦆 [UPLOAD DEBUG] Available row IDs:', app.savedConfigurations.map(r => r.id));
                
                const row = app.savedConfigurations.find(r => r.id === rowId);
                console.log('🦆 [UPLOAD DEBUG] Found row:', row);
                
                if (row) {
                    console.log('🦆 [UPLOAD DEBUG] Row before update:', JSON.stringify(row));
                    
                    // Use the URL for display if available, otherwise use filename
                    const displayValue = data.url || data.filename;
                    console.log('🦆 [UPLOAD DEBUG] Setting display value:', displayValue);
                    console.log('🦆 [UPLOAD DEBUG] Field to update:', field);
                    
                    // Update the row data
                    row[field] = displayValue;
                    
                    console.log('🦆 [UPLOAD DEBUG] Row after update:', JSON.stringify(row));
                    
                    // Force Alpine.js reactivity by creating a new array reference
                    app.savedConfigurations = [...app.savedConfigurations];
                    console.log('🦆 [UPLOAD DEBUG] Forced Alpine reactivity update');
                    
                    // Also update pending edits - use filename for database storage
                    if (!app.pendingEdits) {
                        app.pendingEdits = {};
                    }
                    if (!app.pendingEdits[rowId]) {
                        app.pendingEdits[rowId] = {};
                    }
                    app.pendingEdits[rowId][field] = data.filename; // Store filename in database
                    app.hasUnsavedEdits = true;
                    
                    console.log('🦆 [UPLOAD DEBUG] Updated pending edits:', app.pendingEdits);
                    console.log('🦆 [UPLOAD DEBUG] hasUnsavedEdits set to:', app.hasUnsavedEdits);
                    
                    // Force Alpine.js to detect the change
                    setTimeout(() => {
                        console.log('🦆 [UPLOAD DEBUG] Post-update hasUnsavedEdits check:', app.hasUnsavedEdits);
                    }, 100);
                } else {
                    console.log('🦆 [UPLOAD DEBUG] ❌ Row not found with id:', rowId);
                    console.log('🦆 [UPLOAD DEBUG] Available rows:', app.savedConfigurations);
                }
                
                // Cancel editing mode
                console.log('🦆 [UPLOAD DEBUG] Canceling editing mode...');
                app.cancelEditing();
                
                // Force a small delay to ensure Alpine.js processes the changes
                setTimeout(() => {
                    console.log('🦆 [UPLOAD DEBUG] Post-update check - editingCell:', app.editingCell);
                    console.log('🦆 [UPLOAD DEBUG] Post-update check - row data:', app.savedConfigurations.find(r => r.id === rowId));
                }, 100);
                
            } else {
                console.log('🦆 [UPLOAD DEBUG] ❌ App or savedConfigurations not available, trying manual DOM update...');
                
                // Fallback: Try to update the DOM directly
                const tableCell = document.querySelector(`[data-row-id="${rowId}"][data-field="${field}"]`);
                if (tableCell) {
                    console.log('🦆 [UPLOAD DEBUG] Found table cell, updating directly');
                    const displayValue = data.url || data.filename;
                    
                    // Create image element
                    const img = document.createElement('img');
                    img.src = displayValue;
                    img.alt = `Image for ${field}`;
                    img.className = 'h-12 w-12 object-cover rounded border shadow-sm cursor-pointer hover:shadow-md transition-shadow';
                    img.onclick = () => window.openImageModal && window.openImageModal(displayValue);
                    
                    // Replace cell content
                    tableCell.innerHTML = '';
                    tableCell.appendChild(img);
                } else {
                    console.log('🦆 [UPLOAD DEBUG] ❌ Could not find table cell to update');
                }
                
                // Try to set hasUnsavedEdits flag even if we don't have savedConfigurations
                if (app && typeof app === 'object' && app.hasUnsavedEdits !== undefined) {
                    console.log('🦆 [UPLOAD DEBUG] Setting hasUnsavedEdits flag on Alpine instance...');
                    
                    // Initialize pendingEdits if it doesn't exist
                    if (!app.pendingEdits) {
                        app.pendingEdits = {};
                    }
                    if (!app.pendingEdits[rowId]) {
                        app.pendingEdits[rowId] = {};
                    }
                    
                    // Store the filename for database commit
                    app.pendingEdits[rowId][field] = data.filename;
                    app.hasUnsavedEdits = true;
                    
                    console.log('🦆 [UPLOAD DEBUG] Updated pendingEdits:', app.pendingEdits);
                    console.log('🦆 [UPLOAD DEBUG] hasUnsavedEdits set to:', app.hasUnsavedEdits);
                } else {
                    console.log('🦆 [UPLOAD DEBUG] Could not set hasUnsavedEdits - trying DOM manipulation...');
                    
                    // Try to find and manipulate the Alpine component directly
                    const profileContainer = document.querySelector('[x-data*="profileEntryApp"]');
                    if (profileContainer) {
                        // Try to trigger Alpine.js reactivity by dispatching a custom event
                        const event = new CustomEvent('image-uploaded', {
                            detail: { 
                                rowId, 
                                field, 
                                filename: data.filename,
                                url: data.url || data.filename
                            }
                        });
                        profileContainer.dispatchEvent(event);
                        console.log('🦆 [UPLOAD DEBUG] Dispatched image-uploaded event with URL:', data.url);
                    }
                }
                
                // Still try to cancel editing if we have an app
                if (app && app.cancelEditing) {
                    app.cancelEditing();
                }
            }
            
            if (window.showToast) {
                window.showToast('Image uploaded successfully', 'success');
            }
        } else {
            console.log('🦆 [UPLOAD DEBUG] ❌ Upload failed:', data.error);
            alert('Failed to upload image: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.log('🦆 [UPLOAD DEBUG] ❌ Upload error caught:', error);
        console.log('🦆 [UPLOAD DEBUG] Error details:', error.message);
        console.log('🦆 [UPLOAD DEBUG] Error stack:', error.stack);
        alert('Failed to upload image: ' + error.message);
    });
    
    console.log('🦆 [UPLOAD DEBUG] ========================================');
};