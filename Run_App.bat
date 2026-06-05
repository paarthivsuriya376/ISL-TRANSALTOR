@echo off
title ISL Communicator Pro
echo ===================================================
echo             ISL Communicator Pro Launcher
echo ===================================================
echo.
echo Starting the AI tracking engine and web interface...
echo.

:: Change directory to the script location
cd /d "%~dp0"

:: Run the application using the virtual environment python
.\venv\Scripts\python.exe main_web.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The application closed with an error (Code: %errorlevel%).
    echo Press any key to exit...
    pause > nul
)
