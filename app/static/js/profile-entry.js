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

function profileEntryApp() {
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

            // Load from session storage first
            this.loadFromSession();

            console.log('🦆 [STEP 1] Loading manufacturing types...');
            await this.loadManufacturingTypes();
            console.log('🦆 [STEP 1] Manufacturing types loaded:', this.manufacturingTypes.length, 'types');

            if (this.manufacturingTypeId) {
                console.log('🦆 [STEP 2] Manufacturing type ID found, loading schema...');
                await this.loadSchema();
                console.log('🦆 [STEP 2] Schema loading completed');
            } else {
                console.warn('🦆 [WARNING] No manufacturingTypeId provided - cannot load schema');
            }

            // Setup navigation guards
            this.setupNavigationGuards();

            console.log('🦆 [DUCK DEBUG] ========================================');
            console.log('🦆 [DUCK DEBUG] Initialization Complete');
            console.log('🦆 [DUCK DEBUG] Final state:', {
                loading: this.loading,
                hasSchema: !!this.schema,
                schemaSection: this.schema?.sections?.length || 0,
                error: this.error
            });
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

                // Pre-calculate component types for stable rendering
                if (this.schema && this.schema.sections) {
                    console.log('🦆 [SCHEMA] Pre-calculating component types...');
                    this.schema.sections.forEach(section => {
                        if (section.fields) {
                            section.fields.forEach(field => {
                                // Calculate and store component type once
                                field.componentType = field.ui_component || this.getUIComponent(field);

                                // Debug logging
                                console.log(`🦆 Field: ${field.name} -> componentType: ${field.componentType}`);
                            });
                        }
                    });
                }
                console.log('🦆 [SCHEMA] ✅ Schema parsed successfully!');
                console.log('🦆 [SCHEMA] Schema structure:', {
                    manufacturing_type_id: this.schema.manufacturing_type_id,
                    sections_count: this.schema.sections?.length || 0,
                    has_conditional_logic: !!this.schema.conditional_logic,
                    conditional_fields: Object.keys(this.schema.conditional_logic || {}).length
                });
                console.log('🦆 [SCHEMA] Full schema object:', this.schema);

                console.log('🦆 [SCHEMA] Initializing form data...');
                this.initializeFormData();
                console.log('🦆 [SCHEMA] Form data initialized:', this.formData);

                console.log('🦆 [SCHEMA] Updating field visibility...');
                this.updateFieldVisibility();
                console.log('🦆 [SCHEMA] Field visibility updated:', this.fieldVisibility);

                console.log('🦆 [SCHEMA] ✅ Schema loading completed successfully!');
            } catch (err) {
                console.error('🦆 [SCHEMA ERROR] ❌❌❌ EXCEPTION CAUGHT ❌❌❌');
                console.error('🦆 [SCHEMA ERROR] Error message:', err.message);
                console.error('🦆 [SCHEMA ERROR] Error stack:', err.stack);
                console.error('🦆 [SCHEMA ERROR] Full error object:', err);
                this.error = 'Failed to load form schema: ' + err.message;
            } finally {
                console.log('🦆 [SCHEMA] Setting loading state to false...');
                this.loading = false;
                console.log('🦆 [SCHEMA] ========================================');
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
            if (!this.schema) return;

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
            const multiSelectFields = ['reinforcement_steel', 'colours'];
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
                'reinforcement_steel': ['multi choice from steel database'],
                'colours': ['White', 'whit, nussbaum', 'RAL9016', 'RAL7016']
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
            const file = event.target.files[0];
            if (!file) return;

            // Update form data with filename
            this.updateField(fieldName, file.name);

            // Create image preview if it's an image
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    // Force Alpine.js reactivity using spread
                    this.imagePreviews = {
                        ...this.imagePreviews,
                        [fieldName]: e.target.result
                    };
                };
                reader.readAsDataURL(file);
            }
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

            } catch (err) {
                console.error('Error saving configuration:', err);
                this.error = err.message || 'Failed to save configuration';
                showToast(err.message || 'Failed to save configuration', 'error');
            } finally {
                this.saving = false;
            }
        },

        prepareSaveData() {
            const saveData = { ...this.formData };

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
            if (firstErrorField) {
                const element = document.getElementById(firstErrorField);
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    element.focus();
                }
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
            try {
                const saveData = this.prepareSaveData();
                const response = await fetch('/api/v1/admin/entry/profile/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(saveData)
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    if (response.status === 422 && errorData.detail && errorData.detail.field_errors) {
                        this.fieldErrors = { ...this.fieldErrors, ...errorData.detail.field_errors };
                        showToast('Please fix validation errors', 'error');
                        this.scrollToFirstError();
                    } else if (response.status === 401) {
                        showToast('Authentication required', 'error');
                        window.location.href = '/api/v1/admin/login';
                    } else {
                        throw new Error(errorData.detail?.message || 'Failed to record');
                    }
                    return;
                }
                const configuration = await response.json();
                sessionStorage.setItem(COMMIT_STATUS_KEY, 'true');
                this.hasUnsavedData = false;
                showToast('Configuration recorded successfully!', 'success');
                console.log('Recorded:', configuration);
            } catch (err) {
                console.error('Error recording:', err);
                this.error = err.message;
                showToast(err.message || 'Failed to record', 'error');
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