#!/bin/bash

# CAD Platform Quick Start Script

echo "🚀 CAD Generation Platform - Quick Start"
echo "========================================"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install dependencies
echo "📦 Installing dependencies..."
brew install node python postgresql

# Setup Backend
echo "🔧 Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Setup Frontend
echo "🎨 Setting up frontend..."
cd ../frontend
npm install

# Setup Database
echo "🗄️ Setting up database..."
createdb cad_platform || true
psql cad_platform < ../database/init.sql

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && source venv/bin/activate && python main.py"
echo "2. Frontend: cd frontend && npm start"
echo ""
echo "Access the application at: http://localhost:4200"
echo "API available at: http://localhost:8000"
