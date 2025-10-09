#!/bin/bash

# EPIC Issues Dashboard - Quick Start Script
# This script helps you get the dashboard up and running quickly

set -e

echo "=========================================="
echo "EPIC Issues Dashboard - Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo "✅ Node.js found: $(node --version)"
echo ""

# Backend setup
echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Backend dependencies installed"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found in backend directory"
    echo "Please ensure the .env file is present with your Jira credentials"
    exit 1
fi

# Fetch initial data
echo "🔄 Fetching initial data from Jira..."
python jira_client.py

echo "✅ Initial data fetched and categorized"
echo ""

# Start backend in background
echo "🚀 Starting backend server..."
python main.py &
BACKEND_PID=$!
echo "Backend running on PID $BACKEND_PID"

cd ..

# Frontend setup
echo ""
echo "📦 Setting up frontend..."
cd frontend

# Install Node dependencies
echo "Installing Node dependencies..."
npm install

echo "✅ Frontend dependencies installed"
echo ""

# Start frontend
echo "🚀 Starting frontend server..."
echo ""
echo "=========================================="
echo "Dashboard will open at: http://localhost:3003"
echo "API running at: http://localhost:8000"
echo ""
echo "To stop the servers:"
echo "  - Press Ctrl+C for frontend"
echo "  - Kill backend: kill $BACKEND_PID"
echo "=========================================="
echo ""

npm start
