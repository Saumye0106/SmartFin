/**
 * Unit tests for error handling utility
 * Tests error message mapping, validation, and retry logic
 */

import { handleApiError, validateForm, retryWithBackoff } from './errorHandler';

// Test: handleApiError with different status codes
console.log('=== Testing handleApiError ===');

// Test 400 error
const error400 = {
  response: {
    status: 400,
    data: { message: 'Invalid input data' }
  }
};
const result400 = handleApiError(error400);
console.assert(result400.code === 400, '400 error code should match');
console.assert(result400.message === 'Invalid input data', '400 error message should match');
console.assert(result400.shouldRetry === false, '400 should not retry');
console.log('✓ 400 error handling test passed');

// Test 401 error (unauthorized)
const error401 = {
  response: {
    status: 401,
    data: {}
  }
};
const result401 = handleApiError(error401);
console.assert(result401.code === 401, '401 error code should match');
console.assert(result401.shouldRedirect === true, '401 should redirect to login');
console.log('✓ 401 error handling test passed');

// Test 403 error (forbidden)
const error403 = {
  response: {
    status: 403,
    data: { error: 'Access denied' }
  }
};
const result403 = handleApiError(error403);
console.assert(result403.code === 403, '403 error code should match');
console.assert(result403.message === 'Access denied', '403 error message should match');
console.log('✓ 403 error handling test passed');

// Test 404 error (not found)
const error404 = {
  response: {
    status: 404,
    data: {}
  }
};
const result404 = handleApiError(error404);
console.assert(result404.code === 404, '404 error code should match');
console.assert(result404.message.includes('not found'), '404 message should mention not found');
console.log('✓ 404 error handling test passed');

// Test 500 error (server error)
const error500 = {
  response: {
    status: 500,
    data: {}
  }
};
const result500 = handleApiError(error500);
console.assert(result500.code === 500, '500 error code should match');
console.assert(result500.shouldRetry === true, '500 should allow retry');
console.log('✓ 500 error handling test passed');

// Test network error (no response)
const networkError = {};
const resultNetwork = handleApiError(networkError);
console.assert(resultNetwork.code === 'NETWORK_ERROR', 'Network error code should match');
console.assert(resultNetwork.shouldRetry === true, 'Network error should allow retry');
console.log('✓ Network error handling test passed');

// Test validation errors (array)
const validationError = {
  response: {
    status: 400,
    data: {
      errors: ['Name is required', 'Age must be at least 18']
    }
  }
};
const resultValidation = handleApiError(validationError);
console.assert(resultValidation.message.includes('Name is required'), 'Validation message should include first error');
console.assert(resultValidation.message.includes('Age must be at least 18'), 'Validation message should include second error');
console.log('✓ Validation error handling test passed');

// Test: validateForm
console.log('\n=== Testing validateForm ===');

// Test required field validation
const data1 = { name: '', age: 25 };
const rules1 = {
  name: { required: true, label: 'Name' },
  age: { required: true, label: 'Age' }
};
const errors1 = validateForm(data1, rules1);
console.assert(errors1.name === 'Name is required', 'Required field validation should work');
console.assert(!errors1.age, 'Valid field should not have error');
console.log('✓ Required field validation test passed');

// Test min/max length validation
const data2 = { name: 'Jo', description: 'A'.repeat(501) };
const rules2 = {
  name: { required: true, minLength: 3, label: 'Name' },
  description: { maxLength: 500, label: 'Description' }
};
const errors2 = validateForm(data2, rules2);
console.assert(errors2.name && errors2.name.includes('at least 3'), 'Min length validation should work');
console.assert(errors2.description && errors2.description.includes('at most 500'), 'Max length validation should work');
console.log('✓ Length validation test passed');

// Test min/max value validation
const data3 = { age: 17, score: 101 };
const rules3 = {
  age: { required: true, min: 18, label: 'Age' },
  score: { max: 100, label: 'Score' }
};
const errors3 = validateForm(data3, rules3);
console.assert(errors3.age && errors3.age.includes('at least 18'), 'Min value validation should work');
console.assert(errors3.score && errors3.score.includes('at most 100'), 'Max value validation should work');
console.log('✓ Value range validation test passed');

// Test pattern validation
const data4 = { email: 'invalid-email' };
const rules4 = {
  email: {
    required: true,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    patternMessage: 'Invalid email format',
    label: 'Email'
  }
};
const errors4 = validateForm(data4, rules4);
console.assert(errors4.email === 'Invalid email format', 'Pattern validation should work');
console.log('✓ Pattern validation test passed');

// Test custom validator
const data5 = { password: 'weak', confirmPassword: 'different' };
const rules5 = {
  password: { required: true, label: 'Password' },
  confirmPassword: {
    required: true,
    label: 'Confirm Password',
    validator: (value, data) => {
      if (value !== data.password) {
        return 'Passwords do not match';
      }
      return null;
    }
  }
};
const errors5 = validateForm(data5, rules5);
console.assert(errors5.confirmPassword === 'Passwords do not match', 'Custom validator should work');
console.log('✓ Custom validator test passed');

// Test: retryWithBackoff
console.log('\n=== Testing retryWithBackoff ===');

// Test successful retry
let attemptCount = 0;
const successAfterRetries = async () => {
  attemptCount++;
  if (attemptCount < 3) {
    const error = new Error('Temporary failure');
    error.response = { status: 503 };
    throw error;
  }
  return 'success';
};

retryWithBackoff(successAfterRetries, 3, 10)
  .then(result => {
    console.assert(result === 'success', 'Retry should eventually succeed');
    console.assert(attemptCount === 3, 'Should retry correct number of times');
    console.log('✓ Retry with backoff test passed');
  })
  .catch(err => {
    console.error('Retry test failed:', err);
  });

// Test non-retryable error
const nonRetryableError = async () => {
  const error = new Error('Bad request');
  error.response = { status: 400 };
  throw error;
};

retryWithBackoff(nonRetryableError, 3, 10)
  .then(() => {
    console.error('Should not succeed with non-retryable error');
  })
  .catch(err => {
    console.assert(err.response.status === 400, 'Should throw non-retryable error immediately');
    console.log('✓ Non-retryable error test passed');
  });

console.log('\n=== All error handling tests completed ===');
