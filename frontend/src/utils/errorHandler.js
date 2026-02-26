/**
 * Error handling utility for API responses
 * Provides consistent error handling and user-friendly messages
 */

/**
 * Map HTTP status codes to user-friendly messages
 */
const ERROR_MESSAGES = {
  400: 'Invalid data provided. Please check your input and try again.',
  401: 'You need to log in to access this feature.',
  403: 'You don\'t have permission to perform this action.',
  404: 'The requested resource was not found.',
  409: 'This resource already exists.',
  500: 'Server error. Please try again later.',
  503: 'Service temporarily unavailable. Please try again later.',
};

/**
 * Handle API errors and return user-friendly error object
 * @param {Error} error - The error object from API call
 * @returns {Object} - Formatted error object with message and code
 */
export function handleApiError(error) {
  // Network error (no response from server)
  if (!error.response) {
    return {
      message: 'Network error. Please check your connection and try again.',
      code: 'NETWORK_ERROR',
      shouldRetry: true,
    };
  }

  const status = error.response?.status;
  const data = error.response?.data;

  // Extract error message from response
  let message = ERROR_MESSAGES[status] || 'An unexpected error occurred.';
  
  // If server provided a specific error message, use it
  if (data?.message) {
    message = data.message;
  } else if (data?.error) {
    message = data.error;
  } else if (data?.errors) {
    // Handle validation errors (array of errors)
    if (Array.isArray(data.errors)) {
      message = data.errors.join(', ');
    } else if (typeof data.errors === 'object') {
      // Handle field-specific errors
      message = Object.entries(data.errors)
        .map(([field, error]) => `${field}: ${error}`)
        .join(', ');
    }
  }

  return {
    message,
    code: status,
    shouldRetry: status >= 500, // Retry on server errors
    shouldRedirect: status === 401, // Redirect to login on auth error
  };
}

/**
 * Show toast notification (placeholder - can be replaced with actual toast library)
 * @param {string} message - Message to display
 * @param {string} type - Type of notification ('success', 'error', 'warning', 'info')
 */
export function showToast(message, type = 'info') {
  // For now, use console and alert
  // In production, replace with a toast library like react-toastify
  console.log(`[${type.toUpperCase()}]`, message);
  
  // You can uncomment this for actual alerts during development
  // if (type === 'error') {
  //   alert(`Error: ${message}`);
  // }
}

/**
 * Handle successful operations with toast notification
 * @param {string} message - Success message
 */
export function handleSuccess(message) {
  showToast(message, 'success');
}

/**
 * Handle errors with toast notification
 * @param {Error} error - Error object
 * @param {string} fallbackMessage - Fallback message if error parsing fails
 */
export function handleError(error, fallbackMessage = 'An error occurred') {
  const errorInfo = handleApiError(error);
  showToast(errorInfo.message || fallbackMessage, 'error');
  
  // Redirect to login if unauthorized
  if (errorInfo.shouldRedirect) {
    setTimeout(() => {
      window.location.href = '/auth';
    }, 1500);
  }
  
  return errorInfo;
}

/**
 * Retry function with exponential backoff
 * @param {Function} fn - Async function to retry
 * @param {number} maxRetries - Maximum number of retries
 * @param {number} delay - Initial delay in ms
 * @returns {Promise} - Result of the function
 */
export async function retryWithBackoff(fn, maxRetries = 3, delay = 1000) {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      const errorInfo = handleApiError(error);
      
      // Don't retry if it's not a retryable error
      if (!errorInfo.shouldRetry) {
        throw error;
      }
      
      // Don't retry on last attempt
      if (i < maxRetries - 1) {
        const backoffDelay = delay * Math.pow(2, i);
        console.log(`Retrying in ${backoffDelay}ms... (attempt ${i + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, backoffDelay));
      }
    }
  }
  
  throw lastError;
}

/**
 * Validate form data and return errors
 * @param {Object} data - Form data to validate
 * @param {Object} rules - Validation rules
 * @returns {Object} - Object with field errors
 */
export function validateForm(data, rules) {
  const errors = {};
  
  for (const [field, rule] of Object.entries(rules)) {
    const value = data[field];
    
    // Required check
    if (rule.required && (!value || value.toString().trim() === '')) {
      errors[field] = `${rule.label || field} is required`;
      continue;
    }
    
    // Skip other validations if field is empty and not required
    if (!value && !rule.required) {
      continue;
    }
    
    // Min length
    if (rule.minLength && value.length < rule.minLength) {
      errors[field] = `${rule.label || field} must be at least ${rule.minLength} characters`;
    }
    
    // Max length
    if (rule.maxLength && value.length > rule.maxLength) {
      errors[field] = `${rule.label || field} must be at most ${rule.maxLength} characters`;
    }
    
    // Pattern
    if (rule.pattern && !rule.pattern.test(value)) {
      errors[field] = rule.patternMessage || `${rule.label || field} format is invalid`;
    }
    
    // Min value
    if (rule.min !== undefined && Number(value) < rule.min) {
      errors[field] = `${rule.label || field} must be at least ${rule.min}`;
    }
    
    // Max value
    if (rule.max !== undefined && Number(value) > rule.max) {
      errors[field] = `${rule.label || field} must be at most ${rule.max}`;
    }
    
    // Custom validator
    if (rule.validator) {
      const customError = rule.validator(value, data);
      if (customError) {
        errors[field] = customError;
      }
    }
  }
  
  return errors;
}

export default {
  handleApiError,
  handleError,
  handleSuccess,
  showToast,
  retryWithBackoff,
  validateForm,
};
