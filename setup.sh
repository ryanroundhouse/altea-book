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

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✓ .env created from env.example"
    else
        cat > .env << 'EOF'
# Altea Active Credentials
ALTEA_EMAIL=your-email@example.com
ALTEA_PASSWORD=your-password-here

# Mailgun Configuration (optional)
MAILGUN_DOMAIN=your-mailgun-domain.mailgun.org
MAILGUN_API_KEY=key-your-api-key-here
FROM_EMAIL=altea-booking@your-domain.com
TO_EMAIL=your-email@example.com
WIFE_EMAIL=wife-email@example.com
EOF
        echo "✓ .env created"
    fi
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your credentials!"
else
    echo ""
    echo "✓ .env already exists"
fi

# Create src directory if it doesn't exist
mkdir -p src

echo ""
echo "==================================="
echo "✓ Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your credentials (ALTEA_EMAIL and ALTEA_PASSWORD)"
echo "2. (Optional) Add Mailgun settings to .env for email notifications"
echo "3. Activate the virtual environment: source venv/bin/activate"
echo "4. Run the script: python main.py"
echo ""
echo "To run on a schedule (cron), add this line to your crontab:"
echo "0 9 * * * cd $(pwd) && $(pwd)/venv/bin/python $(pwd)/main.py >> $(pwd)/booking.log 2>&1"
echo ""

