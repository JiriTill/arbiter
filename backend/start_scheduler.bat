@echo off
REM Start RQ Scheduler for The Arbiter
REM Usage: start_scheduler.bat

echo ==============================================
echo The Arbiter - Starting RQ Scheduler
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

REM Install rq-scheduler if not present
pip show rq-scheduler >nul 2>&1 || pip install rq-scheduler

echo Starting scheduler...
echo.

python -m app.jobs.scheduler
