# SmartFin Frontend

Modern, responsive financial health dashboard built with HTML/CSS/JavaScript and Chart.js.

## Features

- **Interactive Score Display** - Animated circular progress indicator
- **Spending Breakdown** - Doughnut chart visualization
- **Financial Ratios** - Animated progress bars for expense, savings, EMI ratios
- **Risk Alerts** - Color-coded anomaly detection
- **Personalized Guidance** - Strengths, warnings, and recommendations
- **Investment Advice** - Rule-based investment suggestions
- **What-If Simulator** - Interactive scenario testing
- **Responsive Design** - Works on desktop, tablet, and mobile

## Tech Stack

- HTML5
- CSS3 (Modern, responsive design)
- Vanilla JavaScript (ES6+)
- Chart.js 4.4.0 (from CDN)

## File Structure

```
frontend/
├── index.html              # Main HTML file
├── css/
│   └── styles.css          # All styles (responsive, animations)
├── js/
│   ├── api.js              # API service layer
│   ├── charts.js           # Chart.js visualizations
│   └── app.js              # Main application logic
└── README.md               # This file
```

## Setup & Usage

### Prerequisites

1. Flask backend must be running on `http://localhost:5000`

```bash
cd backend
python app.py
```

### Run Frontend

**Option 1: Direct File Open**
```bash
# Simply open index.html in your browser
open frontend/index.html
```

**Option 2: Local Server (Recommended)**
```bash
# Python 3
cd frontend
python -m http.server 8000

# Then visit: http://localhost:8000
```

**Option 3: VS Code Live Server**
- Right-click `index.html` → "Open with Live Server"

## How to Use

### 1. Enter Financial Details

Fill in the form with your monthly financial data:
- Income
- Rent/Housing
- Food & Groceries
- Travel & Transport
- Shopping & Entertainment
- EMI & Loans
- Savings

### 2. Click "Analyze My Finances"

The system will:
- Send data to ML backend
- Predict your financial health score (0-100)
- Classify into 5 categories (Poor → Excellent)
- Analyze spending patterns
- Detect anomalies and risks
- Provide personalized guidance
- Suggest suitable investments

### 3. View Comprehensive Analysis

**Score Card:**
- Animated score display
- Category badge (Poor/Average/Good/Very Good/Excellent)
- Color-coded visualization

**Spending Breakdown:**
- Interactive doughnut chart
- Percentage allocation across categories

**Financial Ratios:**
- Expense ratio (expenses / income)
- Savings ratio (savings / income)
- EMI burden (EMI / income)

**Alerts & Warnings:**
- Critical: Red alerts (spending > income, debt trap)
- High: Yellow warnings (zero savings, high EMI)
- Medium: Blue notices (low buffer)
- Low: Gray tips (spending priorities)

**Guidance:**
- ✓ Strengths (green boxes)
- ⚠ Warnings (red boxes)
- → Recommendations (blue boxes)

**Investment Advice:**
- Eligibility status
- Suitable investment types
- Recommended allocation
- Risk levels
- Educational explanations

### 4. Try What-If Simulator

Experiment with changes:
1. Adjust shopping amount
2. Adjust savings amount
3. Click "Run Simulation"
4. See new predicted score
5. View score change (+/- impact)

## API Integration

Frontend communicates with Flask backend via REST API:

### Endpoints Used

**1. POST /api/predict**
```javascript
{
  "income": 50000,
  "rent": 15000,
  "food": 8000,
  // ...
}
```

**2. POST /api/whatif**
```javascript
{
  "current": {...},
  "modified": {...}
}
```

## Design Features

### Color Scheme

- Primary: #3b82f6 (Blue)
- Secondary: #8b5cf6 (Purple)
- Success: #10b981 (Green)
- Warning: #f59e0b (Amber)
- Danger: #ef4444 (Red)

### Animations

- Score circle animation (2s ease-in-out)
- Ratio bar animations (1s staggered)
- Number count-up effect
- Smooth scroll to results
- Hover effects on cards

### Responsive Breakpoints

- Desktop: 1200px+
- Tablet: 768px - 1199px
- Mobile: < 768px

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Backend Connection Error

**Problem:** "Error connecting to backend"

**Solution:**
1. Check Flask server is running:
   ```bash
   cd backend
   python app.py
   ```
2. Verify server is on port 5000
3. Check browser console for CORS errors

### Charts Not Displaying

**Problem:** Charts don't appear

**Solution:**
1. Check internet connection (Chart.js loads from CDN)
2. Open browser console for errors
3. Verify Chart.js CDN is accessible

### CORS Issues

**Problem:** "CORS policy blocked"

**Solution:**
- Backend already has `flask-cors` enabled
- If issue persists, try running frontend via local server (not file://)

## Sample Data

Click "Load Sample Data" button to populate form with:
- Income: Rs.50,000
- Rent: Rs.15,000
- Food: Rs.8,000
- Travel: Rs.3,000
- Shopping: Rs.5,000
- EMI: Rs.10,000
- Savings: Rs.9,000

Expected Score: ~60 (Good)

## Performance

- Initial Load: < 1s
- API Response: < 500ms
- Chart Rendering: < 200ms
- Total Interaction: < 2s

## Future Enhancements

- [ ] Save/Load user profiles
- [ ] Historical score tracking
- [ ] Multiple what-if scenarios comparison
- [ ] Export reports as PDF
- [ ] Dark mode toggle
- [ ] Mobile app (PWA)

## Credits

- Built for SmartFin ML project
- Chart.js for visualizations
- Modern CSS design patterns

---

**Version:** 1.0
**Last Updated:** January 2025
