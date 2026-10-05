@echo off
setlocal
set "PYTHONDONTWRITEBYTECODE=1"
set "ROOT=%~dp0"
if "%TUKUYO_DATA_DIR%"=="" set "TUKUYO_DATA_DIR=%USERPROFILE%\.tukuyo\v999_data"
if not exist "%TUKUYO_DATA_DIR%" mkdir "%TUKUYO_DATA_DIR%"
cd /d "%ROOT%"
python -B run_tukuyo.py verify-origins || exit /b 1
if not exist "%TUKUYO_DATA_DIR%\state\integration_state.json" python -B run_tukuyo.py --data "%TUKUYO_DATA_DIR%" init --individual-id TUKUYO-v1012-1-001 || exit /b 1
python -B run_tukuyo.py --data "%TUKUYO_DATA_DIR%" chat
