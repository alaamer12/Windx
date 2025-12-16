/**
 * JavaScript Condition Evaluator for Entry Page System
 * 
 * Provides client-side conditional field visibility evaluation
 * with identical logic to the Python ConditionEvaluator.
 * 
 * Features:
 * - Rich set of operators (comparison, string, collection, existence, logical)
 * - Nested field access with dot notation
 * - Performance optimizations with caching
 * - Error handling and validation
 */

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
        matches_pattern: (a, b) => {
            try {
                return new RegExp(b).test(String(a || ''));
            } catch (e) {
                console.warn('Invalid regex pattern:', b);
                return false;
            }
        },
        
        // Collection operators
        in: (a, b) => (Array.isArray(b) ? b : [b]).includes(a),
        not_in: (a, b) => !(Array.isArray(b) ? b : [b]).includes(a),
        any_of: (a, b) => {
            const aArray = Array.isArray(a) ? a : [a];
            return b.some(item => aArray.includes(item));
        },
        all_of: (a, b) => {
            const aArray = Array.isArray(a) ? a : [a];
            return b.every(item => aArray.includes(item));
        },
        
        // Existence operators
        exists: (a, b) => a !== null && a !== undefined && a !== '',
        not_exists: (a, b) => a === null || a === undefined || a === '',
        is_empty: (a, b) => !Boolean(a),
        is_not_empty: (a, b) => Boolean(a),
    };
    
    // Cache for condition evaluation results
    static _cache = new Map();
    static _cacheEnabled = true;
    
    /**
     * Evaluate a condition against form data
     * @param {Object} condition - Condition object with operator, field, value, etc.
     * @param {Object} formData - Form data to evaluate against
     * @returns {boolean} True if condition is met, false otherwise
     */
    static evaluateCondition(condition, formData) {
        if (!condition) return true;
        
        // Check cache first
        if (this._cacheEnabled) {
            const cacheKey = JSON.stringify({ condition, formData });
            if (this._cache.has(cacheKey)) {
                return this._cache.get(cacheKey);
            }
        }
        
        let result;
        
        try {
            result = this._evaluateConditionInternal(condition, formData);
        } catch (error) {
            console.error('Error evaluating condition:', error, condition);
            result = true; // Default to visible on error
        }
        
        // Cache result
        if (this._cacheEnabled) {
            const cacheKey = JSON.stringify({ condition, formData });
            this._cache.set(cacheKey, result);
            
            // Limit cache size
            if (this._cache.size > 1000) {
                const firstKey = this._cache.keys().next().value;
                this._cache.delete(firstKey);
            }
        }
        
        return result;
    }
    
    /**
     * Internal condition evaluation logic
     * @private
     */
    static _evaluateConditionInternal(condition, formData) {
        const operator = condition.operator;
        if (!operator) return true;
        
        // Handle logical operators
        if (operator === 'and') {
            const conditions = condition.conditions || [];
            return conditions.every(c => this.evaluateCondition(c, formData));
        } else if (operator === 'or') {
            const conditions = condition.conditions || [];
            return conditions.some(c => this.evaluateCondition(c, formData));
        } else if (operator === 'not') {
            return !this.evaluateCondition(condition.condition, formData);
        }
        
        // Handle field-based operators
        const field = condition.field;
        if (!field) return true;
        
        const fieldValue = this.getFieldValue(field, formData);
        const expectedValue = condition.value;
        
        const operatorFn = this.OPERATORS[operator];
        if (!operatorFn) {
            throw new Error(`Unknown operator: ${operator}`);
        }
        
        return operatorFn(fieldValue, expectedValue);
    }
    
    /**
     * Get field value supporting dot notation for nested fields
     * @param {string} fieldPath - Field path (supports dot notation like "parent.child")
     * @param {Object} formData - Form data object
     * @returns {*} Field value or undefined if not found
     */
    static getFieldValue(fieldPath, formData) {
        if (!fieldPath.includes('.')) {
            return formData[fieldPath];
        }
        
        // Support nested field access: "parent.child.grandchild"
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
    
    /**
     * Evaluate multiple conditions and return visibility map
     * @param {Object} conditionalLogic - Map of field names to conditions
     * @param {Object} formData - Current form data
     * @returns {Object} Map of field names to visibility boolean
     */
    static evaluateAllConditions(conditionalLogic, formData) {
        const visibility = {};
        
        for (const [fieldName, condition] of Object.entries(conditionalLogic)) {
            visibility[fieldName] = this.evaluateCondition(condition, formData);
        }
        
        return visibility;
    }
    
    /**
     * Clear evaluation cache
     */
    static clearCache() {
        this._cache.clear();
    }
    
    /**
     * Enable or disable caching
     * @param {boolean} enabled - Whether to enable caching
     */
    static setCacheEnabled(enabled) {
        this._cacheEnabled = enabled;
        if (!enabled) {
            this.clearCache();
        }
    }
    
    /**
     * Get cache statistics
     * @returns {Object} Cache statistics
     */
    static getCacheStats() {
        return {
            size: this._cache.size,
            enabled: this._cacheEnabled
        };
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConditionEvaluator;
}

// Make available globally
if (typeof window !== 'undefined') {
    window.ConditionEvaluator = ConditionEvaluator;
}