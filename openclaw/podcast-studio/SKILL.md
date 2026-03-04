---
name: podcast-studio
description: 播客工作室 - 完整的播客制作流程。支持根据主题收集资料、设计脚本、生成音频并上传到TOS。使用场景：(1) 根据主题快速制作播客内容，(2) 自动化播客脚本编写和音频生成，(3) 生成多风格播客（信息类、对话类、叙事类、技术类），(4) 自动上传音频到火山引擎TOS存储，(5) 管理播客元数据和脚本归档。
---

# Podcast Studio - 播客工作室

## Overview

播客工作室提供从主题到音频的完整自动化流程，将播客制作简化为七个步骤：**资料收集 → AI深度分析 → 脚本框架生成 → 脚本内容生成 → 质量检查与优化 → 音频生成 → TOS上传**。

适用于需要快速制作播客内容、自动化脚本编写和音频生成的场景。

**新功能（2026-02-27）：**
- 🤖 **AI深度分析** - 参考url-to-infographic的深度分析思路，提取核心观点、案例、数据、类比、幽默元素等
- 💡 **趣味性增强** - 自动设计开场钩子、幽默元素、金句总结，避免套话和空洞内容
- 🎯 **结构化信息** - 提取并使用具体的数据、案例、故事，代替模糊描述
- ⚡ **降级机制** - LLM分析失败时自动降级到默认分析，保证功能可用

**历史功能（2026-02-11）：**
- ✨ 智能脚本框架生成 - 根据主题和资料特征动态生成合适的脚本结构
- 🔍 脚本质量检查 - 自动检查脚本通畅性和口语化程度
- ⚡ 脚本自动优化 - 根据检查结果自动优化脚本内容

## Quick Start

**重要说明：** 脚本生成交由大模型完成，确保内容与主题高度相关，避免套话化。

**背景音乐（BGM）：** 系统支持自动混合背景音乐，BGM会循环播放并自动调整音量。

### 步骤1：生成脚本Prompt

```bash
# 使用默认设置生成脚本Prompt
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py create "人工智能的发展趋势" --check-only

# 指定风格和时长
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py create "区块链技术" --style tech --duration medium --check-only
```

这会：
1. 生成详细的脚本Prompt并保存到 `/tmp/podcast-studio/prompt_*.txt`
2. 在终端显示Prompt内容
3. 将Prompt发送给大模型生成脚本

### 步骤2：将Prompt发送给大模型

将终端显示的Prompt内容发送给大模型，大模型会返回JSON格式的脚本。

### 步骤3：处理脚本并生成音频

将大模型返回的脚本保存为JSON文件，然后执行：

```bash
# 从JSON文件生成音频（自动混合BGM）
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py generate-audio script.json

# 指定声音
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py generate-audio script.json --voice male-qn-qingse

# 禁用BGM（默认启用）
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py generate-audio script.json --no-bgm

# 使用自定义配置
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py generate-audio script.json --config ~/.podcast_config.json
```

**注意**：BGM 默认启用，所有生成的音频都会自动混合背景音乐。如需禁用，请使用 `--no-bgm` 参数。

### 列出已创建的播客

```bash
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py list
```

### 背景音乐（BGM）配置

**默认配置**：播客工作室已配置默认背景音乐，所有生成的音频都会自动混合 BGM。

**配置文件位置**：`/root/clawd/skills/podcast-studio/config.json`

**当前配置**：
```json
{
  "bgm_file": "/root/clawd/skills/podcast-studio/assets/bgm_default.mp3",
  "bgm_volume": 0.15,
  "bgm_fade_in": 2000,
  "bgm_fade_out": 3000,
  "bgm_enabled_by_default": true
}
```

**BGM 配置参数**：
- `bgm_file`: 背景音乐文件路径（MP3格式，4.6MB）
- `bgm_volume`: BGM音量（0.15 = 15%，不会干扰语音）
- `bgm_fade_in`: 淡入时长（2秒，平滑开始）
- `bgm_fade_out`: 淡出时长（3秒，平滑结束）
- `bgm_enabled_by_default`: 默认启用 BGM

**BGM 混合逻辑**：
- ✅ BGM 会自动循环播放以匹配语音长度
- ✅ 自动降低 BGM 音量（15%，不会干扰语音）
- ✅ 支持淡入淡出效果（平滑过渡）
- ✅ 生成的文件名会添加 `_with_bgm` 后缀

**示例输出**：
```
🎵 正在混合背景音乐...
   语音时长: 180.5 秒
   BGM时长: 151.28 秒（自动循环）
   BGM音量: 15.0%
✅ 背景音乐混合完成: podcast_20260227_104127_with_bgm.mp3
```

**如何禁用 BGM**：

如果你需要生成不带 BGM 的音频（例如测试或特殊需求），可以使用 `--no-bgm` 参数：

```bash
# 生成不带 BGM 的音频
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py create "主题" --no-bgm
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py generate-audio script.json --no-bgm
```

**如何更换 BGM**：

如果你想使用自己的背景音乐：

1. **替换默认 BGM**：
   ```bash
   # 复制你的 BGM 文件到 assets 目录
   cp your_bgm.mp3 /root/clawd/skills/podcast-studio/assets/bgm_default.mp3
   ```

2. **或修改配置文件**：
   ```json
   {
     "bgm_file": "/path/to/your/custom_bgm.mp3",
     "bgm_volume": 0.2  // 调整音量（0.1-0.3 推荐）
   }
   ```

**BGM 音量建议**：
- `0.10-0.15`: 轻柔背景（推荐，不干扰语音）
- `0.15-0.25`: 中等音量（适合有氛围感的播客）
- `0.25-0.35`: 较高音量（可能干扰语音，不推荐）

**测试 BGM**：

运行测试脚本验证 BGM 配置：
```bash
python3 /tmp/test_bgm.py
python3 /tmp/test_podcast_with_bgm.py
```

### 禁用自动优化

```bash
# 跳过脚本优化，直接生成音频
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py create "主题" --no-optimize
```

## 脚本框架生成详解

## Workflow

完整的播客制作流程：

### 1. 资料收集（待实现）

当前脚本包含资料收集的框架，但需要集成实际的web_search功能。当Codex执行此技能时：

- 使用web_search搜索主题相关内容
- 使用web_fetch获取详细资料
- 整理和总结关键信息

**手动收集资料：**

如果你已经收集了资料，可以跳过自动收集，直接提供研究数据：

```python
research_data = {
    "topic": "主题",
    "key_points": ["要点1", "要点2", "要点3"],
    "sources": ["来源1", "来源2"]
}
```

### 2. AI 深度分析（新功能 v2.0）

**核心思路**：参考 url-to-infographic 的 AI 深度分析，在生成脚本前先对主题进行结构化信息提取。

**分析维度**（8个关键元素）：

1. **核心观点（core_viewpoints）** - 3-5个最有价值的见解
   - 独立、有深度、避免套话
   - 示例："从'对话'到'行动'的范式转移：AI 不仅仅是聊天机器人"

2. **案例和故事（cases_and_stories）** - 2-3个真实案例
   - 具体、生动、有细节
   - 格式：`{"name": "案例名", "description": "描述", "lesson": "启示"}`
   - 示例：Devin AI 工程师案例

3. **数据和统计（data_and_stats）** - 具体数字
   - 避免模糊表达（如"很多人"）
   - 格式：`{"data": "数据", "source": "来源", "context": "背景"}`
   - 示例："GPT-4 参数量达到 1.8 万亿"

4. **类比和比喻（analogies_and_metaphors）** - 1-2个生动类比
   - 贴近生活、容易理解
   - 示例："AI 代理就像一个能独立完成任务的实习生"

5. **争议点/反直觉观点（controversial_points）** - 挑战常识
   - 引发思考、有论证支撑
   - 示例："更多参数不等于更强能力"

6. **听众痛点（audience_pain_points）** - 具体问题
   - 真实、能引发共鸣
   - 示例："不知道如何选择合适的 AI 工具"

7. **幽默元素（humor_elements）** - 1-2个幽默点
   - 自嘲、吐槽、讽刺
   - 示例："AI 写代码比我快，但它不会喝咖啡"

8. **金句（golden_quotes）** - 1-2个总结性观点
   - 简洁、有力、易传播
   - 示例："AI 代理不是替代人类，而是放大人类能力"

**分析流程**：

```python
# 1. 触发条件
if research资料不足:
    使用 LLM 智能推断（基于主题和风格）
else:
    使用 LLM 深度分析（基于主题 + 风格 + 研究资料）

# 2. LLM 分析
prompt = 构建分析 prompt（提取8个维度）
analysis = call_llm_api(prompt, timeout=90s)

# 3. 降级机制
if analysis失败:
    使用默认分析（基础观点 + 空案例）
```

**分析结果使用**：

分析结果会传递给脚本生成器，强制要求 LLM 在脚本中使用这些内容：

- ✅ 必须融入核心观点
- ✅ 必须详细讲述案例和故事
- ✅ 必须引用具体数据
- ✅ 必须使用类比解释复杂概念
- ✅ 自然融入幽默元素
- ✅ 用金句作为总结

### 3. 脚本框架生成

系统根据主题和资料特征，智能生成脚本框架：

**特征分析：**
- 内容复杂度（低/中/高）
- 内容类型（通用/技术）
- 目标受众（普通听众/技术听众）
- 关键主题识别
- 技术深度评估

**框架调整：**
- 根据时长（短/中/长）调整段落数量
- 根据风格选择合适的结构模板
- 根据特征自动增减关键段落

### 3. 脚本内容生成

基于框架和资料生成脚本内容，支持四种风格：

**informative（信息类）** - 适合知识科普、技术讲解
- 正式、结构化、信息密集
- 示例："人工智能的发展趋势"

**conversational（对话类）** - 适合轻松话题、生活分享
- 口语化、轻松、互动性强
- 示例："远程办公的未来"

**narrative（叙事类）** - 适合故事、历史、人物传记
- 讲故事风格、有情节起伏
- 示例："改变世界的发明"

**tech（技术类）** - 适合技术深度解析
- 专业、深入、聚焦技术细节
- 示例："区块链技术原理"

### 4. 脚本质量检查（新功能）

自动检查脚本质量，确保适合口语播播：

**通畅性检查：**
- 句子长度分析（平均句长、超长句子检测）
- 过渡词使用（检查段落间是否缺少连接词）
- 用词重复度（检测词汇过度使用）

**口语化检查：**
- 书面语识别（检测"因此，"、"然而，"等正式表达）
- 口语化表达（检查是否使用自然连接词）
- 听众互动（检查"我们"、"大家"、"你"等互动词汇）

**评分系统：**
- 通畅性评分（0-100）
- 口语化评分（0-100）
- 综合评分（0-100）
- 改进建议（详细列出问题和优化方向）

### 5. 脚本优化（新功能）

当脚本评分低于85分时，系统自动进行优化：

**优化规则：**
- 书面语 → 口语化替换（"因此，" → "所以，"）
- 长句自动拆分（在逗号处分句）
- 增加过渡词（段落间添加连接词）
- 增加互动表达（加入"我们"、"大家"等）

**优化结果：**
- 显示修改内容
- 保存优化后的脚本
- 保留原始脚本备份

### 6. 音频生成

使用MiniMax TTS生成高质量音频，支持多种声音：

```bash
# 可用声音
female-tianmei     # 女声-甜美（默认）
female-shaonv      # 女声-少女
male-qn-qingse     # 男声-青涩
male-qinggan       # 男声-情感
female-yujie       # 女声-御姐
male-chunhou       # 男声-醇厚
```

音频参数通过配置文件设置：

```json
{
  "default_voice": "female-tianmei",
  "default_speed": 1.0,
  "default_vol": 1.0
}
```

### 4. TOS上传

自动上传音频到火山引擎TOS存储，返回预签名URL。

**配置TOS：**

首次使用前需要配置TOS凭证：

```bash
python3 /root/clawd/skills/volcengine-tos/scripts/tos_client.py configure \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --region cn-beijing
```

**存储桶结构：**

```
reports01/
└── audio/
    └── {主题}_{timestamp}.mp3
```

## Advanced Usage

## 脚本框架生成详解

**框架生成器会根据以下因素动态生成脚本结构：**

### 核心机制

框架生成器根据主题和资料特征，**智能生成脚本结构**，然后脚本生成器**严格遵循这个动态框架**来填充内容。这确保了脚本结构与主题内容高度匹配。

### 实现细节

**动态框架生成流程：**

1. **特征分析**：
   - 分析资料中的技术关键词数量（算法、架构、系统等）
   - 判断内容复杂度（low/medium/high）
   - 提取关键主题（技术、商业、社会、未来）
   - 评估技术深度和目标受众

2. **框架调整**：
   - 根据风格选择基础结构
   - 根据时长调整段落数量（short=简化，medium=完整，long=扩展）
   - 根据复杂度调整内容深度（高复杂度→增加解释环节）

3. **脚本生成**：
   - **严格使用框架的 sections 结构**
   - 每个段落根据 section_guides 生成内容
   - 结合风格、基调、语言风格进行内容创作
   - 根据复杂度和主题特征调整内容深度

### 输入分析
- **主题内容**：分析主题涉及的技术、商业、社会、未来等维度
- **资料特征**：根据收集到的资料判断复杂度和技术深度
- **播客风格**：选择适合的风格模板
- **时长预期**：调整段落数量和深度

### 框架结构示例

**对话风格（conversational）- 短播客：**
```
1. intro - 开场白
2. background - 背景介绍
3. discussion_points - 讨论要点
4. takeaways - 核心收获
5. outro - 总结结尾
```

**信息风格（informative）- 中等时长：**
```
1. intro - 开场白
2. background - 背景
3. core_concepts - 核心概念
4. applications - 实际应用
5. challenges - 挑战问题
6. case_studies - 案例分析
7. future_trends - 未来趋势
8. practical_guidance - 实践建议
9. outro - 总结结尾
```

### 智能调整

框架生成器会自动根据资料特征调整：
- **高技术深度** → 增加"简化解释"段落
- **复杂度高** → 简化框架，聚焦核心
- **长播客** → 增加"深度探讨"、"问答"等扩展段落

### 框架结构示例对比

**conversational + short**（低复杂度）：
```json
sections: [
  "intro", "background", "discussion_points", "takeaways", "outro"
]
```

**conversational + medium**（高复杂度）：
```json
sections: [
  "intro", "background", "simplification", "discussion_points",
  "takeaways", "call_to_action", "outro"
]
```

**tech + short**：
```json
sections: [
  "intro", "technical_overview", "implementation_details", "best_practices", "outro"
]
```

**informative + medium**：
```json
sections: [
  "intro", "background", "core_concepts", "applications",
  "challenges", "case_studies", "future_trends",
  "practical_guidance", "outro"
]
```

**重要特性：框架结构完全由主题和风格决定，而非固定模板！**

## 脚本质量检查详解

创建配置文件 `~/.podcast_studio_config.json`：

```json
{
  "tos_bucket": "reports01",
  "default_voice": "female-yujie",
  "default_speed": 1.2,
  "default_vol": 1.1,
  "output_format": "mp3"
}
```

使用配置文件：

```bash
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py create "主题" --config ~/.podcast_studio_config.json
```

### 多子主题播客

当主题涉及多个方面时，可以指定子主题：

```bash
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py create "健康生活" \
  --subtopics "饮食" "运动" "睡眠" "心理健康"
```

子主题将用于资料收集和脚本生成（未来版本支持）。

### 查看播客元数据

所有播客的元数据保存在 `/tmp/podcast-studio/metadata_*.json`，包含：

- topic - 主题
- script - 完整脚本
- research - 研究资料
- audio_file - 音频文件路径
- tos_url - TOS链接
- created_at - 创建时间

## Codex Integration

当Codex使用此技能时：

1. **接收主题请求** - 用户说"帮我做一个关于X的播客"
2. **资料收集** - 使用web_search收集相关资料（待实现）
3. **生成脚本框架** - 根据主题和资料特征智能生成框架结构
4. **生成脚本内容** - 基于框架生成脚本内容
5. **质量检查** - 自动检查脚本通畅性和口语化
6. **脚本优化** - 根据检查结果自动优化（评分<85时）
7. **音频生成** - 使用TTS生成音频文件
8. **TOS上传** - 上传音频并返回链接
9. **返回结果** - 提供脚本预览、质量评分和音频链接

**示例交互：**

```
用户: 帮我做一个关于"远程办公的未来"的播客
Codex: 好的，我来为你创建这个播客...
[执行 podcast_studio.py create]
🎙️ 开始创建播客: 远程办公的未来
📚 收集资料...
🏗️ 生成脚本框架...
✍️ 生成脚本...
🔍 检查脚本质量...
📊 脚本质量评分: 82.5/100
   通畅性: 85 - good
   口语化: 80 - good
⚡ 优化脚本...
✨ 脚本已优化，共进行3处修改
🔊 生成音频...
☁️ 上传到TOS...
✅ 播客创建完成！

播客已创建！
- 脚本风格：对话类
- 时长：约3-5分钟
- 质量评分：82.5/100（优化后预期85+）
- 音频：已上传到TOS
- 链接：[TOS URL]

质量检查结果：
- 通畅性：85分 - 良好
- 口语化：80分 - 良好
- 已应用优化：3处修改

脚本预览（优化后）：
[显示优化后的脚本片段]
```

## AI 深度分析功能详解（v2.0 新增）

### 为什么需要深度分析？

**之前的问题**：
- ❌ 脚本内容浅薄，缺乏深度
- ❌ 大量使用套话（"这是一个非常有意思的话题"）
- ❌ 缺乏具体数据、案例、故事
- ❌ 没有幽默元素，枯燥无味
- ❌ 没有引发思考的争议点

**现在的改进**：
- ✅ 自动提取核心观点（有深度、有见解）
- ✅ 自动搜索和整理案例故事（具体、生动）
- ✅ 自动引用具体数据（避免模糊表达）
- ✅ 自动设计类比和比喻（易于理解）
- ✅ 自动添加幽默元素（自然、有趣）
- ✅ 自动提取金句（易于传播）

### 使用示例

**示例 1：AI 代理主题**

```bash
# 生成播客（自动进行深度分析）
python3 /root/clawd/skills/podcast-studio/scripts/podcast_studio.py create "AI 代理的发展趋势" --style conversational --duration short
```

**深度分析输出**：
```json
{
  "core_viewpoints": [
    "从'对话'到'行动'的范式转移：AI 不仅仅是聊天机器人",
    "单体模型的终结与多智能体协作的兴起"
  ],
  "cases_and_stories": [
    {
      "name": "Devin: 世界上第一个 AI 软件工程师",
      "description": "不仅能写代码，还能像真正的工程师一样规划任务、部署应用、修复 Bug",
      "lesson": "AI 代理已经能独立完成复杂工作流"
    }
  ],
  "data_and_stats": [
    {
      "data": "GPT-4 参数量 1.8 万亿",
      "source": "OpenAI",
      "context": "但参数量不等于能力"
    }
  ],
  "analogies_and_metaphors": [
    "AI 代理就像一个能独立完成任务的实习生"
  ],
  "controversial_points": [
    "更多参数不等于更强能力，架构设计更重要"
  ],
  "audience_pain_points": [
    "不知道如何选择合适的 AI 工具"
  ],
  "humor_elements": [
    "AI 写代码比我快，但它不会喝咖啡"
  ],
  "golden_quotes": [
    "AI 代理不是替代人类，而是放大人类能力"
  ]
}
```

**脚本生成效果对比**：

❌ **优化前**：
```
今天我们来聊聊 AI 代理。这是一个非常有意思的话题。
首先，让我们了解一下 AI 代理的背景。这个领域正在快速发展...
```

✅ **优化后**：
```
你知道吗？现在有个 AI 叫 Devin，它不仅能写代码，还能像个真正的工程师一样规划任务、部署应用、甚至修复 Bug。
这就引出了我们今天要聊的核心问题：AI 代理正在从"对话"转向"行动"。
不再是简单的聊天机器人，而是能独立完成工作流的智能助手。
就像一个不需要喝咖啡的实习生（虽然它确实不需要喝咖啡）。
```

### 分析文件说明

每次运行会生成以下文件（保存在 `/tmp/podcast-studio/`）：

1. **`analysis_prompt_*.txt`** - 分析 prompt（用于调试）
2. **`analysis_*.json`** - 分析结果（8个维度的结构化数据）
3. **`prompt_*.txt`** - 脚本生成 prompt（包含分析结果）
4. **`script_*.json`** - 最终脚本

### 查看分析结果

```bash
# 查看最新的分析结果
cat /tmp/podcast-studio/analysis_*.json | tail -100

# 查看分析 prompt
cat /tmp/podcast-studio/analysis_prompt_*.txt | tail -50
```

### 降级机制

当 LLM 分析失败时，系统会自动降级到默认分析：

```python
# 默认分析包含基础观点，但其他维度为空
default_analysis = {
    "core_viewpoints": [
        "主题正在改变我们的生活方式",
        "理解主题的核心原理很重要"
    ],
    "cases_and_stories": [],  # 空
    "data_and_stats": [],      # 空
    # ... 其他维度为空
}
```

降级后的脚本仍然可以生成，但缺乏深度和趣味性。

## Templates and Customization

### 添加新脚本模板

在 `scripts/podcast_studio.py` 中添加新的模板方法：

```python
def _script_template_custom(self, topic, research, duration):
    """自定义播客脚本模板"""
    return {
        "style": "custom",
        "duration": duration,
        "sections": [
            # 你的自定义段落
        ],
        "created_at": datetime.now().isoformat()
    }
```

然后在 `templates` 字典中注册：

```python
templates = {
    "informative": self._script_template_informative,
    "custom": self._script_template_custom,
    # ...
}
```

### 修改现有模板

编辑对应的 `_script_template_*` 方法，调整内容和结构。

## Limitations and Future Work

**当前限制：**

1. **资料收集** - 需要手动集成web_search，目前是占位符实现
2. **子主题支持** - 子主题参数已定义但未在脚本生成中使用
3. **多声音支持** - 当前统一使用一个声音，不支持对话式多声音
4. **BGM集成** - 不支持背景音乐添加

**未来改进：**

- 集成真实的web_search资料收集
- 支持对话式多声音播客
- 添加背景音乐和音效
- 支持多期播客系列管理
- 提供更丰富的脚本模板库

## Scripts Reference

### scripts/podcast_studio.py

主脚本，提供完整的播客制作功能：

**命令：**

- `create` - 创建新播客
  - `topic` (required) - 播客主题
  - `--subtopics` - 子主题列表
  - `--duration` - 时长预期 (short/medium/long)
  - `--voice` - 声音选择
  - `--style` - 播客风格 (informative/conversational/narrative/tech)
  - `--config` - 配置文件路径

- `list` - 列出已创建的播客

- `script` - 测试脚本生成
  - `topic` (required) - 播客主题
  - `--style` - 播客风格

**Python API:**

```python
from podcast_studio import PodcastStudio

studio = PodcastStudio(config_file="config.json")

# 创建播客
result = studio.create_podcast(
    topic="主题",
    subtopics=["子主题1", "子主题2"],
    duration="short",
    voice="female-tianmei",
    style="informative"
)

# 列出播客
podcasts = studio.list_podcasts()
```

## Dependencies

- minimax-tts (语音合成)
- volcengine-tos (对象存储)
- tos-python-sdk (TOS SDK)
- Python 3.8+

确保相关技能已正确配置并可用。
