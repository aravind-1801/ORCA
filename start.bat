@echo off
echo ==========================================
echo Starting ORCA Marine Telemetry & AI System
echo ==========================================
echo Target URL: http://127.0.0.1:8000/
echo Swagger UI: http://127.0.0.1:8000/docs
echo Health API: http://127.0.0.1:8000/health
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
