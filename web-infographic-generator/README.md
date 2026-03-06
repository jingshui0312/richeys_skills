# 网页内容信息长图生成器 v2

深度分析网页内容并生成专业级信息长图，对齐 36氪、极客公园、少数派专栏的品质。

## 设计理念

**Agent 做分析，CLI 做渲染。** 内容理解由运行此 skill 的 Agent（Claude、GLM、MiniMax 等任意 LLM）完成，CLI 工具负责内容提取和图片渲染，无需额外 API Key。

## 工作流

### Path 1：Agent + CLI（推荐）

```bash
# Step 1：提取网页内容
web-infographic extract "<url>"

# Step 2：Agent 分析内容，生成 content.json（见格式说明）

# Step 3：渲染为信息长图
web-infographic create --content /tmp/content.json --output ~/info_graph/result.png
```

### Path 2：纯 Agent 模式（无 Bash 工具时）

Agent 通过 WebFetch 抓取网页内容 → 分析生成 HTML → 保存到 `~/info_graph/`。

## CLI 命令

```bash
# 提取网页原始内容（输出 JSON，供 Agent 分析）
web-infographic extract "<url>"
web-infographic extract "<url>" --output raw.json

# 从 Agent 生成的 content.json 渲染 PNG
web-infographic create --content content.json [--output ~/info_graph/result.png]

# 仅生成 HTML（用于预览/调试）
web-infographic html --content content.json [--output ~/info_graph/result.html]

# 独立 CLI 模式（需要 AI_GATEWAY_API_KEY，不推荐在 skill 场景使用）
web-infographic analyze "<url>" [--output ~/info_graph/result.png]
```

## Content JSON 格式

Agent 分析后输出以下结构，保存为 JSON 文件供 CLI 渲染：

```json
{
  "meta": {
    "author": "来源/作者",
    "source": "https://example.com/article",
    "title": "中文主标题（15字以内）",
    "subtitle": "ENGLISH SUBTITLE IN CAPS",
    "description": "一句话描述"
  },
  "blocks": [
    {"type": "text", "content": "导语段落"},
    {"type": "insight", "label": "核心洞察", "content": "关键洞察"},
    {"type": "steps", "title": "步骤标题", "items": [
      {"number": 1, "title": "步骤名", "subtitle": "副标题", "points": ["要点1", "要点2"]}
    ]},
    {"type": "section", "title": "章节", "content": "引导文字", "points": ["要点1"]},
    {"type": "comparison", "columns": [
      {"title": "对比A", "subtitle": "副标题", "points": ["要点1"]},
      {"title": "对比B", "subtitle": "副标题", "points": ["要点1"]}
    ]},
    {"type": "questions", "title": "关键问题", "icon": "red", "items": ["问题1？"]},
    {"type": "stats", "items": [{"value": "90%", "label": "描述"}]},
    {"type": "list", "title": "行动清单", "items": ["行动1", "行动2"]},
    {"type": "quote", "content": "结语金句", "source": "来源"},
    {"type": "highlight", "content": "高亮文本"},
    {"type": "divider"}
  ]
}
```

## Block 类型说明

| Block 类型 | 视觉效果 |
|-----------|---------|
| `text` | 正文段落 |
| `insight` | 绿色背景核心洞察框 |
| `steps` | 编号步骤卡片网格 |
| `section` | 带标题的要点列表 |
| `comparison` | 双列对比卡片 |
| `questions` | 黄色背景关键问题 |
| `stats` | 大字数据展示 |
| `list` | 编号行动清单 |
| `quote` | 绿色背景引用结语 |
| `highlight` | 浅绿高亮文本 |
| `divider` | 分割线 |

## 输出

- **默认输出目录**：`~/info_graph/`（不存在时自动创建）
- **格式**：PNG（780px 宽，全页高度）+ HTML 同步保存
- **视觉风格**：绿色/青色主色调，对齐中文科技媒体排版标准

## 兼容性

- **任意 LLM**：SKILL.md 指令与模型无关，Claude、GLM、MiniMax 等均可驱动
- **GLM/MiniMax 输出容错**：`create` 和 `html` 命令自动剥离 Markdown 代码围栏（\`\`\`json ... \`\`\`）
- **内容无截断**：提取上限 30,000 字符，覆盖绝大多数长文

## 环境依赖

- Python 3.11+（含 `requests`、`beautifulsoup4`、`lxml`）
- Node.js + Playwright（用于截图渲染）
- Playwright Chromium 浏览器

```bash
# 安装依赖
bash install.sh
```
