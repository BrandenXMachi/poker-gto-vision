@echo off
REM Development startup script for Poker GTO Vision (Windows)
REM Starts both frontend and backend in separate windows

echo ========================================
echo   Poker GTO Vision Development Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check if Node is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js 18+
    pause
    exit /b 1
)

echo [OK] Prerequisites found
echo.

REM Start Backend in new window
echo Starting Python backend...
start "Poker GTO Backend" cmd /k "cd backend && if exist venv\Scripts\activate (venv\Scripts\activate) else (python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt) && python main.py"

timeout /t 3 /nobreak >nul

REM Start Frontend in new window
echo Starting Next.js frontend...
start "Poker GTO Frontend" cmd /k "cd frontend && if not exist node_modules (npm install) && npm run dev"

echo.
echo ========================================
echo   Both services are starting!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Access from phone: http://YOUR_LAPTOP_IP:3000
echo.
echo Press any key to close this window...
pause >nul
