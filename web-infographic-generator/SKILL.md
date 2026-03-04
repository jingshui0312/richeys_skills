# 网页内容信息长图生成器 v2 / Web Content Infographic Generator

深度分析网页内容并生成专业级编辑水平的信息长图，对齐36氪、极客公园、少数派专栏的品质。

Use this skill whenever the user asks to: generate an infographic, create a long-form image from a URL, analyze web content visually, produce 信息长图, or any task involving converting web articles into professional visual summaries.

## How Claude Should Use This Skill

When the user provides a URL and wants an infographic, follow this workflow:

### Step 1: Extract Content
For **static HTML sites**, the CLI can fetch directly:
```bash
web-infographic analyze "<url>" --output outputs/infographic.png
```

For **JavaScript-rendered sites** (SPA, React, etc.), use the browser tool first:
```bash
browser navigate "<url>"
browser console exec "document.querySelectorAll('h1,h2,h3,p,li,blockquote').forEach(el => { ... })"
```
Then save extracted text and run LLM analysis via Python.

### Step 2: LLM Content Analysis
The skill calls the AI Gateway API (`AI_GATEWAY_BASE_URL` + `/chat/completions`) with `gpt-4o-mini` to:
- Deeply analyze and restructure content in professional Chinese editorial voice
- Produce structured JSON with rich block types (text, insight, steps, comparison, stats, questions, list, quote, etc.)
- Create engaging headlines and concise bullet points

### Step 3: Generate HTML and Screenshot
```bash
# From analyzed JSON:
web-infographic create --content analyzed.json --output outputs/result.png

# Or just generate HTML for preview:
web-infographic html --content analyzed.json --output outputs/result.html
```

The Playwright engine renders a full-page screenshot at 780px width.

## Architecture

- **Rendering Engine**: HTML/CSS + Playwright full-page screenshot (780px width)
- **Content Analysis**: LLM-powered editorial analysis (AI Gateway API)
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
# Analyze URL and generate infographic (works for static HTML sites)
web-infographic analyze "<url>" [--output path.png]

# Generate from pre-analyzed JSON content
web-infographic create --content "content.json" [--output path.png]

# Generate HTML only (for preview/debugging)
web-infographic html --content "content.json" [--output path.html]
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

## Requirements

- Python 3.11+ with `requests`, `beautifulsoup4`, `lxml`
- Node.js with `playwright` package (installed in skill dir)
- Playwright Chromium browser (at `/ms-playwright/`)
- `AI_GATEWAY_API_KEY` and `AI_GATEWAY_BASE_URL` environment variables (required only for URL analyze mode)

## Output

- PNG image: 780px width, auto height, full-page capture
- HTML file: Also saved alongside for preview/editing
- Professional editorial quality matching Chinese tech media standards (36kr, GeekPark, SSPAI)
