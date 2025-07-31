#!/bin/bash

# Vietnamese AI Voice Chat System - Installation Script

echo "🇻🇳 Vietnamese AI Voice Chat System - Installation"
echo "=================================================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version detected (>= 3.8 required)"
else
    echo "❌ Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Creating template..."
    cp .env.template .env 2>/dev/null || echo "Please create .env file with your OpenAI API key"
fi

echo ""
echo "✅ Installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the system: python main.py"
echo ""
echo "🎤 Enjoy your Vietnamese AI Voice Chat!"
