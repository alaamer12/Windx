/**
 * Relations Manager
 * 
 * JavaScript module for managing hierarchical option dependencies.
 * Handles entity CRUD and image uploads.
 */

const RelationsManager = {
    // API base URL
    API_BASE: '/api/v1/admin/relations',
    
    // Image upload URL
    IMAGE_UPLOAD_URL: '/api/v1/admin/entry/upload-image',
    
    // Store actual File objects for upload
    imageFiles: {},
    
    // Store base64 for preview only
    imagePreviews: {},
    
    /**
     * Initialize the Relations Manager
     */
    init() {
        this.setupDragAndDrop();
        console.log('RelationsManager initialized');
    },
    
    /**
     * Setup drag and drop for image containers
     */
    setupDragAndDrop() {
        document.querySelectorAll('.image-upload-box').forEach(container => {
            container.addEventListener('dragover', (e) => {
                e.preventDefault();
                container.style.borderColor = 'var(--primary)';
                container.style.backgroundColor = '#eff6ff';
            });
            
            container.addEventListener('dragleave', (e) => {
                e.preventDefault();
                container.style.borderColor = '';
                container.style.backgroundColor = '';
            });
            
            container.addEventListener('drop', (e) => {
                e.preventDefault();
                container.style.borderColor = '';
                container.style.backgroundColor = '';
                
                const entityType = container.closest('.entity-card').dataset.entityType;
                const file = e.dataTransfer.files[0];
                
                if (file && file.type.startsWith('image/')) {
                    this.processImageFile(file, entityType);
                }
            });
        });
    },
    
    /**
     * Trigger image upload input
     */
    triggerImageUpload(entityType) {
        const input = document.getElementById(`${entityType}_file`);
        if (input) {
            input.click();
        }
    },
    
    /**
     * Handle image file selection
     */
    handleImageSelect(event, entityType) {
        const file = event.target.files[0];
        if (file && file.type.startsWith('image/')) {
            this.processImageFile(file, entityType);
        }
    },
    
    /**
     * Process image file - store File object and show preview
     */
    processImageFile(file, entityType) {
        // Store the actual File object for later upload
        this.imageFiles[entityType] = file;
        
        // Create preview using FileReader
        const reader = new FileReader();
        
        reader.onload = (event) => {
            const base64 = event.target.result;
            this.imagePreviews[entityType] = base64;
            
            // Update preview UI
            const preview = document.getElementById(`${entityType}_preview`);
            const placeholder = document.getElementById(`${entityType}_placeholder`);
            const overlay = document.getElementById(`${entityType}_overlay`);
            
            if (preview && placeholder && overlay) {
                preview.src = base64;
                preview.classList.remove('hidden');
                placeholder.classList.add('hidden');
                overlay.classList.remove('hidden');
            }
        };
        
        reader.readAsDataURL(file);
    },
    
    /**
     * Upload image file to server and get URL
     * @param {string} entityType - The entity type (company, material, etc.)
     * @returns {Promise<string|null>} - The uploaded image URL or null if failed
     */
    async uploadImage(entityType) {
        const file = this.imageFiles[entityType];
        if (!file) {
            return null;
        }
        
        console.log(`🔗 [RELATIONS] Uploading image for ${entityType}:`, file.name);
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(this.IMAGE_UPLOAD_URL, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });
            
            const result = await response.json();
            console.log(`🔗 [RELATIONS] Image upload result for ${entityType}:`, result);
            
            if (result.success && result.url) {
                return result.url;
            } else {
                console.warn(`🔗 [RELATIONS] Image upload failed for ${entityType}:`, result.error);
                return null;
            }
        } catch (error) {
            console.error(`🔗 [RELATIONS] Image upload error for ${entityType}:`, error);
            return null;
        }
    },

    /**
     * Record all entities - main save action
     * Creates entities AND the dependency path linking them
     */
    async recordAll() {
        console.log('🔗 [RELATIONS] recordAll() called');
        const entityTypes = ['company', 'material', 'opening_system', 'system_series', 'color'];
        let savedEntities = {};  // Track saved entity IDs
        let errors = [];
        
        for (const entityType of entityTypes) {
            const card = document.querySelector(`.entity-card[data-entity-type="${entityType}"]`);
            if (!card) continue;
            
            // Get form data
            const nameInput = card.querySelector(`[name="${entityType}_name"]`);
            const name = nameInput?.value?.trim();
            
            // Skip if no name entered
            if (!name) {
                console.log(`🔗 [RELATIONS] Skipping ${entityType} - no name`);
                continue;
            }
            
            console.log(`🔗 [RELATIONS] Processing ${entityType}: "${name}"`);

            // Build data object
            const data = {
                entity_type: entityType,
                name: name,
                metadata: {}
            };
            
            // Get entity ID if editing
            const entityIdInput = card.querySelector(`[name="${entityType}_entity_id"]`);
            const entityId = entityIdInput?.value;
            
            // Add optional fields
            const priceInput = card.querySelector(`[name="${entityType}_price_from"]`);
            if (priceInput?.value) {
                data.price_from = parseFloat(priceInput.value);
            }
            
            const descInput = card.querySelector(`[name="${entityType}_description"]`);
            if (descInput?.value) {
                data.description = descInput.value;
            }
            
            // Upload image if one was selected and get the URL
            if (this.imageFiles[entityType]) {
                console.log(`🔗 [RELATIONS] Uploading image for ${entityType}...`);
                const imageUrl = await this.uploadImage(entityType);
                if (imageUrl) {
                    data.image_url = imageUrl;
                    console.log(`🔗 [RELATIONS] ✅ Image uploaded, URL: ${imageUrl}`);
                }
            }
            
            // Add metadata fields
            card.querySelectorAll('[name^="' + entityType + '_metadata."]').forEach(input => {
                const key = input.name.replace(`${entityType}_metadata.`, '');
                if (input.type === 'checkbox') {
                    data.metadata[key] = input.checked;
                } else if (input.value !== '') {
                    data.metadata[key] = isNaN(parseFloat(input.value)) ? input.value : parseFloat(input.value);
                }
            });
            
            try {
                let response;
                console.log(`🔗 [RELATIONS] Sending data for ${entityType}:`, data);
                
                if (entityId) {
                    // Update existing entity
                    response = await fetch(`${this.API_BASE}/entities/${entityId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                } else {
                    // Create new entity
                    response = await fetch(`${this.API_BASE}/entities`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                }
                
                const result = await response.json();
                console.log(`🔗 [RELATIONS] Response for ${entityType}:`, response.status, result);
                
                if (response.ok && result.entity) {
                    savedEntities[entityType] = result.entity.id;
                    console.log(`🔗 [RELATIONS] ✅ Saved ${entityType} with ID: ${result.entity.id}`);
                    this.resetCardForm(entityType);
                } else if (response.ok && entityId) {
                    // Update case - use existing ID
                    savedEntities[entityType] = parseInt(entityId);
                    console.log(`🔗 [RELATIONS] ✅ Updated ${entityType} with ID: ${entityId}`);
                    this.resetCardForm(entityType);
                } else {
                    // Handle error - detail might be string or object
                    let errorMsg = 'Error';
                    console.log(`🔗 [RELATIONS] ❌ Error for ${entityType}, result.detail:`, result.detail, typeof result.detail);
                    if (result.detail) {
                        if (typeof result.detail === 'string') {
                            errorMsg = result.detail;
                        } else if (result.detail.message) {
                            errorMsg = result.detail.message;
                        } else if (Array.isArray(result.detail)) {
                            // Pydantic validation errors
                            errorMsg = result.detail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
                        } else {
                            errorMsg = JSON.stringify(result.detail);
                        }
                    }
                    errors.push(`${entityType}: ${errorMsg}`);
                }
            } catch (error) {
                console.error(`Error saving ${entityType}:`, error);
                errors.push(`${entityType}: Network error`);
            }
        }
        
        // Create dependency path if we have all required entities
        const requiredTypes = ['company', 'material', 'opening_system', 'system_series', 'color'];
        const hasAllRequired = requiredTypes.every(type => savedEntities[type]);
        
        if (hasAllRequired) {
            try {
                const pathData = {
                    company_id: savedEntities.company,
                    material_id: savedEntities.material,
                    opening_system_id: savedEntities.opening_system,
                    system_series_id: savedEntities.system_series,
                    color_id: savedEntities.color
                };
                
                console.log('Creating dependency path:', pathData);
                
                const pathResponse = await fetch(`${this.API_BASE}/paths`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(pathData)
                });
                
                const pathResult = await pathResponse.json();
                
                if (pathResponse.ok) {
                    showToast(`Relation path created: ${pathResult.path?.description || 'Success'}`, 'success');
                } else {
                    // Path might already exist, which is fine
                    let pathErrorMsg = 'Error creating path';
                    if (pathResult.detail) {
                        if (typeof pathResult.detail === 'string') {
                            pathErrorMsg = pathResult.detail;
                        } else if (pathResult.detail.message) {
                            pathErrorMsg = pathResult.detail.message;
                        } else {
                            pathErrorMsg = JSON.stringify(pathResult.detail);
                        }
                    }
                    
                    if (pathErrorMsg.includes('already exists')) {
                        showToast('Entities saved. Path already exists.', 'info');
                    } else {
                        errors.push(`Path: ${pathErrorMsg}`);
                    }
                }
            } catch (error) {
                console.error('Error creating path:', error);
                errors.push('Path: Network error');
            }
        } else if (Object.keys(savedEntities).length > 0) {
            // Some entities saved but not all - warn user
            const missing = requiredTypes.filter(type => !savedEntities[type]);
            showToast(`Entities saved. Missing for path: ${missing.join(', ')}`, 'warning');
        }
        
        // Show final result
        const savedCount = Object.keys(savedEntities).length;
        if (savedCount > 0 && errors.length === 0) {
            showToast(`${savedCount} entity(s) saved successfully`, 'success');
        } else if (errors.length > 0) {
            showToast(`Errors: ${errors.join(', ')}`, 'error');
        } else if (savedCount === 0) {
            showToast('No data to save. Please fill in at least one entity.', 'info');
        }
    },
    
    /**
     * Reset a single card form
     */
    resetCardForm(entityType) {
        const card = document.querySelector(`.entity-card[data-entity-type="${entityType}"]`);
        if (!card) return;
        
        // Reset all inputs
        card.querySelectorAll('input:not([type="file"]), textarea').forEach(input => {
            if (input.type === 'checkbox') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
        
        // Reset file input
        const fileInput = document.getElementById(`${entityType}_file`);
        if (fileInput) {
            fileInput.value = '';
        }
        
        // Reset image storage
        delete this.imageFiles[entityType];
        delete this.imagePreviews[entityType];
        
        const preview = document.getElementById(`${entityType}_preview`);
        const placeholder = document.getElementById(`${entityType}_placeholder`);
        const overlay = document.getElementById(`${entityType}_overlay`);
        
        if (preview) {
            preview.src = '';
            preview.classList.add('hidden');
        }
        if (placeholder) placeholder.classList.remove('hidden');
        if (overlay) overlay.classList.add('hidden');
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    RelationsManager.init();
});
