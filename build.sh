#!/bin/bash
# Build script for creating Peacock executable

echo "🦚 Building Peacock Executable..."
echo "=================================="

# Check if pyinstaller is installed
if ! command -v pyinstaller &> /dev/null
then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.spec

# Build executable
echo "Building executable..."
pyinstaller --onefile \
    --name Peacock \
    --icon=peacock.ico \
    --add-data "config.example.json:." \
    peacock.py

# Create distribution package
echo "Creating distribution package..."
mkdir -p Peacock-Distribution
cp dist/Peacock* Peacock-Distribution/
cp config.example.json Peacock-Distribution/
cp README.md Peacock-Distribution/
cp LICENSE Peacock-Distribution/

echo ""
echo "✓ Build complete!"
echo "✓ Executable: dist/Peacock"
echo "✓ Distribution package: Peacock-Distribution/"
echo ""
echo "To create a ZIP for sharing:"
echo "  zip -r Peacock.zip Peacock-Distribution/"
