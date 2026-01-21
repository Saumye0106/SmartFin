@echo off
echo ===================================
echo Starting SmartFin Application
echo ===================================
echo.

echo Starting Backend on port 5000...
start "SmartFin Backend" cmd /k "cd backend && python app.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend on port 8000...
start "SmartFin Frontend" cmd /k "cd frontend && python start_frontend.py"

timeout /t 2 /nobreak >nul

echo.
echo ===================================
echo SmartFin is starting!
echo ===================================
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:8000
echo.
echo Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:8000
echo.
echo Press any key to stop all servers...
pause >nul

taskkill /FI "WINDOWTITLE eq SmartFin Backend*" /F
taskkill /FI "WINDOWTITLE eq SmartFin Frontend*" /F
