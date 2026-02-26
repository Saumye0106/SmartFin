import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './RiskAssessment.css';

// Questions from backend RiskAssessmentService
const QUESTIONS = {
  1: {
    text: "How would you react to a 20% drop in your investment portfolio?",
    options: [
      { value: 1, label: "Sell everything immediately" },
      { value: 2, label: "Sell some investments" },
      { value: 3, label: "Hold steady" },
      { value: 4, label: "Buy a little more" },
      { value: 5, label: "Buy significantly more" }
    ]
  },
  2: {
    text: "What is your primary financial goal timeline?",
    options: [
      { value: 1, label: "Short-term (< 3 years)" },
      { value: 2, label: "Medium-term (3-10 years)" },
      { value: 3, label: "Long-term (> 10 years)" }
    ]
  },
  3: {
    text: "How much investment experience do you have?",
    options: [
      { value: 1, label: "None - I'm just starting" },
      { value: 2, label: "Some - I've invested before" },
      { value: 3, label: "Extensive - I'm very experienced" }
    ]
  },
  4: {
    text: "What percentage of your income can you afford to lose?",
    options: [
      { value: 1, label: "0-5% - Very little" },
      { value: 2, label: "5-10% - Some" },
      { value: 3, label: "10-20% - A moderate amount" },
      { value: 4, label: "20%+ - A significant amount" }
    ]
  },
  5: {
    text: "How do you feel about market volatility?",
    options: [
      { value: 1, label: "Very uncomfortable" },
      { value: 2, label: "Somewhat uncomfortable" },
      { value: 3, label: "Neutral" },
      { value: 4, label: "Somewhat comfortable" },
      { value: 5, label: "Very comfortable" }
    ]
  }
};

function RiskAssessment() {
  const [answers, setAnswers] = useState({});
  const [currentQuestion, setCurrentQuestion] = useState(1);
  const [completed, setCompleted] = useState(false);
  const [riskScore, setRiskScore] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const totalQuestions = Object.keys(QUESTIONS).length;
  const progress = (Object.keys(answers).length / totalQuestions) * 100;

  const handleAnswer = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleNext = () => {
    if (currentQuestion < totalQuestions) {
      setCurrentQuestion(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 1) {
      setCurrentQuestion(prev => prev - 1);
    }
  };

  const calculateScore = () => {
    // Weights from backend
    const weights = {
      1: 0.25,
      2: 0.20,
      3: 0.15,
      4: 0.25,
      5: 0.15
    };

    let weightedSum = 0;
    let maxPossible = 0;

    for (let qId = 1; qId <= 5; qId++) {
      const answer = answers[qId];
      const weight = weights[qId];
      const maxAnswer = Math.max(...QUESTIONS[qId].options.map(o => o.value));
      
      const normalized = (answer - 1) / (maxAnswer - 1);
      weightedSum += normalized * weight;
      maxPossible += weight;
    }

    const score = Math.round(weightedSum * 9 + 1);
    return Math.max(1, Math.min(10, score));
  };

  const getRiskCategory = (score) => {
    if (score <= 3) return { label: 'Conservative', color: '#10b981', description: 'You prefer low-risk investments with stable returns' };
    if (score <= 6) return { label: 'Moderate', color: '#f59e0b', description: 'You balance risk and reward in your investment strategy' };
    return { label: 'Aggressive', color: '#ef4444', description: 'You\'re comfortable with high-risk investments for potential high returns' };
  };

  const handleSubmit = async () => {
    const score = calculateScore();
    setRiskScore(score);
    setCompleted(true);
    setSubmitting(true);

    try {
      // Update profile with risk tolerance score
      await api.updateProfile({ risk_tolerance: score });
      
      // Wait a moment to show the result
      setTimeout(() => {
        navigate('/profile');
      }, 3000);
    } catch (err) {
      console.error('Error updating risk tolerance:', err);
      // Still navigate after showing result
      setTimeout(() => {
        navigate('/profile');
      }, 3000);
    } finally {
      setSubmitting(false);
    }
  };

  const isComplete = Object.keys(answers).length === totalQuestions;
  const currentQuestionData = QUESTIONS[currentQuestion];

  if (completed && riskScore) {
    const category = getRiskCategory(riskScore);
    
    return (
      <div className="min-h-screen bg-[#030303] text-white flex items-center justify-center p-6">
        {/* Background Effects */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <div className="absolute inset-0 bg-grid"></div>
          <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-purple-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
          <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-violet-500/15 rounded-full blur-[100px] mix-blend-screen"></div>
        </div>

        {/* Result Card */}
        <div className="relative z-10 glass-panel rounded-2xl max-w-2xl w-full p-8 md:p-12 text-center animate-fade-in-up">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-500/10 border border-green-500/20 mb-6">
            <iconify-icon icon="solar:check-circle-bold" className="text-green-400 text-5xl"></iconify-icon>
          </div>
          
          <h1 className="font-display text-3xl md:text-4xl font-bold text-white mb-2">
            Assessment Complete!
          </h1>
          <p className="text-white/50 mb-8">Your risk tolerance has been calculated</p>

          <div 
            className="inline-flex flex-col items-center justify-center w-40 h-40 rounded-full mb-6 shadow-2xl"
            style={{ backgroundColor: `${category.color}20`, border: `2px solid ${category.color}40` }}
          >
            <div className="text-6xl font-bold" style={{ color: category.color }}>
              {riskScore}
            </div>
            <div className="text-xs font-bold uppercase tracking-wider mt-2" style={{ color: category.color }}>
              Risk Score
            </div>
          </div>

          <h2 className="text-2xl font-bold mb-2" style={{ color: category.color }}>
            {category.label}
          </h2>
          <p className="text-white/60 mb-8 max-w-md mx-auto">
            {category.description}
          </p>

          <div className="glass-panel rounded-lg p-4 border border-white/10 mb-6">
            <p className="text-sm text-white/70">
              Your profile has been updated with your risk tolerance score.
            </p>
            <p className="text-sm text-white/50 mt-1">
              Redirecting to your profile...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030303] text-white">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] right-[20%] w-[600px] h-[600px] bg-purple-500/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-violet-500/15 rounded-full blur-[100px] mix-blend-screen"></div>
      </div>

      {/* Navigation Header */}
      <nav className="fixed top-0 left-0 w-full z-50 transition-all duration-300">
        <div className="absolute inset-0 bg-black/50 backdrop-blur-md border-b border-white/5"></div>
        <div className="max-w-7xl mx-auto px-6 h-16 relative flex items-center justify-between">
          {/* Logo */}
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-3 group transition-all hover:opacity-80"
          >
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-purple-500/50 transition-colors">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-purple-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">RISK ASSESSMENT</span>
          </button>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <div className="text-[10px] font-mono text-purple-400 bg-purple-950/20 px-3 py-1.5 rounded-full border border-purple-500/20">
              {currentTime.toLocaleTimeString('en-US', { hour12: false })}
            </div>
            <button
              onClick={() => navigate('/profile')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium"
            >
              <iconify-icon icon="solar:arrow-left-linear" width="16"></iconify-icon>
              <span className="hidden md:inline">Back to Profile</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-16 px-6 flex items-center justify-center min-h-screen">
        <div className="max-w-3xl w-full">
          {/* Hero Section */}
          <section className="mb-8 text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
              <span className="text-xs text-white/50 font-medium tracking-widest uppercase">Risk Analysis</span>
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
              Risk Tolerance <span className="text-gradient-purple">Assessment</span>
            </h1>
            <p className="text-white/50 max-w-2xl mx-auto">
              Answer 5 questions to determine your investment risk profile
            </p>
          </section>

          {/* Progress Section */}
          <div className="glass-panel rounded-xl p-6 mb-6 border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-white/50 font-medium">Progress</span>
              <span className="text-xs text-white/70 font-mono">
                {Object.keys(answers).length} / {totalQuestions}
              </span>
            </div>
            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-500 to-violet-600 transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Question Card */}
          <div className="glass-panel rounded-xl p-8 border border-white/10 mb-6">
            <div className="mb-6">
              <div className="text-xs text-purple-400 font-bold uppercase tracking-wider mb-3">
                Question {currentQuestion} of {totalQuestions}
              </div>
              <h2 className="text-2xl md:text-3xl font-bold text-white leading-tight">
                {currentQuestionData.text}
              </h2>
            </div>

            <div className="space-y-3">
              {currentQuestionData.options.map(option => (
                <button
                  key={option.value}
                  onClick={() => handleAnswer(currentQuestion, option.value)}
                  className={`w-full flex items-center gap-4 p-4 rounded-lg border-2 transition-all text-left ${
                    answers[currentQuestion] === option.value
                      ? 'bg-purple-500/10 border-purple-500/50 shadow-lg shadow-purple-900/20'
                      : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20'
                  }`}
                >
                  <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all ${
                    answers[currentQuestion] === option.value
                      ? 'border-purple-500 bg-purple-500'
                      : 'border-white/30'
                  }`}>
                    {answers[currentQuestion] === option.value && (
                      <div className="w-2 h-2 rounded-full bg-white"></div>
                    )}
                  </div>
                  <span className="text-white font-medium">{option.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <div className="flex gap-3">
            <button
              onClick={handlePrevious}
              disabled={currentQuestion === 1}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-sm font-semibold disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <iconify-icon icon="solar:arrow-left-linear" width="18"></iconify-icon>
              Previous
            </button>

            {currentQuestion < totalQuestions ? (
              <button
                onClick={handleNext}
                disabled={!answers[currentQuestion]}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700 border border-purple-400/20 transition-all text-sm font-semibold shadow-lg shadow-purple-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
                <iconify-icon icon="solar:arrow-right-linear" width="18"></iconify-icon>
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!isComplete || submitting}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 border border-green-400/20 transition-all text-sm font-semibold shadow-lg shadow-green-900/30 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <>
                    <iconify-icon icon="solar:spinner-solid" className="animate-spin text-lg"></iconify-icon>
                    Submitting...
                  </>
                ) : (
                  <>
                    <iconify-icon icon="solar:check-circle-linear" width="18"></iconify-icon>
                    Complete Assessment
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-20 border-t border-white/10 bg-black/50 backdrop-blur-md py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-purple-400 text-lg"></iconify-icon>
                <span className="font-display font-bold text-white">SmartFin</span>
                <span className="text-[10px] text-white/30 font-mono">v2.0.4</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                <span className="text-white/40">System Operational</span>
              </div>
            </div>
            <div className="text-xs text-white/30">
              Educational Use Only • College Project
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default RiskAssessment;
