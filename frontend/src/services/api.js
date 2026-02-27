import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';
const AUTH_BASE_URL = import.meta.env.VITE_AUTH_BASE_URL || 'http://127.0.0.1:5000';

// Set up axios interceptor to handle 401 errors
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('=== 401 AUTHENTICATION ERROR ===');
      console.error('Request URL:', error.config?.url);
      console.error('Request method:', error.config?.method);
      console.error('Request headers:', error.config?.headers);
      console.error('Error response:', error.response?.data);
      console.error('Token in localStorage:', localStorage.getItem('sf_token'));
      console.error('Token in axios defaults:', axios.defaults.headers.common['Authorization']);
      console.error('================================');
      
      // Token expired or invalid - redirect to login after a delay
      setTimeout(() => {
        localStorage.removeItem('sf_token');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userId');
        delete axios.defaults.headers.common['Authorization'];
        window.location.href = '/auth';
      }, 2000); // Increased delay to 2 seconds to see console logs
    }
    return Promise.reject(error);
  }
);

// Initialize auth token from localStorage on app load
const storedToken = localStorage.getItem('sf_token');
if (storedToken && storedToken !== 'demo-token') {
  axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
}

const api = {
  async predict(financialData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/predict`, financialData);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw new Error('Failed to get prediction. Make sure the backend is running.');
    }
  },

  async whatIf(currentData, modifiedData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/whatif`, {
        current: currentData,
        modified: modifiedData
      });
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw new Error('Failed to run simulation.');
    }
  },

  async getModelInfo() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/model-info`);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw new Error('Failed to get model info.');
    }
  }
  ,
  // Auth methods
  async register(email, password) {
    try {
      const response = await axios.post(`${AUTH_BASE_URL}/register`, { email, password });
      return response.data;
    } catch (error) {
      console.error('Auth register error:', error);
      const errorMsg = error?.response?.data?.error || error?.response?.data?.message || 'Registration failed';
      throw new Error(errorMsg);
    }
  },

  async login(email, password) {
    try {
      const response = await axios.post(`${AUTH_BASE_URL}/login`, { email, password });
      const token = response.data?.token;
      if (token) {
        this.setAuthToken(token);
      }
      return response.data;
    } catch (error) {
      console.error('Auth login error:', error);
      const errorMsg = error?.response?.data?.error || error?.response?.data?.message || 'Login failed';
      throw new Error(errorMsg);
    }
  },

  // Password Reset methods
  async forgotPassword(email) {
    try {
      const response = await axios.post(`${AUTH_BASE_URL}/forgot-password`, { email });
      return response.data;
    } catch (error) {
      console.error('Forgot password error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to generate reset code';
      throw new Error(errorMsg);
    }
  },

  async verifyResetCode(email, resetCode) {
    try {
      const response = await axios.post(`${AUTH_BASE_URL}/verify-reset-code`, { 
        email, 
        reset_code: resetCode 
      });
      return response.data;
    } catch (error) {
      console.error('Verify reset code error:', error);
      const errorMsg = error?.response?.data?.error || 'Invalid reset code';
      throw new Error(errorMsg);
    }
  },

  async resetPassword(email, resetCode, newPassword) {
    try {
      const response = await axios.post(`${AUTH_BASE_URL}/reset-password`, { 
        email, 
        reset_code: resetCode,
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      console.error('Reset password error:', error);
      const errorMsg = error?.response?.data?.error || 'Password reset failed';
      throw new Error(errorMsg);
    }
  },

  setAuthToken(token) {
    if (token) {
      localStorage.setItem('sf_token', token);
      if (token !== 'demo-token') {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      }
    } else {
      localStorage.removeItem('sf_token');
      delete axios.defaults.headers.common['Authorization'];
    }
  },

  getStoredToken() {
    return localStorage.getItem('sf_token');
  },

  // Profile Management methods
  async createProfile(profileData) {
    try {
      const token = this.getStoredToken();
      const response = await axios.post(`${API_BASE_URL}/api/profile/create`, profileData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Create profile error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to create profile';
      throw new Error(errorMsg);
    }
  },

  async getProfile() {
    try {
      const token = this.getStoredToken();
      const response = await axios.get(`${API_BASE_URL}/api/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      if (error?.response?.status === 404) {
        return null; // Profile doesn't exist yet
      }
      console.error('Get profile error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to get profile';
      throw new Error(errorMsg);
    }
  },

  async updateProfile(updates) {
    try {
      const token = this.getStoredToken();
      const response = await axios.put(`${API_BASE_URL}/api/profile/update`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Update profile error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to update profile';
      throw new Error(errorMsg);
    }
  },

  async createGoal(goalData) {
    try {
      const token = this.getStoredToken();
      const response = await axios.post(`${API_BASE_URL}/api/profile/goals`, goalData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Create goal error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to create goal';
      throw new Error(errorMsg);
    }
  },

  async getGoals(status = null) {
    try {
      const token = this.getStoredToken();
      const url = status 
        ? `${API_BASE_URL}/api/profile/goals?status=${status}`
        : `${API_BASE_URL}/api/profile/goals`;
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Get goals error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to get goals';
      throw new Error(errorMsg);
    }
  },

  async updateGoal(goalId, updates) {
    try {
      const token = this.getStoredToken();
      const response = await axios.put(`${API_BASE_URL}/api/profile/goals/${goalId}`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Update goal error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to update goal';
      throw new Error(errorMsg);
    }
  },

  async deleteGoal(goalId) {
    try {
      const token = this.getStoredToken();
      await axios.delete(`${API_BASE_URL}/api/profile/goals/${goalId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return true;
    } catch (error) {
      console.error('Delete goal error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to delete goal';
      throw new Error(errorMsg);
    }
  },

  // Investment Calculator methods
  async calculateSIP(sipData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/sip-calculator`, sipData);
      return response.data;
    } catch (error) {
      console.error('SIP calculation error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to calculate SIP';
      throw new Error(errorMsg);
    }
  },

  async calculateLumpsum(lumpsumData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/lumpsum-calculator`, lumpsumData);
      return response.data;
    } catch (error) {
      console.error('Lumpsum calculation error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to calculate Lumpsum';
      throw new Error(errorMsg);
    }
  },

  // Twilio OTP methods
  async sendOTP(to, channel = 'sms') {
    try {
      const response = await axios.post(`${AUTH_BASE_URL}/send-otp`, { to, channel });
      return response.data;
    } catch (error) {
      console.error('Send OTP error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to send OTP';
      throw new Error(errorMsg);
    }
  },

  async verifyOTP(to, code) {
    try {
      const response = await axios.post(`${AUTH_BASE_URL}/verify-otp`, { to, code });
      return response.data;
    } catch (error) {
      console.error('Verify OTP error:', error);
      const errorMsg = error?.response?.data?.error || 'Invalid or expired OTP';
      throw new Error(errorMsg);
    }
  },

  async forgotPasswordOTP(email, otpCode = null, newPassword = null) {
    try {
      const payload = { email };
      if (otpCode && newPassword) {
        payload.otp_code = otpCode;
        payload.new_password = newPassword;
      }
      
      const response = await axios.post(`${AUTH_BASE_URL}/forgot-password-otp`, payload);
      return response.data;
    } catch (error) {
      console.error('Forgot password OTP error:', error);
      const errorMsg = error?.response?.data?.error || 'Password reset failed';
      throw new Error(errorMsg);
    }
  },

  // Phone Management methods
  async getUserPhone() {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found. Please login again.');
      }
      const response = await axios.get(`${AUTH_BASE_URL}/get-phone`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Get phone error:', error);
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please login again.');
      }
      const errorMsg = error?.response?.data?.error || error.message || 'Failed to get phone number';
      throw new Error(errorMsg);
    }
  },

  async updatePhone(phone, otpCode = null) {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found. Please login again.');
      }
      const payload = { phone };
      if (otpCode) {
        payload.otp_code = otpCode;
      }
      
      const response = await axios.post(`${AUTH_BASE_URL}/update-phone`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Update phone error:', error);
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please login again.');
      }
      const errorMsg = error?.response?.data?.error || error.message || 'Failed to update phone number';
      throw new Error(errorMsg);
    }
  },

  // Email Verification methods
  async sendEmailVerification(email, userId = null) {
    try {
      const payload = { email };
      if (userId) {
        payload.user_id = userId;
      }
      const response = await axios.post(`${AUTH_BASE_URL}/send-email-verification`, payload);
      return response.data;
    } catch (error) {
      console.error('Send email verification error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to send verification code';
      throw new Error(errorMsg);
    }
  },

  async verifyEmail(email, code, userId = null) {
    try {
      const payload = { email, code };
      if (userId) {
        payload.user_id = userId;
      }
      const response = await axios.post(`${AUTH_BASE_URL}/verify-email`, payload);
      return response.data;
    } catch (error) {
      console.error('Verify email error:', error);
      const errorMsg = error?.response?.data?.error || 'Invalid or expired verification code';
      throw new Error(errorMsg);
    }
  },

  async checkEmailVerification() {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }
      const response = await axios.get(`${AUTH_BASE_URL}/check-email-verification`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Check email verification error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to check verification status';
      throw new Error(errorMsg);
    }
  },

  // Profile Picture methods
  async uploadProfilePicture(file) {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE_URL}/api/profile/upload-picture`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Upload profile picture error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to upload profile picture';
      throw new Error(errorMsg);
    }
  },

  async deleteProfilePicture() {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await axios.delete(`${API_BASE_URL}/api/profile/delete-picture`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Delete profile picture error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to delete profile picture';
      throw new Error(errorMsg);
    }
  },

  // Loan Management methods
  async createLoan(loanData) {
    try {
      const token = this.getStoredToken();
      console.log('createLoan - Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'null');
      console.log('createLoan - Global axios auth header:', axios.defaults.headers.common['Authorization']);
      
      if (!token) {
        throw new Error('No authentication token found');
      }

      console.log('createLoan - Making request to:', `${API_BASE_URL}/api/loans`);
      console.log('createLoan - Loan data:', loanData);
      
      const response = await axios.post(`${API_BASE_URL}/api/loans`, loanData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('createLoan - Success:', response.data);
      return response.data;
    } catch (error) {
      console.error('Create loan error:', error);
      console.error('Error response:', error?.response);
      console.error('Error status:', error?.response?.status);
      console.error('Error data:', error?.response?.data);
      const errorMsg = error?.response?.data?.message || error?.response?.data?.error || 'Failed to create loan';
      throw new Error(errorMsg);
    }
  },

  async getUserLoans(userId) {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await axios.get(`${API_BASE_URL}/api/loans/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Get user loans error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to get loans';
      throw new Error(errorMsg);
    }
  },

  async getLoan(loanId) {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await axios.get(`${API_BASE_URL}/api/loans/${loanId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Get loan error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to get loan';
      throw new Error(errorMsg);
    }
  },

  async updateLoan(loanId, updates) {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await axios.put(`${API_BASE_URL}/api/loans/${loanId}`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Update loan error:', error);
      const errorMsg = error?.response?.data?.message || error?.response?.data?.error || 'Failed to update loan';
      throw new Error(errorMsg);
    }
  },

  async deleteLoan(loanId) {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      console.log('Deleting loan:', loanId);
      const response = await axios.delete(`${API_BASE_URL}/api/loans/${loanId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('Delete response:', response.status, response.data);
      return response.data;
    } catch (error) {
      console.error('Delete loan error:', error);
      const errorMsg = error?.response?.data?.message || error?.response?.data?.error || 'Failed to delete loan';
      console.error('Error message:', errorMsg);
      throw new Error(errorMsg);
    }
  },

  async recordPayment(loanId, paymentData) {
    try {
      const token = this.getStoredToken();
      console.log('recordPayment - Token:', token ? `${token.substring(0, 20)}...` : 'null');
      console.log('recordPayment - Loan ID:', loanId);
      console.log('recordPayment - Payment data:', paymentData);
      
      if (!token) {
        throw new Error('No authentication token found');
      }

      console.log('recordPayment - Making request to:', `${API_BASE_URL}/api/loans/${loanId}/payments`);
      const response = await axios.post(`${API_BASE_URL}/api/loans/${loanId}/payments`, paymentData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('recordPayment - Success:', response.data);
      return response.data;
    } catch (error) {
      console.error('Record payment error:', error);
      console.error('Error response:', error?.response?.data);
      console.error('Error status:', error?.response?.status);
      const errorMsg = error?.response?.data?.message || error?.response?.data?.error || error.message || 'Failed to record payment';
      throw new Error(errorMsg);
    }
  },

  async getPaymentHistory(loanId) {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await axios.get(`${API_BASE_URL}/api/loans/${loanId}/payments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Get payment history error:', error);
      const errorMsg = error?.response?.data?.error || 'Failed to get payment history';
      throw new Error(errorMsg);
    }
  },

  async deletePayment(loanId, paymentId) {
    try {
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      console.log('Deleting payment:', paymentId, 'for loan:', loanId);
      const response = await axios.delete(`${API_BASE_URL}/api/loans/${loanId}/payments/${paymentId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('Delete payment response:', response.status, response.data);
      return response.data;
    } catch (error) {
      console.error('Delete payment error:', error);
      const errorMsg = error?.response?.data?.message || error?.response?.data?.error || 'Failed to delete payment';
      throw new Error(errorMsg);
    }
  },

  async getLoanMetrics(userId) {
    try {
      console.log('getLoanMetrics called with userId:', userId);
      
      if (!userId) {
        throw new Error('User ID is required');
      }
      
      const token = this.getStoredToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      console.log('Making request to:', `${API_BASE_URL}/api/loans/metrics/${userId}`);
      const response = await axios.get(`${API_BASE_URL}/api/loans/metrics/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('getLoanMetrics response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Get loan metrics error:', error);
      console.error('Error response:', error?.response?.data);
      const errorMsg = error?.response?.data?.message || error?.response?.data?.error || error.message || 'Failed to get loan metrics';
      throw new Error(errorMsg);
    }
  },
};


export default api;
