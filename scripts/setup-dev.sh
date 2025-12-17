#!/bin/bash
# Setup script for dev-tools environment

echo "🛠️  Setting up Music Review App development tools..."

# Check if virtualenvwrapper is available
if ! command -v mkvirtualenv &> /dev/null; then
    echo "❌ virtualenvwrapper not found. Please install it first:"
    echo "   pip install virtualenvwrapper"
    echo "   Add to ~/.bashrc: source /usr/local/bin/virtualenvwrapper.sh"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$HOME/.virtualenvs/music_review_devtools" ]; then
    echo "📦 Creating virtual environment: music_review_devtools"
    mkvirtualenv music_review_devtools
else
    echo "✅ Virtual environment already exists: music_review_devtools"
fi

# Activate environment and install dependencies
echo "📥 Installing dependencies..."
workon music_review_devtools
pip install -r dev-tools/requirements.txt

echo "✅ Dev-tools setup completed!"
echo ""
echo "🚀 To use the development environment:"
echo "   workon music_review_devtools"
echo "   cd dev-tools/"
echo "   python test_rabbitmq.py"