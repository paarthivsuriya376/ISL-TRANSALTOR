@echo off
title ISL Communicator Pro - Setup Installer
echo ===================================================
echo             ISL Communicator Pro Setup
echo ===================================================
echo.

:: Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please download and install Python (version 3.10 is recommended) from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b
)

echo Python detected. Setting up virtual environment...
echo.

:: Create a virtual environment if it doesn't exist
if not exist venv (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists. Skipping creation.
)

echo.
echo Installing required packages (this may take a few minutes)...
echo.

:: Upgrade pip and install requirements
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\pip.exe install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies. Please check your internet connection.
    pause
    exit /b
)

echo.
echo ===================================================
echo Setup complete! You can now run the application.
echo Double-click 'Run_App.bat' to start.
echo ===================================================
echo.
pause
