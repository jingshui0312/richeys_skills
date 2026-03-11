#!/bin/bash
# Installation script for github-manager skill

echo "Installing github-manager skill..."

# Verify gh CLI is available
if command -v gh &>/dev/null; then
    echo "✓ gh CLI: $(gh --version | head -1)"
else
    echo "✗ gh CLI not found. Please install it first:"
    echo "  macOS:  brew install gh"
    echo "  Linux:  sudo apt install gh  (or see https://cli.github.com)"
    exit 1
fi

# Check authentication status
if gh auth status &>/dev/null; then
    echo "✓ GitHub authentication: already logged in"
else
    echo "⚠ GitHub not authenticated. Set your token before use:"
    echo "  export GITHUB_TOKEN=your_token_here"
    echo "  Or run: gh auth login"
fi

echo ""
echo "✓ Installation complete!"
echo ""
echo "Usage:"
echo "  Ask Claude to interact with any GitHub repo, e.g.:"
echo "  \"帮我查看 owner/repo 的仓库信息\""
echo "  \"列出 owner/repo 最近的 Issues\""
echo "  \"帮我在 owner/repo 创建一个 PR\""
