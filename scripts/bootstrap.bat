@echo off
REM LifeLink AI dev bootstrap helper for Windows.
REM Usage: scripts\bootstrap.bat [backend|frontend|all]

cd /d "%~dp0.."

if exist .env (
  echo > .env already exists, skipping
) else (
  copy .env.example .env >nul
  echo > Created .env from .env.example
)

if "%1"=="" set ARG=all
if not "%1"=="" set ARG=%1

if "%ARG%"=="backend" goto backend
if "%ARG%"=="frontend" goto frontend
if "%ARG%"=="all" goto all
goto end

:backend
cd backend
if not exist .venv python -m venv .venv
if exist .venv\Scripts\python.exe (set VPY=.venv\Scripts\python.exe) else (set VPY=.venv\bin\python)
%VPY% -m pip install --upgrade pip
%VPY% -m pip install -e ".[dev]"
goto end

:frontend
cd frontend
call npm install
goto end

:all
cd /d "%~dp0.."
call scripts\bootstrap.bat backend
call scripts\bootstrap.bat frontend
goto end

:end
echo Done.
