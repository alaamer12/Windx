/**
 * Enhanced error handling utilities for API responses
 */

export interface ApiError {
  message: string
  type: 'network' | 'server' | 'validation' | 'auth' | 'unknown'
  status?: number
  details?: any
}

/**
 * Extract meaningful error information from various error types
 */
export function parseApiError(error: any): ApiError {
  // Network/Connection errors
  if (!error.response) {
    if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
      return {
        message: 'Unable to connect to server. Please check your internet connection.',
        type: 'network'
      }
    }
    
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return {
        message: 'Request timed out. Please try again.',
        type: 'network'
      }
    }
    
    return {
      message: error.message || 'Connection failed. Please try again.',
      type: 'network'
    }
  }

  const status = error.response.status
  const data = error.response.data

  // Authentication errors
  if (status === 401) {
    return {
      message: 'Authentication required. Please log in.',
      type: 'auth',
      status
    }
  }

  if (status === 403) {
    return {
      message: 'Access denied. You don\'t have permission for this action.',
      type: 'auth',
      status
    }
  }

  // Validation errors (400)
  if (status === 400) {
    let message = 'Invalid request data.'
    
    if (data?.detail) {
      if (typeof data.detail === 'string') {
        message = data.detail
      } else if (Array.isArray(data.detail)) {
        // FastAPI validation errors
        const validationErrors = data.detail.map((err: any) => {
          const field = err.loc?.join('.') || 'field'
          return `${field}: ${err.msg}`
        }).join(', ')
        message = `Validation errors: ${validationErrors}`
      }
    }
    
    return {
      message,
      type: 'validation',
      status,
      details: data
    }
  }

  // Server errors (500)
  if (status >= 500) {
    let message = 'Server error occurred. Please try again later.'
    
    // Try to extract more specific error information
    if (data?.detail) {
      if (typeof data.detail === 'string') {
        // Check for common database errors
        if (data.detail.includes('duplicate key') || data.detail.includes('already exists')) {
          message = 'This item already exists. Please use a different name.'
        } else if (data.detail.includes('foreign key') || data.detail.includes('not found')) {
          message = 'Referenced item not found. Please check your selections.'
        } else if (data.detail.includes('invalid input') || data.detail.includes('cannot be interpreted')) {
          message = 'Invalid data format. Please check your input values.'
        } else {
          message = `Server error: ${data.detail}`
        }
      }
    }
    
    return {
      message,
      type: 'server',
      status,
      details: data
    }
  }

  // Client errors (404, etc.)
  if (status >= 400 && status < 500) {
    let message = `Request failed (${status}).`
    
    if (data?.detail) {
      message = typeof data.detail === 'string' ? data.detail : message
    }
    
    return {
      message,
      type: 'unknown',
      status,
      details: data
    }
  }

  // Fallback for unknown errors
  return {
    message: error.message || 'An unexpected error occurred.',
    type: 'unknown',
    status,
    details: data
  }
}

/**
 * Get a user-friendly error message from any error
 */
export function getErrorMessage(error: any): string {
  return parseApiError(error).message
}