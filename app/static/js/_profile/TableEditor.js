class TableEditor {
    static async commitTableChanges(pendingEdits) {
        if (Object.keys(pendingEdits).length === 0) {
            return { success: true, successCount: 0, errorCount: 0 };
        }

        let successCount = 0;
        let errorCount = 0;

        try {
            // Process each row's edits
            for (const [rowId, edits] of Object.entries(pendingEdits)) {
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

            return { success: true, successCount, errorCount };
        } catch (err) {
            console.error('Error committing changes:', err);
            return { success: false, error: err.message, successCount, errorCount };
        }
    }

    static async deleteRow(rowId) {
        if (!confirm('Are you sure you want to delete this configuration?')) {
            return { success: false, cancelled: true };
        }

        try {
            const response = await fetch(`/api/v1/admin/entry/profile/configuration/${rowId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                return { success: true };
            } else {
                return { success: false, error: 'Failed to delete' };
            }
        } catch (err) {
            console.error('Delete error:', err);
            return { success: false, error: err.message };
        }
    }

    static saveInlineEdit(rowId, field, newValue, originalValue, pendingEdits, savedConfigurations) {
        console.log('Saving inline edit:', rowId, field, newValue, 'Original:', originalValue);

        // If value hasn't changed, just return
        if (newValue === originalValue || (newValue === '' && originalValue === 'N/A')) {
            return { changed: false, pendingEdits, savedConfigurations };
        }

        // Store the edit in pending edits (don't save to server yet)
        const updatedPendingEdits = { ...pendingEdits };
        if (!updatedPendingEdits[rowId]) {
            updatedPendingEdits[rowId] = {};
        }
        updatedPendingEdits[rowId][field] = newValue || 'N/A';

        // Update local display immediately
        const updatedConfigurations = [...savedConfigurations];
        const row = updatedConfigurations.find(r => r.id === rowId);
        if (row) {
            row[field] = newValue || 'N/A';
        }

        console.log('Edit stored locally. Pending edits:', updatedPendingEdits);
        
        return { 
            changed: true, 
            pendingEdits: updatedPendingEdits, 
            savedConfigurations: updatedConfigurations 
        };
    }
}