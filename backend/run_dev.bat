@echo off
cd /d "%~dp0"
echo Backend baslatiliyor: http://localhost:8000 (health: http://localhost:8000/health)
set PYTHONPATH=%~dp0
echo %DATABASE_URL%|findstr /i "herosteps" >nul 2>&1 && set DATABASE_URL=
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
