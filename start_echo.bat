@echo off
echo Starting ECHO: The Omniscient Creative Environment
echo ================================================

echo Starting FastAPI Backend...
start "ECHO API" cmd /k "python echo_api.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo Starting React Frontend...
cd echo-ui
start "ECHO UI" cmd /k "npm start"

echo.
echo ECHO System Starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to continue...
pause > nul