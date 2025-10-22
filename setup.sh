#!/bin/bash

echo "================================================"
echo "AI Podcast Generator - Setup Script"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check ffmpeg
echo ""
echo "Checking ffmpeg..."
ffmpeg -version > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "Warning: ffmpeg is not installed."
    echo "Audio processing requires ffmpeg."
    echo ""
    echo "Install with:"
    echo "  macOS:   brew install ffmpeg"
    echo "  Ubuntu:  sudo apt-get install ffmpeg"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit backend/.env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - SPEECHMATICS_API_KEY"
    echo ""
fi

# Create output directory
cd ..
mkdir -p output

echo ""
echo "================================================"
echo "Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Run: cd backend && python app.py"
echo "4. Open: http://localhost:5000"
echo ""
