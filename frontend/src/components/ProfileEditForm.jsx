import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './ProfileEditForm.css';

// Phone Update Component
function PhoneUpdateSection() {
  const [phone, setPhone] = useState('');
  const [currentPhone, setCurrentPhone] = useState(null);
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState(1); // 1: Enter phone, 2: Verify OTP
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchCurrentPhone();
  }, []);

  const fetchCurrentPhone = async () => {
    try {
      const data = await api.getUserPhone();
      setCurrentPhone(data.phone);
      setPhone(data.phone || '');
    } catch (err) {
      console.error('Error fetching phone:', err);
    }
  };

  const handleSendOTP = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await api.updatePhone(phone);
      setSuccess('OTP sent to your phone! Please check your messages.');
      setStep(2);
    } catch (err) {
      setError(err.message || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    setLoading(true);
    setError('');

    try {
      await api.updatePhone(phone, otp);
      setSuccess('Phone number updated successfully!');
      setCurrentPhone(phone);
      setStep(1);
      setOtp('');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.message || 'Invalid or expired OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/5 rounded-xl p-6 border border-white/10 mb-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center">
          <iconify-icon icon="solar:phone-bold-duotone" className="text-cyan-400 text-xl"></iconify-icon>
        </div>
        <div>
          <h3 className="text-lg font-bold">Phone Number</h3>
          <p className="text-xs text-white/60">Required for password reset via OTP</p>
        </div>
      </div>

      {success && (
        <div className="mb-4 p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/30 flex items-start gap-3">
          <iconify-icon icon="solar:check-circle-linear" className="text-emerald-400 mt-0.5 shrink-0"></iconify-icon>
          <div className="text-xs text-emerald-400">{success}</div>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-danger-950/30 border border-danger-500/30 flex items-start gap-3">
          <iconify-icon icon="solar:danger-triangle-linear" className="text-danger-400 mt-0.5 shrink-0"></iconify-icon>
          <div className="text-xs text-danger-400">{error}</div>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Phone Number
              {!currentPhone && <span className="text-amber-400 ml-2">(Not set)</span>}
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+1234567890"
              className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all text-sm"
            />
            <p className="text-xs text-white/40 mt-1">Format: +[country code][number] (e.g., +917880308989)</p>
          </div>
          <button
            type="button"
            onClick={handleSendOTP}
            disabled={loading || !phone}
            className="w-full px-4 py-2.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 hover:border-cyan-500/40 transition-all text-sm font-medium text-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Sending OTP...' : currentPhone ? 'Update Phone Number' : 'Add Phone Number'}
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Enter OTP Code</label>
            <input
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="000000"
              maxLength="6"
              className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all text-sm text-center tracking-widest"
            />
            <p className="text-xs text-white/40 mt-1">Check your phone for the 6-digit code</p>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => { setStep(1); setOtp(''); setError(''); }}
              className="flex-1 px-4 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-sm font-medium"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleVerifyOTP}
              disabled={loading || otp.length !== 6}
              className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Verifying...' : 'Verify OTP'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ProfileEditForm() {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    location: '',
    risk_tolerance: '',
    notification_preferences: {
      email: true,
      push: false,
      in_app: true,
      frequency: 'daily'
    }
  });
  const [currentPictureUrl, setCurrentPictureUrl] = useState(null);
  const [uploadingPicture, setUploadingPicture] = useState(false);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isCreate, setIsCreate] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const data = await api.getProfile();
      if (data && data.profile) {
        setFormData({
          name: data.profile.name || '',
          age: data.profile.age || '',
          location: data.profile.location || '',
          risk_tolerance: data.profile.risk_tolerance || '',
          notification_preferences: data.profile.notification_preferences || {
            email: true,
            push: false,
            in_app: true,
            frequency: 'daily'
          }
        });
        setCurrentPictureUrl(data.profile.profile_picture_url || null);
        setIsCreate(false);
      } else {
        setIsCreate(true);
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
      setIsCreate(true);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (!/^[A-Za-z\s]{2,100}$/.test(formData.name)) {
      newErrors.name = 'Name must contain only letters and spaces (2-100 characters)';
    }

    const age = parseInt(formData.age);
    if (!formData.age) {
      newErrors.age = 'Age is required';
    } else if (isNaN(age) || age < 18 || age > 120) {
      newErrors.age = 'Age must be between 18 and 120';
    }

    if (!formData.location.trim()) {
      newErrors.location = 'Location is required';
    } else if (formData.location.length > 200) {
      newErrors.location = 'Location must be 200 characters or less';
    }

    if (formData.risk_tolerance) {
      const risk = parseInt(formData.risk_tolerance);
      if (isNaN(risk) || risk < 1 || risk > 10) {
        newErrors.risk_tolerance = 'Risk tolerance must be between 1 and 10';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleNotificationChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      notification_preferences: {
        ...prev.notification_preferences,
        [name]: type === 'checkbox' ? checked : value
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);

    try {
      const submitData = {
        name: formData.name.trim(),
        age: parseInt(formData.age),
        location: formData.location.trim(),
        notification_preferences: formData.notification_preferences
      };

      if (formData.risk_tolerance) {
        submitData.risk_tolerance = parseInt(formData.risk_tolerance);
      }

      if (isCreate) {
        await api.createProfile(submitData);
      } else {
        await api.updateProfile(submitData);
      }

      navigate('/profile');
    } catch (err) {
      setErrors({ submit: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    navigate(isCreate ? '/dashboard' : '/profile');
  };

  const handlePictureUploadSuccess = () => {
    // Refresh profile to get updated picture URL
    fetchProfile();
  };

  const handlePictureUpload = async (file) => {
    setUploadingPicture(true);
    try {
      const result = await api.uploadProfilePicture(file);
      setCurrentPictureUrl(result.profile_picture_url);
      // Show success feedback
      setTimeout(() => {
        fetchProfile();
      }, 500);
    } catch (err) {
      alert(err.message || 'Failed to upload picture');
    } finally {
      setUploadingPicture(false);
    }
  };

  const handlePictureDelete = async () => {
    if (!confirm('Are you sure you want to delete your profile picture?')) return;
    
    setUploadingPicture(true);
    try {
      await api.deleteProfilePicture();
      setCurrentPictureUrl(null);
      // Show success feedback
      setTimeout(() => {
        fetchProfile();
      }, 500);
    } catch (err) {
      alert(err.message || 'Failed to delete picture');
    } finally {
      setUploadingPicture(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#030303] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-12 h-12 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin mb-4"></div>
          <p className="text-white/60">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030303] text-white">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-cyan-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-500/15 rounded-full blur-[100px] mix-blend-screen"></div>
      </div>

      {/* Navigation Header */}
      <nav className="fixed top-0 left-0 w-full z-50">
        <div className="absolute inset-0 bg-black/50 backdrop-blur-md border-b border-white/5"></div>
        <div className="max-w-7xl mx-auto px-6 h-16 relative flex items-center justify-between">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-3 group transition-all hover:opacity-80"
          >
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-cyan-500/50 transition-colors">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-cyan-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">{isCreate ? 'CREATE PROFILE' : 'EDIT PROFILE'}</span>
          </button>

          <button
            onClick={handleCancel}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium"
          >
            <iconify-icon icon="solar:close-circle-linear" width="16"></iconify-icon>
            <span>Cancel</span>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="relative z-10 pt-24 pb-12 px-6">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="mb-8 text-center">
            {/* Profile Picture Section */}
            {!isCreate && (
              <div className="relative inline-block mb-4">
                {/* Loading overlay */}
                {uploadingPicture && (
                  <div className="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center z-10">
                    <div className="w-8 h-8 border-4 border-white/20 border-t-white rounded-full animate-spin"></div>
                  </div>
                )}
                
                {currentPictureUrl ? (
                  <img 
                    src={`http://127.0.0.1:5000${currentPictureUrl}`}
                    alt="Profile"
                    className="w-24 h-24 mx-auto rounded-full object-cover border-4 border-cyan-500/20"
                  />
                ) : (
                  <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-3xl font-bold border-4 border-cyan-500/20">
                    {formData.name ? formData.name.charAt(0).toUpperCase() : <iconify-icon icon="solar:user-bold-duotone" className="text-white"></iconify-icon>}
                  </div>
                )}
                
                {/* Upload/Delete Buttons */}
                <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 flex gap-2">
                  <label className="cursor-pointer">
                    <input
                      type="file"
                      accept="image/jpeg,image/jpg,image/png,image/webp"
                      onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) {
                          // Validate file type
                          const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
                          if (!allowedTypes.includes(file.type)) {
                            alert('Invalid file format. Please use JPEG, PNG, or WebP');
                            return;
                          }
                          // Validate file size (5MB max)
                          if (file.size > 5 * 1024 * 1024) {
                            alert('File too large. Maximum size is 5MB');
                            return;
                          }
                          // Upload immediately
                          handlePictureUpload(file);
                        }
                      }}
                      className="hidden"
                      disabled={uploadingPicture}
                    />
                    <div className={`w-10 h-10 rounded-full bg-cyan-500 hover:bg-cyan-600 flex items-center justify-center shadow-lg transition-all border-2 border-white ${uploadingPicture ? 'opacity-50 cursor-not-allowed' : ''}`}>
                      <iconify-icon icon="solar:camera-bold" className="text-white text-lg"></iconify-icon>
                    </div>
                  </label>
                  
                  {currentPictureUrl && (
                    <button
                      type="button"
                      onClick={handlePictureDelete}
                      disabled={uploadingPicture}
                      className={`w-10 h-10 rounded-full bg-rose-500 hover:bg-rose-600 flex items-center justify-center shadow-lg transition-all border-2 border-white ${uploadingPicture ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <iconify-icon icon="solar:trash-bin-trash-bold" className="text-white text-lg"></iconify-icon>
                    </button>
                  )}
                </div>
              </div>
            )}
            
            {isCreate && (
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
                <iconify-icon icon="solar:user-bold-duotone" className="text-white text-3xl"></iconify-icon>
              </div>
            )}
            
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              {isCreate ? 'Create Your Profile' : 'Edit Profile'}
            </h1>
            <p className="text-white/60">
              {isCreate ? 'Tell us about yourself to get personalized insights' : 'Update your information'}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {errors.submit && (
              <div className="glass-panel rounded-xl p-4 border-rose-500/50 bg-rose-500/10">
                <div className="flex items-center gap-3">
                  <iconify-icon icon="solar:danger-triangle-bold-duotone" className="text-rose-400 text-xl"></iconify-icon>
                  <p className="text-rose-400 text-sm">{errors.submit}</p>
                </div>
              </div>
            )}

            {/* Personal Information Section */}
            <div className="glass-panel rounded-2xl p-6">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <iconify-icon icon="solar:user-id-bold-duotone" className="text-cyan-400"></iconify-icon>
                Personal Information
              </h3>

              <div className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium mb-2 text-white/80">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className={`w-full bg-white/5 border ${errors.name ? 'border-rose-500/50' : 'border-white/10'} rounded-lg px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all`}
                    placeholder="John Doe"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-rose-400">{errors.name}</p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="age" className="block text-sm font-medium mb-2 text-white/80">
                      Age *
                    </label>
                    <input
                      type="number"
                      id="age"
                      name="age"
                      value={formData.age}
                      onChange={handleChange}
                      className={`w-full bg-white/5 border ${errors.age ? 'border-rose-500/50' : 'border-white/10'} rounded-lg px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all`}
                      placeholder="30"
                      min="18"
                      max="120"
                    />
                    {errors.age && (
                      <p className="mt-1 text-sm text-rose-400">{errors.age}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="location" className="block text-sm font-medium mb-2 text-white/80">
                      Location *
                    </label>
                    <input
                      type="text"
                      id="location"
                      name="location"
                      value={formData.location}
                      onChange={handleChange}
                      className={`w-full bg-white/5 border ${errors.location ? 'border-rose-500/50' : 'border-white/10'} rounded-lg px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all`}
                      placeholder="New York, USA"
                    />
                    {errors.location && (
                      <p className="mt-1 text-sm text-rose-400">{errors.location}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label htmlFor="risk_tolerance" className="block text-sm font-medium mb-2 text-white/80">
                    Risk Tolerance (1-10)
                  </label>
                  <input
                    type="number"
                    id="risk_tolerance"
                    name="risk_tolerance"
                    value={formData.risk_tolerance}
                    onChange={handleChange}
                    className={`w-full bg-white/5 border ${errors.risk_tolerance ? 'border-rose-500/50' : 'border-white/10'} rounded-lg px-4 py-3 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all`}
                    placeholder="Leave empty to take assessment later"
                    min="1"
                    max="10"
                  />
                  {errors.risk_tolerance && (
                    <p className="mt-1 text-sm text-rose-400">{errors.risk_tolerance}</p>
                  )}
                  <p className="mt-1 text-xs text-white/40">Or take the risk assessment questionnaire for a personalized score</p>
                </div>
              </div>
            </div>

            {/* Notification Preferences Section */}
            <div className="glass-panel rounded-2xl p-6">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <iconify-icon icon="solar:bell-bold-duotone" className="text-cyan-400"></iconify-icon>
                Notification Preferences
              </h3>

              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <label className="flex items-center gap-3 p-4 bg-white/5 rounded-lg border border-white/10 hover:border-cyan-500/30 transition-all cursor-pointer">
                    <input
                      type="checkbox"
                      name="email"
                      checked={formData.notification_preferences.email}
                      onChange={handleNotificationChange}
                      className="w-5 h-5 rounded border-white/20 bg-white/5 text-cyan-500 focus:ring-cyan-500/50"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-sm">Email</div>
                      <div className="text-xs text-white/40">Get updates via email</div>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 p-4 bg-white/5 rounded-lg border border-white/10 hover:border-cyan-500/30 transition-all cursor-pointer">
                    <input
                      type="checkbox"
                      name="push"
                      checked={formData.notification_preferences.push}
                      onChange={handleNotificationChange}
                      className="w-5 h-5 rounded border-white/20 bg-white/5 text-cyan-500 focus:ring-cyan-500/50"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-sm">Push</div>
                      <div className="text-xs text-white/40">Browser notifications</div>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 p-4 bg-white/5 rounded-lg border border-white/10 hover:border-cyan-500/30 transition-all cursor-pointer">
                    <input
                      type="checkbox"
                      name="in_app"
                      checked={formData.notification_preferences.in_app}
                      onChange={handleNotificationChange}
                      className="w-5 h-5 rounded border-white/20 bg-white/5 text-cyan-500 focus:ring-cyan-500/50"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-sm">In-App</div>
                      <div className="text-xs text-white/40">Notifications in app</div>
                    </div>
                  </label>
                </div>

                <div>
                  <label htmlFor="frequency" className="block text-sm font-medium mb-2 text-white/80">
                    Notification Frequency
                  </label>
                  <select
                    id="frequency"
                    name="frequency"
                    value={formData.notification_preferences.frequency}
                    onChange={handleNotificationChange}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
                  >
                    <option value="immediate" className="bg-[#0a0a0a]">Immediate</option>
                    <option value="daily" className="bg-[#0a0a0a]">Daily Digest</option>
                    <option value="weekly" className="bg-[#0a0a0a]">Weekly Summary</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Phone Number Update Section */}
            <PhoneUpdateSection />

            {/* Form Actions */}
            <div className="flex gap-4">
              <button
                type="button"
                onClick={handleCancel}
                disabled={submitting}
                className="flex-1 px-6 py-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <iconify-icon icon="solar:check-circle-bold" width="20"></iconify-icon>
                    <span>{isCreate ? 'Create Profile' : 'Save Changes'}</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default ProfileEditForm;
