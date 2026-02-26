# SmartFin - Quick Start Guide (New UI)

## 🚀 Getting Started

### Prerequisites
- Python 3.8+ with virtual environment activated
- Node.js 16+ and npm installed
- Both servers running (see below)

---

## 🖥️ Running the Application

### 1. Start Backend Server
```bash
cd backend
python app.py
```
**Backend URL:** http://127.0.0.1:5000

### 2. Start Frontend Server
```bash
cd frontend
npm run dev
```
**Frontend URL:** http://localhost:5173/

---

## 🎨 New UI Features

### Landing Page
- **URL:** http://localhost:5173/
- Modern hero section with animated AI chat interface
- Glass morphism feature cards
- Smooth scroll animations
- Professional design matching FinCore template

### Authentication
- Click "Get Started" or "Initialize Protocol" button
- Modern authentication page with:
  - Real-time field validation
  - Password visibility toggle
  - Error handling with animations
  - Social login buttons (UI only)

### Dashboard
- After login, access full SmartFin features:
  - Financial health analysis
  - ML-powered predictions
  - Interactive charts
  - What-if simulator
  - Personalized guidance

---

## 🎯 User Flow

```
Landing Page → Click "Get Started" → Auth Page → Login/Register → Dashboard
```

### Test Accounts
Create a new account or use existing credentials from `backend/auth.db`

---

## 🛠️ Development Commands

### Frontend
```bash
cd frontend

# Development server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

### Backend
```bash
cd backend

# Start server
python app.py

# Run tests
python test_api.py
```

---

## 📁 Project Structure

```
smartfin-copy/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LandingPage.jsx      # New landing page
│   │   │   ├── Navigation.jsx       # Navigation bar
│   │   │   ├── Hero.jsx             # Hero section with animation
│   │   │   ├── Features.jsx         # Feature cards
│   │   │   ├── Integration.jsx      # How it works section
│   │   │   ├── CTA.jsx              # Call to action
│   │   │   ├── Footer.jsx           # Footer
│   │   │   ├── AuthPage.jsx         # New auth page
│   │   │   └── MainDashboard.jsx    # Main app dashboard
│   │   ├── services/
│   │   │   └── api.js               # Backend API calls
│   │   ├── App.jsx                  # Main app component
│   │   └── index.css                # Global styles
│   ├── index.html                   # HTML entry point
│   ├── tailwind.config.js           # Tailwind configuration
│   └── package.json                 # Dependencies
├── backend/
│   ├── app.py                       # Flask server
│   ├── auth.db                      # SQLite database
│   └── requirements.txt             # Python dependencies
└── docs/
    └── session_summary/
        └── 2026-02-09-fincore-conversion.md
```

---

## 🎨 Design System

### Colors
- **Primary:** Cyan (#06b6d4, #22d3ee)
- **Background:** Black (#030303)
- **Text:** White with opacity variants
- **Error:** Red (#ef4444)

### Fonts
- **Display:** Space Grotesk (headings)
- **Body:** Inter (text)
- **Code:** JetBrains Mono (code)

### Effects
- Glass morphism panels
- Backdrop blur
- Gradient text
- Smooth animations
- Hover transitions

---

## 🔧 Troubleshooting

### Frontend won't start
```bash
cd frontend
npm install
npm run dev
```

### Backend won't start
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### CORS errors
- Backend is configured for ports: 5173, 5174, 5175, 3000
- Check `backend/app.py` CORS configuration

### Build errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 📊 Current Status

✅ Frontend: Running on http://localhost:5173/  
✅ Backend: Running on http://127.0.0.1:5000  
✅ Build: Successful  
✅ Tests: Passing  

---

## 🎯 Key Features

### Landing Page
- Animated hero with AI visualization
- Feature showcase with glass effects
- Integration flow diagram
- Professional footer

### Authentication
- Login and registration
- Field validation
- Error handling
- JWT token authentication

### Dashboard
- Financial health scoring
- ML predictions
- Interactive charts
- What-if simulator
- Personalized alerts
- Investment advice

---

## 📝 Notes

- The new UI uses Tailwind CSS v4
- All animations are CSS-based (no heavy JS libraries)
- UnicornStudio provides the animated background
- Backend API remains unchanged
- All existing features are preserved

---

## 🚀 Next Steps

1. Open http://localhost:5173/ in your browser
2. Explore the new landing page
3. Click "Get Started" to test authentication
4. Create an account or login
5. Use the financial analysis features

---

## 📚 Documentation

- Full session summary: `docs/session_summary/2026-02-09-fincore-conversion.md`
- Original docs: `docs/vscode_docs/`
- API documentation: `backend/README.md`

---

**Enjoy your new SmartFin UI! 🎉**
