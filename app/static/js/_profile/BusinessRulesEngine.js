/**
 * Business Rules Engine for Profile Entry
 * 
 * Implements type-based field availability and validation rules
 * based on the CSV business rules specification.
 */
class BusinessRulesEngine {
    /**
     * Evaluate field availability based on current form data
     * @param {Object} formData - Current form data
     * @returns {Object} Field visibility map
     */
    static evaluateFieldAvailability(formData) {
        const visibility = {};
        const productType = (formData.type || '').toLowerCase();
        const openingSystem = (formData.opening_system || '').toLowerCase();

        // Business Rule 1: "Renovation only for frame" → Only when Type = "Frame"
        visibility.renovation = productType === 'frame';

        // Business Rule 2: "builtin Flyscreen track only for sliding frame" → Only for sliding frames
        visibility.builtin_flyscreen_track = (
            productType === 'frame' && openingSystem.includes('sliding')
        );

        // Business Rule 3: "Total width only for frame with builtin flyscreen"
        visibility.total_width = (
            productType === 'frame' && formData.builtin_flyscreen_track === true
        );

        // Business Rule 4: "flyscreen track height only for frame with builtin flyscreen"
        visibility.flyscreen_track_height = (
            productType === 'frame' && formData.builtin_flyscreen_track === true
        );

        // Business Rule 5: "Sash overlap only for sashs" → Only when Type = "sash"
        visibility.sash_overlap = productType === 'sash';

        // Business Rule 6: "Flying mullion clearances" → Only when Type = "Flying mullion"
        visibility.flying_mullion_horizontal_clearance = productType === 'flying mullion';
        visibility.flying_mullion_vertical_clearance = productType === 'flying mullion';

        // Business Rule 7: "Glazing undercut height only for glazing bead" → Only when Type = "glazing bead"
        visibility.glazing_undercut_height = productType === 'glazing bead';

        // Business Rule 8: "Renovation height mm only for frame"
        visibility.renovation_height = productType === 'frame';

        // Business Rule 9: "Steel material thickness only for reinforcement"
        visibility.steel_material_thickness = productType === 'reinforcement';

        return visibility;
    }

    /**
     * Check if a field is valid for the current context
     * @param {string} fieldName - Field name to check
     * @param {Object} formData - Current form data
     * @returns {boolean} True if field is valid for current context
     */
    static isFieldValidForCurrentContext(fieldName, formData) {
        const fieldAvailability = this.evaluateFieldAvailability(formData);
        
        // If field has a specific rule, use it
        if (fieldName in fieldAvailability) {
            return fieldAvailability[fieldName];
        }
        
        // Default to true for fields without specific rules
        return true;
    }

    /**
     * Get display value for preview, showing 'N/A' for fields that don't apply
     * @param {string} fieldName - Field name
     * @param {*} value - Field value
     * @param {Object} formData - Current form data
     * @returns {string} Display value or 'N/A'
     */
    static getDisplayValue(fieldName, value, formData) {
        if (!this.isFieldValidForCurrentContext(fieldName, formData)) {
            return 'N/A';
        }
        
        // Format the value normally if field is applicable
        if (value === null || value === undefined || value === '') {
            return 'N/A';
        } else if (typeof value === 'boolean') {
            return value ? 'yes' : 'no';
        } else if (Array.isArray(value)) {
            return value.length > 0 ? value.join(', ') : 'N/A';
        } else {
            return String(value);
        }
    }

    /**
     * Validate business rules and return field-specific errors
     * @param {Object} formData - Form data to validate
     * @returns {Object} Field errors from business rule violations
     */
    static validateBusinessRules(formData) {
        const errors = {};
        const productType = (formData.type || '').toLowerCase();
        const openingSystem = (formData.opening_system || '').toLowerCase();

        // Rule 1: Renovation should only have values for frames
        if (formData.renovation !== null && formData.renovation !== undefined && 
            formData.renovation !== '' && productType !== 'frame') {
            errors.renovation = 'Renovation is only applicable for frame types';
        }

        // Rule 2: Builtin flyscreen track should only be set for sliding frames
        if (formData.builtin_flyscreen_track !== null && formData.builtin_flyscreen_track !== undefined &&
            !(productType === 'frame' && openingSystem.includes('sliding'))) {
            errors.builtin_flyscreen_track = 'Builtin flyscreen track is only applicable for sliding frames';
        }

        // Rule 3: Total width should only be set when builtin flyscreen is enabled
        if (formData.total_width !== null && formData.total_width !== undefined && formData.total_width !== '' &&
            !(productType === 'frame' && formData.builtin_flyscreen_track === true)) {
            errors.total_width = 'Total width is only applicable when builtin flyscreen track is enabled';
        }

        // Rule 4: Flyscreen track height should only be set when builtin flyscreen is enabled
        if (formData.flyscreen_track_height !== null && formData.flyscreen_track_height !== undefined && 
            formData.flyscreen_track_height !== '' &&
            !(productType === 'frame' && formData.builtin_flyscreen_track === true)) {
            errors.flyscreen_track_height = 'Flyscreen track height is only applicable when builtin flyscreen track is enabled';
        }

        // Rule 5: Sash overlap should only have values for sash types
        if (formData.sash_overlap !== null && formData.sash_overlap !== undefined && 
            formData.sash_overlap !== '' && productType !== 'sash') {
            errors.sash_overlap = 'Sash overlap is only applicable for sash types';
        }

        // Rule 6: Flying mullion clearances should only have values for flying mullion types
        if (formData.flying_mullion_horizontal_clearance !== null && 
            formData.flying_mullion_horizontal_clearance !== undefined && 
            formData.flying_mullion_horizontal_clearance !== '' && productType !== 'flying mullion') {
            errors.flying_mullion_horizontal_clearance = 'Flying mullion horizontal clearance is only applicable for flying mullion types';
        }

        if (formData.flying_mullion_vertical_clearance !== null && 
            formData.flying_mullion_vertical_clearance !== undefined && 
            formData.flying_mullion_vertical_clearance !== '' && productType !== 'flying mullion') {
            errors.flying_mullion_vertical_clearance = 'Flying mullion vertical clearance is only applicable for flying mullion types';
        }

        // Rule 7: Glazing undercut height should only have values for glazing bead types
        if (formData.glazing_undercut_height !== null && formData.glazing_undercut_height !== undefined && 
            formData.glazing_undercut_height !== '' && productType !== 'glazing bead') {
            errors.glazing_undercut_height = 'Glazing undercut height is only applicable for glazing bead types';
        }

        // Rule 8: Renovation height should only have values for frame types
        if (formData.renovation_height !== null && formData.renovation_height !== undefined && 
            formData.renovation_height !== '' && productType !== 'frame') {
            errors.renovation_height = 'Renovation height is only applicable for frame types';
        }

        // Rule 9: Steel material thickness should only have values for reinforcement types
        if (formData.steel_material_thickness !== null && formData.steel_material_thickness !== undefined && 
            formData.steel_material_thickness !== '' && productType !== 'reinforcement') {
            errors.steel_material_thickness = 'Steel material thickness is only applicable for reinforcement types';
        }

        return errors;
    }

    /**
     * Get list of fields that should be disabled based on current context
     * @param {Object} formData - Current form data
     * @returns {Array} Array of field names that should be disabled
     */
    static getDisabledFields(formData) {
        const fieldAvailability = this.evaluateFieldAvailability(formData);
        const disabledFields = [];

        for (const [fieldName, isAvailable] of Object.entries(fieldAvailability)) {
            if (!isAvailable) {
                disabledFields.push(fieldName);
            }
        }

        return disabledFields;
    }

    /**
     * Update field visibility in the UI based on business rules
     * @param {Object} formData - Current form data
     * @param {HTMLElement} formElement - Form element containing fields
     */
    static updateFieldVisibility(formData, formElement) {
        const fieldAvailability = this.evaluateFieldAvailability(formData);

        for (const [fieldName, isAvailable] of Object.entries(fieldAvailability)) {
            const fieldElement = formElement.querySelector(`[name="${fieldName}"]`);
            const fieldContainer = fieldElement?.closest('.field-container, .form-group, .mb-3');

            if (fieldContainer) {
                if (isAvailable) {
                    fieldContainer.style.display = '';
                    fieldElement.disabled = false;
                } else {
                    fieldContainer.style.display = 'none';
                    fieldElement.disabled = true;
                    // Clear the field value when hiding
                    if (fieldElement.type === 'checkbox') {
                        fieldElement.checked = false;
                    } else {
                        fieldElement.value = '';
                    }
                }
            }
        }
    }
}