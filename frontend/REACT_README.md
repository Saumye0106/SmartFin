# SmartFin React Frontend

Modern React-based frontend for the SmartFin Financial Health Platform.

## 🚀 Tech Stack

- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **CSS3** - Modern styling

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── FinancialForm.jsx        # Input form
│   │   ├── ScoreDisplay.jsx         # Score circle display
│   │   ├── SpendingChart.jsx        # Pie chart visualization
│   │   ├── RatiosDashboard.jsx      # Financial ratios
│   │   ├── AlertsPanel.jsx          # Risk alerts
│   │   ├── GuidancePanel.jsx        # Personalized advice
│   │   ├── InvestmentAdvice.jsx     # Investment suggestions
│   │   └── WhatIfSimulator.jsx      # Scenario testing
│   ├── services/
│   │   └── api.js                   # API service layer
│   ├── App.jsx                      # Main app component
│   ├── App.css                      # Global styles
│   └── main.jsx                     # Entry point
├── index.html
├── package.json
└── vite.config.js
```

## 🎯 Features

### ✅ Components Implemented

1. **FinancialForm** - 7-field input form with validation
2. **ScoreDisplay** - Animated circular score gauge (0-100)
3. **SpendingChart** - Interactive pie chart with tooltips
4. **RatiosDashboard** - Animated progress bars for ratios
5. **AlertsPanel** - Color-coded risk alerts
6. **GuidancePanel** - Strengths, warnings, recommendations
7. **InvestmentAdvice** - Rule-based investment suggestions
8. **WhatIfSimulator** - Test financial scenarios

### 🎨 Design Features

- **Responsive** - Works on mobile, tablet, desktop
- **Animated** - Smooth transitions and count-up effects
- **Modern UI** - Clean, professional design
- **Color-coded** - Visual indicators for financial health
- **Accessible** - Semantic HTML and ARIA labels

## 🛠️ Installation

```bash
# Install dependencies
npm install
```

## 🏃 Running the App

### Development Mode
```bash
npm run dev
```
Visit: `http://localhost:5173`

### Production Build
```bash
npm run build
npm run preview
```

## 🔗 Backend Connection

The frontend connects to the Flask backend at:
```
http://localhost:5000
```

Make sure the backend is running:
```bash
cd ../backend
python app.py
```

## 📊 API Integration

### Endpoints Used

1. **POST /api/predict** - Get financial health score
2. **POST /api/whatif** - Run what-if simulation
3. **GET /api/model-info** - Get model metadata

### API Service

All API calls are handled through `src/services/api.js`:

```javascript
import api from './services/api';

// Predict score
const result = await api.predict(financialData);

// What-if simulation
const simulation = await api.whatIf(currentData, modifiedData);

// Model info
const modelInfo = await api.getModelInfo();
```

## 🧪 Testing Flow

1. Open `http://localhost:5173`
2. Click "Load Sample Data"
3. Click "Analyze My Finances"
4. View all sections:
   - Score display
   - Spending chart
   - Financial ratios
   - Risk alerts
   - Guidance
   - Investment advice
5. Try What-If Simulator

## 📦 Dependencies

```json
{
  "react": "^19.2.0",
  "react-dom": "^19.2.0",
  "recharts": "^3.7.0",
  "axios": "^1.13.4"
}
```

## 🚀 Quick Start (All-in-One)

Use the batch script:
```bash
# Windows
START_SMARTFIN.bat
```

This starts:
1. Backend on port 5000
2. Frontend on port 5173
3. Opens browser automatically

## 🐛 Troubleshooting

### Issue: API Connection Failed
**Solution:** Ensure backend is running on port 5000

### Issue: Port 5173 Already in Use
**Solution:** Kill the process or change port in `vite.config.js`

### Issue: Charts Not Rendering
**Solution:** Check browser console, verify recharts is installed

### Issue: Blank Page
**Solution:** Check browser console for errors, verify all components imported correctly

---

**Version:** 2.0.0 (React)  
**Last Updated:** February 2026  
**Status:** ✅ Production Ready
