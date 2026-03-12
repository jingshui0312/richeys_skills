#!/usr/bin/env python3
"""
YouTube Subtitle Collage Renderer v2 — Storyboard Edition
Fetches YouTube pre-generated storyboard thumbnails (no video download needed),
overlays Chinese subtitle text, and stacks horizontal strips into a PNG collage.
"""

import sys
import json
import argparse
import subprocess
import os
import re
import io
import textwrap
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...", file=sys.stderr)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
                    '--break-system-packages', 'Pillow'], check=True)
    from PIL import Image, ImageDraw, ImageFont


# ── Layout constants ──────────────────────────────────────────────────────────
STRIP_WIDTH   = 900
STRIP_HEIGHT  = 240
GAP           = 4     # white gap between strips
FONT_SIZE     = 44
FONT_SIZE_TS  = 20
SUB_PAD_X     = 28
SUB_PAD_Y     = 14
SUB_BG_ALPHA  = 185
SUB_BOTTOM    = 22
MAX_LINE_CHARS = 22


def find_chinese_font(size: int):
    candidates = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Supplemental/NotoSansCJK-Regular.ttc',
        '/opt/homebrew/opt/font-noto-sans-cjk-sc/share/fonts/opentype/NotoSansCJKsc-Regular.otf',
        os.path.expanduser('~/Library/Fonts/NotoSansSC-Regular.ttf'),
        os.path.expanduser('~/Library/Fonts/SourceHanSansSC-Regular.otf'),
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJKsc-Regular.otf',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def parse_ts_to_seconds(ts: str) -> float:
    parts = ts.strip().split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


# ── Storyboard fetching ───────────────────────────────────────────────────────

def get_storyboard_meta(youtube_url: str) -> dict | None:
    """
    Use yt-dlp to retrieve storyboard fragment URLs and video duration.
    Returns dict with: rows, cols, total_frames, duration, secs_per_frame, fragments[]
    Tries sb0 (320×180/frame) first, falls back to sb1 (160×90/frame).
    """
    base_args = [
        'yt-dlp',
        '--cookies-from-browser', 'chrome',
        '--js-runtimes', 'node', '--remote-components', 'ejs:github',
        '--no-warnings',
    ]

    # Fetch formats + top-level duration in one call
    result = subprocess.run(
        base_args + [
            '--print', '%(duration)s',
            '--print', '%(formats.:.{format_id,rows,columns,fragments})j',
            youtube_url,
        ],
        capture_output=True, text=True, timeout=90,
    )

    if result.returncode != 0 or not result.stdout.strip():
        return None

    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:
        return None

    try:
        duration = float(lines[0])
        formats  = json.loads(lines[1])
    except (ValueError, json.JSONDecodeError):
        return None

    for sb_id in ('sb0', 'sb1'):
        sb = next((f for f in formats if f.get('format_id') == sb_id), None)
        if not sb:
            continue
        frags = sb.get('fragments', [])
        rows  = sb.get('rows', 3)
        cols  = sb.get('columns', 3)
        if not frags:
            continue

        total_frames   = len(frags) * rows * cols
        secs_per_frame = duration / total_frames

        print(f"Storyboard {sb_id}: {rows}×{cols}/sheet × {len(frags)} sheets "
              f"= {total_frames} frames, {secs_per_frame:.2f}s/frame", file=sys.stderr)

        return {
            'rows': rows,
            'cols': cols,
            'total_frames': total_frames,
            'duration': duration,
            'secs_per_frame': secs_per_frame,
            'fragments': [fr['url'] for fr in frags],
        }

    return None


def fetch_frame_from_storyboard(meta: dict, timestamp_str: str) -> Image.Image | None:
    """
    Download the storyboard sheet containing the given timestamp and crop out the frame.
    """
    seconds = parse_ts_to_seconds(timestamp_str)
    frame_idx = int(seconds / meta['secs_per_frame'])
    frame_idx = max(0, min(frame_idx, meta['total_frames'] - 1))

    frames_per_sheet = meta['rows'] * meta['cols']
    sheet_idx = frame_idx // frames_per_sheet
    frame_in_sheet = frame_idx % frames_per_sheet
    row = frame_in_sheet // meta['cols']
    col = frame_in_sheet % meta['cols']

    if sheet_idx >= len(meta['fragments']):
        return None

    url = meta['fragments'][sheet_idx]
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, timeout=12) as r:
            data = r.read()
    except Exception as e:
        print(f"    ↳ storyboard fetch error: {e}", file=sys.stderr)
        return None

    sheet = Image.open(io.BytesIO(data)).convert('RGB')
    fw = sheet.size[0] // meta['cols']
    fh = sheet.size[1] // meta['rows']
    return sheet.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))


# ── Strip composition ─────────────────────────────────────────────────────────

def wrap_text(text: str, max_chars: int) -> list[str]:
    cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    if cjk / max(len(text), 1) > 0.4:
        lines = []
        while len(text) > max_chars:
            lines.append(text[:max_chars])
            text = text[max_chars:]
        if text:
            lines.append(text)
        return lines
    return textwrap.wrap(text, width=max_chars)


def make_strip(frame: Image.Image | None, text: str,
               timestamp: str, highlight: bool,
               font_main, font_ts, full_frame: bool = False) -> tuple:
    """
    Build a STRIP_WIDTH × strip_h strip with subtitle overlay.
    full_frame=True: show the entire video frame at natural height (16:9 → ~506px).
    full_frame=False: crop to lower 60% at STRIP_HEIGHT (240px).
    Returns (image, subtitle_y).
    """

    # ── Background ────────────────────────────────────────────────────────────
    if frame is not None:
        w, h = frame.size
        scale = STRIP_WIDTH / w
        new_h = int(h * scale)
        img = frame.resize((STRIP_WIDTH, new_h), Image.LANCZOS)
        if full_frame:
            strip = img.copy()
            strip_h = new_h
        else:
            # Crop: lower 60% of frame (subtitle zone + scene context)
            crop_start = int(new_h * 0.40)
            crop_end = crop_start + STRIP_HEIGHT
            if crop_end > new_h:
                crop_start = max(0, new_h - STRIP_HEIGHT)
                crop_end = new_h
            strip = img.crop((0, crop_start, STRIP_WIDTH, min(crop_end, new_h)))
            if strip.size[1] < STRIP_HEIGHT:
                bg = Image.new('RGB', (STRIP_WIDTH, STRIP_HEIGHT), (15, 15, 15))
                bg.paste(strip, (0, 0))
                strip = bg
            else:
                strip = strip.resize((STRIP_WIDTH, STRIP_HEIGHT), Image.LANCZOS)
            strip_h = STRIP_HEIGHT
    else:
        strip_h = STRIP_HEIGHT
        strip = Image.new('RGB', (STRIP_WIDTH, strip_h), (20, 20, 20))

    strip = strip.convert('RGBA')

    # ── Subtitle text ─────────────────────────────────────────────────────────
    lines = wrap_text(text, MAX_LINE_CHARS)
    _tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))

    def measure(t, f):
        bb = _tmp.textbbox((0, 0), t, font=f)
        return bb[2] - bb[0], bb[3] - bb[1]

    line_sizes  = [measure(l, font_main) for l in lines]
    line_h      = max((h for _, h in line_sizes), default=0)
    line_spacing = 8
    block_h     = len(lines) * line_h + max(0, len(lines) - 1) * line_spacing
    max_line_w  = max((w for w, _ in line_sizes), default=0)

    bar_w = max_line_w + SUB_PAD_X * 2
    bar_h = block_h + SUB_PAD_Y * 2
    bar_x = max(10, (STRIP_WIDTH - bar_w) // 2)
    bar_y = max(4, strip_h - bar_h - SUB_BOTTOM)

    # Semi-transparent subtitle background
    overlay = Image.new('RGBA', (STRIP_WIDTH, strip_h), (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)
    ov.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
        radius=8,
        fill=(0, 0, 0, SUB_BG_ALPHA),
    )
    strip = Image.alpha_composite(strip, overlay)

    draw = ImageDraw.Draw(strip)
    ty = bar_y + SUB_PAD_Y
    for line, (lw, lh) in zip(lines, line_sizes):
        tx = (STRIP_WIDTH - lw) // 2
        draw.text((tx + 2, ty + 2), line, font=font_main, fill=(0, 0, 0, 160))
        draw.text((tx, ty), line, font=font_main, fill=(255, 255, 255, 255))
        ty += lh + line_spacing

    # ── Timestamp badge ───────────────────────────────────────────────────────
    if timestamp:
        ts_label = f'▶ {timestamp}'
        tsw, tsh = measure(ts_label, font_ts)
        pad = 6
        ts_ov = Image.new('RGBA', (STRIP_WIDTH, strip_h), (0, 0, 0, 0))
        ImageDraw.Draw(ts_ov).rounded_rectangle(
            [14, 14, 14 + tsw + pad * 2, 14 + tsh + pad * 2],
            radius=4, fill=(210, 0, 0, 220),
        )
        strip = Image.alpha_composite(strip, ts_ov)
        ImageDraw.Draw(strip).text((14 + pad, 14 + pad), ts_label,
                                   font=font_ts, fill=(255, 255, 255, 255))

    # ── Highlight border ──────────────────────────────────────────────────────
    if highlight:
        ImageDraw.Draw(strip).rectangle(
            [0, 0, STRIP_WIDTH - 1, strip_h - 1],
            outline=(255, 30, 30, 255), width=5,
        )

    return strip.convert('RGB'), bar_y


# ── Main render ───────────────────────────────────────────────────────────────

def render_collage(data: dict, output_path: str):
    meta   = data.get('meta', {})
    quotes = data.get('quotes', [])
    url    = meta.get('url', '')

    font_main = find_chinese_font(FONT_SIZE)
    font_ts   = find_chinese_font(FONT_SIZE_TS)

    # Get storyboard metadata once (single yt-dlp call)
    sb_meta = None
    if url:
        print("Fetching storyboard metadata...", file=sys.stderr)
        sb_meta = get_storyboard_meta(url)
        if not sb_meta:
            print("Warning: storyboard unavailable — using dark fallback strips.", file=sys.stderr)

    strips = []
    for i, q in enumerate(quotes):
        ts        = q.get('timestamp', '')
        text      = q.get('translation') or q.get('text', '')
        highlight = q.get('highlight', False)

        frame = None
        if sb_meta and ts:
            print(f"  [{i+1:2d}/{len(quotes)}] {ts}  →  fetching storyboard frame…", file=sys.stderr)
            frame = fetch_frame_from_storyboard(sb_meta, ts)
            if frame is None:
                print(f"           ↳ fallback", file=sys.stderr)

        strip, sub_y = make_strip(frame, text, ts, highlight, font_main, font_ts,
                                   full_frame=(i == 0))
        strips.append((strip, sub_y))

    # Stack strips: first strip at full natural height; subsequent strips cropped from subtitle bar down
    strip_heights = []
    for i, (s, sub_y) in enumerate(strips):
        strip_heights.append(s.size[1] if i == 0 else STRIP_HEIGHT - sub_y)

    total_h = sum(strip_heights) + max(0, len(strips) - 1) * GAP
    collage = Image.new('RGB', (STRIP_WIDTH, total_h), (255, 255, 255))
    y = 0
    for i, (s, sub_y) in enumerate(strips):
        if i == 0:
            collage.paste(s, (0, y))
        else:
            cropped = s.crop((0, sub_y, STRIP_WIDTH, STRIP_HEIGHT))
            collage.paste(cropped, (0, y))
        y += strip_heights[i] + GAP

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    collage.save(output_path, 'PNG', optimize=True)
    print(f"Saved: {output_path}  ({STRIP_WIDTH}×{total_h}px)", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--content', required=True, help='Collage JSON file')
    parser.add_argument('--output', default=None, help='Output PNG path')
    args = parser.parse_args()

    with open(args.content, 'r', encoding='utf-8') as f:
        raw = f.read()
    raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw)
    data = json.loads(raw)

    output_dir = Path.home() / 'info_graph'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output or str(output_dir / 'youtube-subtitle-collage.png')

    render_collage(data, output_path)
    print(output_path)


if __name__ == '__main__':
    main()
