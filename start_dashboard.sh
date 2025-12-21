#!/bin/bash
# Start the FastAPI web dashboard

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"

echo "🚀 Starting YouTube Metadata Manager Dashboard..."
echo "📊 Dashboard: http://localhost:8000/admin"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""

uvicorn app:app --reload --host 0.0.0.0 --port 8000
