"""
SmartFin - Flask Backend
Main application file for financial health scoring and guidance
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import sqlite3
import json
import uuid
import logging

# Configure logging - MUST be before Flask app creation
import sys

# Ensure unbuffered output
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

# Create custom formatter
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Console handler with immediate flushing
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(log_format))

# File handler with immediate flushing
file_handler = logging.FileHandler('backend.log', mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(log_format))

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[console_handler, file_handler],
    force=True
)

logger = logging.getLogger(__name__)

# Ensure handlers flush immediately
for handler in logging.root.handlers:
    handler.flush()

# Force print to console
print("\n" + "="*80, file=sys.stdout, flush=True)
print("SMARTFIN BACKEND LOGGING INITIALIZED", file=sys.stdout, flush=True)
print("="*80 + "\n", file=sys.stdout, flush=True)
sys.stdout.flush()

# Load environment variables
load_dotenv()

# Custom logger class that flushes after every message
class FlushingLogger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=None):
        super()._log(level, msg, args, exc_info, extra, stack_info)
        for handler in self.handlers:
            handler.flush()
        for handler in logging.root.handlers:
            handler.flush()

logging.setLoggerClass(FlushingLogger)
logger = logging.getLogger(__name__)

# Import retirement planning API
from retirement_planning.api import retirement_bp
from retirement_planning.migrations import RetirementPlanningMigrations
from guidance_engine import PersonalizedGuidanceEngine

# Import new ML core modules
from portfolio_optimizer.api import portfolio_bp
from nudge_engine.api import nudge_bp

# Import blueprints extracted from this file
from auth.api import auth_bp
from profile_management.api import profile_bp
from budget.api import budget_bp
from budget.service import current_month_string, build_budget_summary, build_analysis_payload_from_summary

from db_core import DB_PATH, get_db, close_connection, execute_query, row_to_dict, rows_to_list

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'smartfin-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# File upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'profile_pictures')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'webp'}

jwt = JWTManager(app)

CORS(app, 
     origins=["https://saumye0106.github.io", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# Handle CORS preflight requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        headers = response.headers
        headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
        headers["Access-Control-Allow-Headers"] = request.headers.get("Access-Control-Request-Headers", "Content-Type,Authorization")
        headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
        headers["Access-Control-Allow-Credentials"] = "true"
        return response

@app.after_request
def log_response(response):
    logger.debug(f"{request.method} {request.path} -> {response.status_code}")
    return response

app.teardown_appcontext(close_connection)

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(budget_bp)

# Global error handler
@app.errorhandler(Exception)
def handle_all_errors(error):
    import traceback
    logger.error(f"Unhandled exception: {str(error)}\n{traceback.format_exc()}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

def init_db():
    """Initialize the database with required tables"""
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    
    # Users table (existing)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            email_verified INTEGER DEFAULT 0,
            email_verification_token TEXT,
            email_verification_expires TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Password reset tokens table (new)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reset_code TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # User profiles table (new)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users_profile (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL CHECK (age >= 18 AND age <= 120),
            location TEXT NOT NULL,
            risk_tolerance INTEGER CHECK (risk_tolerance >= 1 AND risk_tolerance <= 10),
            profile_picture_url TEXT,
            notification_preferences TEXT DEFAULT '{"email": true, "push": false, "in_app": true, "frequency": "daily"}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Financial goals table (new)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS financial_goals (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            goal_type TEXT NOT NULL CHECK (goal_type IN ('short-term', 'long-term')),
            target_amount REAL NOT NULL CHECK (target_amount > 0),
            target_date TEXT NOT NULL,
            priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users_profile(user_id) ON DELETE CASCADE
        )
    ''')

    # Monthly budgets table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS monthly_budgets (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            monthly_income REAL NOT NULL DEFAULT 0 CHECK (monthly_income >= 0),
            planned_savings REAL NOT NULL DEFAULT 0 CHECK (planned_savings >= 0),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, month)
        )
    ''')

    # Category-level budget allocations for each month
    cur.execute('''
        CREATE TABLE IF NOT EXISTS budget_categories (
            id TEXT PRIMARY KEY,
            budget_id TEXT NOT NULL,
            category TEXT NOT NULL,
            planned_amount REAL NOT NULL CHECK (planned_amount >= 0),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (budget_id) REFERENCES monthly_budgets(id) ON DELETE CASCADE,
            UNIQUE(budget_id, category)
        )
    ''')

    # Expense entries table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expense_entries (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            budget_id TEXT,
            expense_date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK (amount > 0),
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (budget_id) REFERENCES monthly_budgets(id) ON DELETE SET NULL
        )
    ''')
    
    # Loans table (loan history enhancement)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            loan_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            loan_type TEXT NOT NULL CHECK (loan_type IN ('personal', 'home', 'auto', 'education')),
            loan_amount REAL NOT NULL CHECK (loan_amount > 0),
            loan_tenure INTEGER NOT NULL CHECK (loan_tenure > 0),
            monthly_emi REAL NOT NULL CHECK (monthly_emi > 0),
            interest_rate REAL NOT NULL CHECK (interest_rate >= 0 AND interest_rate <= 50),
            loan_start_date TEXT NOT NULL,
            loan_maturity_date TEXT NOT NULL,
            default_status INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Loan payments table (loan history enhancement)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS loan_payments (
            payment_id TEXT PRIMARY KEY,
            loan_id TEXT NOT NULL,
            payment_date TEXT NOT NULL,
            payment_amount REAL NOT NULL CHECK (payment_amount > 0),
            payment_status TEXT NOT NULL CHECK (payment_status IN ('on-time', 'late', 'missed')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
        )
    ''')
    
    # Loan metrics table (loan history enhancement - for caching)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS loan_metrics (
            user_id INTEGER PRIMARY KEY,
            loan_diversity_score REAL CHECK (loan_diversity_score >= 0 AND loan_diversity_score <= 100),
            payment_history_score REAL CHECK (payment_history_score >= 0 AND payment_history_score <= 100),
            loan_maturity_score REAL CHECK (loan_maturity_score >= 0 AND loan_maturity_score <= 100),
            payment_statistics TEXT,
            loan_statistics TEXT,
            calculated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Persistent chat sessions table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT,
            conversation_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_message_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for better query performance
    cur.execute('CREATE INDEX IF NOT EXISTS idx_users_profile_user_id ON users_profile(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_financial_goals_user_id ON financial_goals(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_financial_goals_priority ON financial_goals(priority)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_financial_goals_status ON financial_goals(status)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_code ON password_reset_tokens(reset_code)')
    
    # Loan-related indexes
    cur.execute('CREATE INDEX IF NOT EXISTS idx_loans_user_id ON loans(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_loans_loan_type ON loans(loan_type)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_loans_default_status ON loans(default_status)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_loans_deleted_at ON loans(deleted_at)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_loan_payments_loan_id ON loan_payments(loan_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_loan_payments_payment_date ON loan_payments(payment_date)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_loan_payments_payment_status ON loan_payments(payment_status)')

    # Budget/expense indexes
    cur.execute('CREATE INDEX IF NOT EXISTS idx_monthly_budgets_user_month ON monthly_budgets(user_id, month)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_budget_categories_budget_id ON budget_categories(budget_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_expense_entries_user_date ON expense_entries(user_id, expense_date)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_expense_entries_category ON expense_entries(category)')

    # Chat session indexes
    cur.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_message_at ON chat_sessions(last_message_at)')
    
    db.commit()
    db.close()
    
    # Initialize retirement planning tables
    RetirementPlanningMigrations.create_tables(DB_PATH)

# Initialize database
init_db()

def _run_prediction_analysis(data):
    # Calculate expenses from individual categories if provided
    expenses = data.get('expenses', 0)
    if expenses == 0 and any(k in data for k in ['rent', 'food', 'travel', 'shopping']):
        expenses = (data.get('rent', 0) + data.get('food', 0) +
                   data.get('travel', 0) + data.get('shopping', 0))

    # Get optional fields with defaults
    age = data.get('age', 30)
    has_loan = data.get('has_loan', False)
    loan_amount = data.get('loan_amount', 0)
    interest_rate = data.get('interest_rate', 0)

    # Prepare features for enhanced model prediction
    features = pd.DataFrame([[
        data['income'],           # income
        expenses,                 # expenses
        data['savings'],          # savings
        data['emi'],              # emi
        age,                      # age
        int(has_loan),            # has_loan_numeric
        loan_amount,              # loan_amount_filled
        interest_rate             # interest_rate_filled
    ]], columns=feature_names)

    # Predict score
    predicted_score = float(model.predict(features)[0])
    predicted_score = max(0, min(100, round(predicted_score, 2)))

    # Get classification and enrichments
    classification = classify_score(predicted_score)
    patterns = analyze_spending_patterns(data)
    guidance = generate_guidance(data, predicted_score, patterns)
    anomalies = detect_anomalies(data, patterns)
    investments = suggest_investments(predicted_score, data, patterns)

    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'score': predicted_score,
        'classification': classification,
        'patterns': patterns,
        'guidance': guidance,
        'anomalies': anomalies,
        'investments': investments,
        'model_info': {
            'model_type': model_data['model_type'],
            'accuracy': f"{model_metadata['r2_test']:.2%}",
            'average_error': f"±{model_metadata['mae_test']:.1f} points"
        }
    }

# ==================== LOAD ML MODEL ====================
print("Loading ML model...")
# Get the absolute path to the data directory for enhanced model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Load enhanced model
model_data = joblib.load(os.path.join(DATA_DIR, 'enhanced_model.pkl'))
model = model_data['model']
feature_names = model_data['feature_cols']
model_metadata = model_data['metrics']
print(f"Model loaded: {model_data['model_type']}")
print(f"Model R2 Score: {model_metadata['r2_test']:.4f} (95.85% - Enhanced 8-Factor Model)")

# ==================== HELPER FUNCTIONS ====================

def classify_score(score):
    """
    Classify financial health score into 5 categories
    """
    if score >= 80:
        return {
            'category': 'Excellent',
            'color': '#10b981',  # green
            'emoji': '🌟',
            'description': 'Outstanding financial health! Keep up the great work.'
        }
    elif score >= 65:
        return {
            'category': 'Very Good',
            'color': '#3b82f6',  # blue
            'emoji': '✨',
            'description': 'Strong financial position with room for minor improvements.'
        }
    elif score >= 50:
        return {
            'category': 'Good',
            'color': '#f59e0b',  # amber
            'emoji': '👍',
            'description': 'Decent financial health, but consider optimizing your spending.'
        }
    elif score >= 35:
        return {
            'category': 'Average',
            'color': '#f97316',  # orange
            'emoji': '⚠️',
            'description': 'Your finances need attention. Review your expenses carefully.'
        }
    else:
        return {
            'category': 'Poor',
            'color': '#ef4444',  # red
            'emoji': '🚨',
            'description': 'Critical financial situation. Immediate action required!'
        }


def analyze_spending_patterns(data):
    """
    Analyze spending patterns and provide insights
    """
    income = data['income']
    rent = data['rent']
    food = data['food']
    travel = data['travel']
    shopping = data['shopping']
    emi = data['emi']
    savings = data['savings']

    total_expense = rent + food + travel + shopping + emi

    # Calculate ratios
    expense_ratio = total_expense / income if income > 0 else 0
    savings_ratio = savings / income if income > 0 else 0
    emi_ratio = emi / income if income > 0 else 0

    # Calculate percentage breakdown
    breakdown = {
        'rent': (rent / income * 100) if income > 0 else 0,
        'food': (food / income * 100) if income > 0 else 0,
        'travel': (travel / income * 100) if income > 0 else 0,
        'shopping': (shopping / income * 100) if income > 0 else 0,
        'emi': (emi / income * 100) if income > 0 else 0,
        'savings': (savings / income * 100) if income > 0 else 0
    }

    # Identify highest expense
    expense_categories = {
        'Rent': rent,
        'Food': food,
        'Travel': travel,
        'Shopping': shopping,
        'EMI': emi
    }
    highest_expense = max(expense_categories, key=expense_categories.get)

    patterns = {
        'total_expense': total_expense,
        'expense_ratio': round(expense_ratio, 3),
        'savings_ratio': round(savings_ratio, 3),
        'emi_ratio': round(emi_ratio, 3),
        'breakdown': {k: round(v, 2) for k, v in breakdown.items()},
        'highest_expense_category': highest_expense,
        'highest_expense_amount': expense_categories[highest_expense]
    }

    return patterns


def generate_guidance(data, score, patterns):
    """
    Generate personalized financial guidance based on score and patterns
    """
    try:
        guidance, meta = PersonalizedGuidanceEngine.generate_guidance_ai(
            data, score, patterns, return_meta=True
        )
        app.logger.info(
            "guidance_engine source=%s engine=%s score=%.2f",
            meta.get('source'),
            meta.get('engine'),
            float(score or 0),
        )
        return guidance
    except Exception:
        # Keep legacy fallback behavior for resilience.
        pass

    guidance = {
        'recommendations': [],
        'strengths': [],
        'warnings': []
    }

    income = data['income']
    expense_ratio = patterns['expense_ratio']
    savings_ratio = patterns['savings_ratio']
    emi_ratio = patterns['emi_ratio']

    # Analyze savings
    if savings_ratio >= 0.25:
        guidance['strengths'].append("Excellent savings habit! You're saving 25%+ of your income.")
    elif savings_ratio >= 0.15:
        guidance['strengths'].append("Good savings discipline. Keep it up!")
    elif savings_ratio < 0.05:
        guidance['warnings'].append("Very low savings rate. Try to save at least 10% of income.")
        guidance['recommendations'].append("Set up automatic savings transfers on payday.")

    # Analyze expenses
    if expense_ratio > 0.8:
        guidance['warnings'].append("You're spending over 80% of your income. This is unsustainable.")
        guidance['recommendations'].append("Review all expenses and cut non-essential spending immediately.")
    elif expense_ratio > 0.6:
        guidance['recommendations'].append("Try to reduce total expenses to below 60% of income.")

    # Analyze EMI
    if emi_ratio > 0.4:
        guidance['warnings'].append("EMI is consuming over 40% of income - very high debt burden!")
        guidance['recommendations'].append("Avoid taking new loans. Focus on clearing existing debt.")
    elif emi_ratio > 0.3:
        guidance['recommendations'].append("EMI burden is high. Consider debt consolidation.")
    elif emi_ratio == 0:
        guidance['strengths'].append("No EMI burden - excellent!")

    # Analyze specific categories
    rent_ratio = data['rent'] / income if income > 0 else 0
    if rent_ratio > 0.35:
        guidance['recommendations'].append("Rent is high (>35% of income). Consider finding cheaper accommodation.")

    shopping_ratio = data['shopping'] / income if income > 0 else 0
    if shopping_ratio > 0.15:
        guidance['recommendations'].append("Shopping expenses are high. Try to limit discretionary spending.")

    # Overall recommendations based on score
    if score < 35:
        guidance['recommendations'].insert(0, "URGENT: Create a strict budget and track every expense.")
    elif score < 50:
        guidance['recommendations'].insert(0, "Focus on building an emergency fund of 3-6 months expenses.")
    elif score >= 80:
        guidance['strengths'].append("Excellent financial management! Consider investment opportunities.")

    return guidance


def detect_anomalies(data, patterns):
    """
    Detect financial anomalies and risks
    """
    anomalies = []

    income = data['income']
    savings = data['savings']
    expense_ratio = patterns['expense_ratio']
    savings_ratio = patterns['savings_ratio']
    emi_ratio = patterns['emi_ratio']

    # Critical anomalies
    if expense_ratio > 1.0:
        anomalies.append({
            'severity': 'critical',
            'type': 'deficit',
            'message': 'You are spending MORE than you earn! Immediate action needed.'
        })

    if savings == 0 and income > 20000:
        anomalies.append({
            'severity': 'high',
            'type': 'no_savings',
            'message': 'Zero savings detected. You have no financial cushion for emergencies.'
        })

    if emi_ratio > 0.5:
        anomalies.append({
            'severity': 'critical',
            'type': 'debt_trap',
            'message': 'EMI exceeds 50% of income. Risk of debt trap!'
        })

    # Medium risk anomalies
    if savings_ratio < 0.05 and expense_ratio > 0.7:
        anomalies.append({
            'severity': 'medium',
            'type': 'low_buffer',
            'message': 'Very low savings with high expenses. Financial vulnerability detected.'
        })

    # Warnings
    if data['shopping'] > data['savings'] and data['shopping'] > 5000:
        anomalies.append({
            'severity': 'low',
            'type': 'spending_priority',
            'message': 'Shopping expenses exceed savings. Consider rebalancing priorities.'
        })

    return anomalies


def suggest_investments(score, data, patterns):
    """
    Rule-based investment suggestions based on score and financial profile
    """
    try:
        investments, meta = PersonalizedGuidanceEngine.suggest_investments_ai(
            score, data, patterns, return_meta=True
        )
        app.logger.info(
            "investment_engine source=%s engine=%s score=%.2f",
            meta.get('source'),
            meta.get('engine'),
            float(score or 0),
        )
        return investments
    except Exception:
        # Keep legacy fallback behavior for resilience.
        pass

    suggestions = []

    savings_ratio = patterns['savings_ratio']
    emi_ratio = patterns['emi_ratio']
    monthly_savings = data['savings']

    # Investment eligibility based on score and ratios
    if score >= 70 and savings_ratio >= 0.15 and emi_ratio < 0.3:
        suggestions.append({
            'type': 'Equity Mutual Funds',
            'risk_level': 'Medium to High',
            'allocation': int(monthly_savings * 0.4),
            'description': 'Good financial health allows for growth-oriented investments.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Public Provident Fund (PPF)',
            'risk_level': 'Low',
            'allocation': int(monthly_savings * 0.3),
            'description': 'Tax-saving with guaranteed returns.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Fixed Deposits',
            'risk_level': 'Low',
            'allocation': int(monthly_savings * 0.3),
            'description': 'Safe option for emergency fund.',
            'suitable': True
        })

    elif score >= 50 and savings_ratio >= 0.1:
        suggestions.append({
            'type': 'Hybrid Mutual Funds',
            'risk_level': 'Medium',
            'allocation': int(monthly_savings * 0.5),
            'description': 'Balanced approach for moderate risk appetite.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Recurring Deposits',
            'risk_level': 'Very Low',
            'allocation': int(monthly_savings * 0.5),
            'description': 'Build disciplined savings habit.',
            'suitable': True
        })

    elif score >= 35:
        suggestions.append({
            'type': 'Emergency Fund (Savings Account)',
            'risk_level': 'None',
            'allocation': monthly_savings,
            'description': 'Build emergency fund first before investing.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Equity Investments',
            'risk_level': 'High',
            'allocation': 0,
            'description': 'Focus on stabilizing finances before risky investments. Not recommended at this time.',
            'suitable': False
        })

    else:  # score < 35
        suggestions.append({
            'type': 'Focus on Debt Reduction',
            'risk_level': 'N/A',
            'allocation': monthly_savings,
            'description': 'Clear debts and stabilize finances before investing.',
            'suitable': True
        })
        suggestions.append({
            'type': 'Any Investments',
            'risk_level': 'N/A',
            'allocation': 0,
            'description': 'Investment not advisable until financial health improves.',
            'suitable': False
        })

    return {
        'eligible': score >= 50 and savings_ratio >= 0.1,
        'suggestions': suggestions,
        'message': get_investment_advice(score),
        'advice': get_investment_advice(score)
    }


def get_investment_advice(score):
    """Get overall investment advice based on score"""
    if score >= 80:
        return "Your finances are excellent! Consider aggressive investment strategies for wealth building."
    elif score >= 65:
        return "Good financial position. Diversify investments across equity and debt instruments."
    elif score >= 50:
        return "Decent financial health. Start with low-risk investments and build emergency fund."
    elif score >= 35:
        return "Focus on building emergency fund before investing. Aim for 3 months of expenses."
    else:
        return "Not advisable to invest currently. Focus on reducing debt and increasing savings."


# ==================== API ENDPOINTS ====================

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'SmartFin Financial Health API',
        'version': '1.0',
        'model': model_data['model_type'],
        'model_accuracy': f"{model_metadata['r2_test']:.2%}"
    })


@app.route('/api/predict', methods=['POST'])
def predict_score():
    """
    Main prediction endpoint
    Accepts financial data and returns comprehensive analysis
    """
    try:
        data = request.get_json()

        # Validate input - new enhanced model requires different fields
        required_fields = ['income', 'emi', 'savings']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            if not isinstance(data[field], (int, float)) or data[field] < 0:
                return jsonify({'error': f'Invalid value for {field}. Must be non-negative number.'}), 400

        return jsonify(_run_prediction_analysis(data))

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/predict/from-budget', methods=['POST'])
@jwt_required()
def predict_from_budget():
    """Predict financial health directly from tracked budget + expenses for a month."""
    try:
        user_id = int(get_jwt_identity())
        payload = request.get_json() or {}
        month = payload.get('month', current_month_string())
        summary = build_budget_summary(user_id, month)

        if summary['expense_count'] == 0 and summary['monthly_income'] <= 0:
            return jsonify({'error': 'No budget or expenses found for this month'}), 404

        analysis_input = build_analysis_payload_from_summary(summary)

        # Ensure mandatory fields are present for prediction model.
        for key in ['income', 'emi', 'savings']:
            analysis_input.setdefault(key, 0)

        response = _run_prediction_analysis(analysis_input)
        response['source'] = 'budget_tracker'
        response['month'] = summary['month']
        response['analysis_input'] = analysis_input
        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/whatif', methods=['POST'])
def what_if_simulation():
    """
    What-if simulation endpoint
    Allows users to test different financial scenarios
    """
    try:
        data = request.get_json()

        # Current scenario
        current_data = data.get('current', {})

        # Modified scenario
        modified_data = data.get('modified', {})

        # Helper function to calculate expenses
        def get_expenses(scenario_data):
            expenses = scenario_data.get('expenses', 0)
            if expenses == 0 and any(k in scenario_data for k in ['rent', 'food', 'travel', 'shopping']):
                expenses = (scenario_data.get('rent', 0) + scenario_data.get('food', 0) + 
                           scenario_data.get('travel', 0) + scenario_data.get('shopping', 0))
            return expenses

        # Predict current score
        current_expenses = get_expenses(current_data)
        current_features = pd.DataFrame([[
            current_data.get('income', 0),
            current_expenses,
            current_data.get('savings', 0),
            current_data.get('emi', 0),
            current_data.get('age', 30),
            int(current_data.get('has_loan', False)),
            current_data.get('loan_amount', 0),
            current_data.get('interest_rate', 0)
        ]], columns=feature_names)

        current_score = float(model.predict(current_features)[0])
        current_score = max(0, min(100, round(current_score, 2)))

        # Predict modified score
        modified_expenses = get_expenses(modified_data)
        modified_features = pd.DataFrame([[
            modified_data.get('income', 0),
            modified_expenses,
            modified_data.get('savings', 0),
            modified_data.get('emi', 0),
            modified_data.get('age', 30),
            int(modified_data.get('has_loan', False)),
            modified_data.get('loan_amount', 0),
            modified_data.get('interest_rate', 0)
        ]], columns=feature_names)

        modified_score = float(model.predict(modified_features)[0])
        modified_score = max(0, min(100, round(modified_score, 2)))

        # Calculate impact
        score_change = modified_score - current_score

        response = {
            'success': True,
            'current_score': current_score,
            'modified_score': modified_score,
            'score_change': round(score_change, 2),
            'impact': 'positive' if score_change > 0 else 'negative' if score_change < 0 else 'neutral',
            'current_classification': classify_score(current_score),
            'modified_classification': classify_score(modified_score)
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get information about the ML model"""
    return jsonify({
        'model_type': model_data['model_type'],
        'features': feature_names,
        'performance': {
            'r2_score': model_metadata['r2_test'],
            'mae': model_metadata['mae_test'],
            'rmse': model_metadata['rmse_test']
        }
    })


# ==================== CHAT AGENT ENDPOINT ====================

def _build_chat_session_title(text):
    """Generate a concise session title from the first user message."""
    if not text:
        return 'New Chat'
    normalized = ' '.join(text.strip().split())
    return (normalized[:57] + '...') if len(normalized) > 60 else normalized


def _normalize_session_id(user_id, raw_session_id):
    """Ensure session IDs are user-scoped to avoid cross-user collisions."""
    base = (raw_session_id or '').strip()
    if not base:
        return f'user_{user_id}_default'
    user_prefix = f'user_{user_id}_'
    if base.startswith(user_prefix):
        return base
    return f'{user_prefix}{base}'


def _load_chat_history(user_id, session_id):
    """Load a user's chat history from persistent storage."""
    row = execute_query(
        'SELECT conversation_json FROM chat_sessions WHERE session_id = ? AND user_id = ?',
        (session_id, user_id),
        fetch_one=True
    )
    if not row:
        return []

    raw = row.get('conversation_json') if isinstance(row, dict) else row['conversation_json']
    if not raw:
        return []
    try:
        history = json.loads(raw)
        return history if isinstance(history, list) else []
    except Exception:
        return []


def _save_chat_history(user_id, session_id, user_message, updated_history):
    """Persist chat history, creating session row if missing."""
    now_iso = datetime.now().isoformat()
    existing = execute_query(
        'SELECT session_id, title FROM chat_sessions WHERE session_id = ? AND user_id = ?',
        (session_id, user_id),
        fetch_one=True
    )
    title = existing['title'] if existing and existing['title'] else _build_chat_session_title(user_message)
    # Do not persist internal synthetic context-injection messages as user-visible chat.
    cleaned_history = []
    for msg in (updated_history or []):
        if not isinstance(msg, dict):
            continue
        role = msg.get('role')
        if role not in ('user', 'assistant'):
            continue

        content = msg.get('content')
        if isinstance(content, list):
            internal_context = False
            for block in content:
                if isinstance(block, dict) and isinstance(block.get('text'), str):
                    if block['text'].startswith('Trusted user data context (from internal services, use this for grounding):'):
                        internal_context = True
                        break
            if internal_context:
                continue

        cleaned_history.append(msg)

    conversation_json = json.dumps(cleaned_history)

    if existing:
        execute_query(
            '''
            UPDATE chat_sessions
            SET conversation_json = ?, updated_at = ?, last_message_at = ?, title = COALESCE(title, ?)
            WHERE session_id = ? AND user_id = ?
            ''',
            (conversation_json, now_iso, now_iso, title, session_id, user_id),
            commit=True
        )
    else:
        execute_query(
            '''
            INSERT INTO chat_sessions (session_id, user_id, title, conversation_json, created_at, updated_at, last_message_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (session_id, user_id, title, conversation_json, now_iso, now_iso, now_iso),
            commit=True
        )

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat_endpoint():
    """
    Chat with the SmartFin AI agent.
    Body: { message: str, session_id?: str }
    Auth: Bearer JWT token required
    """
    try:
        user_id = int(get_jwt_identity())
        db = get_db()
        user = db.execute('SELECT id, username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 401

        user_email = user['username']

        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = _normalize_session_id(user_id, data.get('session_id', f'user_{user_id}_default'))

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        # Load persisted conversation history
        conversation_history = _load_chat_history(user_id, session_id)

        # Build app context for tool execution
        app_context = {
            'user_id': user_id,
            'user_email': user_email,
        }

        # Call the chat agent
        from chat_agent import chat as agent_chat
        assistant_text, updated_history, widgets = agent_chat(
            user_message, conversation_history, app_context
        )

        # Persist updated history
        _save_chat_history(user_id, session_id, user_message, updated_history)

        return jsonify({
            'success': True,
            'response': assistant_text,
            'widgets': widgets,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Chat agent error: {str(e)}'
        }), 500


@app.route('/api/chat/clear', methods=['POST'])
@jwt_required()
def clear_chat():
    """Clear chat history for a session."""
    try:
        user_id = int(get_jwt_identity())

        data = request.get_json() or {}
        session_id = _normalize_session_id(user_id, data.get('session_id', f'user_{user_id}_default'))

        execute_query(
            'DELETE FROM chat_sessions WHERE session_id = ? AND user_id = ?',
            (session_id, user_id),
            commit=True
        )

        return jsonify({'success': True, 'message': 'Chat history cleared'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/sessions', methods=['GET'])
@jwt_required()
def list_chat_sessions():
    """List saved chat sessions for the authenticated user."""
    try:
        user_id = int(get_jwt_identity())
        sessions = execute_query(
            '''
            SELECT session_id, title, created_at, updated_at, last_message_at
            FROM chat_sessions
            WHERE user_id = ?
            ORDER BY last_message_at DESC
            ''',
            (user_id,),
            fetch_all=True
        )
        return jsonify({
            'success': True,
            'sessions': rows_to_list(sessions),
            'count': len(sessions)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get a full saved chat history for a session."""
    try:
        user_id = int(get_jwt_identity())
        session_id = _normalize_session_id(user_id, request.args.get('session_id', f'user_{user_id}_default'))
        history = _load_chat_history(user_id, session_id)
        return jsonify({
            'success': True,
            'session_id': session_id,
            'history': history,
            'message_count': len(history)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/session/title', methods=['PUT'])
@jwt_required()
def rename_chat_session():
    """Rename a saved chat session title."""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        session_id = _normalize_session_id(user_id, data.get('session_id'))
        title = (data.get('title') or '').strip()

        if not title:
            return jsonify({'error': 'title is required'}), 400

        existing = execute_query(
            'SELECT session_id FROM chat_sessions WHERE session_id = ? AND user_id = ?',
            (session_id, user_id),
            fetch_one=True
        )
        if not existing:
            return jsonify({'error': 'session not found'}), 404

        execute_query(
            '''
            UPDATE chat_sessions
            SET title = ?, updated_at = ?
            WHERE session_id = ? AND user_id = ?
            ''',
            (title[:120], datetime.now().isoformat(), session_id, user_id),
            commit=True
        )

        return jsonify({'success': True, 'session_id': session_id, 'title': title[:120]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/session', methods=['DELETE'])
@jwt_required()
def delete_chat_session():
    """Delete a specific saved chat session."""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        session_id = _normalize_session_id(user_id, data.get('session_id'))

        execute_query(
            'DELETE FROM chat_sessions WHERE session_id = ? AND user_id = ?',
            (session_id, user_id),
            commit=True
        )

        return jsonify({'success': True, 'message': 'Chat session deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== INVESTMENT CALCULATORS ====================

@app.route('/api/sip-calculator', methods=['POST'])
def calculate_sip():
    """
    Calculate SIP (Systematic Investment Plan) returns
    
    Formula: FV = P × ((1 + r)^n - 1) / r) × (1 + r)
    Where:
    - P = Monthly investment amount
    - r = Monthly rate of return (annual rate / 12)
    - n = Total number of months
    """
    try:
        data = request.get_json()
        
        # Validate input
        monthly_investment = float(data.get('monthly_investment', 0))
        annual_return_rate = float(data.get('annual_return_rate', 0))
        time_period_years = float(data.get('time_period_years', 0))
        
        if monthly_investment <= 0:
            return jsonify({'error': 'Monthly investment must be greater than 0'}), 400
        
        if annual_return_rate < 0 or annual_return_rate > 100:
            return jsonify({'error': 'Annual return rate must be between 0 and 100'}), 400
        
        if time_period_years <= 0 or time_period_years > 50:
            return jsonify({'error': 'Time period must be between 0 and 50 years'}), 400
        
        # Calculate SIP
        monthly_rate = (annual_return_rate / 12) / 100
        total_months = int(time_period_years * 12)
        
        # Total invested amount
        total_invested = monthly_investment * total_months
        
        # Future value calculation
        if monthly_rate == 0:
            # If return rate is 0, future value = total invested
            future_value = total_invested
        else:
            # Standard SIP formula
            future_value = monthly_investment * (((1 + monthly_rate) ** total_months - 1) / monthly_rate) * (1 + monthly_rate)
        
        # Calculate returns
        estimated_returns = future_value - total_invested
        
        # Calculate year-wise breakdown
        yearly_breakdown = []
        for year in range(1, int(time_period_years) + 1):
            months = year * 12
            invested_till_year = monthly_investment * months
            
            if monthly_rate == 0:
                value_till_year = invested_till_year
            else:
                value_till_year = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
            
            returns_till_year = value_till_year - invested_till_year
            
            yearly_breakdown.append({
                'year': year,
                'invested': round(invested_till_year, 2),
                'value': round(value_till_year, 2),
                'returns': round(returns_till_year, 2)
            })
        
        response = {
            'success': True,
            'monthly_investment': round(monthly_investment, 2),
            'annual_return_rate': round(annual_return_rate, 2),
            'time_period_years': round(time_period_years, 2),
            'total_invested': round(total_invested, 2),
            'estimated_returns': round(estimated_returns, 2),
            'future_value': round(future_value, 2),
            'total_months': total_months,
            'yearly_breakdown': yearly_breakdown
        }
        
        return jsonify(response)
    
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500


@app.route('/api/lumpsum-calculator', methods=['POST'])
def calculate_lumpsum():
    """
    Calculate Lumpsum investment returns
    
    Formula: FV = P × (1 + r)^n
    Where:
    - P = Principal amount (lumpsum investment)
    - r = Annual rate of return
    - n = Time period in years
    """
    try:
        data = request.get_json()
        
        # Validate input
        principal_amount = float(data.get('principal_amount', 0))
        annual_return_rate = float(data.get('annual_return_rate', 0))
        time_period_years = float(data.get('time_period_years', 0))
        
        if principal_amount <= 0:
            return jsonify({'error': 'Principal amount must be greater than 0'}), 400
        
        if annual_return_rate < 0 or annual_return_rate > 100:
            return jsonify({'error': 'Annual return rate must be between 0 and 100'}), 400
        
        if time_period_years <= 0 or time_period_years > 50:
            return jsonify({'error': 'Time period must be between 0 and 50 years'}), 400
        
        # Calculate Lumpsum
        annual_rate = annual_return_rate / 100
        
        # Future value calculation
        if annual_rate == 0:
            future_value = principal_amount
        else:
            future_value = principal_amount * ((1 + annual_rate) ** time_period_years)
        
        # Calculate returns
        estimated_returns = future_value - principal_amount
        
        # Calculate year-wise breakdown
        yearly_breakdown = []
        for year in range(1, int(time_period_years) + 1):
            if annual_rate == 0:
                value_till_year = principal_amount
            else:
                value_till_year = principal_amount * ((1 + annual_rate) ** year)
            
            returns_till_year = value_till_year - principal_amount
            
            yearly_breakdown.append({
                'year': year,
                'invested': round(principal_amount, 2),
                'value': round(value_till_year, 2),
                'returns': round(returns_till_year, 2)
            })
        
        response = {
            'success': True,
            'principal_amount': round(principal_amount, 2),
            'annual_return_rate': round(annual_return_rate, 2),
            'time_period_years': round(time_period_years, 2),
            'total_invested': round(principal_amount, 2),
            'estimated_returns': round(estimated_returns, 2),
            'future_value': round(future_value, 2),
            'yearly_breakdown': yearly_breakdown
        }
        
        return jsonify(response)
    
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Calculation error: {str(e)}'}), 500


# ==================== TWILIO OTP ENDPOINTS ====================

from twilio_service import twilio_verify

# ==================== LOAN MANAGEMENT ENDPOINTS ====================

from loan_history_service import LoanHistoryService, ValidationError as LoanValidationError
from loan_metrics_engine import LoanMetricsEngine
from loan_data_serializer import LoanDataSerializer, ParseError

# Initialize loan services
loan_service = LoanHistoryService(DB_PATH)
loan_metrics = LoanMetricsEngine(DB_PATH)
loan_serializer = LoanDataSerializer()


@app.route('/api/loans', methods=['POST'])
@jwt_required()
def create_loan():
    """
    Create a new loan record
    Requires: JWT authentication
    Body: loan_type, loan_amount, loan_tenure, monthly_emi, interest_rate, 
          loan_start_date, loan_maturity_date
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Log request
        logger.info(f"Create loan request from user {user_id}")
        
        # Validate request body exists
        if not data:
            logger.warning(f"Empty request body from user {user_id}")
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide loan data in JSON format'
            }), 400
        
        # Validate and create loan
        loan = loan_service.createLoan(user_id, data)
        
        logger.info(f"Loan created successfully: {loan['loan_id']} for user {user_id}")
        return jsonify({
            'message': 'Loan created successfully',
            'loan': loan
        }), 201
        
    except LoanValidationError as e:
        logger.warning(f"Loan validation failed for user {user_id}: {e.message}")
        return jsonify({
            'error': 'Validation failed',
            'field': e.field,
            'message': e.message,
            'code': e.code
        }), 400
    except sqlite3.Error as e:
        logger.error(f"Database error creating loan for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to create loan. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error creating loan for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/api/loans/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_loans(user_id):
    """
    Get all loans for a specific user
    Requires: JWT authentication + ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check ownership - users can only access their own loans
        if current_user_id != user_id:
            logger.warning(f"User {current_user_id} attempted to access loans for user {user_id}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to access this user\'s loans'
            }), 403
        
        # Get loans
        loans = loan_service.getLoansByUser(user_id)
        
        logger.info(f"Retrieved {len(loans)} loans for user {user_id}")
        return jsonify({
            'loans': loans,
            'count': len(loans)
        }), 200
        
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving loans for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to retrieve loans. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving loans for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/api/loans/<loan_id>', methods=['GET'])
@jwt_required()
def get_loan(loan_id):
    """
    Get specific loan details with payment history
    Requires: JWT authentication + ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get loan
        loan = loan_service.getLoan(loan_id)
        
        if loan is None:
            logger.warning(f"Loan not found: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404
        
        # Check ownership
        if loan['user_id'] != current_user_id:
            logger.warning(f"User {current_user_id} attempted to access loan {loan_id} owned by user {loan['user_id']}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to access this loan'
            }), 403
        
        # Get payment history
        payments = loan_service.getPaymentHistory(loan_id)
        
        # Add payments to loan data
        loan['payments'] = payments
        
        logger.info(f"Retrieved loan {loan_id} for user {current_user_id}")
        return jsonify({
            'loan': loan
        }), 200
        
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to retrieve loan. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/api/loans/<loan_id>', methods=['PUT'])
@jwt_required()
def update_loan(loan_id):
    """
    Update loan information
    Requires: JWT authentication + ownership check
    Body: Fields to update (loan_type, loan_amount, etc.)
    """
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate request body exists
        if not data:
            logger.warning(f"Empty request body for loan update: {loan_id}")
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide fields to update in JSON format'
            }), 400
        
        # Update loan (includes ownership check)
        loan = loan_service.updateLoan(loan_id, current_user_id, data)
        
        logger.info(f"Loan updated successfully: {loan_id} by user {current_user_id}")
        return jsonify({
            'message': 'Loan updated successfully',
            'loan': loan
        }), 200
        
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            logger.warning(f"Loan not found for update: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': error_msg
            }), 404
        elif 'does not own' in error_msg.lower():
            logger.warning(f"User {current_user_id} attempted to update loan {loan_id} without ownership")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to update this loan'
            }), 403
        elif 'deleted' in error_msg.lower() or 'default' in error_msg.lower():
            logger.warning(f"Attempted to update deleted/defaulted loan: {loan_id}")
            return jsonify({
                'error': 'Bad request',
                'message': error_msg
            }), 400
        return jsonify({
            'error': 'Bad request',
            'message': error_msg
        }), 400
    except LoanValidationError as e:
        logger.warning(f"Loan update validation failed for {loan_id}: {e.message}")
        return jsonify({
            'error': 'Validation failed',
            'field': e.field,
            'message': e.message,
            'code': e.code
        }), 400
    except sqlite3.Error as e:
        logger.error(f"Database error updating loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to update loan. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error updating loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/api/loans/<loan_id>', methods=['DELETE'])
@jwt_required()
def delete_loan(loan_id):
    """
    Soft delete a loan
    Requires: JWT authentication + ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Delete loan (includes ownership check)
        success = loan_service.deleteLoan(loan_id, current_user_id)
        
        if success:
            logger.info(f"Loan deleted successfully: {loan_id} by user {current_user_id}")
            return jsonify({
                'message': 'Loan deleted successfully',
                'success': True
            }), 200
        else:
            logger.warning(f"Loan not found for deletion: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404
        
    except ValueError as e:
        error_msg = str(e)
        if 'does not own' in error_msg.lower():
            logger.warning(f"User {current_user_id} attempted to delete loan {loan_id} without ownership")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to delete this loan'
            }), 403
        return jsonify({
            'error': 'Bad request',
            'message': error_msg
        }), 400
    except sqlite3.Error as e:
        logger.error(f"Database error deleting loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to delete loan. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error deleting loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/api/loans/<loan_id>/payments', methods=['POST'])
@jwt_required()
def record_payment(loan_id):
    """
    Record a loan payment
    Requires: JWT authentication + loan ownership check
    Body: payment_date, payment_amount
    """
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        logger.info(f"Recording payment - loan_id: {loan_id}, data: {data}")
        
        # Validate request body exists
        if not data:
            logger.warning(f"Empty request body for payment recording: {loan_id}")
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide payment data in JSON format'
            }), 400
        
        # Check loan exists and user owns it
        loan = loan_service.getLoan(loan_id)
        if loan is None:
            logger.warning(f"Loan not found for payment: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404
        
        if loan['user_id'] != current_user_id:
            logger.warning(f"User {current_user_id} attempted to record payment for loan {loan_id} owned by user {loan['user_id']}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to record payment for this loan'
            }), 403
        
        # Record payment
        payment = loan_service.recordPayment(loan_id, data)
        
        logger.info(f"Payment recorded successfully: {payment['payment_id']} for loan {loan_id}")
        return jsonify({
            'message': 'Payment recorded successfully',
            'payment': payment
        }), 201
        
    except LoanValidationError as e:
        logger.warning(f"Payment validation failed for loan {loan_id}: {e.message}")
        return jsonify({
            'error': 'Validation failed',
            'field': e.field,
            'message': e.message,
            'code': e.code
        }), 400
    except ValueError as e:
        logger.error(f"Value error recording payment for loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Not found',
            'message': str(e)
        }), 404
    except sqlite3.Error as e:
        logger.error(f"Database error recording payment for loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to record payment. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error recording payment for loan {loan_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/api/loans/<loan_id>/payments', methods=['GET'])
@jwt_required()
def get_payment_history(loan_id):
    """
    Get payment history for a loan
    Requires: JWT authentication + loan ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check loan exists and user owns it
        loan = loan_service.getLoan(loan_id)
        if loan is None:
            logger.warning(f"Loan not found for payment history: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404
        
        if loan['user_id'] != current_user_id:
            logger.warning(f"User {current_user_id} attempted to access payment history for loan {loan_id} owned by user {loan['user_id']}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to access payment history for this loan'
            }), 403
        
        # Get payment history
        payments = loan_service.getPaymentHistory(loan_id)
        
        logger.info(f"Retrieved {len(payments)} payments for loan {loan_id}")
        return jsonify({
            'payments': payments,
            'count': len(payments)
        }), 200
        
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving payment history for loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to retrieve payment history. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving payment history for loan {loan_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/api/loans/<loan_id>/payments/<payment_id>', methods=['DELETE'])
@jwt_required()
def delete_payment(loan_id, payment_id):
    """
    Delete a payment record
    Requires: JWT authentication + loan ownership check
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check loan exists and user owns it
        loan = loan_service.getLoan(loan_id)
        if loan is None:
            logger.warning(f"Loan not found for payment deletion: {loan_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Loan not found'
            }), 404
        
        if loan['user_id'] != current_user_id:
            logger.warning(f"User {current_user_id} attempted to delete payment for loan {loan_id} owned by user {loan['user_id']}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to delete payment for this loan'
            }), 403
        
        # Delete the payment
        deleted = loan_service.deletePayment(payment_id, loan_id)
        
        if not deleted:
            logger.warning(f"Payment not found for deletion: {payment_id}")
            return jsonify({
                'error': 'Not found',
                'message': 'Payment not found'
            }), 404
        
        logger.info(f"Payment deleted successfully: {payment_id} for loan {loan_id}")
        return jsonify({
            'message': 'Payment deleted successfully',
            'payment_id': payment_id
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error deleting payment {payment_id}: {str(e)}")
        return jsonify({
            'error': 'Validation error',
            'message': str(e)
        }), 400
    except sqlite3.Error as e:
        logger.error(f"Database error deleting payment {payment_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to delete payment. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error deleting payment {payment_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/api/loans/metrics/<int:user_id>', methods=['GET'])
@jwt_required()
def get_loan_metrics(user_id):
    """
    Get calculated loan metrics for a user
    Uses cached metrics if available and recent (within 5 minutes)
    Requires: JWT authentication + ownership check
    Returns: loan_diversity_score, payment_history_score, loan_maturity_score,
             payment_statistics, loan_statistics
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Check ownership - users can only access their own metrics
        if current_user_id != user_id:
            logger.warning(f"User {current_user_id} attempted to access metrics for user {user_id}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Not authorized to access this user\'s metrics'
            }), 403
        
        # Check if cached metrics exist and are recent (within 5 minutes)
        db = get_db()
        cur = db.cursor()
        
        cur.execute('''
            SELECT loan_diversity_score, payment_history_score, loan_maturity_score,
                   payment_statistics, loan_statistics, calculated_at
            FROM loan_metrics
            WHERE user_id = ?
        ''', (user_id,))
        
        cached_row = cur.fetchone()
        
        if cached_row:
            cached_data = row_to_dict(cached_row)
            calculated_at = datetime.fromisoformat(cached_data['calculated_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            # If cache is less than 5 minutes old, use it
            if (now - calculated_at).total_seconds() < 300:
                logger.info(f"Using cached metrics for user {user_id}")
                
                # Parse JSON fields
                payment_stats = json.loads(cached_data['payment_statistics']) if cached_data['payment_statistics'] else {}
                loan_stats = json.loads(cached_data['loan_statistics']) if cached_data['loan_statistics'] else {}
                
                metrics = {
                    'loan_diversity_score': cached_data['loan_diversity_score'],
                    'payment_history_score': cached_data['payment_history_score'],
                    'loan_maturity_score': cached_data['loan_maturity_score'],
                    'payment_statistics': payment_stats,
                    'loan_statistics': loan_stats,
                    'calculated_at': cached_data['calculated_at'],
                    'cached': True
                }
                
                return jsonify({
                    'metrics': metrics
                }), 200
        
        # Cache is stale or doesn't exist, recalculate
        logger.info(f"Recalculating metrics for user {user_id}")
        
        loan_diversity_score = loan_metrics.calculateLoanDiversityScore(user_id)
        payment_history_score = loan_metrics.calculatePaymentHistoryScore(user_id)
        loan_maturity_score = loan_metrics.calculateLoanMaturityScore(user_id)
        
        # Get statistics
        payment_statistics = loan_metrics.getPaymentStatistics(user_id)
        loan_statistics = loan_metrics.getLoanStatistics(user_id)
        
        # Store in cache
        now = datetime.now(timezone.utc).isoformat()
        payment_stats_json = json.dumps(payment_statistics)
        loan_stats_json = json.dumps(loan_statistics)
        
        try:
            cur.execute('''
                INSERT OR REPLACE INTO loan_metrics
                (user_id, loan_diversity_score, payment_history_score, loan_maturity_score,
                 payment_statistics, loan_statistics, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                loan_diversity_score,
                payment_history_score,
                loan_maturity_score,
                payment_stats_json,
                loan_stats_json,
                now
            ))
            db.commit()
            logger.info(f"Cached metrics for user {user_id}")
        except sqlite3.Error as e:
            logger.warning(f"Failed to cache metrics for user {user_id}: {str(e)}")
            # Continue anyway, just don't cache
        
        metrics = {
            'loan_diversity_score': loan_diversity_score,
            'payment_history_score': payment_history_score,
            'loan_maturity_score': loan_maturity_score,
            'payment_statistics': payment_statistics,
            'loan_statistics': loan_statistics,
            'calculated_at': now,
            'cached': False
        }
        
        logger.info(f"Retrieved loan metrics for user {user_id}")
        return jsonify({
            'metrics': metrics
        }), 200
        
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving metrics for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Failed to retrieve loan metrics. Please try again later.'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error retrieving metrics for user {user_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


# ==================== REGISTER BLUEPRINTS ====================
app.register_blueprint(retirement_bp)
app.register_blueprint(portfolio_bp)
app.register_blueprint(nudge_bp)


# ==================== RUN SERVER ====================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("SmartFin Backend Server Starting...")
    print("="*60)
    print(f"Model: {model_data['model_type']}")
    print(f"Accuracy: {model_metadata['r2_test']:.2%}")
    print("="*60 + "\n")

    # Configure all loggers to output to console
    import logging as werkzeug_logging
    
    # Set root logger
    root_logger = werkzeug_logging.getLogger()
    root_logger.setLevel(werkzeug_logging.DEBUG)
    
    # Set Flask logger
    flask_logger = werkzeug_logging.getLogger('flask')
    flask_logger.setLevel(werkzeug_logging.DEBUG)
    
    # Set Werkzeug logger
    werkzeug_log = werkzeug_logging.getLogger('werkzeug')
    werkzeug_log.setLevel(werkzeug_logging.DEBUG)
    
    # Set our app logger
    app_logger = werkzeug_logging.getLogger(__name__)
    app_logger.setLevel(werkzeug_logging.DEBUG)
    
    logger.info("Starting Flask app with debug logging enabled")
    
    # Use Waitress WSGI server (more reliable than Flask dev server for HTTP)
    try:
        from waitress import serve
        logger.info("Starting with Waitress WSGI server on port 5000...")
        serve(app, host='0.0.0.0', port=5000, threads=4)
    except ImportError:
        logger.warning("Waitress not installed, falling back to Flask dev server")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
