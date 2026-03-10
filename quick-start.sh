#!/bin/bash
# Issue Automator - Quick Start Script
# Run this script to set up the project

set -e

echo "============================================================"
echo "       Issue Automator - Quick Start Setup"
echo "============================================================"
echo ""

# Check Python
echo "[1/5] Checking Python..."
if command -v python &> /dev/null; then
    PYTHON_CMD=python
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi
echo "✓ Python: $($PYTHON_CMD --version)"

# Check pip
echo ""
echo "[2/5] Checking pip..."
$PYTHON_CMD -m pip --version > /dev/null 2>&1 || {
    echo "❌ pip not found. Please install pip"
    exit 1
}
echo "✓ pip installed"

# Check Git
echo ""
echo "[3/5] Checking Git..."
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git"
    exit 1
fi
echo "✓ Git: $(git --version)"

# Create .env file if not exists
echo ""
echo "[4/5] Checking .env configuration..."
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  Please edit .env and add your GitHub token:"
    echo "   GITHUB_TOKEN=ghp_your_token_here"
    echo "   GITHUB_WEBHOOK_SECRET=your_secret_here"
else
    echo "✓ .env file exists"
fi

# Install dependencies
echo ""
echo "[5/5] Installing dependencies..."
$PYTHON_CMD -m pip install -e . --quiet
echo "✓ Dependencies installed"

echo ""
echo "============================================================"
echo "                    Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your GitHub credentials:"
echo "   GITHUB_TOKEN=ghp_your_token_here"
echo "   GITHUB_WEBHOOK_SECRET=your_webhook_secret"
echo ""
echo "2. Start the webhook server:"
echo "   issue-automator automation start"
echo ""
echo "3. Configure GitHub webhook:"
echo "   URL: http://your-server:8080/webhook"
echo "   Secret: (same as GITHUB_WEBHOOK_SECRET)"
echo ""
echo "Documentation: https://github.com/ninesun666/ai-issue-automator"
echo ""
