#!/bin/bash

# Altea Booking Bot Setup Script
# This script sets up the environment and dependencies for the booking bot

set -e  # Exit on any error

echo "==================================="
echo "Altea Booking Bot - Setup Script"
echo "==================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed."
    echo "Please install pip3 and try again."
    exit 1
fi

echo "✓ Found pip3"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Python dependencies installed"

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers (this may take a few minutes)..."
playwright install chromium
echo "✓ Playwright Chromium browser installed"

# Install system dependencies for Playwright (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo ""
    echo "Installing system dependencies for Playwright..."
    playwright install-deps chromium
    echo "✓ System dependencies installed"
fi

# Create config.yaml if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo ""
    echo "Creating config.yaml template..."
    cat > config.yaml << 'EOF'
credentials:
  email: "your-email@example.com"
  password: "YOUR_PASSWORD_HERE"
EOF
    echo "✓ config.yaml created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit config.yaml and add your credentials!"
else
    echo ""
    echo "✓ config.yaml already exists"
fi

# Create src directory if it doesn't exist
mkdir -p src

echo ""
echo "==================================="
echo "✓ Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit config.yaml with your credentials"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the script: python main.py"
echo ""
echo "To run on a schedule (cron), add this line to your crontab:"
echo "0 9 * * * cd $(pwd) && $(pwd)/venv/bin/python $(pwd)/main.py >> $(pwd)/booking.log 2>&1"
echo ""

