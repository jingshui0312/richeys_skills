#!/bin/bash
# Install script for youtube-subtitle-collage skill

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing youtube-subtitle-collage skill..."

# Make CLI executable
chmod +x "$SKILL_DIR/youtube-subtitle-collage"

# Install Python dependencies
echo "Installing Python packages..."
python3 -m pip install -q --break-system-packages \
    youtube-transcript-api \
    yt-dlp \
    Pillow 2>/dev/null || \
python3 -m pip install -q \
    youtube-transcript-api \
    yt-dlp \
    Pillow 2>/dev/null || true

# Check ffmpeg (required for frame extraction)
if command -v ffmpeg &>/dev/null; then
    echo "ffmpeg: $(ffmpeg -version 2>&1 | head -1)"
else
    echo ""
    echo "⚠️  ffmpeg not found. Install it for video frame extraction:"
    echo "   macOS:  brew install ffmpeg"
    echo "   Ubuntu: sudo apt install ffmpeg"
    echo ""
    echo "   Without ffmpeg, 'create' will use dark fallback strips."
fi

# Install Node.js + Playwright (for legacy 'html' command)
if command -v node &>/dev/null; then
    echo "Installing Playwright (for html command)..."
    cd "$SKILL_DIR"
    if [ ! -f package.json ]; then
        echo '{"name":"youtube-subtitle-collage","type":"module","private":true}' > package.json
    fi
    npm install --save playwright 2>/dev/null || true
    npx playwright install chromium 2>/dev/null || true
else
    echo "Note: Node.js not found. The 'html' command will not be available."
fi

echo "Installation complete."
