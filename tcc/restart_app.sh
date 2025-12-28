#!/bin/bash
echo "🛑 Killing old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
pkill -f "python3 start_app.py" 2>/dev/null

echo "♻️  Cleaning up..."
sleep 1

echo "🚀 Starting App..."
python3 start_app.py
