---
name: infographic-renderer
version: 1.0.0
description: Generate professional long-form infographic images from structured content. Matches the editorial quality of 36kr, GeekPark, and SSPAI.
author: HappyCapy
tags:
  - infographic
  - image-generation
  - visualization
---

# 信息长图渲染器 / Infographic Renderer

将结构化内容 JSON 渲染为专业级信息长图（PNG），品质对标 36氪、极客公园、少数派专栏。

**Scope: direct content input only — NOT for URLs.**

Use this skill when the user provides content directly: pasted article text, a transcript, a document, notes, or any in-conversation text that should be turned into an infographic. Do NOT use this skill when the user provides a URL — use `web-infographic-generator` instead.

## Workflow — Choose a Path Based on Available Tools

---

### Path 1: Agent + CLI (Bash tool available)

**Step 1 — Agent analyzes source content**

The agent reads the user's provided content (article text, URL content, video transcript, etc.) and produces structured JSON following the Content JSON Format and Editorial Principles below. Save to `/tmp/content.json`.

**Step 2 — Render to PNG**
```bash
web-infographic create --content /tmp/content.json --output ~/info_graph/result.png
```

**Generate HTML only (for preview/debugging):**
```bash
web-infographic html --content /tmp/content.json --output ~/info_graph/result.html
```

---

### Path 2: Agent-Only (no Bash tool available)

**Step 1 — Agent analyzes content** → produces blocks JSON per the format below.

**Step 2 — Agent generates HTML directly** using the HTML Design Spec below, and outputs it as an artifact or file.

---

### Editorial Principles (Step 1 — all paths)

- 标题要有冲击力，能引发好奇心（15字以内）
- 每个 block 的文案都要重新撰写，不是简单摘抄原文
- 用中文撰写，保持专业但不晦涩
- 创造视觉节奏：大标题 → 导语 → 洞察 → 步骤 → 深入分析 → 数据 → 总结
- 总共产出 8-15 个 blocks，确保内容丰富但不冗余
- 对于英文原文，需要翻译并进行二次创作，而非直译

## Content Block Types

| Block Type | Description | Visual |
|-----------|-------------|--------|
| `text` | Body paragraph | Regular text |
| `insight` | Key insight box | Green background, white text |
| `steps` | Numbered step cards | Grid of cards with numbered circles |
| `section` | Content section with heading | Heading + bullet points |
| `comparison` | Two-column comparison | Side-by-side cards |
| `questions` | Key questions | Yellow background, red bullets |
| `stats` | Data highlights | Large numbers display |
| `list` | Numbered list | Action items with green numbers |
| `quote` | Quote/conclusion | Green background with quote marks |
| `highlight` | Highlighted text | Light green background |
| `divider` | Visual separator | Horizontal line |

## Content JSON Format

```json
{
  "meta": {
    "author": "Author / Source Name",
    "source": "https://example.com/article",
    "title": "Chinese Main Title (15 chars max)",
    "subtitle": "ENGLISH SUBTITLE IN CAPS",
    "description": "One-line description"
  },
  "blocks": [
    {"type": "text", "content": "Introduction paragraph..."},
    {"type": "insight", "label": "核心洞察", "content": "Key insight text..."},
    {"type": "steps", "title": "Section Title", "items": [
      {"number": 1, "title": "Step Name", "subtitle": "Brief desc", "points": ["Point 1", "Point 2"]}
    ]},
    {"type": "section", "title": "Heading", "content": "Lead text", "points": ["Point 1"]},
    {"type": "comparison", "columns": [
      {"title": "Column A", "subtitle": "Sub", "points": ["Point 1"]},
      {"title": "Column B", "subtitle": "Sub", "points": ["Point 1"]}
    ]},
    {"type": "questions", "title": "Key Questions", "icon": "red", "items": ["Question 1?"]},
    {"type": "stats", "items": [{"value": "90%", "label": "Description"}]},
    {"type": "list", "title": "Action Items", "items": ["Item 1", "Item 2"]},
    {"type": "quote", "content": "Powerful closing statement", "source": "Attribution"}
  ]
}
```

## CLI Commands (Path 1 only)

```bash
# Render JSON to PNG (780px wide, full-page)
web-infographic create --content content.json [--output path.png]

# Generate HTML only (for preview or manual screenshot)
web-infographic html --content content.json [--output path.html]
```

## HTML Design Spec (for Path 2 — no CLI)

When generating HTML directly, use these design tokens and structure:

**Page:** 780px wide, white background, `font-family: 'Noto Sans SC', sans-serif`, load from Google Fonts.

**Colors:**
- Accent: `#1a9a6b` (green) — used for headings, bullets, numbers, insight/quote backgrounds
- Accent light: `#e8f5ee` — highlight block background
- Yellow bg: `#fef9e7`, border `#f0d858` — questions block
- Red: `#e74c3c` — question bullets

**Block HTML patterns** (container `<div class="container">` with `padding: 48px 50px`):

- `text` → `<div class="block-text"><p>…</p></div>`
- `insight` → green background div, white text, label + content
- `steps` → CSS grid of cards, each with numbered circle (accent bg), title, subtitle, bullet list
- `section` → heading with 2px accent bottom border + bullet list with `▸` prefix
- `comparison` → 2-column CSS grid, each column in `#f8fafb` card
- `questions` → yellow bg, left 4px accent border, `❓` icon, red `●` bullets
- `stats` → yellow bg, large font (36px 900 weight) values in grid
- `list` → numbered items with accent-colored numbers
- `quote` → green background, `❝` mark, white text
- `divider` → `<hr>` with `#e8e8e8` color

Footer: source URL in accent color, separated by `1px #eee` top border.

## Architecture

- **Rendering Engine**: HTML/CSS + Playwright full-page screenshot (780px width)
- **Content Analysis**: Always performed by the running agent's own LLM
- **Visual Design**: Clean editorial style with green/teal accent
- **Typography**: Noto Sans SC (Google Fonts) for Chinese, system sans-serif for English

## Requirements (Path 1 only)

- Python 3.11+
- Node.js with `playwright` package (auto-installed on first run)
- Playwright Chromium browser

## Output

- **Fixed output directory**: `~/info_graph/` — always use this path
- **Path 1**: PNG (780px wide, full-page) + HTML file saved alongside
- **Path 2**: HTML artifact or file
