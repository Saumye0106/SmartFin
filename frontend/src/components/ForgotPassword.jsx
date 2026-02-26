import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: Email, 2: OTP, 3: New Password
  const [email, setEmail] = useState('');
  const [phoneHint, setPhoneHint] = useState(''); // To show masked phone
  const [otpCode, setOtpCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSendOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // Validate email format
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address (e.g., user@example.com)');
      setLoading(false);
      return;
    }

    try {
      // Send OTP to user's registered phone
      const response = await api.forgotPasswordOTP(email);
      setPhoneHint(response.phone_hint || '');
      setSuccess(response.message || 'OTP sent to your registered phone!');
      setStep(2);
    } catch (err) {
      setError(err.message || 'Failed to send OTP. Please check your email or contact support.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    try {
      // Reset password using OTP-verified session
      await api.forgotPasswordOTP(email, otpCode, newPassword);
      setSuccess('Password reset successfully! Redirecting to login...');
      setTimeout(() => {
        navigate('/auth');
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to reset password. Please try again.');
    } finally {
      setLoading(false);
    }
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

      {/* Main Card */}
      <main className="w-full max-w-md px-6 relative z-10">
        <div className="glass-panel rounded-2xl p-8 md:p-10 relative overflow-hidden animate-fade-in-up">
          {/* Header */}
          <div className="mb-8 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-tr from-cyan-500/10 to-transparent border border-white/5 mb-4 shadow-lg shadow-cyan-900/20">
              <iconify-icon icon="solar:lock-password-unlocked-linear" className="text-cyan-400 text-2xl"></iconify-icon>
            </div>
            <h1 className="font-display text-2xl font-semibold text-white mb-2 tracking-tight">
              {step === 1 && 'Reset Password'}
              {step === 2 && 'Enter OTP & New Password'}
            </h1>
            <p className="text-sm text-white/50">
              {step === 1 && 'Enter your email to receive an OTP'}
              {step === 2 && 'Enter the code sent to your phone and set a new password'}
            </p>
          </div>

          {/* Success Message */}
          {success && (
            <div className="mb-6 p-3 rounded-lg bg-green-950/30 border border-green-500/30 flex items-start gap-3 animate-fade-in">
              <iconify-icon icon="solar:check-circle-linear" className="text-green-400 mt-0.5 shrink-0"></iconify-icon>
              <div className="text-xs text-green-400 leading-relaxed">
                {success}
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-3 rounded-lg bg-danger-950/30 border border-danger-500/30 flex items-start gap-3 animate-fade-in">
              <iconify-icon icon="solar:danger-triangle-linear" className="text-danger-400 mt-0.5 shrink-0"></iconify-icon>
              <div className="text-xs text-danger-400 leading-relaxed">
                {error}
              </div>
            </div>
          )}

          {/* Step 1: Email Only */}
          {step === 1 && (
            <form onSubmit={handleSendOTP} className="space-y-5" noValidate>
              <div className="space-y-1.5 group">
                <label htmlFor="email" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-cyan-400">
                  Email Address
                </label>
                <div className="relative">
                  <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200"
                    placeholder="name@smartfin.ai"
                    required
                  />
                  <iconify-icon 
                    icon="solar:letter-linear" 
                    className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-cyan-400 transition-colors text-lg"
                  ></iconify-icon>
                </div>
                <p className="text-[10px] text-white/30 pl-1">We'll send an OTP to your registered phone number</p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="relative w-full group overflow-hidden rounded-lg bg-white py-2.5 transition-all hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {!loading && (
                  <>
                    <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                    <span className="relative text-sm font-semibold text-black flex items-center justify-center gap-2">
                      Send OTP
                      <iconify-icon icon="solar:arrow-right-linear" className="transition-transform group-hover:translate-x-1"></iconify-icon>
                    </span>
                  </>
                )}
                {loading && (
                  <div className="flex items-center justify-center text-black">
                    <iconify-icon icon="solar:spinner-solid" className="animate-spin text-xl"></iconify-icon>
                  </div>
                )}
              </button>
            </form>
          )}

          {/* Step 2: OTP + New Password Combined */}
          {step === 2 && (
            <form onSubmit={handleResetPassword} className="space-y-5" noValidate>
              {phoneHint && (
                <div className="p-3 rounded-lg bg-cyan-950/30 border border-cyan-500/30">
                  <div className="text-xs text-cyan-400 text-center">
                    OTP sent to: {phoneHint}
                  </div>
                </div>
              )}

              <div className="space-y-1.5 group">
                <label htmlFor="otpCode" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-cyan-400">
                  OTP Code
                </label>
                <div className="relative">
                  <input
                    type="text"
                    id="otpCode"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 tracking-widest text-center"
                    placeholder="000000"
                    maxLength="6"
                    required
                  />
                  <iconify-icon 
                    icon="solar:key-linear" 
                    className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-cyan-400 transition-colors text-lg"
                  ></iconify-icon>
                </div>
                <p className="text-[10px] text-white/30 pl-1">Check your phone for the 6-digit code</p>
              </div>

              <div className="space-y-1.5 group">
                <label htmlFor="newPassword" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-cyan-400">
                  New Password
                </label>
                <div className="relative">
                  <input
                    type="password"
                    id="newPassword"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200"
                    placeholder="••••••••••••"
                    required
                  />
                  <iconify-icon 
                    icon="solar:lock-password-linear" 
                    className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-cyan-400 transition-colors text-lg"
                  ></iconify-icon>
                </div>
              </div>

              <div className="space-y-1.5 group">
                <label htmlFor="confirmPassword" className="text-[10px] uppercase tracking-widest text-white/40 font-medium transition-colors group-focus-within:text-cyan-400">
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    type="password"
                    id="confirmPassword"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200"
                    placeholder="••••••••••••"
                    required
                  />
                  <iconify-icon 
                    icon="solar:lock-password-linear" 
                    className="absolute left-3.5 top-3 text-white/30 group-focus-within:text-cyan-400 transition-colors text-lg"
                  ></iconify-icon>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="relative w-full group overflow-hidden rounded-lg bg-white py-2.5 transition-all hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {!loading && (
                  <>
                    <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                    <span className="relative text-sm font-semibold text-black flex items-center justify-center gap-2">
                      Reset Password
                      <iconify-icon icon="solar:check-circle-linear" className="transition-transform group-hover:scale-110"></iconify-icon>
                    </span>
                  </>
                )}
                {loading && (
                  <div className="flex items-center justify-center text-black">
                    <iconify-icon icon="solar:spinner-solid" className="animate-spin text-xl"></iconify-icon>
                  </div>
                )}
              </button>

              <button
                type="button"
                onClick={() => setStep(1)}
                className="w-full text-xs text-white/40 hover:text-white/60 transition-colors"
              >
                Use different email
              </button>
            </form>
          )}

          {/* Footer */}
          <p className="mt-8 text-center text-xs text-white/30">
            Remember your password?{' '}
            <button
              onClick={() => navigate('/auth')}
              className="font-medium text-cyan-400 hover:text-cyan-300 hover:underline underline-offset-4 transition-colors"
            >
              Back to login
            </button>
          </p>
        </div>

        {/* Compliance Text */}
        <p className="text-center text-[10px] text-white/20 mt-6 max-w-xs mx-auto">
          Protected by SmartFin Shield. <br />
          Your security is our priority.
        </p>
      </main>
    </div>
  );
};

export default ForgotPassword;
