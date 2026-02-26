import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './ProfilePage.css';

// Phone Number Display Component
function PhoneNumberDisplay() {
  const [phone, setPhone] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPhone();
  }, []);

  const fetchPhone = async () => {
    try {
      const data = await api.getUserPhone();
      setPhone(data.phone);
    } catch (err) {
      console.error('Error fetching phone:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-sm text-white/40">Loading...</div>;
  }

  if (!phone) {
    return (
      <div className="text-sm text-amber-400 flex items-center gap-2">
        <iconify-icon icon="solar:danger-triangle-linear" width="16"></iconify-icon>
        Not set (required for password reset)
      </div>
    );
  }

  return <div className="text-sm font-medium">{phone}</div>;
}

function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const data = await api.getProfile();
      if (data === null) {
        // Profile doesn't exist yet (404)
        setError('profile_not_found');
      } else if (data && data.profile) {
        setProfile(data.profile);
      } else {
        setError('No profile found');
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getRiskCategory = (score) => {
    if (score <= 3) return { label: 'Conservative', color: 'emerald', icon: 'solar:shield-check-bold-duotone' };
    if (score <= 7) return { label: 'Moderate', color: 'amber', icon: 'solar:chart-2-bold-duotone' };
    return { label: 'Aggressive', color: 'rose', icon: 'solar:fire-bold-duotone' };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#030303] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-12 h-12 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin mb-4"></div>
          <p className="text-white/60">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error === 'profile_not_found') {
    return (
      <div className="min-h-screen bg-[#030303] text-white">
        {/* Background Effects */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <div className="absolute inset-0 bg-grid"></div>
          <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-cyan-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        </div>

        <div className="relative z-10 flex items-center justify-center min-h-screen px-6">
          <div className="max-w-md w-full text-center">
            <div className="glass-panel rounded-2xl p-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-cyan-500/10 flex items-center justify-center">
                <iconify-icon icon="solar:user-plus-bold-duotone" className="text-cyan-400 text-3xl"></iconify-icon>
              </div>
              <h2 className="text-2xl font-bold mb-2">Create Your Profile</h2>
              <p className="text-white/60 mb-6">Get started by setting up your financial profile</p>
              <button
                onClick={() => navigate('/profile/create')}
                className="w-full px-6 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 transition-all font-medium"
              >
                Create Profile
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="w-full mt-3 px-6 py-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-all font-medium"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#030303] text-white flex items-center justify-center px-6">
        <div className="glass-panel rounded-2xl p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-rose-500/10 flex items-center justify-center">
            <iconify-icon icon="solar:danger-triangle-bold-duotone" className="text-rose-400 text-3xl"></iconify-icon>
          </div>
          <h2 className="text-xl font-bold mb-2">Error Loading Profile</h2>
          <p className="text-white/60 mb-6">{error}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-all font-medium"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const riskInfo = profile.risk_tolerance ? getRiskCategory(profile.risk_tolerance) : null;

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
            <span className="text-[10px] text-white/30 font-mono">PROFILE</span>
          </button>

          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium"
          >
            <iconify-icon icon="solar:arrow-left-linear" width="16"></iconify-icon>
            <span>Back to Dashboard</span>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="relative z-10 pt-24 pb-12 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              My Profile
            </h1>
            <p className="text-white/60">Manage your personal and financial information</p>
          </div>

          {/* Profile Cards Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Personal Info Card */}
            <div className="lg:col-span-2 glass-panel rounded-2xl p-6">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  {profile.profile_picture_url ? (
                    <img 
                      src={`http://127.0.0.1:5000${profile.profile_picture_url}`}
                      alt={profile.name}
                      className="w-16 h-16 rounded-full object-cover border-2 border-cyan-500/20"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-2xl font-bold">
                      {profile.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <h2 className="text-2xl font-bold">{profile.name}</h2>
                    <p className="text-white/60 text-sm">{profile.location}</p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/profile/edit')}
                  className="px-4 py-2 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 hover:border-cyan-500/40 transition-all text-sm font-medium text-cyan-400"
                >
                  <iconify-icon icon="solar:pen-linear" width="16" className="inline mr-2"></iconify-icon>
                  Edit Profile
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <div className="text-white/60 text-xs mb-1">Age</div>
                  <div className="text-2xl font-bold">{profile.age}</div>
                </div>
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <div className="text-white/60 text-xs mb-1">Member Since</div>
                  <div className="text-sm font-medium">
                    {new Date(profile.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                  </div>
                </div>
              </div>

              {/* Phone Number Section */}
              <div className="mt-4 bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-white/60 text-xs mb-1">Phone Number</div>
                    <PhoneNumberDisplay />
                  </div>
                  <button
                    onClick={() => navigate('/profile/edit')}
                    className="px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 hover:border-cyan-500/40 transition-all text-xs font-medium text-cyan-400"
                  >
                    {profile.phone ? 'Update' : 'Add Phone'}
                  </button>
                </div>
              </div>
            </div>

            {/* Risk Tolerance Card */}
            <div className="glass-panel rounded-2xl p-6">
              <h3 className="text-lg font-bold mb-4">Risk Tolerance</h3>
              {riskInfo ? (
                <>
                  <div className={`w-20 h-20 mx-auto mb-4 rounded-full bg-${riskInfo.color}-500/10 flex items-center justify-center`}>
                    <iconify-icon icon={riskInfo.icon} className={`text-${riskInfo.color}-400 text-4xl`}></iconify-icon>
                  </div>
                  <div className="text-center mb-4">
                    <div className="text-2xl font-bold mb-1">{profile.risk_tolerance}/10</div>
                    <div className={`text-${riskInfo.color}-400 font-medium`}>{riskInfo.label}</div>
                  </div>
                  <button
                    onClick={() => navigate('/risk-assessment')}
                    className="w-full px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-sm font-medium"
                  >
                    Retake Assessment
                  </button>
                </>
              ) : (
                <>
                  <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
                    <iconify-icon icon="solar:question-circle-bold-duotone" className="text-white/40 text-4xl"></iconify-icon>
                  </div>
                  <p className="text-white/60 text-sm text-center mb-4">Take our risk assessment to get personalized recommendations</p>
                  <button
                    onClick={() => navigate('/risk-assessment')}
                    className="w-full px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 transition-all text-sm font-medium"
                  >
                    Take Assessment
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Notification Preferences Card */}
          <div className="glass-panel rounded-2xl p-6 mb-6">
            <h3 className="text-lg font-bold mb-4">Notification Preferences</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Email</span>
                  <iconify-icon 
                    icon={profile.notification_preferences.email ? "solar:check-circle-bold" : "solar:close-circle-bold"} 
                    className={profile.notification_preferences.email ? "text-emerald-400" : "text-white/20"}
                    width="20"
                  ></iconify-icon>
                </div>
                <div className="text-xs text-white/60">
                  {profile.notification_preferences.email ? 'Enabled' : 'Disabled'}
                </div>
              </div>
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Push</span>
                  <iconify-icon 
                    icon={profile.notification_preferences.push ? "solar:check-circle-bold" : "solar:close-circle-bold"} 
                    className={profile.notification_preferences.push ? "text-emerald-400" : "text-white/20"}
                    width="20"
                  ></iconify-icon>
                </div>
                <div className="text-xs text-white/60">
                  {profile.notification_preferences.push ? 'Enabled' : 'Disabled'}
                </div>
              </div>
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">In-App</span>
                  <iconify-icon 
                    icon={profile.notification_preferences.in_app ? "solar:check-circle-bold" : "solar:close-circle-bold"} 
                    className={profile.notification_preferences.in_app ? "text-emerald-400" : "text-white/20"}
                    width="20"
                  ></iconify-icon>
                </div>
                <div className="text-xs text-white/60">
                  {profile.notification_preferences.in_app ? 'Enabled' : 'Disabled'}
                </div>
              </div>
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Frequency</span>
                  <iconify-icon icon="solar:bell-bold-duotone" className="text-cyan-400" width="20"></iconify-icon>
                </div>
                <div className="text-xs text-white/60 capitalize">
                  {profile.notification_preferences.frequency}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={() => navigate('/goals')}
              className="glass-panel rounded-xl p-6 hover:bg-white/5 transition-all group text-left"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-cyan-500/10 flex items-center justify-center group-hover:bg-cyan-500/20 transition-colors">
                  <iconify-icon icon="solar:target-bold-duotone" className="text-cyan-400 text-2xl"></iconify-icon>
                </div>
                <div>
                  <h4 className="font-bold mb-1">Financial Goals</h4>
                  <p className="text-sm text-white/60">Manage your savings targets</p>
                </div>
                <iconify-icon icon="solar:arrow-right-linear" className="text-white/40 ml-auto text-xl"></iconify-icon>
              </div>
            </button>

            <button
              onClick={() => navigate('/profile/edit')}
              className="glass-panel rounded-xl p-6 hover:bg-white/5 transition-all group text-left"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
                  <iconify-icon icon="solar:settings-bold-duotone" className="text-blue-400 text-2xl"></iconify-icon>
                </div>
                <div>
                  <h4 className="font-bold mb-1">Edit Profile</h4>
                  <p className="text-sm text-white/60">Update your information</p>
                </div>
                <iconify-icon icon="solar:arrow-right-linear" className="text-white/40 ml-auto text-xl"></iconify-icon>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
