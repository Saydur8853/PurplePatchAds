@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo    PurplePatch Ads Analyzer Launcher
echo ========================================
echo.

:MAIN_MENU
echo Please choose an option:
echo   1. Setup Environment (First time setup)
echo   2. Start Application (Full launcher with checks)
echo   3. Quick Start (Simple launcher)
echo   4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto SETUP
if "%choice%"=="2" goto FULL_START
if "%choice%"=="3" goto QUICK_START
if "%choice%"=="4" goto EXIT
echo Invalid choice. Please try again.
echo.
goto MAIN_MENU

:SETUP
echo.
echo ========================================
echo    PurplePatch Ads Analyzer Setup
echo ========================================
echo.

echo This will set up the PurplePatch Ads Analyzer project.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://python.org
    echo.
    pause
    goto MAIN_MENU
)

echo Python is installed.
python --version

echo.
echo Creating virtual environment...
if exist "venv\" (
    echo Virtual environment already exists.
) else (
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment!
        pause
        goto MAIN_MENU
    )
    echo Virtual environment created successfully.
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages...
pip install --upgrade pip
pip install flask pandas matplotlib seaborn beautifulsoup4 requests werkzeug

echo.
echo Checking required directories...
if not exist "uploads\" mkdir uploads
if not exist "output\" mkdir output
if not exist "static\" mkdir static
if not exist "templates\" mkdir templates

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
pause
goto MAIN_MENU

:FULL_START
echo.
echo ========================================
echo    Starting PurplePatch Ads Analyzer
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "app.py" (
    echo ERROR: app.py not found!
    echo Please make sure this batch file is in the PurplePatchAds project directory.
    echo Current directory: %CD%
    echo.
    pause
    goto MAIN_MENU
)

echo Checking virtual environment...
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run Setup Environment first (option 1).
    echo.
    pause
    goto MAIN_MENU
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment!
    echo.
    pause
    goto MAIN_MENU
)

echo.
echo Checking required dependencies...
python -c "import flask, pandas, matplotlib, seaborn, beautifulsoup4, requests" 2>nul
if %ERRORLEVEL% neq 0 (
    echo Some dependencies might be missing. Installing requirements...
    pip install flask pandas matplotlib seaborn beautifulsoup4 requests werkzeug
    echo.
)

echo.
echo Starting PurplePatch Ads Analyzer...
echo.
echo The application will be available at:
echo   Local:    http://127.0.0.1:5000
echo   Network:  http://192.168.1.102:5000 (if network accessible)
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the Flask application
python app.py

echo.
echo ========================================
echo Server stopped.
echo.
pause
goto MAIN_MENU

:QUICK_START
echo.
echo Starting PurplePatch Ads Analyzer (Quick Mode)...
echo.

REM Activate virtual environment and start app
call venv\Scripts\activate.bat && python app.py

echo.
echo Server stopped.
echo.
pause
goto MAIN_MENU

:EXIT
echo.
echo Goodbye!
exit /b 0