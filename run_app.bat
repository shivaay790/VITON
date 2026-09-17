@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "PYTHONWARNINGS=ignore::FutureWarning"
REM Pinecone settings, if any, are read from backend\.env

echo Starting ezyZip backend and frontend...
echo.

REM Free backend/frontend ports if stale processes are running.
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do taskkill /PID %%P /F >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":5173 .*LISTENING"') do taskkill /PID %%P /F >nul 2>&1

REM Start backend in a new terminal window.
if exist "%ROOT_DIR%backend\venv\Scripts\python.exe" (
    start "ezyZip Backend" /D "%ROOT_DIR%backend" "%ROOT_DIR%backend\venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8000
) else (
    echo [WARN] backend venv python not found, using system Python
    start "ezyZip Backend" /D "%ROOT_DIR%backend" python -m uvicorn main:app --reload --port 8000
)

REM Start frontend in a new terminal window.
start "ezyZip Frontend" /D "%ROOT_DIR%frontend" npm.cmd run dev

echo Both servers are starting in separate windows.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo.
pause
