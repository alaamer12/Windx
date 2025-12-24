class FormHelpers {
    static getUIComponent(field) {
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
    }

    static getFieldOptions(fieldName) {
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
    }

    static getFieldUnit(fieldName) {
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
    }

    static getDefaultValue(field) {
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
    }

    static getPreviewValue(header, formData, fieldVisibility) {
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

        const value = formData[fieldName];

        // Handle conditional field visibility - if field is hidden, show N/A
        if (fieldVisibility[fieldName] === false) {
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
    }

    static getPreviewHeaders() {
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
    }

    static prepareSaveData(formData, manufacturingTypeId, schema, fieldVisibility) {
        const saveData = {
            ...formData,
            manufacturing_type_id: manufacturingTypeId
        };

        // Remove fields that are not visible (conditional logic)
        if (schema) {
            for (const section of schema.sections) {
                for (const field of section.fields) {
                    if (fieldVisibility[field.name] === false) {
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
    }

    static getCompletedFieldsCount(schema, formData, fieldVisibility) {
        if (!schema) return 0;

        let completed = 0;
        for (const section of schema.sections) {
            for (const field of section.fields) {
                if (fieldVisibility[field.name] !== false) {
                    const value = formData[field.name];
                    if (value !== null && value !== undefined && value !== '' &&
                        !(Array.isArray(value) && value.length === 0)) {
                        completed++;
                    }
                }
            }
        }
        return completed;
    }

    static getTotalFieldsCount(schema, fieldVisibility) {
        if (!schema) return 0;

        let total = 0;
        for (const section of schema.sections) {
            for (const field of section.fields) {
                if (fieldVisibility[field.name] !== false) {
                    total++;
                }
            }
        }
        return total;
    }

    static isValueChanged(header, formData, lastSavedData) {
        if (!lastSavedData) return false;

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

        return formData[fieldName] !== lastSavedData[fieldName];
    }
}