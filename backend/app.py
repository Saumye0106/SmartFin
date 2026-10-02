"""
SmartFin - Flask Backend
Main application file for financial health scoring and guidance
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from datetime import timedelta
import os
import sqlite3
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

# Import new ML core modules
from portfolio_optimizer.api import portfolio_bp
from nudge_engine.api import nudge_bp

# Import blueprints extracted from this file
from auth.api import auth_bp
from profile_management.api import profile_bp
from budget.api import budget_bp
from loans.api import loans_bp
from chat.api import chat_bp
from calculators.api import calculators_bp
from legacy_scorer.api import legacy_scorer_bp
from statement_import.api import statement_import_bp
from statement_import.migrations import create_tables as create_statement_import_tables
from legacy_scorer.model import model_data, model_metadata

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
    create_statement_import_tables(DB_PATH)

# Initialize database
init_db()

# ==================== REGISTER BLUEPRINTS ====================
app.register_blueprint(retirement_bp)
app.register_blueprint(portfolio_bp)
app.register_blueprint(nudge_bp)
app.register_blueprint(loans_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(calculators_bp)
app.register_blueprint(legacy_scorer_bp)
app.register_blueprint(statement_import_bp)


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
