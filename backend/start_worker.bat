@echo off
REM Start RQ Worker for The Arbiter
REM Usage: start_worker.bat

echo ==============================================
echo The Arbiter - Starting RQ Worker
echo ==============================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Check if Redis is accessible
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Redis ping failed. Make sure Redis is running.
    echo   You can install Redis for Windows or use Docker:
    echo   docker run -d -p 6379:6379 redis:latest
    echo.
)

echo Starting worker...
echo.

python -m app.jobs.worker
