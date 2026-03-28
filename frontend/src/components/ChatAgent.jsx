import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import SmartFinFooter from './SmartFinFooter';
import api from '../services/api';
import './ChatAgent.css';

// ==================== Helper: Format currency ====================
const formatINR = (num) => {
  if (num === undefined || num === null) return '—';
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
  if (num >= 100000) return `₹${(num / 100000).toFixed(2)} L`;
  if (num >= 1000) return `₹${(num / 1000).toFixed(1)}K`;
  return `₹${Math.round(num).toLocaleString('en-IN')}`;
};

// ==================== Helper: Score color ====================
const getScoreColor = (score) => {
  if (score >= 75) return '#34d399';
  if (score >= 50) return '#fbbf24';
  if (score >= 25) return '#f97316';
  return '#f87171';
};

const getProgressClass = (score) => {
  if (score >= 75) return 'good';
  if (score >= 50) return 'warning';
  return 'danger';
};

// ==================== Widget: Financial Health Score ====================
const ScoreWidget = ({ data }) => {
  const { score, classification, patterns, guidance, anomalies, investments } = data;
  const color = getScoreColor(score);
  const circumference = 2 * Math.PI * 28;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="widget-card">
      <div className="widget-header">
        <iconify-icon icon="solar:health-linear" width="16"></iconify-icon>
        <span className="widget-title">Financial Health Score</span>
      </div>
      <div className="score-widget">
        <div className="score-ring">
          <svg viewBox="0 0 64 64">
            <circle className="score-ring-bg" cx="32" cy="32" r="28" />
            <circle
              className="score-ring-fill"
              cx="32" cy="32" r="28"
              stroke={color}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="score-ring-value" style={{ color }}>{score}</div>
        </div>
        <div className="score-details">
          <div className="score-classification">{classification}</div>
          <div className="score-label">out of 100</div>
        </div>
      </div>

      {/* Spending Patterns */}
      {patterns && (
        <div style={{ marginTop: '0.75rem' }}>
          <div className="stats-grid">
            {patterns.savings_rate !== undefined && (
              <div className="stat-item">
                <span className="stat-label">Savings Rate</span>
                <span className={`stat-value ${patterns.savings_rate >= 20 ? 'positive' : 'negative'}`}>
                  {patterns.savings_rate?.toFixed(1)}%
                </span>
              </div>
            )}
            {patterns.expense_ratio !== undefined && (
              <div className="stat-item">
                <span className="stat-label">Expense Ratio</span>
                <span className={`stat-value ${patterns.expense_ratio <= 60 ? 'positive' : 'negative'}`}>
                  {patterns.expense_ratio?.toFixed(1)}%
                </span>
              </div>
            )}
            {patterns.emi_ratio !== undefined && (
              <div className="stat-item">
                <span className="stat-label">EMI Burden</span>
                <span className={`stat-value ${patterns.emi_ratio <= 30 ? 'positive' : 'negative'}`}>
                  {patterns.emi_ratio?.toFixed(1)}%
                </span>
              </div>
            )}
            {patterns.rent_ratio !== undefined && (
              <div className="stat-item">
                <span className="stat-label">Rent Ratio</span>
                <span className="stat-value">{patterns.rent_ratio?.toFixed(1)}%</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Anomalies (warnings) */}
      {anomalies && anomalies.length > 0 && (
        <div style={{ marginTop: '0.75rem' }}>
          <div className="widget-list">
            {anomalies.slice(0, 3).map((a, i) => (
              <div key={i} className="widget-list-item list-item-warn">
                <iconify-icon icon="solar:danger-triangle-linear" width="14"></iconify-icon>
                <span>{typeof a === 'string' ? a : a.message || a.description || JSON.stringify(a)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== Widget: What-If Comparison ====================
const WhatIfWidget = ({ data }) => {
  const { current_score, modified_score, score_change, impact } = data;

  return (
    <div className="widget-card">
      <div className="widget-header">
        <iconify-icon icon="solar:magic-stick-3-linear" width="16"></iconify-icon>
        <span className="widget-title">What-If Simulation</span>
      </div>
      <div className="stats-grid">
        <div className="stat-item">
          <span className="stat-label">Current Score</span>
          <span className="stat-value">{current_score}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Modified Score</span>
          <span className="stat-value" style={{ color: getScoreColor(modified_score) }}>{modified_score}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Change</span>
          <span className={`stat-value ${score_change > 0 ? 'positive' : score_change < 0 ? 'negative' : ''}`}>
            {score_change > 0 ? '+' : ''}{score_change}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Impact</span>
          <span className={`stat-value ${impact === 'positive' ? 'positive' : impact === 'negative' ? 'negative' : ''}`}>
            {impact?.charAt(0).toUpperCase() + impact?.slice(1)}
          </span>
        </div>
      </div>
    </div>
  );
};

// ==================== Widget: Retirement Plan ====================
const RetirementWidget = ({ data }) => {
  const { calculation, readiness } = data;
  const readinessScore = readiness?.readiness_score || 0;

  return (
    <div className="widget-card">
      <div className="widget-header">
        <iconify-icon icon="solar:chart-2-linear" width="16"></iconify-icon>
        <span className="widget-title">Retirement Plan</span>
      </div>
      <div className="retirement-stats">
        <div className="retirement-stat">
          <div className="retirement-stat-value">{formatINR(calculation?.required_corpus)}</div>
          <div className="retirement-stat-label">Target Corpus</div>
        </div>
        <div className="retirement-stat">
          <div className="retirement-stat-value">{formatINR(calculation?.projected_savings)}</div>
          <div className="retirement-stat-label">Projected Savings</div>
        </div>
        <div className="retirement-stat">
          <div className="retirement-stat-value">{formatINR(calculation?.required_monthly_savings)}</div>
          <div className="retirement-stat-label">Monthly Needed</div>
        </div>
      </div>
      <div className="progress-bar-container">
        <div className="progress-bar-label">
          <span>Readiness Score</span>
          <span>{readinessScore}/100</span>
        </div>
        <div className="progress-bar-track">
          <div
            className={`progress-bar-fill ${getProgressClass(readinessScore)}`}
            style={{ width: `${Math.min(100, readinessScore)}%` }}
          />
        </div>
      </div>
    </div>
  );
};

// ==================== Widget: Loan Overview ====================
const LoanWidget = ({ data }) => {
  const loans = data.loans || [];
  if (loans.length === 0) return null;

  return (
    <div className="widget-card">
      <div className="widget-header">
        <iconify-icon icon="solar:wallet-money-linear" width="16"></iconify-icon>
        <span className="widget-title">Loan Overview</span>
      </div>
      <div className="widget-list">
        {loans.slice(0, 4).map((loan, i) => (
          <div key={i} className="widget-list-item list-item-info">
            <iconify-icon icon="solar:document-text-linear" width="14"></iconify-icon>
            <span>
              {loan.loan_type || 'Loan'}: {formatINR(loan.loan_amount)} 
              @ {loan.interest_rate}% — EMI {formatINR(loan.emi_amount)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ==================== Widget: Goals ====================
const GoalsWidget = ({ data }) => {
  const goals = data.goals || [];
  if (goals.length === 0) return null;

  return (
    <div className="widget-card">
      <div className="widget-header">
        <iconify-icon icon="solar:target-linear" width="16"></iconify-icon>
        <span className="widget-title">Financial Goals</span>
      </div>
      <div className="widget-list">
        {goals.slice(0, 4).map((goal, i) => {
          const progress = goal.target_amount > 0
            ? Math.min(100, Math.round((goal.current_amount / goal.target_amount) * 100))
            : 0;
          return (
            <div key={i} style={{ marginBottom: '0.5rem' }}>
              <div className="widget-list-item list-item-tip">
                <iconify-icon icon="solar:flag-linear" width="14"></iconify-icon>
                <span>{goal.goal_name}: {formatINR(goal.current_amount)} / {formatINR(goal.target_amount)}</span>
              </div>
              <div className="progress-bar-track" style={{ marginLeft: '1.5rem', marginTop: '0.25rem' }}>
                <div
                  className={`progress-bar-fill ${getProgressClass(progress)}`}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ==================== Widget: User Profile ====================
const ProfileWidget = ({ data }) => {
  if (data.message) return null; // No profile

  return (
    <div className="widget-card">
      <div className="widget-header">
        <iconify-icon icon="solar:user-circle-linear" width="16"></iconify-icon>
        <span className="widget-title">Profile Summary</span>
      </div>
      <div className="stats-grid">
        {data.full_name && (
          <div className="stat-item">
            <span className="stat-label">Name</span>
            <span className="stat-value">{data.full_name}</span>
          </div>
        )}
        {data.age && (
          <div className="stat-item">
            <span className="stat-label">Age</span>
            <span className="stat-value">{data.age}</span>
          </div>
        )}
        {data.monthly_income && (
          <div className="stat-item">
            <span className="stat-label">Monthly Income</span>
            <span className="stat-value">{formatINR(data.monthly_income)}</span>
          </div>
        )}
        {data.occupation && (
          <div className="stat-item">
            <span className="stat-label">Occupation</span>
            <span className="stat-value">{data.occupation}</span>
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== Widget Router ====================
const ToolWidget = ({ widget }) => {
  const { tool, result } = widget;
  if (!result || result.error) return null;

  switch (tool) {
    case 'predict_financial_health':
      return <ScoreWidget data={result} />;
    case 'whatif_simulation':
      return <WhatIfWidget data={result} />;
    case 'calculate_retirement_plan':
      return <RetirementWidget data={result} />;
    case 'get_loan_overview':
      return <LoanWidget data={result} />;
    case 'get_user_goals':
      return <GoalsWidget data={result} />;
    case 'get_user_profile':
      // Profile lookups are often background context fetches for the LLM.
      // Suppress this widget to avoid repetitive "Profile Summary" cards.
      return null;
    default:
      return null;
  }
};

// ==================== Format assistant text with basic markdown ====================
const formatText = (text) => {
  if (!text) return '';
  // Bold: **text** or __text__
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/__(.*?)__/g, '<strong>$1</strong>');
  // Italic: *text* or _text_
  formatted = formatted.replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
  // Inline code: `text`
  formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
  // Line breaks
  formatted = formatted.replace(/\n/g, '<br/>');
  // Bullet lists: lines starting with - or •
  formatted = formatted.replace(/(?:^|<br\/>)\s*[-•]\s+(.*?)(?=<br\/>|$)/g, '<br/>• $1');
  return formatted;
};

// ==================== Suggestion Prompts ====================
const SUGGESTIONS = [
  {
    icon: 'solar:health-linear',
    text: 'Analyze my financial health and spending patterns',
  },
  {
    icon: 'solar:magic-stick-3-linear',
    text: 'What if I increase my savings by ₹10,000/month?',
  },
  {
    icon: 'solar:chart-2-linear',
    text: 'Help me plan my retirement',
  },
  {
    icon: 'solar:target-linear',
    text: 'Show me my financial goals and progress',
  },
  {
    icon: 'solar:wallet-money-linear',
    text: 'Show my budget and expense summary for this month',
  },
  {
    icon: 'solar:chart-square-linear',
    text: 'Analyze my budget data and tell me overspending categories',
  },
];

const QUICK_SHORTCUTS = [
  'Analyze my budget data for this month',
  'Show my budget and expense summary for this month',
  'What categories am I overspending in this month?'
];

// ==================== Main ChatAgent Component ====================
const ChatAgent = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [chatSessions, setChatSessions] = useState([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [renamingSessionId, setRenamingSessionId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [lastOpenedSessionId, setLastOpenedSessionId] = useState(null);
  const [pendingDeleteSession, setPendingDeleteSession] = useState(null);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceError, setVoiceError] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const textareaRef = useRef(null);
  const inputValueRef = useRef('');
  const recognitionRef = useRef(null);
  const speechBaseTextRef = useRef('');
  const speechStartingRef = useRef(false);
  const speechStopRequestedRef = useRef(false);
  const speechFallbackTriedRef = useRef(false);
  const speechRetryCountRef = useRef(0);
  const speechRetryTimerRef = useRef(null);

  useEffect(() => {
    inputValueRef.current = inputValue;
  }, [inputValue]);

  const parseHistoryMessageText = useCallback((content) => {
    if (!content) return '';
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) {
      return content
        .filter((block) => block && typeof block === 'object' && typeof block.text === 'string')
        .map((block) => block.text)
        .join('\n')
        .trim();
    }
    return '';
  }, []);

  const toDisplayMessages = useCallback(
    (history) =>
      (history || [])
        .filter((msg) => msg && (msg.role === 'user' || msg.role === 'assistant'))
        .map((msg, idx) => ({
          role: msg.role,
          content: parseHistoryMessageText(msg.content),
          timestamp: msg.timestamp || new Date().toISOString(),
          _idx: idx,
        }))
        .filter((msg) => Boolean(msg.content)),
    [parseHistoryMessageText]
  );

  const fetchSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    try {
      const response = await api.getChatSessions();
      setChatSessions(response.sessions || []);
    } catch (err) {
      setError(err.message || 'Failed to load saved sessions');
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  const startRenamingSession = useCallback((session) => {
    setRenamingSessionId(session.session_id);
    setRenameValue(session.title || 'Untitled Chat');
  }, []);

  const cancelRenamingSession = useCallback(() => {
    setRenamingSessionId(null);
    setRenameValue('');
  }, []);

  const saveSessionRename = useCallback(
    async (targetSessionId) => {
      const trimmed = renameValue.trim();
      if (!trimmed) return;
      try {
        await api.renameChatSession(targetSessionId, trimmed);
        setRenamingSessionId(null);
        setRenameValue('');
        fetchSessions();
      } catch (err) {
        setError(err.message || 'Failed to rename session');
      }
    },
    [renameValue, fetchSessions]
  );

  const handleDeleteSession = useCallback(
    async (targetSessionId) => {
      try {
        await api.deleteChatSession(targetSessionId);
        if (targetSessionId === sessionId) {
          setSessionId(null);
          setMessages([]);
        }
        if (targetSessionId === lastOpenedSessionId) {
          setLastOpenedSessionId(null);
        }
        fetchSessions();
      } catch (err) {
        setError(err.message || 'Failed to delete session');
      }
    },
    [fetchSessions, lastOpenedSessionId, sessionId]
  );

  const confirmDeleteSession = useCallback(async () => {
    if (!pendingDeleteSession?.session_id) return;
    await handleDeleteSession(pendingDeleteSession.session_id);
    setPendingDeleteSession(null);
  }, [handleDeleteSession, pendingDeleteSession]);

  const loadSession = useCallback(
    async (nextSessionId) => {
      if (!nextSessionId) return;
      setError(null);
      setIsLoading(true);
      try {
        const response = await api.getChatHistory(nextSessionId);
        setSessionId(nextSessionId);
        setLastOpenedSessionId(nextSessionId);
        setMessages(toDisplayMessages(response.history));
      } catch (err) {
        setError(err.message || 'Failed to load chat history');
      } finally {
        setIsLoading(false);
      }
    },
    [toDisplayMessages]
  );

  const startNewSession = useCallback(() => {
    const nextSessionId = `chat_${Date.now()}`;
    setSessionId(nextSessionId);
    setMessages([]);
    setError(null);
    if (textareaRef.current) textareaRef.current.style.height = '24px';
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
  }, []);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return undefined;
    }

    setSpeechSupported(true);
    const recognition = new SpeechRecognition();
    const clearRetryTimer = () => {
      if (speechRetryTimerRef.current) {
        clearTimeout(speechRetryTimerRef.current);
        speechRetryTimerRef.current = null;
      }
    };

    const queueRecognitionRetry = (delayMs = 300) => {
      clearRetryTimer();
      speechRetryTimerRef.current = setTimeout(() => {
        speechRetryTimerRef.current = null;
        try {
          recognition.start();
        } catch {
          // If retry fails, the user can try manually.
        }
      }, delayMs);
    };

    const configureRecognition = (useFallback = false) => {
      recognition.lang = useFallback ? (navigator.language || 'en-US') : 'en-IN';
      recognition.continuous = !useFallback;
      recognition.interimResults = !useFallback;
      recognition.maxAlternatives = 1;
    };
    configureRecognition(false);

    recognition.onstart = () => {
      clearRetryTimer();
      speechStartingRef.current = false;
      speechRetryCountRef.current = 0;
      setIsListening(true);
      setVoiceError(null);
      speechBaseTextRef.current = (inputValueRef.current || '').trim();
    };

    recognition.onend = () => {
      clearRetryTimer();
      speechStartingRef.current = false;
      setIsListening(false);
      speechBaseTextRef.current = (inputValueRef.current || '').trim();
      speechStopRequestedRef.current = false;
    };

    recognition.onerror = (event) => {
      speechStartingRef.current = false;
      if (event.error === 'aborted') {
        return;
      }
      if (event.error === 'no-speech') {
        setVoiceError('No speech detected. Please try again.');
      } else if (event.error === 'not-allowed') {
        setVoiceError('Microphone permission denied. Enable mic access in your browser.');
      } else if (event.error === 'service-not-allowed') {
        setVoiceError('Speech recognition service is blocked in this browser/profile.');
      } else if (event.error === 'audio-capture') {
        setVoiceError('No microphone found. Connect a mic and try again.');
      } else if (event.error === 'network') {
        if (navigator.onLine === false) {
          setVoiceError('You appear to be offline. Reconnect internet and try voice typing again.');
          return;
        }

        // Detect if browser is Brave or another privacy-focused browser
        const isBrave = navigator.brave ? true : /Brave/.test(navigator.userAgent);
        if (isBrave) {
          setVoiceError('Brave blocks Web Speech API by default. Try Chrome, Edge, or Safari, or enable it in Brave settings.');
          return;
        }

        // Retry once for transient network issues
        if (speechRetryCountRef.current === 0) {
          speechRetryCountRef.current = 1;
          configureRecognition(true);
          setVoiceError('Network issue detected. Retrying...');
          queueRecognitionRetry(400);
          return;
        }

        // If retry failed, likely a persistent service issue
        setVoiceError('Voice typing is unavailable. Try a different browser (Chrome/Edge/Safari) or keep typing manually.');
      } else if (event.error === 'language-not-supported') {
        if (!speechFallbackTriedRef.current) {
          speechFallbackTriedRef.current = true;
          configureRecognition(true);
          setVoiceError('Language fallback applied. Retrying voice typing...');
          queueRecognitionRetry(250);
          return;
        }
        setVoiceError('Selected speech language is not supported in this browser.');
      } else {
        setVoiceError(`Voice typing error: ${event.error || 'unknown'}. Please try again.`);
      }
    };

    recognition.onresult = (event) => {
      let finalText = '';
      let interimText = '';

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const transcript = (event.results[i][0]?.transcript || '').trim();
        if (!transcript) continue;
        if (event.results[i].isFinal) {
          finalText += `${transcript} `;
        } else {
          interimText += `${transcript} `;
        }
      }

      if (finalText.trim()) {
        speechBaseTextRef.current = [speechBaseTextRef.current, finalText.trim()].filter(Boolean).join(' ').trim();
      }

      const composed = [speechBaseTextRef.current, interimText.trim()]
        .filter(Boolean)
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim();

      setInputValue(composed);
      setTimeout(() => handleTextareaResize(), 0);
    };

    recognitionRef.current = recognition;

    return () => {
      clearRetryTimer();
      try {
        recognition.stop();
      } catch {
        // ignore cleanup stop errors
      }
      recognitionRef.current = null;
      speechFallbackTriedRef.current = false;
      speechRetryCountRef.current = 0;
    };
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  useEffect(() => {
    if (!sessionId && chatSessions.length > 0) {
      loadSession(chatSessions[0].session_id);
    }
  }, [chatSessions, loadSession, sessionId]);

  // Auto-resize textarea
  const handleTextareaResize = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = '24px';
      el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }
  };

  // Send message
  const sendMessage = async (text) => {
    const message = text || inputValue.trim();
    if (!message || isLoading) return;

    if (isListening && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
    }

    setInputValue('');
    setError(null);
    if (textareaRef.current) textareaRef.current.style.height = '24px';

    // Add user message
    const userMsg = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await api.sendChatMessage(message, sessionId);

      if (response.success) {
        if (response.session_id) {
          setSessionId(response.session_id);
          setLastOpenedSessionId(response.session_id);
        }

        const assistantMsg = {
          role: 'assistant',
          content: response.response,
          widgets: response.widgets || [],
          timestamp: response.timestamp || new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        fetchSessions();
      } else {
        setError(response.error || 'Something went wrong');
      }
    } catch (err) {
      setError(err.message || 'Failed to connect to AI assistant');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleVoiceToggle = () => {
    if (!speechSupported || isLoading) return;
    setVoiceError(null);

    if (navigator.onLine === false) {
      setVoiceError('You are offline. Reconnect internet and try voice typing again.');
      return;
    }

    if (!window.isSecureContext) {
      setVoiceError('Voice typing requires a secure context (HTTPS or localhost).');
      return;
    }

    if (!recognitionRef.current) {
      setVoiceError('Voice typing is unavailable in this browser.');
      return;
    }

    if (isListening || speechStartingRef.current) {
      speechStopRequestedRef.current = true;
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      return;
    }

    try {
      speechFallbackTriedRef.current = false;
      speechRetryCountRef.current = 0;
      if (speechRetryTimerRef.current) {
        clearTimeout(speechRetryTimerRef.current);
        speechRetryTimerRef.current = null;
      }
      speechStartingRef.current = true;
      speechStopRequestedRef.current = false;
      recognitionRef.current.start();
    } catch (e) {
      speechStartingRef.current = false;
      if (e?.name === 'InvalidStateError') {
        setVoiceError('Voice capture is already starting. Please wait a second and try again.');
      } else {
        setVoiceError('Could not start voice typing. Please try again.');
      }
    }
  };

  // Clear chat
  const handleClearChat = async () => {
    if (!sessionId) {
      setMessages([]);
      return;
    }
    try {
      await api.clearChatHistory(sessionId);
    } catch (e) {
      // ignore
    }
    setMessages([]);
    setError(null);
    setVoiceError(null);
    fetchSessions();
  };

  // Format timestamp
  const formatTime = (ts) => {
    try {
      return new Date(ts).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return '';
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="chat-page">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid"></div>
        <div className="absolute top-[-20%] left-[30%] w-[500px] h-[500px] bg-pink-500/10 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
        <div className="absolute bottom-[-10%] right-[-5%] w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[100px] mix-blend-screen"></div>
      </div>

      {/* Navigation Header */}
      <nav className="fixed top-0 left-0 w-full z-50 transition-all duration-300">
        <div className="absolute inset-0 bg-black/50 backdrop-blur-md border-b border-white/5"></div>
        <div className="max-w-7xl mx-auto px-6 h-16 relative flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-3 group transition-all hover:opacity-80"
          >
            <div className="w-8 h-8 flex items-center justify-center bg-white/5 rounded-lg border border-white/10 group-hover:border-pink-500/50 transition-colors">
              <iconify-icon icon="solar:layers-minimalistic-bold-duotone" className="text-pink-400 text-xl"></iconify-icon>
            </div>
            <span className="font-display font-bold text-lg text-white">SmartFin</span>
            <span className="text-[10px] text-white/30 font-mono">AI ASSISTANT</span>
          </button>

          <div className="flex items-center gap-3">
            {hasMessages && (
              <button onClick={handleClearChat} className="chat-clear-btn">
                <iconify-icon icon="solar:trash-bin-minimalistic-linear" width="14"></iconify-icon>
                <span>Clear Chat</span>
              </button>
            )}
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all text-xs font-medium text-white/70"
            >
              <iconify-icon icon="solar:home-2-linear" width="16"></iconify-icon>
              <span className="hidden md:inline">Dashboard</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Sidebar */}
      <Sidebar />

      {/* Chat Container */}
      <div className="chat-container">
        <aside className="chat-session-panel">
          <div className="chat-session-header">
            <p className="chat-session-title">Saved Chats</p>
            <div className="chat-session-actions">
              <button className="chat-session-btn" onClick={startNewSession}>
                <iconify-icon icon="solar:add-circle-linear" width="14"></iconify-icon>
                <span>New</span>
              </button>
              <button className="chat-session-btn" onClick={fetchSessions} disabled={isLoadingSessions}>
                <iconify-icon icon="solar:refresh-linear" width="14"></iconify-icon>
                <span>Refresh</span>
              </button>
            </div>
          </div>
          <div className="chat-session-list">
            {isLoadingSessions ? (
              <p className="chat-session-empty">Loading sessions...</p>
            ) : chatSessions.length === 0 ? (
              <p className="chat-session-empty">No saved chats yet.</p>
            ) : (
              chatSessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`chat-session-item ${sessionId === session.session_id ? 'active' : ''} ${lastOpenedSessionId === session.session_id ? 'last-opened' : ''}`}
                  onClick={() => loadSession(session.session_id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      loadSession(session.session_id);
                    }
                  }}
                >
                  {renamingSessionId === session.session_id ? (
                    <div className="chat-session-rename-row" onClick={(e) => e.stopPropagation()}>
                      <input
                        className="chat-session-rename-input"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') saveSessionRename(session.session_id);
                          if (e.key === 'Escape') cancelRenamingSession();
                        }}
                        autoFocus
                      />
                      <button className="chat-session-icon-btn" onClick={() => saveSessionRename(session.session_id)}>
                        <iconify-icon icon="solar:check-circle-linear" width="14"></iconify-icon>
                      </button>
                      <button className="chat-session-icon-btn" onClick={cancelRenamingSession}>
                        <iconify-icon icon="solar:close-circle-linear" width="14"></iconify-icon>
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="chat-session-item-top">
                        <span className="chat-session-item-title">{session.title || 'Untitled Chat'}</span>
                        <div className="chat-session-item-tools" onClick={(e) => e.stopPropagation()}>
                          <button className="chat-session-icon-btn" onClick={() => startRenamingSession(session)}>
                            <iconify-icon icon="solar:pen-linear" width="12"></iconify-icon>
                          </button>
                          <button className="chat-session-icon-btn danger" onClick={() => setPendingDeleteSession(session)}>
                            <iconify-icon icon="solar:trash-bin-trash-linear" width="12"></iconify-icon>
                          </button>
                        </div>
                      </div>
                      {lastOpenedSessionId === session.session_id && <span className="chat-session-tag">Last opened</span>}
                      <span className="chat-session-item-meta">{formatTime(session.last_message_at || session.updated_at)}</span>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </aside>

        <div className="chat-main-pane">
        <div className="chat-pane-header">
          <div className="chat-pane-eyebrow">
            <span className="chat-pane-dot"></span>
            <span>AI Assistant</span>
          </div>
          <h1 className="chat-pane-title">SmartFin <span className="chat-pane-title-accent">Chatbot</span></h1>
          <p className="chat-pane-subtitle">Ask about budgets, loans, goals, and retirement with context from your saved data.</p>
        </div>

        {/* Welcome Screen or Messages */}
        {!hasMessages ? (
          <div className="chat-welcome">
            <div className="welcome-icon">
              <iconify-icon icon="solar:chat-round-dots-bold-duotone" width="40" style={{ color: 'rgba(236, 72, 153, 0.7)' }}></iconify-icon>
            </div>
            <div>
              <h2 className="welcome-title">SmartFin AI Assistant</h2>
              <p className="welcome-subtitle">
                I can analyze your finances, run what-if simulations, plan your retirement, 
                and provide personalized financial advice. How can I help you today?
              </p>
            </div>
            <div className="welcome-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  className="suggestion-chip"
                  onClick={() => sendMessage(s.text)}
                >
                  <iconify-icon icon={s.icon} width="18"></iconify-icon>
                  <span>{s.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role}`}>
                <div className={`message-avatar ${msg.role === 'user' ? 'user-avatar' : 'assistant-avatar'}`}>
                  <iconify-icon
                    icon={msg.role === 'user' ? 'solar:user-linear' : 'solar:chat-round-dots-linear'}
                    width="16"
                  ></iconify-icon>
                </div>
                <div className="message-content">
                  <div
                    className="message-bubble"
                    dangerouslySetInnerHTML={{
                      __html: msg.role === 'assistant' ? formatText(msg.content) : msg.content,
                    }}
                  />
                  {/* Render widgets for assistant messages */}
                  {msg.widgets && msg.widgets.length > 0 && (
                    <div className="message-widgets">
                      {msg.widgets.map((w, wi) => (
                        <ToolWidget key={wi} widget={w} />
                      ))}
                    </div>
                  )}
                  <div className="message-time">{formatTime(msg.timestamp)}</div>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isLoading && (
              <div className="typing-indicator">
                <div className="message-avatar assistant-avatar">
                  <iconify-icon icon="solar:chat-round-dots-linear" width="16"></iconify-icon>
                </div>
                <div>
                  <div className="typing-dots">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                  <span className="typing-label">SmartFin AI is thinking...</span>
                </div>
              </div>
            )}

            {/* Error display */}
            {error && (
              <div className="chat-error">
                <iconify-icon icon="solar:danger-triangle-linear" width="16"></iconify-icon>
                <span>{error}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input Area */}
        <div className="chat-input-area">
          <div className="chat-input-wrapper">
            <textarea
              ref={textareaRef}
              className="chat-input"
              placeholder="Ask about your finances..."
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                handleTextareaResize();
              }}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              rows={1}
            />
            <button
              className={`chat-voice-btn ${isListening ? 'listening' : ''}`}
              onClick={handleVoiceToggle}
              disabled={!speechSupported || isLoading}
              title={speechSupported ? (isListening ? 'Stop voice typing' : 'Start voice typing') : 'Voice typing not supported'}
            >
              <iconify-icon icon={isListening ? 'solar:stop-circle-linear' : 'solar:microphone-linear'} width="18"></iconify-icon>
            </button>
            <button
              className="chat-send-btn"
              onClick={() => sendMessage()}
              disabled={!inputValue.trim() || isLoading}
              title="Send message"
            >
              <iconify-icon icon="solar:arrow-up-linear" width="20"></iconify-icon>
            </button>
          </div>
          <div className="chat-input-hint">
            {isListening
              ? 'Listening... speak clearly to fill the message box'
              : 'SmartFin AI can analyze your data, run simulations, and provide financial advice'}
          </div>
          {voiceError && <div className="chat-voice-error">{voiceError}</div>}
          <div className="quick-shortcuts">
            {QUICK_SHORTCUTS.map((prompt) => (
              <button
                key={prompt}
                className="quick-shortcut-chip"
                onClick={() => sendMessage(prompt)}
                disabled={isLoading}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
        </div>
      </div>

      {pendingDeleteSession && (
        <div className="chat-modal-overlay" role="dialog" aria-modal="true">
          <div className="chat-modal-card">
            <div className="chat-modal-header">
              <iconify-icon icon="solar:danger-circle-linear" width="18"></iconify-icon>
              <h3>Delete chat session?</h3>
            </div>
            <p className="chat-modal-text">
              This will permanently remove <strong>{pendingDeleteSession.title || 'Untitled Chat'}</strong> and its saved history.
            </p>
            <div className="chat-modal-actions">
              <button className="chat-modal-btn" onClick={() => setPendingDeleteSession(null)}>
                Cancel
              </button>
              <button className="chat-modal-btn danger" onClick={confirmDeleteSession}>
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      <SmartFinFooter iconClass="text-pink-400" statusDotClass="bg-pink-400" />
    </div>
  );
};

export default ChatAgent;
