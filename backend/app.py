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
from datetime import datetime, timedelta
import os
import sqlite3
import json
import uuid

# Load environment variables
load_dotenv()

# Import validation schemas
from validation_schemas import (
    profile_create_schema,
    profile_update_schema,
    goal_create_schema,
    goal_update_schema,
    validate_request_data
)

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'smartfin-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# File upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'profile_pictures')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'webp'}

jwt = JWTManager(app)

CORS(app, origins=["https://saumye0106.github.io", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"])  # Enable CORS for GitHub Pages and local dev

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

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
    
    # Create indexes for better query performance
    cur.execute('CREATE INDEX IF NOT EXISTS idx_users_profile_user_id ON users_profile(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_financial_goals_user_id ON financial_goals(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_financial_goals_priority ON financial_goals(priority)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_financial_goals_status ON financial_goals(status)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_code ON password_reset_tokens(reset_code)')
    
    db.commit()
    db.close()

# Initialize database
init_db()

# ==================== DATABASE HELPER FUNCTIONS ====================

def execute_query(query, params=(), fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a database query with proper error handling
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit transaction
    
    Returns:
        Query result or None
    """
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(query, params)
        if commit:
            db.commit()
            return cur.lastrowid
        if fetch_one:
            return cur.fetchone()
        if fetch_all:
            return cur.fetchall()
        return None
    except sqlite3.Error as e:
        if commit:
            db.rollback()
        raise e


def row_to_dict(row):
    """Convert sqlite3.Row to dictionary"""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dictionaries"""
    return [dict(row) for row in rows]

# ==================== LOAD ML MODEL ====================
print("Loading ML model...")
# Get the absolute path to the ml directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(BASE_DIR, 'ml')

model = joblib.load(os.path.join(ML_DIR, 'financial_health_model.pkl'))
feature_names = joblib.load(os.path.join(ML_DIR, 'feature_names.pkl'))
model_metadata = joblib.load(os.path.join(ML_DIR, 'model_metadata.pkl'))
print(f"Model loaded: {model_metadata['model_type']}")
print(f"Model R2 Score: {model_metadata['test_r2']:.4f}")

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
        'model': model_metadata['model_type'],
        'model_accuracy': f"{model_metadata['test_r2']:.2%}"
    })


@app.route('/api/predict', methods=['POST'])
def predict_score():
    """
    Main prediction endpoint
    Accepts financial data and returns comprehensive analysis
    """
    try:
        data = request.get_json()

        # Validate input
        required_fields = ['income', 'rent', 'food', 'travel', 'shopping', 'emi', 'savings']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            if not isinstance(data[field], (int, float)) or data[field] < 0:
                return jsonify({'error': f'Invalid value for {field}. Must be non-negative number.'}), 400

        # Prepare features for prediction
        features = pd.DataFrame([[
            data['income'],
            data['rent'],
            data['food'],
            data['travel'],
            data['shopping'],
            data['emi'],
            data['savings']
        ]], columns=feature_names)

        # Predict score
        predicted_score = float(model.predict(features)[0])
        predicted_score = max(0, min(100, round(predicted_score, 2)))  # Clamp between 0-100

        # Get classification
        classification = classify_score(predicted_score)

        # Analyze spending patterns
        patterns = analyze_spending_patterns(data)

        # Generate guidance
        guidance = generate_guidance(data, predicted_score, patterns)

        # Detect anomalies
        anomalies = detect_anomalies(data, patterns)

        # Suggest investments
        investments = suggest_investments(predicted_score, data, patterns)

        # Build response
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'score': predicted_score,
            'classification': classification,
            'patterns': patterns,
            'guidance': guidance,
            'anomalies': anomalies,
            'investments': investments,
            'model_info': {
                'model_type': model_metadata['model_type'],
                'accuracy': f"{model_metadata['test_r2']:.2%}",
                'average_error': f"±{model_metadata['mae']:.1f} points"
            }
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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

        # Predict current score
        current_features = pd.DataFrame([[
            current_data['income'],
            current_data['rent'],
            current_data['food'],
            current_data['travel'],
            current_data['shopping'],
            current_data['emi'],
            current_data['savings']
        ]], columns=feature_names)

        current_score = float(model.predict(current_features)[0])
        current_score = max(0, min(100, round(current_score, 2)))

        # Predict modified score
        modified_features = pd.DataFrame([[
            modified_data['income'],
            modified_data['rent'],
            modified_data['food'],
            modified_data['travel'],
            modified_data['shopping'],
            modified_data['emi'],
            modified_data['savings']
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
        'model_type': model_metadata['model_type'],
        'features': feature_names,
        'performance': {
            'r2_score': model_metadata['test_r2'],
            'mae': model_metadata['mae'],
            'rmse': model_metadata['rmse']
        },
        'training_samples': model_metadata['n_samples']
    })


# ==================== AUTH ENDPOINTS ====================

@app.route('/register', methods=['POST'])
def register():
    """Register a new user and send email verification"""
    try:
        data = request.get_json()
        print(f"Register request data: {data}")  # Debug logging
        username = data.get('email')  # Frontend sends 'email' field
        password = data.get('password')

        if not username or not password:
            print(f"Missing fields - username: {username}, password: {password}")  # Debug
            return jsonify({'error': 'Username and password required'}), 400

        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, username):
            return jsonify({'error': 'Invalid email address format'}), 400

        if len(password) < 6:
            print(f"Password too short: {len(password)} chars")  # Debug
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        db = get_db()
        cur = db.cursor()

        # Check if user exists
        cur.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cur.fetchone():
            return jsonify({'error': 'User already exists'}), 409

        # Create user (email_verified defaults to 0)
        password_hash = generate_password_hash(password)
        cur.execute(
            'INSERT INTO users (username, password_hash, created_at, email_verified) VALUES (?, ?, ?, 0)',
            (username, password_hash, datetime.utcnow().isoformat())
        )
        db.commit()
        
        # Get the new user's ID
        user_id = cur.lastrowid

        # Send email verification OTP
        from twilio_service import twilio_verify
        verification_result = twilio_verify.send_otp(username, 'email')
        
        if verification_result['success']:
            # Store verification expiry
            expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            cur.execute(
                'UPDATE users SET email_verification_expires = ? WHERE id = ?',
                (expires_at, user_id)
            )
            db.commit()

        # Create tokens (user can login but will be prompted to verify email)
        access_token = create_access_token(identity=str(user_id))
        refresh_token = create_refresh_token(identity=str(user_id))

        return jsonify({
            'message': 'User registered successfully. Please verify your email.',
            'token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id,
                'username': username,
                'email_verified': False
            },
            'verification_sent': verification_result['success']
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    """Login user and return JWT tokens"""
    try:
        data = request.get_json()
        username = data.get('email')  # Frontend sends 'email' field
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, username):
            return jsonify({'error': 'Invalid email address format'}), 400

        db = get_db()
        cur = db.cursor()

        # Get user
        cur.execute('SELECT id, username, password_hash, email_verified FROM users WHERE username = ?', (username,))
        user = cur.fetchone()

        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Create tokens
        access_token = create_access_token(identity=str(user['id']))
        refresh_token = create_refresh_token(identity=str(user['id']))

        return jsonify({
            'token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email_verified': bool(user['email_verified'])
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """Protected endpoint - requires valid JWT"""
    current_user_id = get_jwt_identity()
    return jsonify({'message': 'Access granted', 'user_id': current_user_id}), 200


@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify({'token': new_access_token}), 200


@app.route('/update-phone', methods=['POST'])
@jwt_required()
def update_phone():
    """
    Update user's phone number with OTP verification
    Step 1: Send OTP to new phone number
    Step 2: Verify OTP and update phone in database
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        phone = data.get('phone')
        otp_code = data.get('otp_code')
        
        if not phone:
            return jsonify({'error': 'Phone number is required'}), 400
        
        # If OTP code provided, verify and update phone
        if otp_code:
            # Verify OTP
            verify_result = twilio_verify.verify_otp(phone, otp_code)
            if not verify_result['success']:
                return jsonify({'error': 'Invalid or expired OTP'}), 400
            
            # Update phone in database
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'UPDATE users SET phone = ? WHERE id = ?',
                (phone, current_user_id)
            )
            db.commit()
            
            return jsonify({
                'message': 'Phone number updated successfully',
                'phone': phone
            }), 200
        
        # Otherwise, send OTP to new phone number
        else:
            send_result = twilio_verify.send_otp(phone, 'sms')
            if send_result['success']:
                return jsonify({
                    'message': 'OTP sent to your phone',
                    'status': send_result['status']
                }), 200
            else:
                return jsonify({'error': send_result.get('error', 'Failed to send OTP')}), 400
    
    except Exception as e:
        return jsonify({'error': f'Failed to update phone: {str(e)}'}), 500


@app.route('/get-phone', methods=['GET'])
@jwt_required()
def get_phone():
    """Get user's current phone number"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        cur = db.cursor()
        
        cur.execute('SELECT phone FROM users WHERE id = ?', (current_user_id,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'phone': user['phone']
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to get phone: {str(e)}'}), 500


# ==================== EMAIL VERIFICATION ENDPOINTS ====================

@app.route('/send-email-verification', methods=['POST'])
def send_email_verification():
    """
    Send email verification OTP to user's email
    Can be called during registration or to resend verification
    """
    try:
        data = request.get_json()
        email = data.get('email')
        user_id = data.get('user_id')  # Optional: for resend after registration
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        db = get_db()
        cur = db.cursor()
        
        # If user_id provided, verify it matches the email
        if user_id:
            cur.execute('SELECT username, email_verified FROM users WHERE id = ?', (user_id,))
            user = cur.fetchone()
            if not user or user['username'] != email:
                return jsonify({'error': 'Invalid user'}), 400
            if user['email_verified']:
                return jsonify({'error': 'Email already verified'}), 400
        else:
            # Check if email exists
            cur.execute('SELECT id, email_verified FROM users WHERE username = ?', (email,))
            user = cur.fetchone()
            if not user:
                return jsonify({'error': 'Email not found'}), 404
            if user['email_verified']:
                return jsonify({'error': 'Email already verified'}), 400
            user_id = user['id']
        
        # Send OTP via Twilio Verify (email channel)
        from twilio_service import twilio_verify
        result = twilio_verify.send_otp(email, 'email')
        
        if result['success']:
            # Store verification attempt timestamp
            expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            cur.execute(
                'UPDATE users SET email_verification_expires = ? WHERE id = ?',
                (expires_at, user_id)
            )
            db.commit()
            
            return jsonify({
                'message': 'Verification code sent to your email',
                'status': result['status'],
                'user_id': user_id
            }), 200
        else:
            return jsonify({'error': result.get('error', 'Failed to send verification code')}), 400
    
    except Exception as e:
        return jsonify({'error': f'Failed to send verification: {str(e)}'}), 500


@app.route('/verify-email', methods=['POST'])
def verify_email():
    """
    Verify email using OTP code
    """
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        user_id = data.get('user_id')  # Optional
        
        if not email or not code:
            return jsonify({'error': 'Email and verification code are required'}), 400
        
        db = get_db()
        cur = db.cursor()
        
        # Get user
        if user_id:
            cur.execute('SELECT id, username, email_verified, email_verification_expires FROM users WHERE id = ?', (user_id,))
        else:
            cur.execute('SELECT id, username, email_verified, email_verification_expires FROM users WHERE username = ?', (email,))
        
        user = cur.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['email_verified']:
            return jsonify({'message': 'Email already verified', 'already_verified': True}), 200
        
        # Check if verification expired
        if user['email_verification_expires']:
            expires_at = datetime.fromisoformat(user['email_verification_expires'])
            if datetime.utcnow() > expires_at:
                return jsonify({'error': 'Verification code expired. Please request a new one.'}), 400
        
        # Verify OTP via Twilio
        from twilio_service import twilio_verify
        result = twilio_verify.verify_otp(email, code)
        
        if result['success']:
            # Mark email as verified
            cur.execute(
                'UPDATE users SET email_verified = 1, email_verification_token = NULL, email_verification_expires = NULL WHERE id = ?',
                (user['id'],)
            )
            db.commit()
            
            return jsonify({
                'message': 'Email verified successfully',
                'verified': True
            }), 200
        else:
            return jsonify({'error': result.get('error', 'Invalid or expired verification code')}), 400
    
    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500


@app.route('/check-email-verification', methods=['GET'])
@jwt_required()
def check_email_verification():
    """Check if current user's email is verified"""
    try:
        current_user_id = get_jwt_identity()
        db = get_db()
        cur = db.cursor()
        
        cur.execute('SELECT email_verified, username FROM users WHERE id = ?', (current_user_id,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'email': user['username'],
            'verified': bool(user['email_verified'])
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to check verification: {str(e)}'}), 500


# ==================== PASSWORD RESET ENDPOINTS ====================

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Generate a password reset code for the user
    In a real app, this would send an email. For this educational project,
    we'll return the code directly.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        db = get_db()
        cur = db.cursor()
        
        # Check if user exists
        cur.execute('SELECT id FROM users WHERE username = ?', (email,))
        user = cur.fetchone()
        
        if not user:
            # For security, don't reveal if email exists
            # But return success anyway
            return jsonify({
                'message': 'If this email exists, a reset code has been generated',
                'reset_code': None  # Don't send code if user doesn't exist
            }), 200
        
        user_id = user['id']
        
        # Generate a 6-digit reset code
        import random
        reset_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Set expiration to 15 minutes from now
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(minutes=15)
        
        # Invalidate any existing unused tokens for this user
        cur.execute(
            'UPDATE password_reset_tokens SET used = 1 WHERE user_id = ? AND used = 0',
            (user_id,)
        )
        
        # Insert new reset token
        cur.execute(
            '''INSERT INTO password_reset_tokens 
               (user_id, reset_code, created_at, expires_at, used) 
               VALUES (?, ?, ?, ?, 0)''',
            (user_id, reset_code, created_at.isoformat(), expires_at.isoformat())
        )
        
        db.commit()
        
        # In a real app, send email here
        # For educational purposes, return the code
        return jsonify({
            'message': 'Reset code generated successfully',
            'reset_code': reset_code,  # Only for educational purposes!
            'expires_in_minutes': 15
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate reset code: {str(e)}'}), 500


@app.route('/verify-reset-code', methods=['POST'])
def verify_reset_code():
    """Verify if a reset code is valid"""
    try:
        data = request.get_json()
        email = data.get('email')
        reset_code = data.get('reset_code')
        
        if not email or not reset_code:
            return jsonify({'error': 'Email and reset code are required'}), 400
        
        db = get_db()
        cur = db.cursor()
        
        # Get user
        cur.execute('SELECT id FROM users WHERE username = ?', (email,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid reset code'}), 400
        
        user_id = user['id']
        
        # Check if code exists and is valid
        cur.execute(
            '''SELECT id, expires_at FROM password_reset_tokens 
               WHERE user_id = ? AND reset_code = ? AND used = 0''',
            (user_id, reset_code)
        )
        token = cur.fetchone()
        
        if not token:
            return jsonify({'error': 'Invalid or expired reset code'}), 400
        
        # Check if expired
        expires_at = datetime.fromisoformat(token['expires_at'])
        if datetime.utcnow() > expires_at:
            return jsonify({'error': 'Reset code has expired'}), 400
        
        return jsonify({
            'message': 'Reset code is valid',
            'valid': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500


@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using a valid reset code"""
    try:
        data = request.get_json()
        email = data.get('email')
        reset_code = data.get('reset_code')
        new_password = data.get('new_password')
        
        if not email or not reset_code or not new_password:
            return jsonify({'error': 'Email, reset code, and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        db = get_db()
        cur = db.cursor()
        
        # Get user
        cur.execute('SELECT id FROM users WHERE username = ?', (email,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid reset code'}), 400
        
        user_id = user['id']
        
        # Check if code exists and is valid
        cur.execute(
            '''SELECT id, expires_at FROM password_reset_tokens 
               WHERE user_id = ? AND reset_code = ? AND used = 0''',
            (user_id, reset_code)
        )
        token = cur.fetchone()
        
        if not token:
            return jsonify({'error': 'Invalid or expired reset code'}), 400
        
        # Check if expired
        expires_at = datetime.fromisoformat(token['expires_at'])
        if datetime.utcnow() > expires_at:
            return jsonify({'error': 'Reset code has expired'}), 400
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        cur.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (new_password_hash, user_id)
        )
        
        # Mark token as used
        cur.execute(
            'UPDATE password_reset_tokens SET used = 1 WHERE id = ?',
            (token['id'],)
        )
        
        db.commit()
        
        return jsonify({
            'message': 'Password reset successfully',
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Password reset failed: {str(e)}'}), 500


# ==================== PROFILE MANAGEMENT ENDPOINTS ====================

from profile_service import ProfileService
from goals_service import GoalsService

# Initialize services
profile_service = ProfileService(DB_PATH)
goals_service = GoalsService(DB_PATH)


@app.route('/api/profile/create', methods=['POST'])
@jwt_required()
def create_profile():
    """
    Create a new user profile
    Requires: JWT authentication
    Body: name, age, location, risk_tolerance (optional), notification_preferences (optional)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate request data
        validated_data, errors = validate_request_data(profile_create_schema, data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Check if profile already exists
        if profile_service.profile_exists(user_id):
            return jsonify({'error': 'Profile already exists for this user'}), 409
        
        # Create profile
        profile = profile_service.create_profile(user_id, validated_data)
        
        return jsonify({
            'message': 'Profile created successfully',
            'profile': profile
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get the authenticated user's profile
    Requires: JWT authentication
    """
    try:
        user_id = int(get_jwt_identity())
        
        # Get profile
        profile = profile_service.get_profile(user_id)
        
        if profile is None:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify({
            'profile': profile
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/profile/update', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update the authenticated user's profile
    Requires: JWT authentication
    Body: name, age, location, risk_tolerance, notification_preferences (all optional)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate request data
        validated_data, errors = validate_request_data(profile_update_schema, data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Update profile
        profile = profile_service.update_profile(user_id, validated_data)
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': profile
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# ==================== PROFILE PICTURE UPLOAD ENDPOINTS ====================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/api/profile/upload-picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    """
    Upload profile picture
    Requires: JWT authentication
    Body: multipart/form-data with 'file' field
    """
    try:
        user_id = int(get_jwt_identity())
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Allowed: JPEG, PNG, WebP'}), 400
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"user_{user_id}_{uuid.uuid4().hex}.{file_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Delete old profile picture if exists
        profile = profile_service.get_profile(user_id)
        if profile and profile.get('profile_picture_url'):
            old_filename = profile['profile_picture_url'].split('/')[-1]
            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
        
        # Save file
        file.save(filepath)
        
        # Generate URL for the file
        picture_url = f"/uploads/profile_pictures/{filename}"
        
        # Update profile with picture URL
        profile_service.update_profile(user_id, {'profile_picture_url': picture_url})
        
        return jsonify({
            'message': 'Profile picture uploaded successfully',
            'profile_picture_url': picture_url
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/profile/delete-picture', methods=['DELETE'])
@jwt_required()
def delete_profile_picture():
    """
    Delete profile picture
    Requires: JWT authentication
    """
    try:
        user_id = int(get_jwt_identity())
        
        # Get current profile
        profile = profile_service.get_profile(user_id)
        
        if not profile or not profile.get('profile_picture_url'):
            return jsonify({'error': 'No profile picture to delete'}), 404
        
        # Delete file from filesystem
        filename = profile['profile_picture_url'].split('/')[-1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Update profile to remove picture URL
        profile_service.update_profile(user_id, {'profile_picture_url': None})
        
        return jsonify({
            'message': 'Profile picture deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


@app.route('/uploads/profile_pictures/<filename>')
def serve_profile_picture(filename):
    """Serve profile picture files"""
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/profile/goals', methods=['POST'])
@jwt_required()
def create_goal():
    """
    Create a new financial goal
    Requires: JWT authentication
    Body: goal_type, target_amount, target_date, priority, description (optional)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate request data
        validated_data, errors = validate_request_data(goal_create_schema, data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Create goal
        goal = goals_service.create_goal(user_id, validated_data)
        
        return jsonify({
            'message': 'Goal created successfully',
            'goal': goal
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/profile/goals', methods=['GET'])
@jwt_required()
def get_goals():
    """
    Get all financial goals for the authenticated user
    Requires: JWT authentication
    Query params: status (optional filter)
    """
    try:
        user_id = int(get_jwt_identity())
        
        # Get optional status filter
        status = request.args.get('status')
        filters = {'status': status} if status else None
        
        # Get goals
        goals = goals_service.get_goals(user_id, filters)
        
        return jsonify({
            'goals': goals,
            'count': len(goals)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/profile/goals/<goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    """
    Update a financial goal
    Requires: JWT authentication + ownership
    Body: goal_type, target_amount, target_date, priority, status, description (all optional)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate request data
        validated_data, errors = validate_request_data(goal_update_schema, data)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Update goal (includes ownership check)
        goal = goals_service.update_goal(goal_id, user_id, validated_data)
        
        return jsonify({
            'message': 'Goal updated successfully',
            'goal': goal
        }), 200
        
    except ValueError as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return jsonify({'error': error_msg}), 404
        elif 'not authorized' in error_msg.lower() or 'does not belong' in error_msg.lower():
            return jsonify({'error': 'Not authorized to update this goal'}), 403
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/profile/goals/<goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    """
    Delete a financial goal
    Requires: JWT authentication + ownership
    """
    try:
        user_id = int(get_jwt_identity())
        
        # Delete goal (includes ownership check)
        success = goals_service.delete_goal(goal_id, user_id)
        
        if success:
            return jsonify({
                'message': 'Goal deleted successfully'
            }), 204
        else:
            return jsonify({'error': 'Goal not found'}), 404
        
    except ValueError as e:
        error_msg = str(e)
        if 'not authorized' in error_msg.lower() or 'does not belong' in error_msg.lower():
            return jsonify({'error': 'Not authorized to delete this goal'}), 403
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


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

@app.route('/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP via Twilio Verify
    Supports SMS, Email, and WhatsApp channels
    """
    try:
        data = request.get_json()
        to = data.get('to')  # Phone number (E.164 format: +1234567890) or email
        channel = data.get('channel', 'sms')  # 'sms', 'email', or 'whatsapp'
        
        if not to:
            return jsonify({'error': 'Recipient (phone/email) is required'}), 400
        
        if channel not in ['sms', 'email', 'whatsapp']:
            return jsonify({'error': 'Invalid channel. Use: sms, email, or whatsapp'}), 400
        
        # Send OTP via Twilio
        result = twilio_verify.send_otp(to, channel)
        
        if result['success']:
            return jsonify({
                'message': f'OTP sent successfully via {channel}',
                'status': result['status'],
                'to': result['to'],
                'channel': result['channel']
            }), 200
        else:
            return jsonify({
                'error': result.get('error', 'Failed to send OTP'),
                'code': result.get('code')
            }), 400
    
    except Exception as e:
        return jsonify({'error': f'Failed to send OTP: {str(e)}'}), 500


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP code via Twilio Verify
    """
    try:
        data = request.get_json()
        to = data.get('to')  # Same phone/email used in send-otp
        code = data.get('code')  # 6-digit OTP code
        
        if not to or not code:
            return jsonify({'error': 'Recipient and code are required'}), 400
        
        # Verify OTP via Twilio
        result = twilio_verify.verify_otp(to, code)
        
        if result['success']:
            return jsonify({
                'message': 'OTP verified successfully',
                'status': result['status'],
                'valid': result['valid']
            }), 200
        else:
            return jsonify({
                'error': result.get('error', 'Invalid or expired OTP'),
                'code': result.get('code')
            }), 400
    
    except Exception as e:
        return jsonify({'error': f'Failed to verify OTP: {str(e)}'}), 500


@app.route('/register-with-otp', methods=['POST'])
def register_with_otp():
    """
    Register a new user with OTP verification
    Step 1: Send OTP to phone/email
    Step 2: Verify OTP and create account
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')  # Optional: E.164 format
        otp_code = data.get('otp_code')  # Required if phone provided
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # If phone provided, verify OTP first
        if phone:
            if not otp_code:
                return jsonify({'error': 'OTP code required for phone verification'}), 400
            
            # Verify OTP
            verify_result = twilio_verify.verify_otp(phone, otp_code)
            if not verify_result['success']:
                return jsonify({'error': 'Invalid or expired OTP'}), 400
        
        # Proceed with registration
        db = get_db()
        cur = db.cursor()
        
        # Check if user exists
        cur.execute('SELECT id FROM users WHERE username = ?', (email,))
        if cur.fetchone():
            return jsonify({'error': 'User already exists'}), 400
        
        # Create user
        password_hash = generate_password_hash(password)
        cur.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (email, password_hash)
        )
        db.commit()
        
        user_id = cur.lastrowid
        
        # Generate tokens
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        
        return jsonify({
            'message': 'Registration successful',
            'token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id,
                'email': email,
                'phone_verified': bool(phone and otp_code)
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@app.route('/forgot-password-otp', methods=['POST'])
def forgot_password_otp():
    """
    SECURE Password reset with Twilio OTP
    Step 1: User provides email → System looks up registered phone → Sends OTP
    Step 2: User verifies OTP → Resets password
    """
    try:
        data = request.get_json()
        email = data.get('email')
        otp_code = data.get('otp_code')
        new_password = data.get('new_password')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        db = get_db()
        cur = db.cursor()
        
        # Get user and their registered phone
        cur.execute('SELECT id, phone FROM users WHERE username = ?', (email,))
        user = cur.fetchone()
        
        if not user:
            # For security, don't reveal if email exists
            return jsonify({'message': 'If this email exists and has a phone number, an OTP has been sent'}), 200
        
        phone = user['phone']
        
        if not phone:
            return jsonify({'error': 'No phone number registered for this account. Please contact support.'}), 400
        
        # If OTP code provided, verify and reset password
        if otp_code and new_password:
            # Verify OTP
            verify_result = twilio_verify.verify_otp(phone, otp_code)
            if not verify_result['success']:
                return jsonify({'error': 'Invalid or expired OTP'}), 400
            
            # Reset password
            password_hash = generate_password_hash(new_password)
            cur.execute(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (password_hash, user['id'])
            )
            db.commit()
            
            return jsonify({'message': 'Password reset successfully'}), 200
        
        # Otherwise, send OTP to user's registered phone
        else:
            send_result = twilio_verify.send_otp(phone, 'sms')
            if send_result['success']:
                # Mask phone number for security (show last 4 digits)
                masked_phone = phone[:-4] + '****' if len(phone) > 4 else '****'
                return jsonify({
                    'message': f'OTP sent to your registered phone ending in {phone[-4:]}',
                    'phone_hint': masked_phone,
                    'status': send_result['status']
                }), 200
            else:
                return jsonify({'error': 'Failed to send OTP. Please try again.'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Failed: {str(e)}'}), 500


# ==================== RUN SERVER ====================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("SmartFin Backend Server Starting...")
    print("="*60)
    print(f"Model: {model_metadata['model_type']}")
    print(f"Accuracy: {model_metadata['test_r2']:.2%}")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=5000)
