# How to Run SmartFin

## ⚠️ IMPORTANT: Don't open index.html directly!

Opening `index.html` as a file (`file://`) causes CORS errors. You need to run a web server.

---

## ✅ Method 1: One-Click Start (Windows)

**Double-click this file:**
```
START_SMARTFIN.bat
```

This will:
1. Start backend on port 5000
2. Start frontend on port 8000
3. Open browser automatically

---

## ✅ Method 2: Manual Start (2 Terminals)

### Terminal 1 - Backend:
```bash
cd backend
python app.py
```

### Terminal 2 - Frontend:
```bash
cd frontend
python start_frontend.py
```

### Then open browser:
```
http://localhost:8000
```

---

## ✅ Method 3: Command Line

### Windows:
```bash
# Start backend
start cmd /k "cd backend && python app.py"

# Start frontend
start cmd /k "cd frontend && python start_frontend.py"

# Open browser
start http://localhost:8000
```

### Linux/Mac:
```bash
# Terminal 1
cd backend && python app.py

# Terminal 2
cd frontend && python -m http.server 8000

# Open http://localhost:8000
```

---

## 🌐 Access URLs

- **Frontend Dashboard:** http://localhost:8000
- **Backend API:** http://localhost:5000
- **API Health Check:** http://localhost:5000/

---

## 🔍 Troubleshooting

### Problem: "Site can't be reached"

**If opening index.html directly:**
- ❌ Don't do this: `file:///C:/Users/.../index.html`
- ✅ Do this: `http://localhost:8000`

**Solution:**
- Use one of the methods above
- Must run through a web server

### Problem: Backend connection error

**Check if backend is running:**
```bash
curl http://localhost:5000
```

Should return:
```json
{
  "status": "online",
  "service": "SmartFin Financial Health API"
}
```

**If not running:**
```bash
cd backend
python app.py
```

### Problem: Port already in use

**Backend (port 5000):**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

**Frontend (port 8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

---

## ✅ Quick Test

1. Start backend: `cd backend && python app.py`
2. Start frontend: `cd frontend && python start_frontend.py`
3. Open: http://localhost:8000
4. Click "Load Sample Data"
5. Click "Analyze My Finances"
6. ✅ Should see score, charts, guidance!

---

## 📝 Summary

**✅ CORRECT:**
- Run via `http://localhost:8000`
- Use web server (Python, batch file)
- Both backend and frontend must be running

**❌ WRONG:**
- Opening `index.html` directly
- Using `file://` protocol
- Only starting backend

---

## 🎯 Currently Running

Based on our setup:
- ✅ Backend: Running on port 5000
- ✅ Frontend: Running on port 8000

**Just open your browser and go to:**
```
http://localhost:8000
```

**That's it!** 🚀
