#!/bin/bash
# Installation script for web-infographic-generator skill

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing web-infographic-generator skill..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q --break-system-packages -r "$SCRIPT_DIR/requirements.txt" 2>&1 | grep -v "externally-managed-environment" || true

# Make scripts executable
chmod +x "$SCRIPT_DIR/web-infographic"
chmod +x "$SCRIPT_DIR/scripts/web_infographic.py"

echo "✓ Installation complete!"
echo ""
echo "Usage: web-infographic analyze <url> [--style tech|business|minimal|creative]"
echo "Example: web-infographic analyze https://example.com/article --style tech"
