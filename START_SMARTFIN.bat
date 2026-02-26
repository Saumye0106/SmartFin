@echo off
echo ===================================
echo Starting SmartFin Application
echo ===================================
echo.

echo Starting Backend on port 5000...
start "SmartFin Backend" cmd /k "cd backend && ..\\.venv\\Scripts\\python.exe app.py"

timeout /t 3 /nobreak >nul

echo Starting React Frontend on port 5173...
start "SmartFin Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 2 /nobreak >nul

echo.
echo ===================================
echo SmartFin is starting!
echo ===================================
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173
echo.
echo Press any key to stop all servers...
pause >nul

taskkill /FI "WINDOWTITLE eq SmartFin Backend*" /F
taskkill /FI "WINDOWTITLE eq SmartFin Frontend*" /F
