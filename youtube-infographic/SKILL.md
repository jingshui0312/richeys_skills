# YouTube Infographic Generator

深度分析 YouTube 视频内容并生成专业级信息长图，效果对标 web 网页版信息长图（36氪、极客公园、少数派专栏品质）。

Use this skill whenever the user asks to: generate an infographic from a YouTube video, create a long-form image from a YouTube URL, analyze YouTube video content visually, or convert a YouTube video into a professional visual summary.

## Skill Locations

- YouTube extractor: `~/.claude/skills/youtube-infographic/youtube-infographic`
- Infographic renderer: `~/.claude/skills/web-infographic-generator/web-infographic`

## User Input

$ARGUMENTS

## Workflow (IMPORTANT - Follow these steps exactly)

### Step 1: Extract YouTube Content

Run the extractor to get video metadata and transcript.

**Standard mode** (production use, up to 4000 chars transcript):
```bash
bash ~/.claude/skills/youtube-infographic/youtube-infographic <YouTube_URL> --output /tmp/yt-video-data.json
```

**Token-saving mode** (for testing/validation, limit transcript):
```bash
bash ~/.claude/skills/youtube-infographic/youtube-infographic <YouTube_URL> --brief --output /tmp/yt-video-data.json
```

**Metadata-only mode** (fastest, when transcript not needed):
```bash
bash ~/.claude/skills/youtube-infographic/youtube-infographic <YouTube_URL> --no-transcript --output /tmp/yt-video-data.json
```

After extraction, read the JSON:
```bash
cat /tmp/yt-video-data.json
```

### Step 2: YOU (Claude) Analyze and Generate JSON

As a professional tech media editor (参考36氪、极客公园、少数派的编辑水平), deeply analyze the video content and produce a structured JSON file. Do NOT rely on any external API — you do the analysis yourself.

#### Key differences from web content analysis:

- `author` = YouTube channel name
- `source` = YouTube video URL (e.g., `https://youtu.be/VIDEO_ID`)
- Focus on the spoken content from the transcript, not just description
- If transcript is in English, translate and rewrite in Chinese
- Highlight key insights, demo highlights, or memorable quotes from the video
- If transcript is truncated, note this and analyze based on available content

#### Editorial Principles

- 标题要有冲击力，能引发好奇心（15字以内）
- 每个 block 的文案都要重新撰写，不是简单摘抄字幕
- 用中文撰写，保持专业但不晦涩
- 信息密度要高，每句话都有价值
- 创造视觉节奏：大标题 → 导语 → 洞察 → 步骤 → 深入分析 → 数据 → 总结
- 总共产出 8-15 个 blocks，确保内容丰富但不冗余
- 对于英文视频，需要翻译并进行二次创作，而非直译
- 副标题 subtitle 使用英文大写

Write the JSON to `/tmp/infographic-content.json`.

#### JSON Format

```json
{
  "meta": {
    "author": "YouTube频道名",
    "source": "https://youtu.be/VIDEO_ID",
    "title": "重新编辑的中文主标题（15字以内，有冲击力）",
    "subtitle": "ENGLISH SUBTITLE IN CAPS",
    "description": "一句话描述（20-30字）"
  },
  "blocks": [
    {"type": "text", "content": "导语段落，2-4句概述性文字"},
    {"type": "insight", "label": "核心洞察", "content": "关键洞察，2-3句话"},
    {"type": "steps", "title": "板块标题", "items": [
      {"number": 1, "title": "步骤标题", "subtitle": "4字描述", "points": ["要点1", "要点2"]},
      {"number": 2, "title": "步骤标题", "subtitle": "4字描述", "points": ["要点1", "要点2"]}
    ]},
    {"type": "section", "title": "板块标题", "content": "可选引导文字", "points": ["要点1", "要点2", "要点3"]},
    {"type": "comparison", "columns": [
      {"title": "对比A标题", "subtitle": "副标题", "points": ["要点1", "要点2"]},
      {"title": "对比B标题", "subtitle": "副标题", "points": ["要点1", "要点2"]}
    ]},
    {"type": "questions", "title": "关键问题", "icon": "red", "items": ["问题1？", "问题2？", "问题3？"]},
    {"type": "stats", "items": [
      {"value": "90%", "label": "描述文字"},
      {"value": "24h", "label": "描述文字"}
    ]},
    {"type": "list", "title": "行动建议", "items": ["建议1", "建议2", "建议3"]},
    {"type": "quote", "content": "一句有力的结语或视频金句", "source": "来源/频道名"},
    {"type": "highlight", "content": "高亮文本段落"},
    {"type": "divider"}
  ]
}
```

### Step 3: Render to Image

Use the web-infographic-generator's `create` command to render the JSON into a PNG:

```bash
bash ~/.claude/skills/web-infographic-generator/web-infographic create --content /tmp/infographic-content.json --output <output_path>.png
```

Default output path: `outputs/youtube-infographic.png` in the current working directory.

If the user only wants HTML preview:
```bash
bash ~/.claude/skills/web-infographic-generator/web-infographic html --content /tmp/infographic-content.json --output <output_path>.html
```

### Step 4: Show Result

After rendering, read the PNG file to show the user the result. Report the output file path.

## Token Saving Tips (Testing)

- Use `--brief` flag to limit transcript to ~1500 chars
- Use `--max-transcript 1000` for even shorter transcript
- Use `--no-transcript` to skip transcript entirely and only use video title + description
- To validate the render pipeline without real video analysis, write a minimal test JSON directly to `/tmp/infographic-content.json` and run the render step

## Requirements

- `youtube-transcript-api` (auto-installed by the script if missing)
- `yt-dlp` for metadata (optional: install with `pip install yt-dlp`)
- Python 3.11+
- Node.js + Playwright (from web-infographic-generator)
- NO external API keys needed — Claude does the content analysis directly

## Output

- PNG image: 780px width, auto height, full-page capture
- HTML file: Also saved alongside for preview/editing
