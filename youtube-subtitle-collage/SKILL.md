---
name: youtube-subtitle-collage
version: 2.0.0
description: Generate a subtitle collage image (字幕拼接图) from a YouTube video — real video frames with Chinese subtitle text overlaid, stacked into a tall PNG.
author: HappyCapy
tags:
  - youtube
  - subtitle
  - collage
  - 字幕拼接图
  - image-generation
---

# YouTube 字幕拼接图 / YouTube Subtitle Collage

从 YouTube 视频中提取真实字幕，挑选精彩片段，截取对应视频帧，叠加中文字幕大字，纵向拼接成长图。

**输出效果**：每条字幕 = 一帧视频截图（横向裁剪条带）+ 底部叠加深色字幕背景 + 中文白色大字。

**Scope: YouTube URL → 真实字幕 → 拼接图**

**与 `youtube-infographic` 的区别：**
- `youtube-infographic`：二次创作，编辑长图
- `youtube-subtitle-collage`：保留原话，视频截帧 + 字幕叠字拼接图

Use this skill when the user asks to: 制作字幕拼接图、把视频字幕做成图、提取视频金句做成卡片图、show real quotes from a YouTube video as a screenshot collage.

## User Input

$ARGUMENTS

## Workflow

### Step 1 — Extract Subtitle Segments

```bash
bash ~/.claude/skills/youtube-subtitle-collage/youtube-subtitle-collage extract '$URL' --output /tmp/yt-segments.json
```

**重要**：URL 必须用单引号包裹，防止 shell 对 `?` 进行 glob 展开。

如果 `extract` 因 IP 被封失败，用 yt-dlp 直接下载字幕（备用方案）：

```bash
# 查看可用字幕语言
yt-dlp --cookies-from-browser chrome --js-runtimes node --remote-components ejs:github --list-subs '$URL' 2>&1 | grep -E "^(en|zh)" | head -20

# 下载字幕（优先中文，其次英文）
yt-dlp --cookies-from-browser chrome --js-runtimes node --remote-components ejs:github \
  --write-sub --sub-lang zh-Hans --skip-download --sub-format json3 \
  -o '/tmp/yt_sub' '$URL' 2>&1
# 如无中文字幕，改 --sub-lang en-US

# 下载视频元数据
yt-dlp --cookies-from-browser chrome --js-runtimes node --remote-components ejs:github \
  --write-info-json --skip-download -o '/tmp/yt_sub' '$URL' 2>&1
```

解析备用字幕（json3 格式）：

```python
import json, re

with open('/tmp/yt_sub.en-US.json3') as f:  # 或 zh-Hans
    subs = json.load(f)
with open('/tmp/yt_sub.info.json') as f:
    info = json.load(f)

print("Title:", info.get('title'))
print("Channel:", info.get('channel', info.get('uploader')))
print("Duration:", info.get('duration_string'))

events = subs.get('events', [])
raw = []
for ev in events:
    segs = ev.get('segs', [])
    text = ' '.join(s.get('utf8','') for s in segs).replace('\n',' ').strip()
    text = re.sub(r'\[.*?\]', '', text).strip()
    if not text: continue
    start_s = ev.get('tStartMs', 0) / 1000
    m, s = divmod(int(start_s), 60); h, m = divmod(m, 60)
    ts = f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'
    raw.append({'timestamp': ts, 'start': start_s, 'text': text})

# Merge into sentence-level segments
merged, buf_text, buf_ts = [], '', ''
for seg in raw:
    if not buf_text: buf_ts = seg['timestamp']
    buf_text = (buf_text + ' ' + seg['text']).strip()
    if re.search(r'[.!?。！？]$', buf_text) and len(buf_text) > 40:
        merged.append({'timestamp': buf_ts, 'text': buf_text})
        buf_text = ''
if buf_text: merged.append({'timestamp': buf_ts, 'text': buf_text})

print(f"Merged: {len(merged)} segments")
for s in merged[::max(1,len(merged)//50)][:50]:
    print(f"[{s['timestamp']}] {s['text'][:120]}")
```

### Step 2 — Select Best Quotes (YOU do this, Claude)

从字幕中选出 **12–18 条**最精彩的片段。选取标准：
- 金句：简洁、可引用、令人印象深刻
- 洞察：揭示关键观点或令人惊讶的事实
- 转折点：论点的重要转变
- 情感共鸣：感人或有趣

**选取原则：**
- 均匀分布时间轴，不要只选开头
- 每段字幕完整表达一个意思
- **`text` 字段：若原字幕为中文，直接填中文；若为英文，填中文翻译**
- `original` 字段（可选）：原文（英文时填写）
- 最多 2 个 `highlight: true`（最重要的金句，显示红色边框）

### Step 3 — Write Collage JSON

保存到 `/tmp/collage-content.json`（**用 Python 写文件，不要用 heredoc**）：

```python
import json

data = {
  "meta": {
    "title": "视频标题",
    "channel": "频道名",
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "duration": "1:23:45"
  },
  "quotes": [
    {
      "timestamp": "0:42",
      "text": "这里填中文字幕（原文中文 or 英文翻译）",
      "highlight": False
    },
    {
      "timestamp": "3:15",
      "text": "最重要的一句话，红框高亮显示。",
      "highlight": True
    }
  ]
}

with open('/tmp/collage-content.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("JSON written, quotes:", len(data["quotes"]))
```

### Step 4 — Render to PNG

```bash
bash ~/.claude/skills/youtube-subtitle-collage/youtube-subtitle-collage create \
  --content /tmp/collage-content.json \
  --output ~/info_graph/subtitle-collage.png
```

此命令会：
1. 自动调用 yt-dlp 获取视频流 URL（需要 Chrome cookies）
2. 用 ffmpeg 在每个时间戳截取视频帧
3. 用 Pillow 叠加字幕文字
4. 拼接成长图

如果视频流获取失败，会自动降级为深色背景条带（不含视频帧）。

**备用：HTML 卡片版（不需要 ffmpeg）：**
```bash
bash ~/.claude/skills/youtube-subtitle-collage/youtube-subtitle-collage html \
  --content /tmp/collage-content.json \
  --output ~/info_graph/subtitle-collage.html
```

### Step 5 — Show Result

读取并展示 PNG 文件，报告文件路径。

## Collage JSON Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `meta.title` | ✅ | 视频标题 |
| `meta.channel` | ✅ | 频道名 |
| `meta.url` | ✅ | 完整 YouTube URL（用于截帧） |
| `meta.duration` | optional | 如 `"1:23:45"` |
| `quotes[].timestamp` | ✅ | 如 `"3:42"` |
| `quotes[].text` | ✅ | **中文字幕文字**（直接显示在图上） |
| `quotes[].highlight` | optional | `true` = 红色边框（最多 2 个） |

## Visual Design

- **Layout**: 900px 宽，每条字幕 = 240px 高横向条带，白色 4px 间隔
- **Frame**: 截取视频帧下方 60% 区域（字幕+场景）
- **Subtitle bar**: 深色半透明圆角背景，中文白色大字（44px），居中
- **Timestamp badge**: 左上角红色标签
- **Highlight**: 红色边框
- **Output**: `~/info_graph/youtube-subtitle-collage.png`

## Requirements

- Python 3.11+ with `youtube-transcript-api`, `yt-dlp`, `Pillow`
- **ffmpeg**（必须）：视频帧提取。安装：`brew install ffmpeg`
- Chrome browser（用于 yt-dlp cookies 认证）
- Node.js + Playwright（可选，仅 `html` 命令需要）
