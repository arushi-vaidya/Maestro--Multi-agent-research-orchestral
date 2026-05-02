#!/bin/bash

echo "🚀 Starting MAESTRO with custom ports..."
echo ""

# Terminal 1: Backend on 8010
echo "Starting backend on port 8010..."
cd backend
export PORT=8010
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
python main.py &
BACKEND_PID=$!

sleep 10

# Terminal 2: Frontend on 3010
echo ""
echo "Starting frontend on port 3010..."
cd ../frontend
export REACT_APP_API_URL=http://localhost:8010
export PORT=3010
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ Both services started:"
echo "   Backend:  http://localhost:8010"
echo "   Frontend: http://localhost:3010"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

wait
