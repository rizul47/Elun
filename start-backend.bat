@echo off
REM Quick start script for local testing

echo ========================================
echo Symbol Art - Local Testing
echo ========================================
echo.

REM Check if Node is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

echo.
echo Setting up backend...
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo ========================================
echo Backend ready!
echo ========================================
echo.
echo Starting FastAPI server on http://localhost:8000
echo.
echo KEEP THIS TERMINAL OPEN
echo.
echo Open a NEW terminal and run: npm run dev
echo Then go to http://localhost:5173
echo.

uvicorn server:app --reload --port 8000

pause
