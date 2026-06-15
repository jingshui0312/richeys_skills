---
name: infographic-renderer-v2
version: 2.0.0
description: 高密度信息长图渲染器 v2。在原版基础上增加信息密度最大化的编排原则、内容模板和密度检查清单，提升单张长图的信息承载量而不牺牲可读性。
author: HappyCapy + 虾丸增强
tags:
  - infographic
  - image-generation
  - visualization
  - density-optimized
---

# 信息长图渲染器 v2 — 高密度增强版

将结构化内容 JSON 渲染为专业级信息长图（PNG），品质对标 36氪、极客公园、少数派专栏。
**v2 增强核心：在保持可读性的前提下，最大化单张长图的信息密度。**

Use this skill whenever the user asks to: generate an infographic from content, create a long-form image, render a visual summary, produce 信息长图, or convert structured content into a professional image.

---

## ⚡ v2 核心变化

| 维度 | v1 原版 | v2 增强 |
|------|---------|---------|
| 信息密度 | 8-15 个 blocks，混合使用 | 12-20 个 blocks，密集编排 |
| 内容模板 | 无 | 5 种分析模板（见下文） |
| 编排策略 | 通用视觉节奏 | 有明确的目标导向策略 |
| 质量检查 | 无 | 密度检查清单（强制） |
| STATS 块使用 | 1-2 处 | 可多处出现，穿插佐证论点 |
| COMPARISON 使用 | 可选 | 分析类内容强制使用 |

---

## Content Completeness (Mandatory — all paths)

⚠️ **必须先确保内容完整，再开始制作信息长图。**

### 内容源优先级（从 URL/视频获取内容时）

按以下优先级选择内容获取方式，确保拿到完整内容：

1. **YouTube 视频** → 优先使用 `yt-dlp` 下载字幕（`--write-auto-sub --sub-lang en --skip-download`），再提取纯文本。这是获取完整视频内容最可靠的方式
2. **有全文的文章页面** → `web_fetch` 抓取，`maxChars` 设为 **100,000**（默认 50K 对长文不够）
3. **截断时的降级方案**：
   - 先尝试增大 `maxChars` 重新抓取
   - 再尝试从其他源（如 podscripts.co、翻译站）获取全文
   - 对于播客/长视频，最终降级到 `yt-dlp` 字幕
4. **禁止在内容截断时直接生成信息长图** — 必须拿到完整内容后再做

### 从 URL 抓取内容时（补充流程）

1. `web_fetch` 的 `maxChars` 设为 **100,000**（长文和播客文稿通常超过 50K）
2. 检查返回结果的 `truncated` 字段：
   - `truncated: false` → 内容完整，继续
   - `truncated: true` → **内容被截断！** 按上述降级方案处理
3. **完整性验证**：对比原文目录/章节列表，确认所有章节都包含在抓取内容中
4. 仅在确认内容完整后，才进入 Step 1 生成结构化 JSON

### 从用户直接提供文本时

检查文本长度是否与预期匹配，是否有明显的截断迹象（如句子未完结、章节不完整）。

---

## Reading Stats（强制 — 所有路径）

⚠️ **生成的 content.json 必须包含 `reading_stats` 字段**，在长图底部展示阅读统计，让用户了解内容覆盖度。

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `chars` | number | 实际阅读的字符数 |
| `paragraphs` | number | 阅读的段落数 |
| `sections` | number | 覆盖的章节数 |
| `source_type` | string | 来源类型（如"文章全文"、"播客文字稿"、"播客介绍页"、"视频字幕"等） |
| `completeness` | string | 完整度描述（如"全文"、"概要"、"节选"、"截断"） |

### 规则
- **诚实标注**：如果只读了摘要/介绍页，`completeness` 必须写"概要"，不能写"全文"
- 所有字段都是可选的，但至少应包含 `chars`、`source_type` 和 `completeness`
- Agent 在 Step 1 生成 content.json 时，必须根据实际抓取情况填写这些数据

---

## Workflow — Choose a Path Based on Available Tools

---

### Path 1: Agent + CLI (Bash tool available)

**Step 1 — Agent analyzes source content**

The agent reads the user's provided content (article text, URL content, video transcript, etc.) and produces structured JSON following the Content JSON Format and Editorial Principles below. Save to `/tmp/content.json`.

**⚠️ v2 强制步骤**：JSON 生成后，必须运行「密度检查清单」（见下文）自检，通过后方可渲染。

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

## 📐 信息密度最大化原则（v2 核心）

以下原则在生成 content.json 时必须遵守：

### 原则一：多样性优先

视觉疲劳来自"重复"。连续出现同类型 block 超过 2 次，立即降低可读性。

**规则：**
- ❌ 不要连续 3 个 `section` 块排在一起
- ❌ 不要连续 2 个 `text` 块
- ✅ 在 `section`（列表）之后插入 `stats`（数据）或 `insight`（洞察）
- ✅ 在 `comparison`（对比）之后插入 `quote`（引文）收尾
- ✅ `divider` 块必须谨慎使用，每张长图不超过 1 次

### 原则二：数据密度法则

**每 3 个非数据块至少搭配 1 个数据块**（`stats` / `comparison` 中的数字 / `section` 中的具体数值）。

规则：
- `stats` 块可以出现多次（v1 限制为 1-2 处，v2 放宽）
- 每个 `section` 的 `points` 列表中，至少有一半的 point 包含具体数字、百分比或时间
- 避免空洞的定性描述（"表现优异""显著提升"），必须附上证据

### 原则三：叙事节奏 VS 信息密度

密度不是堆砌，是"疏密有致"：

| 阶段 | 目标 | 推荐 Block 组合 |
|------|------|----------------|
| 开头钩子 | 高冲击力快速抓住注意力 | `insight` + `stats`（3-4 个关键数字） |
| 展开分析 | 逻辑清晰，信息量大 | `section` + `comparison` + `stats` 交替 |
| 高潮推进 | 最强论证 | `comparison`（左右对比）+ `quote`（引文佐证） |
| 收尾落点 | 余音绕梁 | `quote`（金句收尾）或 `insight`（未来判断） |

### 原则四：无空话条款

每个 block 的内容必须满足以下至少两项：
- 包含具体数据（数字、比例、时间）
- 包含可操作的判断（不是"值得关注"，而是"它能不能成，看三件事"）
- 包含对比（VS 谁、比之前如何、差距多少）

---

## 📋 v2 密度检查清单（强制）

在生成 content.json 后、渲染之前，逐项检查：

```
□ 1. blocks 总数是否在 12-20 之间？（低于 12 密度不足）
□ 2. 是否至少包含 2 个 stats 块？（v2 强制要求多处数据）
□ 3. 分析/对比类内容是否有 comparison 块？（v2 强制要求）
□ 4. 是否至少 1 个 quote 块用于收尾？
□ 5. 是否有连续 3 个相同类型 block？（禁止）
□ 6. 每个 section 的 points 中至少一半含具体数字？
□ 7. 标题是否 ≤ 15 字且有力？
□ 8. 是否有 insight 块作为开篇钩子？
□ 9. 阅读量较大的内容是否有 divider？（最多 1 个）
□ 10. 整体是否形成了"钩子→展开→高潮→收尾"的节奏？
```

**全部通过 → 渲染。有未通过的 → 必须修改内容后再渲染。**

---

## 📋 内容模板模式

根据内容类型选择最合适的模板，填充 blocks 序列。

### 模板 A：公司/产品深度分析（如 OpenRouter 拆解）

适用场景：创业公司分析、产品技术拆解、商业模式研究。

```json
{
  "blocks": [
    {"type": "insight", "label": "一句话定位", "content": "……"},
    {"type": "stats", "items": [{"value": "...", "label": "..."}, ...]},
    {"type": "section", "title": "壁垒一：……", "points": ["数据1", "数据2", "判断1", "判断2"]},
    {"type": "section", "title": "壁垒二：……", "points": ["..."]},
    {"type": "stats", "items": [{"value": "...", "label": "..."}]},  // 中间穿插数据
    {"type": "section", "title": "壁垒三：……", "points": ["..."]},
    {"type": "comparison", "columns": [
      {"title": "核心壁垒", "points": ["...", "..."]},
      {"title": "核心风险", "points": ["...", "..."]}
    ]},
    {"type": "section", "title": "盈利模式", "points": ["..."]},
    {"type": "section", "title": "关键变量", "points": ["关卡一", "关卡二", "关卡三"]},
    {"type": "quote", "content": "金句收尾", "source": "来源"}
  ]
}
```

**特征：** insight 开头 → stats 定调 → 逐个展开壁垒 → comparison 博弈分析 → quote 收尾。

### 模板 B：行业趋势报告

适用场景：市场分析、行业风向、技术趋势。

```json
{
  "blocks": [
    {"type": "stats", "items": [{"value": "...", "label": "..."}, ...]},
    {"type": "text", "content": "引言 / 背景判断"},
    {"type": "section", "title": "趋势一", "points": ["..."]},
    {"type": "section", "title": "趋势二", "points": ["..."]},
    {"type": "section", "title": "趋势三", "points": ["..."]},
    {"type": "stats", "items": [{"value": "...", "label": "..."}]},
    {"type": "insight", "label": "核心判断", "content": "……"},
    {"type": "questions", "title": "需要思考的问题", "items": ["Q1?", "Q2?", "Q3?"]},
    {"type": "quote", "content": "金句收尾", "source": "来源"}
  ]
}
```

**特征：** stats 大数字开场 → 逐条趋势 → 中间再穿插数据强化 → questions 引发思考 → quote 收尾。

### 模板 C：产品评测对比

适用场景：A vs B 产品对比、框架/工具选型。

```json
{
  "blocks": [
    {"type": "insight", "label": "核心结论", "content": "一句话判断"},
    {"type": "comparison", "columns": [
      {"title": "产品 A", "subtitle": "STRENGTHS", "points": ["..."]},
      {"title": "产品 B", "subtitle": "STRENGTHS", "points": ["..."]}
    ]},
    {"type": "comparison", "columns": [
      {"title": "产品 A", "subtitle": "WEAKNESSES", "points": ["..."]},
      {"title": "产品 B", "subtitle": "WEAKNESSES", "points": ["..."]}
    ]},
    {"type": "stats", "items": [{"value": "...", "label": "A关键指标"}, {"value": "...", "label": "B关键指标"}]},
    {"type": "section", "title": "选型建议", "content": "什么场景选 A / 什么场景选 B", "points": ["..."]},
    {"type": "quote", "content": "总结", "source": "来源"}
  ]
}
```

**特征：** 结论先行 → 双对比展示优缺点 → stats 关键指标 → 选型建议。

### 模板 D：数据解读/报告摘要

适用场景：财报解读、研究报告、统计数据可视化。

```json
{
  "blocks": [
    {"type": "stats", "items": [{"value": "...", "label": "核心指标"}, ...]},
    {"type": "text", "content": "数据背景 / 报告核心发现"},
    {"type": "stats", "items": [{"value": "...", "label": "..."}, ...]},
    {"type": "section", "title": "解读一", "points": ["数据1 + 判断1", "数据2 + 判断2"]},
    {"type": "section", "title": "解读二", "points": ["数据3 + 判断3"]},
    {"type": "comparison", "columns": [
      {"title": "预期", "points": ["..."]},
      {"title": "实际", "points": ["..."]}
    ]},
    {"type": "insight", "label": "背后的逻辑", "content": "……"},
    {"type": "quote", "content": "关键引文", "source": "报告来源"}
  ]
}
```

**特征：** 大量 stats 块 → 数据驱动全文 → comparison 做预期差 → insight 揭示本质。

### 模板 E：长文/播客精华摘要

适用场景：万字长文、播客对话、视频深度内容。

```json
{
  "blocks": [
    {"type": "insight", "label": "核心观点", "content": "一句话概括"},
    {"type": "text", "content": "内容背景 / 为什么值得看"},
    {"type": "section", "title": "观点一", "points": ["..."]},
    {"type": "section", "title": "观点二", "points": ["..."]},
    {"type": "quote", "content": "原文金句", "source": "嘉宾/作者"},
    {"type": "section", "title": "观点三", "points": ["..."]},
    {"type": "section", "title": "观点四", "points": ["..."]},
    {"type": "insight", "label": "我的补充判断", "content": "……"},
    {"type": "quote", "content": "收尾", "source": "来源"}
  ]
}
```

**特征：** 核心观点前置 → 逐条摘要 → 原文金句增强说服力 → agent 自己的判断增加附加值。

---

### Editorial Principles (Step 1 — all paths)

- **标题要有冲击力**，能引发好奇心（15字以内）
- **每个 block 的文案都要重新撰写**，不是简单摘抄原文
- **用中文撰写**，保持专业但不晦涩
- **创造视觉节奏**：大标题 → 导语 → 洞察 → 步骤 → 深入分析 → 数据 → 总结
- **v2 总量 12-20 个 blocks**（v1 为 8-15），确保内容丰富但不冗余
- **对于英文原文**，需要翻译并进行二次创作，而非直译
- **每段至少一个硬数据**：文字段落中必须嵌入具体数字（百分比、金额、时间、排名）
- **多使用比较句**：不说"表现很好"，说"比 X 快 3 倍，比 Y 便宜 40%"

---

## Content Block Types

| Block Type | Description | Visual | v2 使用建议 |
|-----------|-------------|--------|------------|
| `text` | Body paragraph | Regular text | ≤2 次，每张图不超过 2 个纯文字段 |
| `insight` | Key insight box | Green background, white text | 至少 1 次，建议在开头和结尾出现 |
| `steps` | Numbered step cards | Grid of cards with numbered circles | 流程/时间线类内容使用 |
| `section` | Content section with heading | Heading + bullet points | 主力 block，每个 point 必须含数据 |
| `comparison` | Two-column comparison | Side-by-side cards | 分析类内容强制使用 |
| `questions` | Key questions | Yellow background, red bullets | 趋势/行业分析类结尾使用 |
| `stats` | Data highlights | Large numbers display | 至少 2 次，可穿插多处 |
| `list` | Numbered list | Action items with green numbers | 行动建议类内容 |
| `quote` | Quote/conclusion | Green background with quote marks | 至少 1 次，建议用于收尾 |
| `highlight` | Highlighted text | Light green background | 关键概念突出 |
| `divider` | Visual separator | Horizontal line | 最多 1 次 |

## Content JSON Format

```json
{
  "meta": {
    "author": "Author / Source Name",
    "source": "https://example.com/article",
    "signature": "虾丸 🐝",
    "title": "Chinese Main Title (15 chars max)",
    "subtitle": "ENGLISH SUBTITLE IN CAPS",
    "description": "One-line description"
  },
  "reading_stats": {
    "chars": 15000,
    "paragraphs": 120,
    "sections": 8,
    "source_type": "播客介绍页",
    "completeness": "概要"
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
# Render JSON to PNG (1080px content width, 3x Retina, full-page)
web-infographic create --content content.json [--output path.png]

# Generate HTML only (for preview or manual screenshot)
web-infographic html --content content.json [--output path.html]
```

## HTML Design Spec (for Path 2 — no CLI)

When generating HTML directly, use these design tokens and structure:

**Page:** 1080px wide, white background, `font-family: 'Noto Sans SC', sans-serif`, load from Google Fonts.

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

- **Rendering Engine**: HTML/CSS + Playwright full-page screenshot (1080px content width, 3x deviceScaleFactor = 3240px output)
- **Content Analysis**: Always performed by the running agent's own LLM
- **Visual Design**: Clean editorial style with green/teal accent
- **Typography**: Noto Sans SC (Google Fonts) for Chinese, system sans-serif for English

## Requirements (Path 1 only)

- Python 3.11+
- Node.js with `playwright` package (auto-installed on first run)
- Playwright Chromium browser

## Output

- **Fixed output directory**: `~/info_graph/` — always use this path
- **Path 1**: PNG (1080px content width, 3x Retina, full-page) + HTML file saved alongside
- **Path 2**: HTML artifact or file
