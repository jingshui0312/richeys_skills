# ⚡ Richey's Claude Skills

<div align="center">

```
 ██████╗ ██╗ ██████╗██╗  ██╗███████╗██╗   ██╗     ██╗     ██╗
 ██╔══██╗██║██╔════╝██║  ██║██╔════╝╚██╗ ██╔╝    ██╔╝    ██╔╝
 ██████╔╝██║██║     ███████║█████╗   ╚████╔╝    ██╔╝    ██╔╝
 ██╔══██╗██║██║     ██╔══██║██╔══╝    ╚██╔╝    ╚██╗    ╚██╗
 ██║  ██║██║╚██████╗██║  ██║███████╗   ██║      ╚██╗    ╚██╗
 ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝   ╚═╝       ╚═╝    ╚═╝
                    S K I L L S
```

**极客饭的 Claude Code 技能集**

![Claude Code](https://img.shields.io/badge/Claude_Code-Skills-orange?style=flat-square&logo=anthropic&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-18+-green?style=flat-square&logo=nodedotjs&logoColor=white)
![License](https://img.shields.io/github/license/jingshui0312/richeys_skills?style=flat-square)

</div>

---

## 什么是 Claude Skills？

> Claude Code Skills 是可复用的 AI 增强模块，让 Claude 具备特定领域的专业能力。  
> 把它理解成给 AI 装插件 —— 安装即用，开箱即战。

```bash
# 安装一个 skill
claude skill install web-infographic-generator

# 然后直接用
web-infographic analyze "https://example.com/article"
```

---

## 技能库

### 🖼️ web-infographic-generator

> 把任意网页变成一张专业信息长图

| 属性 | 值 |
|------|-----|
| 版本 | `1.0.0` |
| 语言 | Python + Node.js |
| 作者 | HappyCapy |
| 风格 | 36氪 / 极客公园 / 少数派 |

**核心能力：**

- 🔗 输入 URL → 输出专业信息长图，全自动
- 🤖 LLM 深度分析，重新撰写内容，非简单摘抄
- 🎨 多种视觉风格：科技 / 商务 / 极简 / 手绘漫画
- 📐 780px 精确排版，完美适配移动端分享
- 🇨🇳 原生中文支持，Noto Sans SC 字体

**快速体验：**

```bash
# 分析文章，生成长图
web-infographic analyze "https://sspai.com/post/xxxxx"

# 手绘风格（推荐）
web-infographic analyze "https://36kr.com/p/xxxxx" --style comic

# 从 JSON 内容生成
web-infographic create --content content.json --output result.png
```

**环境变量：**

```bash
export AI_GATEWAY_API_KEY="your-key"
export AI_GATEWAY_BASE_URL="https://your-gateway/api/v1"
```

---

### 🖼️ infographic-renderer

> 将任意内容（直接文本或 URL）渲染为专业信息长图，可独立使用也可被其他 skill 调用

| 属性 | 值 |
|------|-----|
| 版本 | `1.0.0` |
| 语言 | Python + Node.js |
| 作者 | HappyCapy |
| 风格 | 36氪 / 极客公园 / 少数派 |

**核心能力：**

- 📄 支持直接输入文本或 URL → 输出专业信息长图（PNG）
- 🧱 11 种内容 Block：段落、洞察、步骤卡、对比栏、数据展示、引用等
- 📊 **Reading Stats**：长图底部自动展示阅读统计（字符数、段落数、章节数、来源类型、完整度）
- 🎨 780px 精确排版，绿色设计风格，完美适配移动端分享
- 🤖 无 CLI 环境时，Agent 直接生成 HTML artifact（Path 2）
- 🔌 作为渲染底层供 web-infographic-generator / youtube-infographic 调用

**快速体验：**

```bash
# 从 JSON 内容生成长图（输出到当前目录）
web-infographic create --content content.json --output ./infographic.png

# 仅生成 HTML（预览/调试）
web-infographic html --content content.json --output ./infographic.html
```

> 最小可用的信息长图渲染单元，适合直接输入文本内容的场景。

---

### 🎬 youtube-infographic

> 把任意 YouTube 视频变成一张专业信息长图

| 属性 | 值 |
|------|-----|
| 版本 | `1.0.0` |
| 语言 | Python |
| 作者 | HappyCapy |
| 风格 | 36氪 / 极客公园 / 少数派 |
| 依赖 | web-infographic-generator（渲染层） |

**核心能力：**

- 🎥 输入 YouTube URL → 自动提取字幕 + 视频元数据
- 🤖 Claude 深度分析字幕，翻译并二次创作（非直译）
- 📊 支持长视频（自动截取关键内容，节省 token）
- 🌐 优先抓取中文字幕，回退英文字幕
- 📐 复用 web-infographic-generator 渲染，780px 专业排版

**快速体验：**

```bash
# 标准模式（生产使用，抓取 4000 字符字幕）
youtube-infographic "https://www.youtube.com/watch?v=xxxxx"

# 省 token 模式（测试用，仅 1500 字符）
youtube-infographic "https://youtu.be/xxxxx" --brief

# 仅元数据（最快，跳过字幕）
youtube-infographic "https://youtu.be/xxxxx" --no-transcript
```

**依赖安装：**

```bash
pip install youtube-transcript-api yt-dlp
```

> ⚠️ 需先安装 `web-infographic-generator`，渲染层由其提供。

---

### 📓 obsidian-manager

> 对话式管理 Obsidian 知识库——写日记、记想法、搜笔记，全程不离开 Claude

| 属性 | 值 |
|------|-----|
| 版本 | `1.0.0` |
| 语言 | Python（纯标准库） |
| 触发词 | 写日记 / 记一下 / 搜笔记 / 投到 Inbox / 整理 Inbox |
| 依赖 | 无（Python 自带） |

**核心能力：**

- 📅 日记管理：自动从模板创建今日日记，追加内容到指定 section
- 📥 Inbox 快速投递：一句话把想法存入 Inbox，自动命名
- 📝 笔记 CRUD：创建、读取、编辑、追加 Daily / Inbox / Study / Resource
- 🔍 全文搜索：标题 + 正文搜索，返回上下文片段
- ☁️ iCloud 透明同步：文件写入后自动同步到所有设备

**触发示例：**

```
写日记
记一下：今天完成了 obsidian-manager 的开发
把这段话投到 Inbox，先存着
搜一下关于「异步编程」的笔记
整理一下 Inbox
```

**CLI 用法：**

```bash
TOOL=~/.claude/skills/obsidian-manager/obsidian-tool

$TOOL daily today --create                                        # 创建今日日记
$TOOL daily today --append "内容" --section "今天发生了什么"       # 追加到 section
$TOOL inbox --add "一个新想法"                                    # 快速投递 Inbox
$TOOL inbox --list                                                # 查看 Inbox
$TOOL search "关键词" --limit 10                                  # 全文搜索
$TOOL list --folder Daily --recent 7                              # 最近 7 篇日记
```

---

### 🎬 youtube-subtitle-collage

> 从 YouTube 视频提取真实字幕，截取对应视频帧，叠加中文大字，拼成长图

| 属性 | 值 |
|------|-----|
| 版本 | `2.0.0` |
| 语言 | Python + Pillow |
| 作者 | HappyCapy |

**核心能力：**

- 🎞️ 输入 YouTube URL → 自动提取字幕 + 截取真实视频帧（无需下载视频）
- 🎯 支持主题引导选片：输入"截出人生启发相关的内容"，Claude 按主题筛选金句
- 🖼️ 第一张保留完整 16:9 视频帧，后续条带紧凑拼接，字幕叠加于底部
- 📡 利用 YouTube Storyboard 技术，直接从 CDN 获取缩略图，无 IP 封锁问题
- 🀄 原生中文支持，PingFang / Noto Sans CJK 字体自动检测

**触发示例：**

```
帮我把这个视频做成字幕拼接图：https://www.youtube.com/watch?v=xxxxx
截出这个视频里关于「创业失败」的内容：https://youtu.be/xxxxx
```

**依赖安装：**

```bash
cd youtube-subtitle-collage && bash install.sh
# 依赖：python3, yt-dlp, Pillow, Chrome（cookies 认证）
```

---

### 🦞 openclaw

> 敬请期待...

---

## 安装方法

```bash
# 克隆仓库
git clone https://github.com/jingshui0312/richeys_skills.git
cd richeys_skills

# 安装指定 skill
cd web-infographic-generator && bash install.sh
cd youtube-infographic && bash install.sh
cd youtube-subtitle-collage && bash install.sh
cd obsidian-manager && bash install.sh
cd infographic-renderer && bash install.sh
```

或者直接复制到 Claude Skills 目录：

```bash
cp -r web-infographic-generator ~/.claude/skills/
cp -r youtube-infographic ~/.claude/skills/
cp -r youtube-subtitle-collage ~/.claude/skills/
cp -r obsidian-manager ~/.claude/skills/
cp -r infographic-renderer ~/.claude/skills/
```

---

## 目录结构

```
richeys_skills/
├── web-infographic-generator/   # 网页信息长图生成器
│   ├── skill.json               # Skill 元数据
│   ├── SKILL.md                 # Claude 使用说明
│   ├── web-infographic          # CLI 入口
│   ├── install.sh               # 安装脚本
│   ├── requirements.txt         # Python 依赖
│   └── scripts/
│       ├── web_infographic.py   # 主程序
│       └── screenshot.mjs       # Playwright 截图引擎
├── infographic-renderer/        # 信息长图渲染器（支持文本/URL，含阅读统计）
│   ├── skill.json               # Skill 元数据
│   ├── SKILL.md                 # Claude 使用说明
│   ├── web-infographic          # CLI 入口
│   ├── install.sh               # 安装脚本
│   ├── requirements.txt         # Python 依赖
│   └── scripts/
│       ├── web_infographic.py   # HTML 生成引擎
│       └── screenshot.mjs       # Playwright 截图引擎
├── youtube-infographic/         # YouTube 视频信息长图生成器
│   ├── skill.json               # Skill 元数据
│   ├── SKILL.md                 # Claude 使用说明
│   ├── youtube-infographic      # CLI 入口
│   ├── install.sh               # 安装脚本
│   └── scripts/
│       └── youtube_extract.py   # YouTube 内容提取器
├── youtube-subtitle-collage/    # YouTube 字幕拼接图生成器
│   ├── skill.json               # Skill 元数据
│   ├── SKILL.md                 # Claude 使用说明
│   ├── youtube-subtitle-collage # CLI 入口
│   ├── install.sh               # 安装脚本
│   └── scripts/
│       ├── extract_segments.py  # 字幕提取（均匀采样全视频）
│       └── render_frames.py     # Storyboard 截帧 + Pillow 合成
├── obsidian-manager/            # Obsidian 知识库管理器
│   ├── skill.json               # Skill 元数据
│   ├── SKILL.md                 # Claude 使用说明
│   ├── obsidian-tool            # CLI 入口
│   ├── install.sh               # 安装脚本
│   ├── README.md                # 详细使用文档
│   └── scripts/
│       └── obsidian_tool.py     # 核心实现（纯标准库）
└── openclaw/                    # 🚧 建设中
```

---

<div align="center">

**Made by 极客饭 · Powered by Claude Code**

*工具是死的，用工具的人是活的*

</div>
