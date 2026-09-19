#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================="
echo "Starting ORCA Marine Telemetry & AI System"
echo "=========================================="

if [ ! -d "backend/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv backend/.venv
    backend/.venv/bin/pip install -r backend/requirements.txt
    backend/.venv/bin/pip install aiosqlite
fi

export PYTHONPATH="$DIR"
echo "Starting FastAPI Server on http://localhost:8000 ..."
echo "Interactive Swagger API Docs: http://localhost:8000/docs"
echo "ORCA Mobile Dashboard:        http://localhost:8000"

exec backend/.venv/bin/python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
