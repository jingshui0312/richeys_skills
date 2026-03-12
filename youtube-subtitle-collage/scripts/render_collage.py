#!/usr/bin/env python3
"""
YouTube Subtitle Collage Renderer
Generates an HTML/PNG image from selected subtitle quotes.
Dark YouTube-style design: quote cards with timestamps in a 2-column grid.
"""

import sys
import json
import argparse
import subprocess
import os
import re
from pathlib import Path
from html import escape


def generate_html(data: dict) -> str:
    meta = data.get('meta', {})
    quotes = data.get('quotes', [])

    title = escape(meta.get('title', 'YouTube 字幕集锦'))
    channel = escape(meta.get('channel', ''))
    url = escape(meta.get('url', ''))
    duration = escape(meta.get('duration', ''))

    cards_html = ''
    for q in quotes:
        timestamp = escape(str(q.get('timestamp', '')))
        text = escape(q.get('text', ''))
        translation = q.get('translation', '')
        highlight = q.get('highlight', False)

        card_class = 'card highlight' if highlight else 'card'
        translation_html = f'<p class="translation">{escape(translation)}</p>' if translation else ''

        cards_html += f'''
        <div class="{card_class}">
          <span class="timestamp">▶ {timestamp}</span>
          <p class="quote-text">{text}</p>
          {translation_html}
        </div>'''

    duration_badge = f'<span class="badge">{duration}</span>' if duration else ''

    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&display=swap" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  width: 900px;
  background: #0d0d0d;
  font-family: 'Noto Sans SC', -apple-system, sans-serif;
  color: #f0f0f0;
  -webkit-font-smoothing: antialiased;
}}

.wrapper {{
  padding: 48px 44px 56px;
}}

/* ── Header ── */
.header {{
  margin-bottom: 36px;
  padding-bottom: 28px;
  border-bottom: 1px solid #1e1e1e;
}}

.channel-row {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}}

.yt-badge {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #FF0000;
  border-radius: 5px;
  width: 26px;
  height: 18px;
  flex-shrink: 0;
}}

.yt-badge::after {{
  content: '';
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 4.5px 0 4.5px 9px;
  border-color: transparent transparent transparent #fff;
  margin-left: 2px;
}}

.channel-name {{
  font-size: 12px;
  font-weight: 700;
  color: #FF0000;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}}

.video-title {{
  font-size: 24px;
  font-weight: 900;
  line-height: 1.3;
  color: #ffffff;
  margin-bottom: 14px;
  letter-spacing: -0.3px;
}}

.meta-chips {{
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}}

.badge {{
  background: #1a1a1a;
  border: 1px solid #2e2e2e;
  color: #888;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 500;
  letter-spacing: 0.3px;
}}

.url-text {{
  font-size: 11px;
  color: #3a3a3a;
  font-family: monospace;
}}

/* ── Section label ── */
.section-label {{
  font-size: 10px;
  font-weight: 700;
  color: #FF0000;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  margin-bottom: 18px;
}}

/* ── Card Grid ── */
.grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}}

.card {{
  background: #141414;
  border: 1px solid #1f1f1f;
  border-radius: 10px;
  padding: 18px 20px 16px;
  position: relative;
  break-inside: avoid;
}}

.card.highlight {{
  background: #180808;
  border: 1.5px solid #FF0000;
  box-shadow: 0 0 0 1px rgba(255,0,0,0.08);
}}

.card.highlight .quote-text {{
  color: #ffffff;
}}

.timestamp {{
  display: inline-block;
  background: #FF0000;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 3px;
  margin-bottom: 11px;
  letter-spacing: 0.5px;
  font-variant-numeric: tabular-nums;
}}

.quote-text {{
  font-size: 14px;
  line-height: 1.7;
  color: #c8c8c8;
  font-weight: 400;
}}

.translation {{
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.65;
  color: #666;
  padding-top: 9px;
  border-top: 1px solid #222;
}}

/* ── Footer ── */
.footer {{
  margin-top: 36px;
  padding-top: 18px;
  border-top: 1px solid #181818;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}

.footer-url {{
  font-size: 11px;
  color: #3a3a3a;
  font-family: monospace;
}}

.footer-label {{
  font-size: 10px;
  color: #2a2a2a;
  letter-spacing: 1px;
  text-transform: uppercase;
}}
</style>
</head>
<body>
<div class="wrapper">

  <div class="header">
    <div class="channel-row">
      <div class="yt-badge"></div>
      <span class="channel-name">{channel}</span>
    </div>
    <h1 class="video-title">{title}</h1>
    <div class="meta-chips">
      <span class="badge">字幕集锦</span>
      {duration_badge}
      <span class="url-text">{url}</span>
    </div>
  </div>

  <p class="section-label">精选字幕 · Selected Quotes</p>

  <div class="grid">
    {cards_html}
  </div>

  <div class="footer">
    <span class="footer-url">{url}</span>
    <span class="footer-label">YouTube Subtitle Collage</span>
  </div>

</div>
</body>
</html>'''

    return html


def render_html_to_png(html_path: Path, png_path: Path, width: int = 900):
    skill_dir = Path(__file__).parent.parent
    screenshot_script = skill_dir / 'scripts' / 'screenshot.mjs'

    env = os.environ.copy()
    env['PLAYWRIGHT_BROWSERS_PATH'] = os.environ.get(
        'PLAYWRIGHT_BROWSERS_PATH',
        os.path.expanduser('~/Library/Caches/ms-playwright')
    )
    skill_nm = str(skill_dir / 'node_modules')
    node_paths = [skill_nm] if os.path.isdir(skill_nm) else []
    for p in [os.getcwd(), os.path.expanduser('~')]:
        nm = os.path.join(p, 'node_modules')
        if os.path.isdir(nm) and nm not in node_paths:
            node_paths.append(nm)
    if node_paths:
        env['NODE_PATH'] = ':'.join(node_paths)

    result = subprocess.run(
        ['node', str(screenshot_script), str(html_path), str(png_path), str(width)],
        capture_output=True, text=True, env=env
    )

    if result.returncode != 0:
        print(f"Screenshot error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(result.stdout.strip(), file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='Render YouTube subtitle collage to PNG')
    subparsers = parser.add_subparsers(dest='command')

    create_p = subparsers.add_parser('create', help='Render collage JSON to PNG')
    create_p.add_argument('--content', required=True, help='Collage content JSON file')
    create_p.add_argument('--output', default=None, help='Output PNG path')

    html_p = subparsers.add_parser('html', help='Generate HTML only (no screenshot)')
    html_p.add_argument('--content', required=True, help='Collage content JSON file')
    html_p.add_argument('--output', default=None, help='Output HTML path')

    args = parser.parse_args()

    if args.command not in ('create', 'html'):
        parser.print_help()
        sys.exit(1)

    with open(args.content, 'r', encoding='utf-8') as f:
        raw = f.read()
    raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw)
    data = json.loads(raw)

    html = generate_html(data)

    output_dir = Path.home() / 'info_graph'
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        base_path = Path(args.output)
        base_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        base_path = output_dir / 'youtube-subtitle-collage'

    if args.command == 'html':
        html_path = base_path if str(base_path).endswith('.html') else base_path.with_suffix('.html')
        html_path.write_text(html, encoding='utf-8')
        print(str(html_path))
        return

    # create: render to PNG
    html_path = base_path.with_suffix('.html')
    png_path = base_path.with_suffix('.png')

    html_path.write_text(html, encoding='utf-8')
    print(f"HTML saved: {html_path}", file=sys.stderr)

    render_html_to_png(html_path, png_path)
    print(str(png_path))


if __name__ == '__main__':
    main()
