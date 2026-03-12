#!/bin/bash
# Install script for youtube-subtitle-collage skill

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing youtube-subtitle-collage skill..."

# Make CLI executable
chmod +x "$SKILL_DIR/youtube-subtitle-collage"

# Install Python dependencies
echo "Installing Python packages..."
python3 -m pip install -q --break-system-packages youtube-transcript-api 2>/dev/null || \
python3 -m pip install -q youtube-transcript-api 2>/dev/null || true

# Optional: yt-dlp for richer metadata
python3 -m pip install -q --break-system-packages yt-dlp 2>/dev/null || \
python3 -m pip install -q yt-dlp 2>/dev/null || true

# Install Node.js + Playwright
if command -v node &>/dev/null; then
    echo "Installing Playwright..."
    cd "$SKILL_DIR"
    if [ ! -f package.json ]; then
        echo '{"name":"youtube-subtitle-collage","type":"module","private":true}' > package.json
    fi
    npm install --save playwright 2>/dev/null || true
    node -e "const { chromium } = require('playwright'); chromium.launch().then(b => b.close());" 2>/dev/null || \
    npx playwright install chromium 2>/dev/null || true
else
    echo "Warning: Node.js not found. Install Node.js to enable PNG rendering."
fi

echo "Installation complete."
