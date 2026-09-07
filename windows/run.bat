@echo off
setlocal enabledelayedexpansion

REM Set working directory to the project root
cd /d "%~dp0.."

echo ==========================================================
echo Starting Smart Building Management System (Windows)...
echo ==========================================================

REM Check if virtual environment exists
IF NOT EXIST "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found! 
    echo Please run .\windows\install.ps1 first to setup the system.
    pause
    exit /b
)

REM Get the local IPv4 address
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr "IPv4 Address"') do (
    set ip=%%A
    set ip=!ip: =!
)

echo.
echo ==========================================================
echo Server is starting... 
echo You can view the app from THIS computer at: 
echo http://localhost:8000
echo.
echo To access the app from ANY DEVICE on your Wi-Fi/Network:
if defined ip (
    echo http://!ip!:8000
) else (
    echo [Could not detect local IP automatically - check ipconfig]
)
echo ==========================================================
echo.
echo NOTE: If Windows Firewall asks for permission, click "Allow Access" 
echo so other devices on your network can reach the server.
echo.

.\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
