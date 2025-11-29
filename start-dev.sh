#!/bin/bash

# Development startup script for Poker GTO Vision
# Starts both frontend and backend in separate terminals

echo "🎰 Starting Poker GTO Vision Development Environment"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+"
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

echo "✅ Prerequisites found"
echo ""

# Function to start backend
start_backend() {
    echo "🐍 Starting Python backend..."
    cd backend
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "⚠️  Virtual environment not found. Creating one..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    echo "✅ Backend starting on http://0.0.0.0:8000"
    python main.py
}

# Function to start frontend
start_frontend() {
    echo "⚛️  Starting Next.js frontend..."
    cd frontend
    
    # Install deps if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo "⚠️  node_modules not found. Installing dependencies..."
        npm install
    fi
    
    echo "✅ Frontend starting on http://localhost:3000"
    npm run dev
}

# Start both in background
start_backend &
BACKEND_PID=$!

sleep 2

start_frontend &
FRONTEND_PID=$!

echo ""
echo "🚀 Both services started!"
echo "📱 Access from phone: http://YOUR_LAPTOP_IP:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
