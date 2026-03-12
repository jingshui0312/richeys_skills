---
name: youtube-subtitle-collage
version: 1.0.0
description: Generate a dark-themed subtitle collage image (字幕拼接图) from a YouTube video — preserves actual spoken words as timestamped quote cards.
author: HappyCapy
tags:
  - youtube
  - subtitle
  - collage
  - 字幕拼接图
  - image-generation
---

# YouTube 字幕拼接图 / YouTube Subtitle Collage

从 YouTube 视频中提取真实字幕，挑选最有价值的片段，生成深色风格的字幕拼接图（PNG）。

**Scope: YouTube URL → 真实字幕 → 拼接图**

**与 `youtube-infographic` 的区别：**
- `youtube-infographic`：把视频内容重新编辑为文章式信息长图（二次创作）
- `youtube-subtitle-collage`：保留原始字幕原文，以时间戳卡片形式拼接展示（忠实呈现）

Use this skill when the user asks to: 制作字幕拼接图、把视频字幕做成图、提取视频金句做成卡片图、show real quotes from a YouTube video.

## User Input

$ARGUMENTS

## Workflow

### Step 1 — Extract Subtitle Segments

```bash
bash ~/.claude/skills/youtube-subtitle-collage/youtube-subtitle-collage extract <YouTube_URL> --output /tmp/yt-segments.json
```

Read the output:
```bash
cat /tmp/yt-segments.json
```

The JSON contains: `title`, `channel`, `url`, `duration`, `transcript_language`, `segments[]` (each with `timestamp` + `text`).

### Step 2 — Select Best Quotes (YOU do this, Claude)

Read through all segments and select **10–20 of the most impactful ones**. Criteria:
- 金句：concise, quotable, memorable
- 洞察：reveals a key insight or surprising fact
- 转折点：marks a shift in the argument
- 情感：emotionally resonant or funny

**Selection rules:**
- 均匀分布时间轴，不要只选开头
- 每段字幕尽量完整表达一个意思（必要时合并相邻几条）
- 若原文为英文，`translation` 字段填写中文翻译；若原文为中文，`translation` 可留空
- 最多 2 个 `highlight: true`（用于最重要的金句，显示红色边框）

### Step 3 — Write Collage JSON

Save to `/tmp/collage-content.json`:

```json
{
  "meta": {
    "title": "视频标题（可适当缩短，保留核心信息）",
    "channel": "频道名",
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "duration": "12:34"
  },
  "quotes": [
    {
      "timestamp": "0:42",
      "text": "原文字幕内容，保持原话不改动",
      "translation": "中文翻译（原文为英文时填写）",
      "highlight": false
    },
    {
      "timestamp": "3:15",
      "text": "This is the most important sentence in the video.",
      "translation": "这是视频中最重要的一句话。",
      "highlight": true
    }
  ]
}
```

### Step 4 — Render to PNG

```bash
bash ~/.claude/skills/youtube-subtitle-collage/youtube-subtitle-collage create \
  --content /tmp/collage-content.json \
  --output ~/info_graph/subtitle-collage.png
```

For HTML preview only:
```bash
bash ~/.claude/skills/youtube-subtitle-collage/youtube-subtitle-collage html \
  --content /tmp/collage-content.json \
  --output ~/info_graph/subtitle-collage.html
```

### Step 5 — Show Result

Read and display the PNG. Report the file path.

## Collage JSON Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `meta.title` | ✅ | Video title (can be shortened) |
| `meta.channel` | ✅ | YouTube channel name |
| `meta.url` | ✅ | Full YouTube URL |
| `meta.duration` | optional | e.g. `"12:34"` |
| `quotes[].timestamp` | ✅ | e.g. `"3:42"` |
| `quotes[].text` | ✅ | Original subtitle text, verbatim |
| `quotes[].translation` | optional | Chinese translation if original is English |
| `quotes[].highlight` | optional | `true` = red border card (use max 2) |

## Visual Design

- **Background**: Dark (#0d0d0d), YouTube dark mode aesthetic
- **Layout**: 2-column card grid, 900px wide
- **Timestamp**: Red badge (YouTube red #FF0000) on each card
- **Highlight cards**: Red border for the most impactful quotes
- **Typography**: Noto Sans SC, white/gray text
- **Output**: `~/info_graph/youtube-subtitle-collage.png`

## Requirements

- Python 3.11+ with `youtube-transcript-api`, `yt-dlp` (optional, for metadata)
- Node.js + Playwright (Chromium) for PNG rendering
