#!/bin/bash
# Quick setup script for sales-qualifier

echo "🚀 Setting up Sales Lead Qualifier..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
else
    echo "✅ .env file already exists"
fi

# Create output directory
mkdir -p output

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. (Optional) Add RAPIDAPI_KEY for real LinkedIn scraping"
echo "3. Run: python main.py"
echo ""
echo "To activate the virtual environment later:"
echo "  source venv/bin/activate"
