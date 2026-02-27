// SmartFin Financial Health Platform - Architecture Diagram Generation Prompt
// Format: Mermaid/PlantUML compatible architecture description
// Last Updated: February 27, 2026

// SYSTEM OVERVIEW
// SmartFin is a full-stack financial health assessment platform with:
// - React 18 SPA frontend (Vite build tool, Tailwind CSS, Redux state management)
// - Flask backend API (Python, 20+ endpoints)
// - Gradient Boosting ML model (scikit-learn, 95.85% R² accuracy)
// - SQLite database (7 tables, real-time score calculation)
// - Twilio integration for OTP/SMS verification
// - Real-time financial scoring without database persistence

// ARCHITECTURE LAYERS

// Layer 1: PRESENTATION LAYER (Frontend - React)
class PresentationLayer {
    // Main Pages
    LandingPage: "Marketing/intro page"
    AuthPage: "Login/Register forms"
    MainDashboard: "Primary user dashboard"
    FinancialForm: "Score input form"
    ScoreDisplay: "Score visualization"
    WhatIfSimulator: "Scenario analysis"
    LoanManagementPage: "Loan operations"
    GoalsManager: "Financial goals"
    ProfilePage: "User profile"
    RiskAssessment: "Risk analysis"
    
    // Components
    Components: [
        "ScoreDisplay (50+ components total)",
        "LoanForm, PaymentForm, LoanListView",
        "GoalsManager, ProfileEditForm",
        "WhatIfSimulator, RiskAssessment",
        "SpendingChart, RatiosDashboard",
        "AlertsPanel, GuidancePanel"
    ]
    
    // Services
    APIClient: "axios-based HTTP client"
    StateManagement: "React hooks (useState) + localStorage for persistence"
    Routing: "React Router v6 for navigation"
    Styling: "Tailwind CSS + custom CSS"
    Charts: "Recharts + D3.js"
}

// STATE MANAGEMENT ARCHITECTURE (React Hooks)
class StateManagement {
    // App-Level State (AppContent component)
    app_state: {
        user: "Current logged-in user info (id, username, email)",
        authLoading: "Authentication check in progress",
        loading: "Financial analysis in progress",
        result: "Financial score result from /api/predict",
        currentData: "Submitted financial data",
        error: "Error messages from API calls"
    }
    
    // Persistence Layer
    localStorage: {
        jwt_token: "Authentication token for API requests",
        userId: "Current user ID",
        userEmail: "Current user email"
    }
    
    // Protected Routes
    ProtectedRoutes: {
        implementation: "React Router v6 with conditional rendering",
        check: "Verify JWT token exists in localStorage",
        redirect: "Redirect to login if not authenticated"
    }
    
    // Component-Level State
    component_state: {
        FinancialForm: "Form input values, validation errors",
        LoanForm: "Loan details, EMI calculations",
        PaymentForm: "Payment amount, date, status",
        GoalsManager: "Goal list, form state",
        ProfilePage: "Profile data, edit mode",
        WhatIfSimulator: "Scenario parameters, results"
    }
    
    // Note: Redux is listed in package.json but NOT actively used
    // All state management is handled via React hooks and localStorage
}

// Layer 2: API LAYER (Backend - Flask)
class APILayer {
    // Authentication Endpoints
    POST_register: "/api/register"
    POST_login: "/api/login"
    POST_refresh: "/api/refresh"
    POST_forgot_password: "/api/forgot-password"
    
    // Financial Scoring Endpoints
    POST_predict: "/api/predict (main scoring endpoint)"
    POST_whatif: "/api/whatif (scenario simulation)"
    GET_model_info: "/api/model-info"
    
    // Loan Management Endpoints
    POST_create_loan: "/api/loans"
    GET_user_loans: "/api/loans/<user_id>"
    POST_record_payment: "/api/loans/<id>/payment"
    GET_loan_metrics: "/api/loans/<id>/metrics"
    
    // Goals Endpoints
    POST_create_goal: "/api/goals"
    GET_goals: "/api/goals/<user_id>"
    POST_sip_calculator: "/api/calculate-sip"
    POST_lumpsum_calculator: "/api/calculate-lumpsum"
    
    // Profile Endpoints
    POST_create_profile: "/api/profile"
    GET_profile: "/api/profile/<user_id>"
    POST_upload_picture: "/api/upload-profile-picture"
    DELETE_picture: "/api/delete-profile-picture/<filename>"
    
    // OTP/Verification Endpoints
    POST_send_otp: "/api/send-otp"
    POST_verify_otp: "/api/verify-otp"
    POST_email_verification: "/api/send-email-verification"
    POST_verify_email: "/api/verify-email"
}

// Layer 3: BUSINESS LOGIC LAYER (Services)
class BusinessLogicLayer {
    // Core Services
    FinancialHealthScorer: {
        method: "calculateFinancialHealthScore()",
        type: "Rule-based 5-factor model",
        factors: ["Savings", "Debt", "Expense", "Balance", "LifeStage"]
    }
    
    LoanHistoryService: {
        methods: ["createLoan()", "recordPayment()", "calculateMetrics()"],
        features: ["EMI calculation", "Payment tracking", "Loan metrics"]
    }
    
    LoanMetricsEngine: {
        methods: ["calculateEMI()", "calculateMetrics()", "generateReport()"],
        features: ["Interest calculation", "Amortization", "Metrics"]
    }
    
    GoalsService: {
        methods: ["createGoal()", "calculateSIP()", "calculateLumpsum()"],
        features: ["Goal tracking", "Investment calculations"]
    }
    
    ProfileService: {
        methods: ["createProfile()", "updateProfile()", "uploadPicture()"],
        features: ["Profile management", "Picture upload"]
    }
    
    RiskAssessmentService: {
        methods: ["assessRisk()", "generateReport()"],
        features: ["Risk analysis", "Recommendations"]
    }
    
    TwilioService: {
        methods: ["sendOTP()", "sendSMS()"],
        features: ["OTP delivery", "SMS notifications"]
    }
}

// Layer 4: ML/PREDICTION LAYER
class MLPredictionLayer {
    // Model Configuration
    Algorithm: "GradientBoostingRegressor"
    Framework: "scikit-learn"
    
    // Model Parameters
    n_estimators: 200
    max_depth: 10
    learning_rate: 0.1
    
    // Training Data
    training_records: 52424
    train_test_split: "80/20"
    
    // Input Features (7)
    features: [
        "income",
        "expenses",
        "savings",
        "emi",
        "age",
        "has_loan",
        "loan_amount",
        "interest_rate"
    ]
    
    // Target Variable
    target: "financial_health_score (0-100)"
    
    // Performance Metrics
    r2_score: 0.9585
    mae: 1.03
    rmse: 1.34
    
    // Model Artifacts
    artifacts: [
        "financial_health_model.pkl",
        "feature_names.pkl",
        "model_metadata.pkl"
    ]
    
    // Prediction Pipeline
    prediction_flow: [
        "Load model from pkl file",
        "Prepare feature vector",
        "model.predict(features)",
        "Clamp score to 0-100",
        "Classify score",
        "Analyze patterns",
        "Generate guidance"
    ]
}

// Layer 5: DATA LAYER (Database)
class DataLayer {
    // Database Type
    type: "SQLite"
    file: "auth.db"
    
    // 7 Tables (Actual Implementation)
    users: {
        columns: ["id", "username", "password_hash", "phone", "email_verified", "email_verification_token", "created_at"]
        purpose: "User authentication and account management"
    }
    
    password_reset_tokens: {
        columns: ["id", "user_id", "reset_code", "created_at", "expires_at", "used"]
        purpose: "Password reset management"
    }
    
    users_profile: {
        columns: ["user_id", "name", "age", "location", "risk_tolerance", "profile_picture_url", "notification_preferences", "created_at", "updated_at"]
        purpose: "User profile information"
    }
    
    financial_goals: {
        columns: ["id", "user_id", "goal_type", "target_amount", "target_date", "priority", "status", "description", "created_at", "updated_at"]
        purpose: "Financial goals tracking"
    }
    
    loans: {
        columns: ["loan_id", "user_id", "loan_type", "loan_amount", "loan_tenure", "monthly_emi", "interest_rate", "loan_start_date", "loan_maturity_date", "default_status", "created_at", "updated_at", "deleted_at"]
        purpose: "Loan records and details"
    }
    
    loan_payments: {
        columns: ["payment_id", "loan_id", "payment_date", "payment_amount", "payment_status", "created_at", "updated_at"]
        purpose: "Payment history tracking"
    }
    
    loan_metrics: {
        columns: ["user_id", "loan_diversity_score", "payment_history_score", "loan_maturity_score", "payment_statistics", "loan_statistics", "calculated_at"]
        purpose: "Cached loan metrics for performance"
    }
    
    // IMPORTANT: Financial scores are NOT stored in database
    // They are calculated on-the-fly using ML model via /api/predict endpoint
    // This provides real-time scoring based on current data
}

// Layer 6: EXTERNAL INTEGRATIONS
class ExternalIntegrations {
    // SMS/OTP Service
    Twilio: {
        service: "SMS and OTP delivery",
        methods: ["send_otp()", "send_sms()"]
    }
    
    // File Storage
    FileSystem: {
        location: "backend/uploads/profile_pictures/",
        types: ["JPG", "PNG"]
    }
}

// DATA FLOW DIAGRAMS

// Flow 1: SCORE PREDICTION
flow_score_prediction {
    start: "User enters financial data"
    step1: "Frontend validates input"
    step2: "POST /api/predict"
    step3: "Backend validates input"
    step4: "Load ML model"
    step5: "Prepare feature vector"
    step6: "model.predict(features)"
    step7: "Clamp score 0-100"
    step8: "Classify score"
    step9: "Analyze spending patterns"
    step10: "Generate guidance"
    step11: "Detect anomalies"
    step12: "Suggest investments"
    step13: "Return JSON response"
    step14: "Frontend displays score"
    end: "User sees results"
}

// Flow 2: LOAN MANAGEMENT
flow_loan_management {
    start: "User creates loan"
    step1: "Frontend validates input"
    step2: "POST /api/loans"
    step3: "Backend validates input"
    step4: "Calculate EMI"
    step5: "Store in database"
    step6: "Return loan details"
    step7: "Frontend displays loan"
    step8: "User records payment"
    step9: "POST /api/loans/<id>/payment"
    step10: "Backend records payment"
    step11: "Update loan status"
    step12: "Calculate metrics"
    step13: "Return updated loan"
    step14: "Frontend displays metrics"
    end: "User sees loan progress"
}

// Flow 3: ML MODEL TRAINING
flow_model_training {
    start: "Load combined dataset (52,424 records)"
    step1: "Calculate 8-factor scores for each record"
    step2: "Prepare 7 input features (income, expenses, savings, emi, age, has_loan, loan_amount, interest_rate)"
    step3: "Split data (80% train = 41,939 records, 20% test = 10,485 records)"
    step4: "Initialize GradientBoostingRegressor (200 trees, max_depth=10, learning_rate=0.1)"
    step5: "Train model on training set"
    step6: "Evaluate on test set"
    step7: "Calculate metrics (R²=95.85%, MAE=1.03, RMSE=1.34)"
    step8: "Analyze feature importance (EMI=53.71%, Savings=17.97%, Income=13.66%, Expenses=12.95%)"
    step9: "Save model artifacts (financial_health_model.pkl, feature_names.pkl, model_metadata.pkl)"
    end: "Model ready for production predictions"
}

// Flow 4: REAL-TIME SCORE PREDICTION (Key Differentiator)
flow_score_prediction_realtime {
    start: "User submits financial data via /api/predict"
    step1: "Backend validates input (required fields, data types, ranges)"
    step2: "Load ML model from pkl file (financial_health_model.pkl)"
    step3: "Load feature names (feature_names.pkl)"
    step4: "Prepare feature vector from user input"
    step5: "model.predict(features) - returns raw score"
    step6: "Clamp score to 0-100 range"
    step7: "Classify score (Excellent/Very Good/Good/Average/Poor)"
    step8: "Analyze spending patterns"
    step9: "Generate personalized guidance"
    step10: "Detect anomalies in spending"
    step11: "Suggest investments based on score"
    step12: "Return comprehensive JSON response"
    step13: "Frontend displays score with visualization"
    note: "IMPORTANT: Score is NOT stored in database - calculated on-the-fly for real-time accuracy"
    end: "User sees real-time financial health assessment"
}

// DEPLOYMENT ARCHITECTURE

// Current Deployment
deployment_current {
    frontend: "React SPA (Vite build)"
    backend: "Flask development server"
    database: "SQLite (local file)"
    ml_model: "Loaded from pkl files"
    hosting: "Local/Development"
}

// Production Deployment (Recommended)
deployment_production {
    frontend: "Vite build → CDN/Static hosting"
    backend: "Gunicorn WSGI server → Docker container"
    database: "PostgreSQL → Cloud database"
    ml_model: "Model versioning system"
    cache: "Redis for caching"
    hosting: "Cloud (AWS/GCP/Azure)"
    ci_cd: "GitHub Actions"
    monitoring: "Prometheus + Grafana"
}

// TECHNOLOGY STACK SUMMARY

tech_stack {
    // Frontend (React SPA)
    frontend: {
        framework: "React 18",
        build_tool: "Vite",
        styling: "Tailwind CSS",
        state_management: "React hooks (useState) + localStorage",
        routing: "React Router v6",
        charts: "Recharts + D3.js",
        http_client: "Axios",
        components: "50+ React components",
        pages: [
            "LandingPage",
            "AuthPage (Login/Register)",
            "MainDashboard",
            "FinancialForm",
            "ScoreDisplay",
            "WhatIfSimulator",
            "LoanManagementPage",
            "GoalsManager",
            "ProfilePage",
            "RiskAssessment"
        ]
    }
    
    // Backend (Flask API)
    backend: {
        framework: "Flask (Python)",
        database: "SQLite (auth.db)",
        authentication: "JWT tokens",
        password_hashing: "bcrypt",
        validation: "Custom schemas",
        sms_otp: "Twilio API",
        file_upload: "Werkzeug",
        endpoints: "20+ REST endpoints",
        services: [
            "financial_health_scorer.py (5-factor rule-based)",
            "loan_history_service.py",
            "loan_metrics_engine.py",
            "goals_service.py",
            "profile_service.py",
            "risk_assessment_service.py",
            "twilio_service.py"
        ]
    }
    
    // ML/Data Science
    ml: {
        framework: "scikit-learn",
        algorithm: "GradientBoostingRegressor",
        n_estimators: 200,
        max_depth: 10,
        learning_rate: 0.1,
        data_processing: "Pandas + NumPy",
        serialization: "joblib",
        training_data: "52,424 records",
        input_features: 7,
        output: "Financial health score (0-100)",
        accuracy: "95.85% R²",
        mae: "1.03 points"
    }
    
    // Testing
    testing: {
        backend: "pytest",
        property_based: "Hypothesis",
        test_files: "18+ comprehensive tests",
        coverage: "Unit, integration, property-based"
    }
    
    // External Services
    external: {
        sms_otp: "Twilio",
        file_storage: "Local filesystem (backend/uploads/)"
    }
}

// KEY METRICS

metrics {
    // Performance
    api_response_time: "<500ms"
    model_prediction_time: "<1ms per record"
    page_load_time: "<2s"
    model_load_time: "~100ms"
    database_query_time: "<100ms"
    
    // ML Model Performance
    r2_score: "95.85% (target: 72-78%)"
    mae: "1.03 points (target: <7)"
    rmse: "1.34 points"
    training_data: "52,424 records"
    training_time: "~2 minutes"
    model_size: "~5MB"
    
    // Code Quality
    test_files: "18+ comprehensive tests"
    components: "50+ React components"
    api_endpoints: "20+ endpoints"
    backend_services: "7 service modules"
    
    // Database
    tables: "7 tables"
    indexes: "16 indexes"
    records_capacity: "Scalable to millions"
    
    // Feature Importance (ML Model)
    emi_importance: "53.71% (most important)"
    savings_importance: "17.97%"
    income_importance: "13.66%"
    expenses_importance: "12.95%"
    age_importance: "1.15%"
    loan_amount_importance: "0.34%"
    interest_rate_importance: "0.14%"
    has_loan_importance: "0.08%"
}

// SECURITY FEATURES

security {
    authentication: "JWT tokens with refresh mechanism"
    password: "bcrypt hashing (industry standard)"
    email_verification: "Email confirmation with token expiry"
    otp_verification: "Twilio SMS OTP with time-based expiry"
    input_validation: "Schema validation on all endpoints"
    sql_injection: "Parameterized queries (SQLite prepared statements)"
    cors: "CORS configuration for frontend domain"
    rate_limiting: "Recommended for production"
    soft_deletes: "deleted_at column for data recovery"
    audit_timestamps: "created_at, updated_at on all records"
    foreign_keys: "Referential integrity constraints"
}

// FUTURE ENHANCEMENTS

future_roadmap {
    // Phase 1: Advanced ML
    advanced_ml: [
        "Neural networks",
        "Ensemble methods",
        "Time-series forecasting",
        "Anomaly detection"
    ]
    
    // Phase 2: Features
    new_features: [
        "Mobile app (React Native)",
        "Real-time notifications",
        "Budget tracking",
        "Investment portfolio",
        "Tax planning"
    ]
    
    // Phase 3: Infrastructure
    infrastructure: [
        "Microservices architecture",
        "API gateway",
        "Message queues (RabbitMQ)",
        "Caching layer (Redis)",
        "CDN integration"
    ]
    
    // Phase 4: Analytics
    analytics: [
        "User behavior tracking",
        "Model performance monitoring",
        "A/B testing",
        "Analytics dashboards"
    ]
}

// END OF ARCHITECTURE DIAGRAM PROMPT
// This prompt can be used to generate diagrams in:
// - Mermaid (mermaid.js)
// - PlantUML
// - Draw.io
// - Lucidchart
// - Any architecture diagramming tool
