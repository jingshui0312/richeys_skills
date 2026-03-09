#!/bin/bash
# Installation script for obsidian-manager skill

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_PATH="/Users/richey.li/Library/Mobile Documents/iCloud~md~obsidian/Documents/我的个人知识库"

echo "Installing obsidian-manager skill..."

# Make scripts executable
chmod +x "$SCRIPT_DIR/obsidian-tool"
chmod +x "$SCRIPT_DIR/scripts/obsidian_tool.py"

# Verify vault path
if [ -d "$VAULT_PATH" ]; then
    echo "✓ Vault found at: $VAULT_PATH"
    echo "  Folders: $(ls "$VAULT_PATH" | tr '\n' ' ')"
else
    echo "✗ Vault not found at: $VAULT_PATH"
    echo "  Please ensure iCloud is synced and Obsidian vault path is correct."
    exit 1
fi

# Verify python3
if command -v python3 &>/dev/null; then
    echo "✓ Python3: $(python3 --version)"
else
    echo "✗ python3 not found. Please install Python 3."
    exit 1
fi

echo ""
echo "✓ Installation complete! Pure stdlib, no pip needed."
echo ""
echo "Usage:"
echo "  obsidian-tool daily today --create"
echo "  obsidian-tool daily today --append \"今天完成了项目部署\" --section \"今天发生了什么\""
echo "  obsidian-tool inbox --add \"有个想法需要记下来\""
echo "  obsidian-tool inbox --list"
echo "  obsidian-tool create \"Python 学习笔记\" --folder Study"
echo "  obsidian-tool search \"关键词\" --limit 10"
echo "  obsidian-tool list --folder Daily --recent 7"
