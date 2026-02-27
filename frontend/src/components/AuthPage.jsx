import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const AuthPage = ({ onAuthSuccess, onBack }) => {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    rememberMe: false
  });
  const [errors, setErrors] = useState({});
  const [globalError, setGlobalError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const validateEmail = (email) => {
    // Comprehensive email validation regex
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address (e.g., user@example.com)';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (!isLogin && formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
    setGlobalError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGlobalError('');

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      let response;
      if (isLogin) {
        response = await api.login(formData.email, formData.password);
        
        if (response.token) {
          localStorage.setItem('token', response.token);
          localStorage.setItem('userEmail', formData.email);
          if (response.user?.id) {
            localStorage.setItem('userId', response.user.id.toString());
          }
          onAuthSuccess(response);
        }
      } else {
        // Registration
        response = await api.register(formData.email, formData.password);
        
        if (response.token) {
          localStorage.setItem('token', response.token);
          localStorage.setItem('userEmail', formData.email);
          if (response.user?.id) {
            localStorage.setItem('userId', response.user.id.toString());
          }
          
          // Redirect to email verification page
          navigate('/verify-email', {
            state: {
              email: formData.email,
              userId: response.user?.id,
              verificationSent: response.verification_sent
            }
          });
        }
      }
    } catch (error) {
      console.error('Authentication error:', error);
      
      if (error.message.includes('Network')) {
        setGlobalError('Unable to connect to server. Please check your connection and try again.');
      } else if (error.message.includes('Invalid credentials')) {
        setErrors({
          email: 'Invalid credentials',
          password: 'Invalid credentials'
        });
        setGlobalError('Your credentials could not be verified. Please check your inputs and try again.');
      } else if (error.message.includes('already exists')) {
        setErrors({
          email: 'This email is already registered'
        });
        setGlobalError('An account with this email already exists. Please login instead.');
      } else {
        setGlobalError(error.message || 'An error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({
      email: '',
      password: '',
      confirmPassword: '',
      rememberMe: false
    });
    setErrors({});
    setGlobalError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden font-sans">
      {/* Background Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid pointer-events-none"></div>
        <div className="absolute top-[-20%] left-[20%] w-[600px] h-[600px] bg-cyan-900/10 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-purple-900/10 rounded-full blur-[120px] mix-blend-screen"></div>
      </div>

      {/* Navigation/Brand Header */}
      <div className="absolute top-8 left-8 z-50">
        <button 
          onClick={() => navigate('/')} 
          className="flex items-center gap-3 group opacity-80 hover:opacity-100 transition-opacity"
        >
          <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-cyan-500/50 transition-colors">
            <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-cyan-400 text-xl"></iconify-icon>
          </div>
          <span className="font-display font-semibold text-white tracking-tight">SmartFin</span>
        </button>
      </div>

      {/* Main Auth Card */}
      <main className="w-full max-w-md px-6 relative z-10">
        <div className="glass-panel rounded-2xl p-8 md:p-10 relative overflow-hidden animate-fade-in-up">
          {/* Header */}
          <div className="mb-8 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-tr from-cyan-500/10 to-transparent border border-white/5 mb-4 shadow-lg shadow-cyan-900/20">
              <iconify-icon icon="solar:shield-keyhole-linear" className="text-cyan-400 text-2xl"></iconify-icon>
            </div>
            <h1 className="font-display text-2xl font-semibold text-white mb-2 tracking-tight">
              {isLogin ? 'Welcome back' : 'Create Account'}
            </h1>
            <p className="text-sm text-white/50">
              {isLogin ? 'Enter your credentials to access the neural engine.' : 'Start your journey to financial wellness.'}
            </p>
          </div>

          {/* Global Error Banner */}
          {globalError && (
            <div className="mb-6 p-3 rounded-lg bg-danger-950/30 border border-danger-500/30 flex items-start gap-3 animate-fade-in">
              <iconify-icon icon="solar:danger-triangle-linear" className="text-danger-400 mt-0.5 shrink-0"></iconify-icon>
              <div className="text-xs text-danger-400 leading-relaxed">
                <span className="font-semibold block mb-0.5">Authentication Failed</span>
                {globalError}
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            {/* Email Input */}
            <div className="space-y-1.5 group">
              <label htmlFor="email" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-cyan-400">
                Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={`w-full bg-[#0a0a0a] border ${errors.email ? 'border-danger-500/50 bg-danger-950/5' : 'border-white/10'} rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200`}
                  placeholder="name@smartfin.ai"
                />
                <iconify-icon 
                  icon="solar:letter-linear" 
                  className={`absolute left-3.5 top-3 ${errors.email ? 'text-danger-500' : 'text-white/30 group-focus-within:text-cyan-400'} transition-colors text-lg`}
                ></iconify-icon>
                {errors.email && (
                  <iconify-icon icon="solar:danger-circle-bold" className="absolute right-3.5 top-3 text-danger-500 text-lg"></iconify-icon>
                )}
              </div>
              {errors.email && (
                <p className="text-[11px] text-danger-400 font-medium pl-1 animate-fade-in">{errors.email}</p>
              )}
            </div>

            {/* Password Input */}
            <div className="space-y-1.5 group">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-cyan-400">
                  Password
                </label>
                {isLogin && (
                  <button 
                    type="button"
                    onClick={() => navigate('/forgot-password')} 
                    className="text-[11px] text-white/40 hover:text-cyan-400 transition-colors"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className={`w-full bg-[#0a0a0a] border ${errors.password ? 'border-danger-500/50 bg-danger-950/5' : 'border-white/10'} rounded-lg px-4 py-2.5 pl-10 pr-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200`}
                  placeholder="••••••••••••"
                />
                <iconify-icon 
                  icon="solar:lock-password-linear" 
                  className={`absolute left-3.5 top-3 ${errors.password ? 'text-danger-500' : 'text-white/30 group-focus-within:text-cyan-400'} transition-colors text-lg`}
                ></iconify-icon>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-white/30 hover:text-white transition-colors focus:outline-none"
                >
                  <iconify-icon icon={showPassword ? 'solar:eye-closed-linear' : 'solar:eye-linear'} className="text-lg"></iconify-icon>
                </button>
              </div>
              {errors.password && (
                <p className="text-[11px] text-danger-400 font-medium pl-1 animate-fade-in">{errors.password}</p>
              )}
            </div>

            {/* Confirm Password (Register only) */}
            {!isLogin && (
              <div className="space-y-1.5 group">
                <label htmlFor="confirmPassword" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-cyan-400">
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className={`w-full bg-[#0a0a0a] border ${errors.confirmPassword ? 'border-danger-500/50 bg-danger-950/5' : 'border-white/10'} rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200`}
                    placeholder="••••••••••••"
                  />
                  <iconify-icon 
                    icon="solar:lock-password-linear" 
                    className={`absolute left-3.5 top-3 ${errors.confirmPassword ? 'text-danger-500' : 'text-white/30 group-focus-within:text-cyan-400'} transition-colors text-lg`}
                  ></iconify-icon>
                </div>
                {errors.confirmPassword && (
                  <p className="text-[11px] text-danger-400 font-medium pl-1 animate-fade-in">{errors.confirmPassword}</p>
                )}
              </div>
            )}

            {/* Remember Me */}
            {isLogin && (
              <label className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleInputChange}
                  className="peer sr-only"
                />
                <div className="w-4 h-4 rounded border border-white/20 bg-white/5 flex items-center justify-center transition-all peer-focus:ring-2 peer-focus:ring-cyan-500/30 group-hover:border-white/30 peer-checked:bg-cyan-500 peer-checked:border-cyan-500">
                  <iconify-icon icon="solar:check-read-linear" className="text-[10px] text-black opacity-0 peer-checked:opacity-100 transform scale-50 peer-checked:scale-100 transition-all"></iconify-icon>
                </div>
                <span className="text-xs text-white/60 group-hover:text-white/80 transition-colors select-none">
                  Keep me logged in for 30 days
                </span>
              </label>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="relative w-full group overflow-hidden rounded-lg bg-white py-2.5 transition-all hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {!isLoading && (
                <>
                  <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                  <span className="relative text-sm font-semibold text-black flex items-center justify-center gap-2">
                    {isLogin ? 'Sign In' : 'Create Account'}
                    <iconify-icon icon="solar:arrow-right-linear" className="transition-transform group-hover:translate-x-1"></iconify-icon>
                  </span>
                </>
              )}
              {isLoading && (
                <div className="flex items-center justify-center text-black">
                  <iconify-icon icon="solar:spinner-solid" className="animate-spin text-xl"></iconify-icon>
                </div>
              )}
            </button>

            {/* Divider */}
            <div className="relative py-2">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10"></div>
              </div>
              <div className="relative flex justify-center text-[10px] uppercase tracking-widest">
                <span className="bg-[#0a0a0a] px-2 text-white/30">Or continue with</span>
              </div>
            </div>

            {/* Social Auth */}
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                className="flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 py-2 px-4 text-xs font-medium text-white hover:bg-white/10 hover:border-white/20 transition-all focus:outline-none focus:ring-2 focus:ring-white/20"
              >
                <iconify-icon icon="logos:google-icon" width="16"></iconify-icon>
                Google
              </button>
              <button
                type="button"
                className="flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 py-2 px-4 text-xs font-medium text-white hover:bg-white/10 hover:border-white/20 transition-all focus:outline-none focus:ring-2 focus:ring-white/20"
              >
                <iconify-icon icon="simple-icons:github" width="16" className="text-white"></iconify-icon>
                GitHub
              </button>
            </div>
          </form>

          {/* Footer */}
          <p className="mt-8 text-center text-xs text-white/30">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={toggleMode}
              className="font-medium text-cyan-400 hover:text-cyan-300 hover:underline underline-offset-4 transition-colors"
            >
              {isLogin ? 'Request access' : 'Sign in'}
            </button>
          </p>
        </div>

        {/* Compliance Text */}
        <p className="text-center text-[10px] text-white/20 mt-6 max-w-xs mx-auto">
          Protected by SmartFin Shield. <br />
          By logging in, you agree to our <a href="#" className="hover:text-white/40 underline">Terms</a> and <a href="#" className="hover:text-white/40 underline">Privacy Protocol</a>.
        </p>
      </main>
    </div>
  );
};

export default AuthPage;
