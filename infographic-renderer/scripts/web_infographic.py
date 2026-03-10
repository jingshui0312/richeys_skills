#!/usr/bin/env python3
"""
Web Content Infographic Generator v2
Professional editorial-quality infographic generation using HTML/CSS rendering.
Matches the quality of professional editors and tech KOLs.
"""

import sys
import json
import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _parse_html_content(html: str, url: str, title_fallback: str = "Untitled") -> Dict[str, Any]:
    """Parse HTML string into structured content dict (shared by static and JS fetch)"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')

    # Remove unwanted elements
    for elem in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        elem.decompose()

    # Extract title
    h1 = soup.find('h1')
    title_text = h1.get_text().strip() if h1 else (soup.title.string if soup.title else title_fallback)

    # Try multiple content extraction strategies
    article = (
        soup.find('article') or
        soup.find('main') or
        soup.find(class_=re.compile(r'content|article|post|entry|blog', re.I)) or
        soup.find(id=re.compile(r'content|article|post|entry|main', re.I)) or
        soup.body
    )

    paragraphs = []
    if article:
        for elem in article.find_all(['p', 'h2', 'h3', 'h4', 'li', 'blockquote']):
            text = elem.get_text().strip()
            if len(text) > 15:
                paragraphs.append({"tag": elem.name, "text": text})

    content = "\n\n".join([p["text"] for p in paragraphs])
    return {
        "url": url,
        "title": title_text,
        "content": content[:30000],
        "structured": paragraphs
    }


def fetch_web_content(url: str) -> Dict[str, Any]:
    """Fetch and parse static web content (requests + BeautifulSoup)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()

        result = _parse_html_content(response.text, url)
        print(f"Extracted {len(result['structured'])} paragraphs, {len(result['content'])} chars", file=sys.stderr)
        return result

    except Exception as e:
        print(f"Error fetching content: {e}", file=sys.stderr)
        return {"url": url, "title": "Untitled", "content": "", "structured": []}


def fetch_web_content_js(url: str) -> Dict[str, Any]:
    """Fetch JS-rendered web content using Playwright (for SPA/React/Next.js sites)"""
    skill_dir = Path(__file__).parent.parent

    script = tempfile.NamedTemporaryFile(
        suffix='.mjs', delete=False, mode='w', encoding='utf-8',
        dir=str(skill_dir)
    )
    script.write(f"""
import {{ chromium }} from 'playwright';

const browser = await chromium.launch({{ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] }});
const page = await browser.newPage();
await page.setViewportSize({{ width: 1280, height: 800 }});
try {{
  await page.goto({json.dumps(url)}, {{ waitUntil: 'networkidle', timeout: 30000 }});
}} catch (e) {{
  // networkidle timeout is fine — page may still have content
}}
await page.waitForTimeout(2000);
const title = await page.title();
const html = await page.content();
console.log(JSON.stringify({{ title, html }}));
await browser.close();
""")
    script.close()

    try:
        env = os.environ.copy()
        env['PLAYWRIGHT_BROWSERS_PATH'] = os.environ.get(
            'PLAYWRIGHT_BROWSERS_PATH',
            os.path.expanduser('~/Library/Caches/ms-playwright')
        )

        print(f"JS rendering {url} with Playwright...", file=sys.stderr)
        result = subprocess.run(
            ['node', script.name],
            capture_output=True, text=True, timeout=60, env=env
        )

        if result.returncode != 0:
            print(f"Playwright JS fetch error: {result.stderr[:300]}", file=sys.stderr)
            return {"url": url, "title": "Untitled", "content": "", "structured": []}

        data = json.loads(result.stdout.strip())
        page_title = data.get('title', 'Untitled')
        html_content = data.get('html', '')

        parsed = _parse_html_content(html_content, url, title_fallback=page_title)
        # Prefer page.title() which reflects JS-set document.title
        if page_title and page_title != 'Untitled':
            parsed['title'] = page_title

        print(f"JS-rendered: extracted {len(parsed['structured'])} paragraphs, {len(parsed['content'])} chars", file=sys.stderr)
        return parsed

    except Exception as e:
        print(f"Error in JS fetch: {e}", file=sys.stderr)
        return {"url": url, "title": "Untitled", "content": "", "structured": []}
    finally:
        try:
            os.unlink(script.name)
        except Exception:
            pass


def analyze_with_llm(web_data: Dict[str, Any], max_sections: int = 8) -> Dict[str, Any]:
    """
    Use LLM to deeply analyze content and produce structured editorial blocks.
    Returns a rich block-based structure for HTML rendering.
    """
    api_key = os.environ.get('AI_GATEWAY_API_KEY')

    if not api_key:
        print("Warning: AI_GATEWAY_API_KEY not set, using fallback analysis", file=sys.stderr)
        return fallback_analysis(web_data)

    print("Analyzing content with AI editor...", file=sys.stderr)

    prompt = f"""你是一位顶级科技媒体的资深中文编辑和视觉设计总监。你的任务是将以下网页内容深度分析后，重新编辑成一篇专业的信息长图内容。

你的编辑风格参考：36氪深度报道、极客公园长文、少数派专栏的水平。

## 原文信息
标题：{web_data['title']}
来源：{web_data['url']}

内容：
{web_data['content']}

## 编辑要求

请将内容重新组织为一系列"内容块"(blocks)，每个block有不同类型，用于创建富有视觉节奏的信息长图。

可用的block类型：
1. `header` - 标题区：包含主标题、副标题、来源信息
2. `text` - 正文段落：一段分析性文字（2-4句话）
3. `insight` - 核心洞察框：用醒目的背景色突出1-2句关键洞察
4. `steps` - 编号步骤：2-4个并列的关键步骤/要素，每个有编号、标题和2-3个要点
5. `section` - 内容板块：有标题的内容区，包含多个要点
6. `comparison` - 对比区：两列对比，各有标题和要点
7. `questions` - 关键问题：3-5个引发思考的核心问题
8. `stats` - 数据亮点：2-4个关键数据/指标，大字号展示
9. `list` - 要点列表：带标题的列表项（行动建议、总结等）
10. `quote` - 金句/引用：一句有力的结语或引用
11. `divider` - 分割线：用于视觉节奏分割

## 编辑原则
- 标题要有冲击力，能引发好奇心
- 每个block的文案都要重新撰写，不是简单摘抄原文
- 用中文撰写，保持专业但不晦涩
- 信息密度要高，每句话都有价值
- 创造视觉节奏：大标题 → 导语 → 洞察 → 步骤 → 深入分析 → 数据 → 总结
- 总共产出 8-15 个 blocks，确保内容丰富但不冗余
- 对于英文原文，需要翻译并进行二次创作，而非直译

请严格返回以下JSON格式：
{{
  "meta": {{
    "author": "来源作者或媒体名",
    "source": "{web_data['url']}",
    "title": "重新编辑的中文主标题（15字以内，有冲击力）",
    "subtitle": "FROM PRODUCT BUILDING TO ATTENTION ECONOMY",
    "description": "一句话描述（20-30字）"
  }},
  "blocks": [
    {{
      "type": "text",
      "content": "导语段落文字..."
    }},
    {{
      "type": "insight",
      "label": "核心洞察",
      "content": "用引号括起来的关键洞察，2-3句话"
    }},
    {{
      "type": "steps",
      "title": "板块标题",
      "items": [
        {{"number": 1, "title": "步骤标题", "subtitle": "4字描述", "points": ["要点1", "要点2"]}},
        {{"number": 2, "title": "步骤标题", "subtitle": "4字描述", "points": ["要点1", "要点2"]}}
      ]
    }},
    {{
      "type": "section",
      "title": "板块标题",
      "content": "可选的引导文字",
      "points": ["要点1", "要点2", "要点3"]
    }},
    {{
      "type": "comparison",
      "columns": [
        {{"title": "对比A标题", "subtitle": "副标题", "points": ["要点1", "要点2"]}},
        {{"title": "对比B标题", "subtitle": "副标题", "points": ["要点1", "要点2"]}}
      ]
    }},
    {{
      "type": "questions",
      "title": "关键问题",
      "icon": "red",
      "items": ["问题1？", "问题2？", "问题3？"]
    }},
    {{
      "type": "stats",
      "items": [
        {{"value": "90%", "label": "描述文字"}},
        {{"value": "24h", "label": "描述文字"}}
      ]
    }},
    {{
      "type": "list",
      "title": "行动建议",
      "items": ["建议1", "建议2", "建议3"]
    }},
    {{
      "type": "quote",
      "content": "一句有力的结语",
      "source": "来源"
    }}
  ]
}}"""

    model = os.environ.get('AI_GATEWAY_MODEL', 'gpt-4o-mini')
    print(f"Using model: {model}", file=sys.stderr)

    # Build request body — response_format is optional, not all providers support it
    request_body = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7,
        'max_tokens': 4000,
    }
    if os.environ.get('AI_GATEWAY_JSON_MODE', '1') != '0':
        request_body['response_format'] = {'type': 'json_object'}

    try:
        response = requests.post(
            os.environ.get('AI_GATEWAY_BASE_URL', 'https://your-gateway.example.com/api/v1').rstrip('/') + '/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=request_body,
            timeout=90,
            verify=False
        )

        if response.status_code == 200:
            result = response.json()
            content_text = result['choices'][0]['message']['content']
            # Strip markdown code fences if model wraps JSON in ```json ... ```
            content_text = re.sub(r'^```(?:json)?\s*', '', content_text.strip())
            content_text = re.sub(r'\s*```$', '', content_text)
            analyzed = json.loads(content_text)
            block_count = len(analyzed.get('blocks', []))
            print(f"AI analysis complete: {block_count} content blocks generated", file=sys.stderr)
            return analyzed
        else:
            print(f"API error ({response.status_code}): {response.text[:200]}", file=sys.stderr)
            return fallback_analysis(web_data)

    except Exception as e:
        print(f"LLM analysis error: {e}", file=sys.stderr)
        return fallback_analysis(web_data)


def fallback_analysis(web_data: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based fallback when LLM is unavailable"""
    print("Using fallback content analysis...", file=sys.stderr)

    title = web_data.get('title', 'Untitled')
    content = web_data.get('content', '')

    blocks = []
    blocks.append({"type": "text", "content": content[:200] if content else "Content analysis in progress..."})

    # Split content into sections
    parts = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]

    for i, part in enumerate(parts[:6]):
        blocks.append({
            "type": "section",
            "title": f"Key Point {i+1}",
            "points": [s.strip() for s in part.split('. ') if len(s.strip()) > 20][:4]
        })

    return {
        "meta": {
            "author": "Content Analysis",
            "source": web_data.get('url', ''),
            "title": title[:30],
            "subtitle": "",
            "description": content[:60] if content else ""
        },
        "blocks": blocks
    }


def generate_html(data: Dict[str, Any]) -> str:
    """Generate professional editorial HTML from structured content blocks"""

    meta = data.get('meta', {})
    blocks = data.get('blocks', [])

    # Accent color - green/teal matching the reference
    accent = "#1a9a6b"
    accent_light = "#e8f5ee"
    accent_dark = "#15784f"
    yellow_bg = "#fef9e7"
    yellow_border = "#f0d858"
    red_accent = "#e74c3c"

    # Build blocks HTML
    blocks_html = ""

    for block in blocks:
        btype = block.get('type', 'text')

        if btype == 'text':
            content = block.get('content', '')
            blocks_html += f"""
    <div class="block-text">
      <p>{content}</p>
    </div>"""

        elif btype == 'insight':
            label = block.get('label', '核心洞察')
            content = block.get('content', '')
            blocks_html += f"""
    <div class="block-insight">
      <div class="insight-label">{label}：</div>
      <div class="insight-content">{content}</div>
    </div>"""

        elif btype == 'steps':
            title = block.get('title', '')
            items = block.get('items', [])
            steps_inner = ""
            for item in items:
                num = item.get('number', '')
                t = item.get('title', '')
                sub = item.get('subtitle', '')
                points = item.get('points', [])
                points_html = "".join([f"<li>{p}</li>" for p in points])
                steps_inner += f"""
        <div class="step-card">
          <div class="step-number">{num}</div>
          <div class="step-title">{t}</div>
          <div class="step-subtitle">{sub}</div>
          <ul class="step-points">{points_html}</ul>
        </div>"""
            blocks_html += f"""
    <div class="block-steps">
      {f'<h3 class="block-title">{title}</h3>' if title else ''}
      <div class="steps-grid">{steps_inner}
      </div>
    </div>"""

        elif btype == 'section':
            title = block.get('title', '')
            content = block.get('content', '')
            points = block.get('points', [])
            points_html = "".join([f"<li><span class='bullet'>▸</span> {p}</li>" for p in points])
            blocks_html += f"""
    <div class="block-section">
      <h3 class="section-heading">{title}</h3>
      {f'<p class="section-lead">{content}</p>' if content else ''}
      <ul class="section-points">{points_html}</ul>
    </div>"""

        elif btype == 'comparison':
            columns = block.get('columns', [])
            cols_html = ""
            for col in columns:
                ct = col.get('title', '')
                cs = col.get('subtitle', '')
                cpoints = col.get('points', [])
                cp_html = "".join([f"<li><span class='check'>✦</span> {p}</li>" for p in cpoints])
                cols_html += f"""
        <div class="comp-column">
          <div class="comp-title">{ct}</div>
          {f'<div class="comp-subtitle">{cs}</div>' if cs else ''}
          <ul class="comp-points">{cp_html}</ul>
        </div>"""
            blocks_html += f"""
    <div class="block-comparison">
      <div class="comp-grid">{cols_html}
      </div>
    </div>"""

        elif btype == 'questions':
            title = block.get('title', '')
            items = block.get('items', [])
            icon_color = block.get('icon', 'red')
            qs_html = "".join([f'<li><span class="q-bullet">●</span> {q}</li>' for q in items])
            blocks_html += f"""
    <div class="block-questions">
      <div class="questions-icon">❓</div>
      {f'<h3 class="questions-title">{title}</h3>' if title else ''}
      <ul class="questions-list">{qs_html}</ul>
    </div>"""

        elif btype == 'stats':
            items = block.get('items', [])
            stats_html = ""
            for item in items:
                val = item.get('value', '')
                label = item.get('label', '')
                stats_html += f"""
        <div class="stat-item">
          <div class="stat-value">{val}</div>
          <div class="stat-label">{label}</div>
        </div>"""
            blocks_html += f"""
    <div class="block-stats">
      <div class="stats-grid">{stats_html}
      </div>
    </div>"""

        elif btype == 'list':
            title = block.get('title', '')
            items = block.get('items', [])
            list_html = ""
            for i, item in enumerate(items):
                list_html += f'<li><span class="list-num">{i+1}.</span> {item}</li>'
            blocks_html += f"""
    <div class="block-list">
      <h3 class="list-title">{title}</h3>
      <ol class="numbered-list">{list_html}</ol>
    </div>"""

        elif btype == 'quote':
            content = block.get('content', '')
            source = block.get('source', '')
            blocks_html += f"""
    <div class="block-quote">
      <div class="quote-mark">&#x275D;</div>
      <div class="quote-text">{content}</div>
      {f'<div class="quote-source">{source}</div>' if source else ''}
    </div>"""

        elif btype == 'divider':
            blocks_html += '<div class="block-divider"><hr /></div>'

        elif btype == 'highlight':
            content = block.get('content', '')
            blocks_html += f"""
    <div class="block-highlight">
      <p>{content}</p>
    </div>"""

    # Full HTML with embedded CSS
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Noto+Serif+SC:wght@400;700&display=swap" rel="stylesheet">
<style>
* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #FFFFFF;
  color: #1a1a2e;
  width: 780px;
  margin: 0 auto;
  padding: 0;
  line-height: 1.75;
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
}}

.container {{
  padding: 48px 50px 40px;
  background: #FFFFFF;
}}

/* === HEADER === */
.header {{
  margin-bottom: 32px;
}}

.header-meta {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  color: #666;
}}

.header-meta .icon {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: {accent};
  color: white;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}}

.header-meta .author {{
  color: {accent};
  font-weight: 500;
}}

.header-title {{
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 36px;
  font-weight: 900;
  line-height: 1.3;
  color: #0d0d0d;
  margin-bottom: 10px;
  letter-spacing: -0.5px;
}}

.header-subtitle {{
  font-size: 11px;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 6px;
  font-weight: 400;
}}

.header-desc {{
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}}

/* === BLOCK: TEXT === */
.block-text {{
  margin: 20px 0;
  padding: 0;
}}

.block-text p {{
  font-size: 15px;
  line-height: 1.85;
  color: #333;
}}

/* === BLOCK: INSIGHT === */
.block-insight {{
  margin: 28px 0;
  padding: 22px 28px;
  background: {accent};
  border-radius: 10px;
  color: white;
}}

.insight-label {{
  font-size: 13px;
  font-weight: 700;
  opacity: 0.9;
  margin-bottom: 6px;
}}

.insight-content {{
  font-size: 14.5px;
  line-height: 1.8;
  font-weight: 400;
}}

/* === BLOCK: STEPS === */
.block-steps {{
  margin: 28px 0;
}}

.block-title {{
  font-size: 17px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 16px;
}}

.steps-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 14px;
}}

.step-card {{
  background: #f8fafb;
  border-radius: 10px;
  padding: 20px 16px 18px;
  text-align: center;
  border: 1px solid #eef2f5;
}}

.step-number {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: {accent};
  color: white;
  border-radius: 50%;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 10px;
}}

.step-title {{
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}}

.step-subtitle {{
  font-size: 12px;
  color: #888;
  margin-bottom: 10px;
}}

.step-points {{
  list-style: none;
  text-align: left;
  padding: 0;
}}

.step-points li {{
  font-size: 12.5px;
  color: #555;
  line-height: 1.7;
  padding: 2px 0;
  position: relative;
  padding-left: 12px;
}}

.step-points li::before {{
  content: '·';
  position: absolute;
  left: 0;
  color: {accent};
  font-weight: bold;
}}

/* === BLOCK: SECTION === */
.block-section {{
  margin: 24px 0;
  padding: 0;
}}

.section-heading {{
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 2px solid {accent};
  display: inline-block;
}}

.section-lead {{
  font-size: 15px;
  color: #444;
  line-height: 1.8;
  margin-bottom: 12px;
}}

.section-points {{
  list-style: none;
  padding: 0;
}}

.section-points li {{
  font-size: 14.5px;
  color: #333;
  line-height: 1.8;
  padding: 5px 0;
  padding-left: 22px;
  position: relative;
}}

.section-points li .bullet {{
  position: absolute;
  left: 0;
  color: {accent};
  font-weight: bold;
  font-size: 14px;
}}

/* === BLOCK: COMPARISON === */
.block-comparison {{
  margin: 28px 0;
}}

.comp-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}}

.comp-column {{
  background: #f8fafb;
  border-radius: 10px;
  padding: 20px;
  border: 1px solid #eef2f5;
}}

.comp-title {{
  font-size: 15px;
  font-weight: 700;
  color: {accent};
  margin-bottom: 4px;
}}

.comp-subtitle {{
  font-size: 12px;
  color: #888;
  margin-bottom: 12px;
}}

.comp-points {{
  list-style: none;
  padding: 0;
}}

.comp-points li {{
  font-size: 13.5px;
  color: #444;
  line-height: 1.7;
  padding: 4px 0;
  padding-left: 20px;
  position: relative;
}}

.comp-points li .check {{
  position: absolute;
  left: 0;
  color: {accent};
  font-size: 11px;
}}

/* === BLOCK: QUESTIONS === */
.block-questions {{
  margin: 28px 0;
  padding: 22px 28px;
  background: {yellow_bg};
  border-left: 4px solid {yellow_border};
  border-radius: 0 10px 10px 0;
}}

.questions-icon {{
  font-size: 20px;
  margin-bottom: 8px;
}}

.questions-title {{
  font-size: 16px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 12px;
}}

.questions-list {{
  list-style: none;
  padding: 0;
}}

.questions-list li {{
  font-size: 15px;
  color: #333;
  line-height: 1.8;
  padding: 4px 0;
  padding-left: 22px;
  position: relative;
}}

.questions-list li .q-bullet {{
  position: absolute;
  left: 0;
  color: {red_accent};
  font-size: 10px;
  top: 10px;
}}

/* === BLOCK: STATS === */
.block-stats {{
  margin: 28px 0;
  padding: 28px 0;
  background: {yellow_bg};
  border-radius: 10px;
}}

.stats-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  text-align: center;
}}

.stat-item {{
  padding: 10px;
}}

.stat-value {{
  font-size: 36px;
  font-weight: 900;
  color: #1a1a2e;
  line-height: 1.2;
  letter-spacing: -1px;
}}

.stat-label {{
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}}

/* === BLOCK: LIST === */
.block-list {{
  margin: 24px 0;
}}

.list-title {{
  font-size: 17px;
  font-weight: 700;
  color: {accent};
  margin-bottom: 12px;
}}

.numbered-list {{
  list-style: none;
  padding: 0;
}}

.numbered-list li {{
  font-size: 14.5px;
  color: #333;
  line-height: 1.8;
  padding: 5px 0;
  padding-left: 24px;
  position: relative;
}}

.numbered-list li .list-num {{
  position: absolute;
  left: 0;
  font-weight: 700;
  color: {accent};
}}

/* === BLOCK: QUOTE === */
.block-quote {{
  margin: 32px 0;
  padding: 24px 28px;
  background: {accent};
  border-radius: 10px;
  color: white;
  position: relative;
}}

.quote-mark {{
  font-size: 32px;
  opacity: 0.4;
  margin-bottom: 6px;
  line-height: 1;
}}

.quote-text {{
  font-size: 15px;
  line-height: 1.8;
  font-weight: 500;
}}

.quote-source {{
  font-size: 12px;
  opacity: 0.7;
  margin-top: 10px;
  text-align: right;
}}

/* === BLOCK: HIGHLIGHT === */
.block-highlight {{
  margin: 24px 0;
  padding: 18px 24px;
  background: linear-gradient(135deg, {accent_light} 0%, #f0faf4 100%);
  border-radius: 10px;
  border: 1px solid #c8e6d8;
}}

.block-highlight p {{
  font-size: 15px;
  color: {accent_dark};
  line-height: 1.8;
  font-weight: 500;
}}

/* === BLOCK: DIVIDER === */
.block-divider {{
  margin: 24px 0;
}}

.block-divider hr {{
  border: none;
  height: 1px;
  background: #e8e8e8;
}}

/* === FOOTER === */
.footer {{
  margin-top: 36px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  font-size: 12px;
  color: #aaa;
}}

.footer-source {{
  color: {accent};
}}
</style>
</head>
<body>
<div class="container">

  <!-- HEADER -->
  <div class="header">
    <div class="header-meta">
      <span class="icon">II</span>
      <span class="author">{meta.get('author', '')}</span>
    </div>
    <div class="header-title">{meta.get('title', 'Untitled')}</div>
    <div class="header-subtitle">{meta.get('subtitle', '')}</div>
    <div class="header-desc">{meta.get('description', '')}</div>
  </div>

  <!-- CONTENT BLOCKS -->
  {blocks_html}

  <!-- FOOTER -->
  <div class="footer">
    <span class="footer-source">{meta.get('source', '')}</span>
  </div>

</div>
</body>
</html>"""

    return html


def render_html_to_image(html_content: str, output_path: str, width: int = 780) -> str:
    """Render HTML to PNG image using Playwright for full-page capture"""
    import shutil

    output_path = os.path.expanduser(output_path)

    # Write HTML to temp file
    html_file = tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8')
    html_file.write(html_content)
    html_file.close()

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

    try:
        print("Rendering infographic with Playwright...", file=sys.stderr)

        # Create a small Node.js script for Playwright full-page screenshot
        # Write to skill directory where playwright node_modules are installed
        skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        screenshot_script = tempfile.NamedTemporaryFile(
            suffix='.mjs', delete=False, mode='w', encoding='utf-8',
            dir=skill_dir
        )
        screenshot_script.write(f"""
import {{ chromium }} from 'playwright';
import path from 'path';

const browser = await chromium.launch({{ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] }});
const page = await browser.newPage();
await page.setViewportSize({{ width: {width}, height: 800 }});
await page.goto('file://{html_file.name}', {{ waitUntil: 'networkidle' }});
await page.waitForTimeout(2000);
const h = await page.evaluate(() => document.documentElement.scrollHeight);
await page.setViewportSize({{ width: {width}, height: h }});
await page.waitForTimeout(500);
await page.screenshot({{ path: '{os.path.abspath(output_path)}', fullPage: true, type: 'png' }});
console.log('OK:' + {width} + 'x' + h);
await browser.close();
""")
        screenshot_script.close()

        env = os.environ.copy()
        env['PLAYWRIGHT_BROWSERS_PATH'] = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', os.path.expanduser('~/Library/Caches/ms-playwright'))
        # Always put skill's own node_modules first so playwright is always found
        skill_nm = os.path.join(skill_dir, 'node_modules')
        node_paths = [skill_nm] if os.path.isdir(skill_nm) else []
        for p in [os.getcwd(), os.path.expanduser('~'), '/home/node/a0/workspace']:
            nm = os.path.join(p, 'node_modules')
            if os.path.isdir(nm) and nm not in node_paths:
                node_paths.append(nm)
        if node_paths:
            env['NODE_PATH'] = ':'.join(node_paths)

        result = subprocess.run(
            ['node', screenshot_script.name],
            capture_output=True, text=True, timeout=45,
            env=env
        )

        if result.returncode == 0 and os.path.exists(output_path):
            print(f"Infographic saved: {output_path}", file=sys.stderr)
            return output_path
        else:
            print(f"Playwright error: {result.stderr[:300]}", file=sys.stderr)
            # Fallback: save HTML
            html_output = output_path.replace('.png', '.html')
            shutil.copy2(html_file.name, html_output)
            print(f"Saved HTML fallback: {html_output}", file=sys.stderr)
            return html_output

    finally:
        try:
            os.unlink(html_file.name)
        except:
            pass
        try:
            os.unlink(screenshot_script.name)
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description='Generate professional editorial infographics')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Extract command - fetch URL and output raw content JSON for Claude to analyze
    extract_parser = subparsers.add_parser('extract', help='Extract web content as JSON (for Claude to analyze)')
    extract_parser.add_argument('url', help='Web page URL to extract')
    extract_parser.add_argument('--output', default='-', help='Output JSON file path (default: stdout)')
    extract_parser.add_argument('--js', action='store_true', help='Use Playwright to render JS before extracting (for SPA/React/Next.js sites)')

    # Analyze command - fetch URL and generate (legacy: requires AI_GATEWAY_API_KEY)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze web URL and generate infographic (requires AI_GATEWAY_API_KEY)')
    analyze_parser.add_argument('url', help='Web page URL to analyze')
    analyze_parser.add_argument('--output', default=os.path.expanduser('~/info_graph/infographic.png'), help='Output file path')

    # Create command - from JSON content
    create_parser = subparsers.add_parser('create', help='Create infographic from JSON content')
    create_parser.add_argument('--content', required=True, help='Path to content JSON file')
    create_parser.add_argument('--output', default=os.path.expanduser('~/info_graph/infographic.png'), help='Output file path')

    # HTML command - just generate HTML (for debugging)
    html_parser = subparsers.add_parser('html', help='Generate HTML only (no screenshot)')
    html_parser.add_argument('--content', required=True, help='Path to content JSON file')
    html_parser.add_argument('--output', default=os.path.expanduser('~/info_graph/infographic.html'), help='Output HTML file path')

    args = parser.parse_args()

    if args.command == 'extract':
        print(f"Fetching content from {args.url}...", file=sys.stderr)
        if args.js:
            web_data = fetch_web_content_js(args.url)
        else:
            web_data = fetch_web_content(args.url)

        if not web_data.get('content'):
            hint = " Try --js for JavaScript-rendered sites." if not args.js else ""
            print(f"Warning: No content extracted.{hint}", file=sys.stderr)

        output_json = json.dumps(web_data, ensure_ascii=False, indent=2)

        if args.output == '-':
            print(output_json)
        else:
            os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            print(f"Content saved to: {args.output}", file=sys.stderr)

    elif args.command == 'analyze':
        print(f"Fetching content from {args.url}...", file=sys.stderr)
        web_data = fetch_web_content(args.url)

        if not web_data.get('content'):
            print("Warning: No content extracted from URL. The site may use JavaScript rendering.", file=sys.stderr)

        analyzed = analyze_with_llm(web_data)
        html = generate_html(analyzed)

        # Save HTML version too
        html_path = args.output.replace('.png', '.html')
        os.makedirs(os.path.dirname(html_path) if os.path.dirname(html_path) else 'outputs', exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML saved to: {html_path}", file=sys.stderr)

        # Render to image
        output = render_html_to_image(html, args.output)
        print(f"\nInfographic generated: {output}")

    elif args.command == 'create':
        with open(args.content, 'r', encoding='utf-8') as f:
            raw = f.read()
        # Strip markdown code fences in case agent wrapped JSON in ```json ... ```
        raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
        raw = re.sub(r'\s*```$', '', raw)
        data = json.loads(raw)

        html = generate_html(data)

        # Save HTML
        html_path = args.output.replace('.png', '.html')
        os.makedirs(os.path.dirname(html_path) if os.path.dirname(html_path) else 'outputs', exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML saved to: {html_path}", file=sys.stderr)

        # Render to image
        output = render_html_to_image(html, args.output)
        print(f"\nInfographic generated: {output}")

    elif args.command == 'html':
        with open(args.content, 'r', encoding='utf-8') as f:
            raw = f.read()
        # Strip markdown code fences in case agent wrapped JSON in ```json ... ```
        raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
        raw = re.sub(r'\s*```$', '', raw)
        data = json.loads(raw)

        html = generate_html(data)

        os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else 'outputs', exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML generated: {args.output}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
