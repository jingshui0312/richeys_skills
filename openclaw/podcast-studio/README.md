# Podcast Studio Skill

播客工作室 - 完整的播客制作流程。

## ⚠️ 重要说明

本 Skill 已移除所有敏感信息（API Key、Token 等）。使用前需要配置以下环境变量：

### 必需的环境变量

```bash
# LLM API（用于脚本生成）
export OPENAI_API_KEY="your_api_key_here"

# MiniMax TTS（用于语音合成）
export MINIMAX_API_KEY="your_minimax_key"
export MINIMAX_GROUP_ID="your_group_id"

# 火山引擎 TOS（用于音频上传）
export TOS_ACCESS_KEY="your_access_key"
export TOS_SECRET_KEY="your_secret_key"

# Notion（可选，用于上传播客元数据）
export NOTION_API_KEY="secret_xxx"
export NOTION_PODCAST_DATABASE_ID="your_database_id"
```

## 功能

1. **智能脚本生成** - AI 驱动的播客脚本创作
2. **多风格支持** - 信息类、对话类、叙事类、技术类
3. **高质量音频** - MiniMax TTS 语音合成
4. **背景音乐** - 自动混音，支持自定义 BGM
5. **云端上传** - 自动上传到火山引擎 TOS
6. **Notion 集成** - 播客元数据自动同步

## 安装

```bash
# 1. 克隆到 OpenClaw skills 目录
cd /path/to/openclaw/skills
git clone https://github.com/jingshui0312/richeys_skills.git
ln -s richeys_skills/openclaw/podcast-studio .

# 2. 安装依赖
cd podcast-studio
pip3 install -r requirements.txt

# 3. 配置环境变量
# 编辑 ~/.bashrc 或 ~/.zshrc，添加上述环境变量

# 4. 测试
python3 scripts/podcast_studio.py --help
```

## 使用方法

```bash
# 创建播客（仅生成脚本）
python3 scripts/podcast_studio.py create "人工智能的发展趋势" --check-only

# 生成音频
python3 scripts/podcast_studio.py generate-audio script.json

# 完整流程（脚本 + 音频 + 上传）
python3 scripts/podcast_studio.py create "AI 热点" --upload
```

## 文件结构

```
podcast-studio/
├── scripts/
│   ├── podcast_studio.py       # 主脚本
│   ├── script_generator.py     # 脚本生成器
│   ├── upload_to_notion.py     # Notion 上传
│   └── ai_hotspot_podcast.py   # AI 热点播客
├── assets/
│   └── bgm_default.mp3         # 默认背景音乐
├── config.json                 # 配置文件
└── SKILL.md                    # 完整文档
```

## 文档

- [完整使用指南](USAGE_GUIDE.md)
- [SKILL.md](SKILL.md) - 详细 API 文档
- [Notion 集成](NOTION_INTEGRATION.md)
- [更新日志](UPDATE_2026-02-11.md)

## 许可证

MIT

## 作者

moss @ OpenClaw
