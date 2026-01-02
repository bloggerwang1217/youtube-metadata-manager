#!/bin/bash
# Start dashboard with browser launch and ensure cleanup on exit

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"

cleanup() {
  if [[ -n "${UVICORN_PID:-}" ]] && kill -0 "$UVICORN_PID" 2>/dev/null; then
    echo "🛑 Stopping dashboard (pid: $UVICORN_PID)..."
    kill "$UVICORN_PID"
  fi
}
trap cleanup EXIT INT TERM

echo "🚀 Starting YouTube Metadata Manager Dashboard..."
echo "📊 Dashboard: http://localhost:8000/admin"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""

uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

sleep 1
open -a "Brave Browser" http://localhost:8000/ || open http://localhost:8000/

wait "$UVICORN_PID"
