@echo off
echo 🌟 Starting ECHO - Ambient Cognitive Partner
echo ==========================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Set environment variables
set PYTHONPATH=%CD%

REM Start ECHO
echo 🚀 Launching ECHO...
python main.py

pause