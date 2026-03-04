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
```

或者直接复制到 Claude Skills 目录：

```bash
cp -r web-infographic-generator ~/.claude/skills/
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
└── openclaw/                    # 🚧 建设中
```

---

<div align="center">

**Made by 极客饭 · Powered by Claude Code**

*工具是死的，用工具的人是活的*

</div>
