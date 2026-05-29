#!/bin/bash
cd "$(dirname "$0")"
nohup env PYTHONPATH="$PWD/backend" python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/portfolio_backend.log 2>&1 &
echo "Backend started on port 8000 (PID $!)"
echo "Logs: /tmp/portfolio_backend.log"
