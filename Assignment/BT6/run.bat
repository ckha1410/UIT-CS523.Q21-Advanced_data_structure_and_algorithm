@echo off
:: Student Management System Launcher (Web UI)

cls
echo ============================================================
echo Student Management System - Web Console
echo ============================================================
echo.
echo Open browser at: http://127.0.0.1:5000
echo.

set "APP_PY=D:\Annaconda\python.exe"
if exist "%APP_PY%" (
    echo Using Python: %APP_PY%
    "%APP_PY%" web_app.py
) else (
    echo Using Python from PATH
    python web_app.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Failed to start the application.
    echo Make sure Python 3.8+ is installed and run:
    echo   python -m pip install -r requirements.txt
    pause
)
