@echo off
title Campaign Agent - Starting...

echo.
echo  ================================================
echo    Campaign Agent - One-Click Start
echo  ================================================
echo.

REM ------------------------------------------------------------------
REM 0. Check Python is installed
REM ------------------------------------------------------------------
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 goto :NO_PYTHON
echo  [OK] Python found.

REM ------------------------------------------------------------------
REM 1. Check .env exists
REM ------------------------------------------------------------------
if not exist ".env" goto :NO_ENV
echo  [OK] .env file found.

REM ------------------------------------------------------------------
REM 2. Create virtual environment (first run only)
REM ------------------------------------------------------------------
if exist ".venv\Scripts\activate.bat" goto :VENV_READY
echo  [SETUP] Creating Python virtual environment...
python -m venv .venv
if %ERRORLEVEL% neq 0 goto :VENV_FAIL
echo  [OK] Virtual environment created.

:VENV_READY
echo  [OK] Virtual environment ready.

REM ------------------------------------------------------------------
REM 3. Activate virtual environment
REM ------------------------------------------------------------------
call .venv\Scripts\activate.bat

REM ------------------------------------------------------------------
REM 4. Install dependencies (first run or after update)
REM ------------------------------------------------------------------
if exist ".venv\.deps_installed" goto :DEPS_READY
echo  [SETUP] Installing Python dependencies (this may take a few minutes)...
pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 goto :DEPS_FAIL
echo ok > ".venv\.deps_installed"
echo  [OK] Dependencies installed successfully.
goto :START_SERVER

:DEPS_READY
echo  [OK] Dependencies already installed.

REM ------------------------------------------------------------------
REM 5. Start the server
REM ------------------------------------------------------------------
:START_SERVER

if not exist "outputs" mkdir outputs

echo.
echo  ========================================
echo   Starting Campaign Agent...
echo   Open in browser: http://localhost:8000
echo  ========================================
echo.
echo  Press Ctrl+C to stop the server.
echo.

title Campaign Agent - Running on http://localhost:8000

REM Open browser after a short delay
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

REM Start uvicorn (blocking - keeps the window open)
python -m uvicorn api:app --host 0.0.0.0 --port 8000
goto :DONE

REM ------------------------------------------------------------------
REM Error handlers
REM ------------------------------------------------------------------
:NO_PYTHON
echo  [ERROR] Python is not installed or not in PATH.
echo  Please install Python 3.11+ from https://www.python.org/downloads/
echo  Make sure to check "Add Python to PATH" during installation.
goto :DONE

:NO_ENV
echo  [WARNING] .env file not found!
echo  Creating .env from .env.example ...
copy ".env.example" ".env" >nul
echo.
echo  Please edit .env and fill in your API keys, then re-run start.bat.
notepad ".env"
goto :DONE

:VENV_FAIL
echo  [ERROR] Failed to create virtual environment.
goto :DONE

:DEPS_FAIL
echo  [ERROR] Failed to install dependencies.
goto :DONE

:DONE
echo.
echo  Press any key to exit...
pause >nul
