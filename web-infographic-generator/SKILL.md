# 网页内容信息长图生成器 v2 / Web Content Infographic Generator

深度分析网页内容并生成专业级编辑水平的信息长图，对齐36氪、极客公园、少数派专栏的品质。

Use this skill whenever the user asks to: generate an infographic, create a long-form image from a URL, analyze web content visually, produce 信息长图, or any task involving converting web articles into professional visual summaries.

## Workflow — Choose a Path Based on Available Tools

The agent itself performs the LLM analysis in all cases. Choose a path based on which tools are available.

---

### Path 1: Agent + CLI (Bash tool available)

**Step 1 — Extract raw content**

For static HTML:
```bash
web-infographic extract "<url>"
```

For JavaScript-rendered sites (SPA/React/Next.js):
```bash
web-infographic extract "<url>" --js
```
The `--js` flag uses Playwright (Chromium) to fully render the page before extraction — required for React, Next.js, Vue, and other SPA frameworks. If static extraction yields empty content, always retry with `--js`.

**Step 2 — Agent analyzes content**

The agent reads the raw content and produces structured JSON following the Content JSON Format and Editorial Principles below. Save to `/tmp/content.json`.

**Step 3 — Render**
```bash
web-infographic create --content /tmp/content.json --output ~/info_graph/result.png
```

---

### Path 2: Agent-Only (no Bash tool available)

**Step 1 — Fetch content** via the agent's web browsing / fetch capability.

**Step 2 — Agent analyzes content** → produces blocks JSON per the format below.

**Step 3 — Agent generates HTML directly** using the HTML Design Spec below, and outputs it as an artifact or file.

---

### Editorial Principles (Step 2 — all paths)

- 标题要有冲击力，能引发好奇心（15字以内）
- 每个block的文案都要重新撰写，不是简单摘抄原文
- 用中文撰写，保持专业但不晦涩
- 创造视觉节奏：大标题 → 导语 → 洞察 → 步骤 → 深入分析 → 数据 → 总结
- 总共产出 8-15 个 blocks，确保内容丰富但不冗余
- 对于英文原文，需要翻译并进行二次创作，而非直译

## Architecture

- **Rendering Engine**: HTML/CSS + Playwright full-page screenshot (780px width)
- **Content Extraction**: Python (`requests` + BeautifulSoup) for static HTML; Playwright (Node.js) for JS-rendered pages — CLI `extract` / `extract --js`
- **Content Analysis**: Always performed by the running agent's own LLM (all paths)
- **Visual Design**: Clean editorial style with green/teal accent, matching professional tech media standards
- **Typography**: Noto Sans SC (Google Fonts) for Chinese, system sans-serif for English
- **Skill Location**: `~/.claude/skills/web-infographic-generator/`
- **Playwright node_modules**: installed at skill directory level

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

## CLI Commands

```bash
# Extract raw content for the agent to analyze
web-infographic extract "<url>"                        # static HTML, stdout
web-infographic extract "<url>" --js                   # JS-rendered (SPA/React/Next.js)
web-infographic extract "<url>" --output raw.json      # static, to file
web-infographic extract "<url>" --js --output raw.json # JS-rendered, to file

# Generate infographic from agent-produced content JSON
web-infographic create --content "content.json" [--output path.png]

# Generate HTML only (for preview/debugging)
web-infographic html --content "content.json" [--output path.html]

# LEGACY: Full pipeline with external LLM API (requires AI_GATEWAY_API_KEY)
web-infographic analyze "<url>" [--output path.png]
```

## Content JSON Format

```json
{
  "meta": {
    "author": "Author / Source Name",
    "source": "https://example.com/article",
    "title": "Chinese Main Title (15 chars max)",
    "subtitle": "ENGLISH SUBTITLE",
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

## HTML Design Spec (for Path B — no CLI)

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

## Requirements (Path A only)

- Python 3.11+ with `requests`, `beautifulsoup4`, `lxml`
- Node.js with `playwright` package (installed in skill dir)
- Playwright Chromium browser (at `~/Library/Caches/ms-playwright`)

## Output

- **Fixed output directory**: `~/info_graph/` — always use this, never /tmp or other paths
- **Path 1**: PNG (780px wide, full-page) + HTML file saved alongside in same directory
- **Path 2**: HTML artifact or file saved to output directory
- Professional editorial quality matching Chinese tech media standards (36kr, GeekPark, SSPAI)
