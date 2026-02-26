import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api';

const EmailVerification = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [userId, setUserId] = useState(null);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [codeSent, setCodeSent] = useState(false);

  useEffect(() => {
    // Get email and userId from location state (passed from registration)
    if (location.state?.email) {
      setEmail(location.state.email);
    }
    if (location.state?.userId) {
      setUserId(location.state.userId);
    }
    if (location.state?.verificationSent) {
      setCodeSent(true);
    }
  }, [location]);

  const handleSendCode = async () => {
    if (!email) {
      setError('Please enter your email address');
      return;
    }

    // Validate email format
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address (e.g., user@example.com)');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await api.sendEmailVerification(email, userId);
      setSuccess('Verification code sent to your email!');
      setCodeSent(true);
    } catch (err) {
      setError(err.message || 'Failed to send verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    
    if (!code || code.length !== 6) {
      setError('Please enter the 6-digit verification code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await api.verifyEmail(email, code, userId);
      setSuccess('Email verified successfully! Redirecting...');
      
      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (err) {
      setError(err.message || 'Invalid or expired verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden font-sans bg-[#030303]">
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

      {/* Main Verification Card */}
      <main className="w-full max-w-md px-6 relative z-10">
        <div className="glass-panel rounded-2xl p-8 md:p-10 relative overflow-hidden animate-fade-in-up">
          {/* Header */}
          <div className="mb-8 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-tr from-cyan-500/10 to-transparent border border-white/5 mb-4 shadow-lg shadow-cyan-900/20">
              <iconify-icon icon="solar:letter-opened-linear" className="text-cyan-400 text-2xl"></iconify-icon>
            </div>
            <h1 className="font-display text-2xl font-semibold text-white mb-2 tracking-tight">
              Verify Your Email
            </h1>
            <p className="text-sm text-white/50">
              We've sent a 6-digit code to your email address
            </p>
          </div>

          {/* Success Message */}
          {success && (
            <div className="mb-6 p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/30 flex items-start gap-3 animate-fade-in">
              <iconify-icon icon="solar:check-circle-linear" className="text-emerald-400 mt-0.5 shrink-0"></iconify-icon>
              <div className="text-xs text-emerald-400 leading-relaxed">
                <span className="font-semibold block mb-0.5">Success!</span>
                {success}
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-3 rounded-lg bg-danger-950/30 border border-danger-500/30 flex items-start gap-3 animate-fade-in">
              <iconify-icon icon="solar:danger-triangle-linear" className="text-danger-400 mt-0.5 shrink-0"></iconify-icon>
              <div className="text-xs text-danger-400 leading-relaxed">
                <span className="font-semibold block mb-0.5">Error</span>
                {error}
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleVerify} className="space-y-5">
            {/* Email Display */}
            <div className="space-y-1.5">
              <label className="text-[10px] uppercase tracking-widest text-white/40 font-medium">
                Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 pl-10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200"
                  placeholder="your@email.com"
                  disabled={codeSent}
                />
                <iconify-icon 
                  icon="solar:letter-linear" 
                  className="absolute left-3.5 top-3 text-white/30 text-lg"
                ></iconify-icon>
              </div>
            </div>

            {/* Verification Code Input */}
            {codeSent && (
              <div className="space-y-1.5">
                <label className="text-[10px] uppercase tracking-widest text-white/40 font-medium">
                  Verification Code
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-200 text-center tracking-widest text-lg"
                    placeholder="000000"
                    maxLength="6"
                  />
                </div>
                <p className="text-xs text-white/40 text-center mt-2">
                  Check your email for the 6-digit code
                </p>
              </div>
            )}

            {/* Action Buttons */}
            {!codeSent ? (
              <button
                type="button"
                onClick={handleSendCode}
                disabled={loading || !email}
                className="relative w-full group overflow-hidden rounded-lg bg-white py-2.5 transition-all hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {!loading && (
                  <>
                    <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                    <span className="relative text-sm font-semibold text-black flex items-center justify-center gap-2">
                      Send Verification Code
                      <iconify-icon icon="solar:letter-linear" className="transition-transform group-hover:translate-x-1"></iconify-icon>
                    </span>
                  </>
                )}
                {loading && (
                  <div className="flex items-center justify-center text-black">
                    <iconify-icon icon="solar:spinner-solid" className="animate-spin text-xl"></iconify-icon>
                  </div>
                )}
              </button>
            ) : (
              <div className="space-y-3">
                <button
                  type="submit"
                  disabled={loading || code.length !== 6}
                  className="relative w-full group overflow-hidden rounded-lg bg-white py-2.5 transition-all hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {!loading && (
                    <>
                      <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                      <span className="relative text-sm font-semibold text-black flex items-center justify-center gap-2">
                        Verify Email
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
                  onClick={handleSendCode}
                  disabled={loading}
                  className="w-full text-xs text-white/40 hover:text-cyan-400 transition-colors"
                >
                  Didn't receive the code? Resend
                </button>
              </div>
            )}

            {/* Skip Button */}
            <button
              type="button"
              onClick={handleSkip}
              className="w-full text-xs text-white/40 hover:text-white/60 transition-colors mt-4"
            >
              Skip for now (verify later)
            </button>
          </form>
        </div>

        {/* Info Text */}
        <p className="text-center text-[10px] text-white/20 mt-6 max-w-xs mx-auto">
          Email verification helps secure your account and enables password recovery.
        </p>
      </main>
    </div>
  );
};

export default EmailVerification;
