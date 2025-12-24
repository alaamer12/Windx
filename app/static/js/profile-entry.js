// Profile Entry Application JavaScript
// This file uses modular classes loaded from separate files

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
            return FormValidator.isFormValid(this.schema, this.formData, this.fieldVisibility, this.fieldErrors);
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
            const sessionData = SessionManager.loadFromSession();
            this.formData = { ...this.formData, ...sessionData.data };
            this.hasUnsavedData = sessionData.hasUnsavedData;

            console.log('🦆 [STEP 1] Loading manufacturing types...');
            this.manufacturingTypes = await DataLoader.loadManufacturingTypes();
            console.log('🦆 [STEP 1] Manufacturing types loaded:', this.manufacturingTypes.length, 'types');

            if (this.manufacturingTypeId) {
                console.log('🦆 [STEP 2] Manufacturing type ID found, loading schema and previews...');
                this.loading = true;
                try {
                    const [schema, previews] = await Promise.all([
                        DataLoader.loadSchema(this.manufacturingTypeId),
                        DataLoader.loadPreviews(this.manufacturingTypeId)
                    ]);
                    
                    this.schema = this.processSchema(schema);
                    this.savedConfigurations = previews;
                    console.log('🦆 [STEP 2] Data loading completed');
                } catch (err) {
                    console.error('🦆 [ERROR] Failed to load data:', err);
                    this.error = err.message;
                } finally {
                    this.loading = false;
                }
            } else {
                console.warn('🦆 [WARNING] No manufacturingTypeId provided - cannot load schema');
            }

            // Setup navigation guards
            SessionManager.setupNavigationGuards(() => this.hasUnsavedData);

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

        processSchema(schema) {
            if (!schema || !schema.sections) {
                console.warn('🦆 [SCHEMA] ⚠️ LOUD DUCK DEBUG - Schema has no sections!');
                return schema;
            }

            // Force Alpine.js reactivity by triggering multiple updates
            const processedSchema = { ...schema };
            
            console.log('🦆 [SCHEMA] Pre-calculating component types...');
            processedSchema.sections.forEach((section, sectionIndex) => {
                console.log(`🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Section ${sectionIndex}:`, section.title, 'Fields:', section.fields?.length || 0);
                section.fields.forEach((field, fieldIndex) => {
                    console.log(`🦆 [SCHEMA] ✨ LOUD DUCK DEBUG - Field ${fieldIndex}:`, field.name, 'Type:', field.data_type);
                    field.componentType = FormHelpers.getUIComponent(field);
                    // Set default value if not in formData
                    if (this.formData[field.name] === undefined) {
                        this.formData[field.name] = FormHelpers.getDefaultValue(field);
                    }
                });
            });
            console.log('🦆 [SCHEMA] ✅ Schema processing complete');
            
            return processedSchema;
        },

        async loadManufacturingTypes() {
            try {
                this.manufacturingTypes = await DataLoader.loadManufacturingTypes();
            } catch (err) {
                this.error = err.message;
            }
        },

        async loadSchema() {
            this.loading = true;
            this.error = null;
            try {
                const schema = await DataLoader.loadSchema(this.manufacturingTypeId);
                this.schema = this.processSchema(schema);
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        async loadPreviews() {
            try {
                this.savedConfigurations = await DataLoader.loadPreviews(this.manufacturingTypeId);
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
            
            const result = TableEditor.saveInlineEdit(rowId, field, newValue, originalValue, this.pendingEdits, this.savedConfigurations);
            
            if (result.changed) {
                this.pendingEdits = result.pendingEdits;
                this.savedConfigurations = result.savedConfigurations;
                this.hasUnsavedEdits = true;
            }

            this.cancelEditing();
        },

        async commitTableChanges() {
            if (Object.keys(this.pendingEdits).length === 0) {
                return;
            }

            this.committingChanges = true;

            try {
                const result = await TableEditor.commitTableChanges(this.pendingEdits);
                
                // Clear pending edits and show results
                this.pendingEdits = {};
                this.hasUnsavedEdits = false;

                if (result.errorCount === 0) {
                    showToast(`Successfully committed ${result.successCount} changes`, 'success');
                } else if (result.successCount > 0) {
                    showToast(`Committed ${result.successCount} changes, ${result.errorCount} failed`, 'warning');
                } else {
                    showToast(`Failed to commit ${result.errorCount} changes`, 'error');
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
            const result = await TableEditor.deleteRow(rowId);
            
            if (result.success) {
                this.savedConfigurations = this.savedConfigurations.filter(r => r.id !== rowId);
                if (window.showToast) {
                    window.showToast('Deleted successfully', 'success');
                }
            } else if (!result.cancelled) {
                alert(result.error || 'Failed to delete');
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
                            this.formData[field.name] = FormHelpers.getDefaultValue(field);
                        }
                    }
                }
            }
        },

        getDefaultValue(field) {
            return FormHelpers.getDefaultValue(field);
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
            return FormHelpers.getUIComponent(field);
        },

        getFieldOptions(fieldName) {
            return FormHelpers.getFieldOptions(fieldName);
        },

        getFieldUnit(fieldName) {
            return FormHelpers.getFieldUnit(fieldName);
        },

        updateMultiSelectField(fieldName, selectElement) {
            const selectedOptions = Array.from(selectElement.selectedOptions).map(option => option.value);
            this.updateField(fieldName, selectedOptions);
        },

        handleFileChange(fieldName, event) {
            ImageHandler.handleFileChange(
                fieldName, 
                event, 
                (field, value) => this.updateField(field, value),
                this.imagePreviews,
                (previews) => { this.imagePreviews = previews; }
            );
        },

        clearFile(fieldName) {
            ImageHandler.clearFile(
                fieldName,
                (field, value) => this.updateField(field, value),
                this.imagePreviews,
                (previews) => { this.imagePreviews = previews; }
            );
        },

        // Image handling methods
        isImageField(fieldName) {
            return ImageHandler.isImageField(fieldName);
        },

        openImageModal(imageSrc) {
            window.openImageModal(imageSrc);
        },

        handleInlineImageChange(rowId, field, event) {
            window.handleInlineImageChange(rowId, field, event);
        },

        getImageUrl(filename) {
            return ImageHandler.getImageUrl(filename);
        },

        // Add debugging method to check template conditions
        debugImageField(header, rowValue) {
            return ImageHandler.debugImageField(header, rowValue);
        },

        updateField(fieldName, value) {
            // Update form data
            this.formData[fieldName] = value;

            // Save to session storage
            SessionManager.saveToSession(this.formData);
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

            const isVisible = this.isFieldVisible(fieldName);
            const fieldErrors = FormValidator.validateField(field, value, isVisible);
            
            // Update field errors
            if (Object.keys(fieldErrors).length > 0) {
                this.fieldErrors = { ...this.fieldErrors, ...fieldErrors };
            } else {
                // Clear error if validation passes
                const updatedErrors = { ...this.fieldErrors };
                delete updatedErrors[fieldName];
                this.fieldErrors = updatedErrors;
            }
        },

        validateAllFields() {
            this.fieldErrors = FormValidator.validateAllFields(this.schema, this.formData, this.fieldVisibility);
        },

        getPreviewValue(header) {
            return FormHelpers.getPreviewValue(header, this.formData, this.fieldVisibility);
        },

        // Enhanced preview headers matching exact CSV structure
        get previewHeaders() {
            return FormHelpers.getPreviewHeaders();
        },

        async saveConfiguration() {
            // Validate all fields before saving
            this.validateAllFields();

            if (!this.isFormValid) {
                showToast('Please fix validation errors before saving', 'error');
                this.scrollToFirstError();
                return;
            }

            this.saving = true;
            this.error = null;

            try {
                const saveData = this.prepareSaveData();
                const result = await ConfigurationSaver.saveConfiguration(saveData);

                if (result.success) {
                    showToast('Configuration saved successfully!', 'success');
                    this.lastSavedData = { ...this.formData };

                    // Optionally redirect or update URL
                    if (result.configuration.id) {
                        const url = new URL(window.location);
                        url.searchParams.set('configuration_id', result.configuration.id);
                        window.history.replaceState({}, '', url);
                    }

                    console.log('Saved configuration:', result.configuration);
                    await this.loadPreviews();
                } else {
                    const errorInfo = ConfigurationSaver.handleSaveError(result.status, result.errorData);
                    
                    if (errorInfo.fieldErrors) {
                        this.fieldErrors = { ...this.fieldErrors, ...errorInfo.fieldErrors };
                        if (errorInfo.showFieldErrors) {
                            this.scrollToFirstError();
                        }
                    }
                    
                    if (errorInfo.redirect) {
                        showToast(errorInfo.message, 'error');
                        window.location.href = errorInfo.redirect;
                        return;
                    }
                    
                    throw new Error(errorInfo.message);
                }
            } catch (err) {
                console.error('Error saving configuration:', err);
                this.error = err.message || 'Failed to save configuration';
                showToast(err.message || 'Failed to save configuration', 'error');
            } finally {
                this.saving = false;
            }
        },

        prepareSaveData() {
            return FormHelpers.prepareSaveData(this.formData, this.manufacturingTypeId, this.schema, this.fieldVisibility);
        },

        scrollToFirstError() {
            FormValidator.scrollToFirstError(this.fieldErrors, this.activeTab, (tab) => { this.activeTab = tab; });
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
            return FormHelpers.isValueChanged(header, this.formData, this.lastSavedData);
        },

        getCompletedFieldsCount() {
            return FormHelpers.getCompletedFieldsCount(this.schema, this.formData, this.fieldVisibility);
        },

        getTotalFieldsCount() {
            return FormHelpers.getTotalFieldsCount(this.schema, this.fieldVisibility);
        },

        // Session Storage Management - now handled by SessionManager
        loadFromSession() {
            const sessionData = SessionManager.loadFromSession();
            this.formData = { ...this.formData, ...sessionData.data };
            this.hasUnsavedData = sessionData.hasUnsavedData;
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
            this.fieldErrors = {};
            
            try {
                const saveData = this.prepareSaveData();
                console.log('🔄 Sending data to server:', saveData);
                
                const result = await ConfigurationSaver.saveConfiguration(saveData);
                console.log('📡 Server response:', result);
                
                if (result.success) {
                    console.log('✅ Configuration saved successfully:', result.configuration);
                    SessionManager.markAsCommitted();
                    this.hasUnsavedData = false;
                    showToast('Configuration recorded successfully!', 'success');
                    await this.loadPreviews();
                } else {
                    const errorInfo = ConfigurationSaver.handleSaveError(result.status, result.errorData);
                    
                    if (errorInfo.fieldErrors) {
                        this.fieldErrors = { ...this.fieldErrors, ...errorInfo.fieldErrors };
                        console.log('🎯 Updated field errors:', this.fieldErrors);
                        if (errorInfo.showFieldErrors) {
                            this.scrollToFirstError();
                            showToast('Please fix the highlighted validation errors', 'error', 8000);
                            return;
                        }
                    }
                    
                    if (errorInfo.redirect) {
                        showToast(errorInfo.message, 'error');
                        window.location.href = errorInfo.redirect;
                        return;
                    }
                    
                    throw new Error(errorInfo.message);
                }
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
            SessionManager.setupNavigationGuards(() => this.hasUnsavedData);
        }
    };
}