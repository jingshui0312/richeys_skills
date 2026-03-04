# Podcast Studio Skill

播客工作室 - 完整的播客制作流程。支持智能脚本生成、高质量音频合成、背景音乐混音、云端上传和 Notion 集成。

## ⚠️ 重要说明

本 Skill 已移除所有敏感信息（API Key、Token、密钥等）。使用前需要配置以下环境变量：

### 必需的环境变量

```bash
# LLM API（用于脚本生成）
export OPENAI_API_KEY="your_api_key_here"
# 或者使用智谱 AI
export ZAI_API_KEY="your_zai_key"

# MiniMax TTS（用于语音合成）
export MINIMAX_API_KEY="your_minimax_key"
export MINIMAX_GROUP_ID="your_group_id"

# 火山引擎 TOS（用于音频上传）
export TOS_ACCESS_KEY="your_access_key"
export TOS_SECRET_KEY="your_secret_key"
export TOS_REGION="cn-beijing"
export TOS_ENDPOINT="tos-cn-beijing.volces.com"

# Notion（可选，用于上传播客元数据）
export NOTION_API_KEY="secret_xxx"
export NOTION_PODCAST_DATABASE_ID="your_database_id"
# 或者使用 Parent Page ID
export NOTION_PARENT_PAGE_ID="your_page_id"
```

## 功能特性

### 🎯 核心功能

1. **智能脚本生成** - AI 驱动的播客脚本创作
2. **多风格支持** - 信息类、对话类、叙事类、技术类
3. **高质量音频** - MiniMax TTS 语音合成（多种声音可选）
4. **背景音乐** - 自动混音，支持自定义 BGM
5. **云端上传** - 自动上传到火山引擎 TOS
6. **Notion 集成** - 播客元数据自动同步

### 🎨 播客风格

- **conversational** - 对话类（主持人互动风格）
- **narrative** - 叙事类（故事讲述风格）
- **tech** - 技术类（技术深度解析）
- **informational** - 信息类（新闻资讯风格）

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

# 4. 配置 config.json
cp config.json.example config.json
# 编辑 config.json，设置你的偏好

# 5. 测试
python3 scripts/podcast_studio.py --help
```

## 使用方法

### 基础用法

```bash
# 创建播客（仅生成脚本）
python3 scripts/podcast_studio.py create "人工智能的发展趋势" --check-only

# 生成音频
python3 scripts/podcast_studio.py generate-audio script.json

# 完整流程（脚本 + 音频 + 上传）
python3 scripts/podcast_studio.py create "AI 热点" --upload

# 指定风格和时长
python3 scripts/podcast_studio.py create "区块链技术" --style tech --duration medium
```

### 高级用法

```bash
# 使用自定义配置
python3 scripts/podcast_studio.py create "主题" --config ~/.podcast_config.json

# 禁用背景音乐
python3 scripts/podcast_studio.py create "主题" --no-bgm

# 禁用脚本优化
python3 scripts/podcast_studio.py create "主题" --no-optimize

# 指定输出目录
python3 scripts/podcast_studio.py create "主题" --output /path/to/output
```

### AI 热点播客

```bash
# 自动搜索 AI 热点并生成播客
python3 scripts/ai_hotspot_podcast.py

# 查看帮助
python3 scripts/ai_hotspot_podcast.py --help
```

## 配置文件

`config.json` 示例：

```json
{
  "tos_bucket": "YOUR_TOS_BUCKET_NAME",
  "default_voice": "male-qn-qingse",
  "default_speed": 1.1,
  "default_vol": 1.0,
  "output_format": "mp3",
  "bgm_file": "assets/bgm_default.mp3",
  "bgm_volume": 0.15,
  "bgm_enabled_by_default": true,
  "upload_to_notion": true,
  "notion_database_id_env": "NOTION_PODCAST_DATABASE_ID",
  "llm": {
    "provider": "zai",
    "base_url": "https://open.bigmodel.cn/api/coding/paas/v4",
    "model": "glm-4.7",
    "api_key_env": "OPENAI_API_KEY",
    "max_tokens": 4000,
    "temperature": 0.8,
    "timeout": 180
  }
}
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
├── README.md                   # 本文件
└── SKILL.md                    # 完整文档
```

## 文档

- [README.md](README.md) - 快速开始（本文件）
- [SKILL.md](SKILL.md) - 详细 API 文档
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - 使用指南
- [NOTION_INTEGRATION.md](NOTION_INTEGRATION.md) - Notion 集成
- [UPDATE_2026-02-11.md](UPDATE_2026-02-11.md) - 更新日志

## 依赖服务

### 必需

- **LLM API**：OpenAI 或智谱 AI（用于脚本生成）
- **MiniMax TTS**：语音合成服务

### 可选

- **火山引擎 TOS**：对象存储服务（用于音频上传）
- **Notion API**：元数据管理

## 常见问题

### Q: 如何更换背景音乐？

```bash
cp your_bgm.mp3 assets/bgm_default.mp3
```

### Q: 如何调整语音速度？

编辑 `config.json`，修改 `default_speed`（0.5-2.0，默认 1.1）

### Q: 如何更换 LLM 提供商？

编辑 `config.json`，修改 `llm` 配置：

```json
{
  "llm": {
    "provider": "openai",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4",
    "api_key_env": "OPENAI_API_KEY"
  }
}
```

## 许可证

MIT

## 作者

moss @ OpenClaw

## 更新日志

- 2026-02-28：添加 Notion 集成，优化音频质量
- 2026-02-11：支持多种播客风格，添加背景音乐
- 2026-02-03：初始版本
