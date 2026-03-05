#!/bin/bash
# Setup script for Healthcare Insurance Intelligence Platform

set -e

echo "🏥 Healthcare Insurance Intelligence Platform - Setup"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please update .env with your configuration (especially OPENAI_API_KEY)"
else
    echo "ℹ️  .env file already exists"
fi
echo ""

# Create data directory
echo "Creating data directory..."
mkdir -p data/chroma
echo "✅ Data directory created"
echo ""

# Check if PostgreSQL is running
echo "Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client found"
    echo "ℹ️  Make sure PostgreSQL server is running and database is created"
else
    echo "⚠️  PostgreSQL client not found. You can use Docker Compose instead:"
    echo "   docker-compose up -d postgres"
fi
echo ""

echo "=================================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Start PostgreSQL (or run: docker-compose up -d postgres)"
echo "3. Run migrations: alembic upgrade head"
echo "4. Start the development server: make dev"
echo ""
echo "For more information, see README.md"
