#\!/bin/bash
# YouTube Infographic Generator - Install Script

echo "Installing youtube-infographic dependencies..."

# Install youtube-transcript-api
python3 -m pip install --break-system-packages youtube-transcript-api 2>/dev/null || \
python3 -m pip install youtube-transcript-api

# Install yt-dlp (optional, for video metadata)
python3 -m pip install --break-system-packages yt-dlp 2>/dev/null || \
python3 -m pip install yt-dlp

# Make CLI wrapper executable
chmod +x "$(dirname "$0")/youtube-infographic"

echo "Done\! This skill requires web-infographic-generator for rendering."
echo "Make sure web-infographic-generator is also installed."
