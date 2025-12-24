class ConfigurationSaver {
    static async saveConfiguration(saveData) {
        try {
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
                return {
                    success: false,
                    status: response.status,
                    errorData
                };
            }

            const configuration = await response.json();
            return {
                success: true,
                configuration
            };
        } catch (err) {
            console.error('Error saving configuration:', err);
            return {
                success: false,
                error: err.message || 'Failed to save configuration'
            };
        }
    }

    static handleSaveError(status, errorData) {
        const errors = {};
        let message = 'Failed to save configuration';

        if (status === 422) {
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
                    
                    return {
                        fieldErrors: fieldErrorsFromServer,
                        message: 'Please fix the highlighted validation errors',
                        showFieldErrors: true
                    };
                }
                // If detail is an object with specific field_errors (EntryService custom validation)
                else if (errorData.detail.field_errors) {
                    return {
                        fieldErrors: errorData.detail.field_errors,
                        message: 'Please fix the highlighted validation errors',
                        showFieldErrors: true
                    };
                }
                // Generic detail message
                else {
                    message = errorData.detail.message || errorData.detail || 'Validation failed';
                }
            }
        } else if (status === 401) {
            return {
                redirect: '/api/v1/admin/login',
                message: 'Authentication session expired'
            };
        } else if (status === 500) {
            message = 'Server Error: ' + (errorData.detail?.message || 'Internal server error occurred');
        } else {
            message = errorData.message || errorData.detail || `Server returned ${status}`;
        }

        return { message, showFieldErrors: false };
    }
}