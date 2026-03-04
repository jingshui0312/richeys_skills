# Podcast Studio - 脚本生成与检查功能使用指南

## 快速开始

### 1. 基本使用（推荐）

```bash
# 创建播客，自动启用脚本生成、检查和优化
python3 /path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py \
  create "人工智能的发展趋势" \
  --style conversational \
  --duration medium
```

**输出示例：**
```
🎙️  开始创建播客: 人工智能的发展趋势
📚 收集资料...
🏗️  生成脚本框架...
✍️  生成脚本...
🔍 检查脚本质量...
📊 脚本质量评分: 82.5/100
   通畅性: 85 - good
   口语化: 80 - good
⚡  优化脚本...
✨ 脚本已优化，共进行3处修改
🔊 生成音频...
☁️ 上传到TOS...
✅ 播客创建完成！
```

### 2. 仅检查脚本（不生成音频）

```bash
python3 /path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py \
  create "远程办公的未来" \
  --style conversational \
  --check-only
```

### 3. 禁用自动优化

```bash
python3 /path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py \
  create "区块链技术" \
  --no-optimize
```

## 命令行参数

### 基本参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `topic` | 播客主题（必需） | `"人工智能的发展趋势"` |
| `--style` | 播客风格 | `conversational`, `informative`, `narrative`, `tech` |
| `--duration` | 时长预期 | `short`, `medium`, `long` |
| `--voice` | 声音选择 | `male-qn-qingse`, `female-tianmei` 等 |
| `--config` | 配置文件路径 | `~/.podcast_studio_config.json` |

### 新增参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--check-only` | 仅检查脚本，不生成音频 | `False` |
| `--no-optimize` | 禁用脚本自动优化 | `False` |

## 播客风格说明

### 1. conversational（对话类）- 推荐
- **特点：** 轻松、自然、像和朋友聊天
- **适用：** 日常话题、观点分享、生活体验
- **框架结构（中等时长）：**
  - 开场白 → 背景介绍 → 个人观点 → 讨论要点 → 常见问题 → 真实例子 → 核心收获 → 行动号召 → 总结结尾

### 2. informative（信息类）
- **特点：** 专业、清晰、结构化
- **适用：** 知识科普、技术讲解、行业分析
- **框架结构（中等时长）：**
  - 开场白 → 背景 → 核心概念 → 实际应用 → 挑战问题 → 案例分析 → 未来趋势 → 实践建议 → 总结结尾

### 3. narrative（叙事类）
- **特点：** 有故事感、引人入胜
- **适用：** 历史事件、人物传记、发展故事
- **框架结构（中等时长）：**
  - 开场钩子 → 故事开端 → 故事发展 → 高潮部分 → 结局部分 → 反思总结 → 结尾

### 4. tech（技术类）
- **特点：** 专业、深入、聚焦技术
- **适用：** 技术深度解析、架构设计、最佳实践
- **框架结构（中等时长）：**
  - 开场 → 技术概览 → 架构设计 → 实现细节 → 最佳实践 → 常见陷阱 → 进阶话题 → 工具资源 → 结尾

## 时长预期

| 时长 | 预计字数 | 段落数量 | 适用场景 |
|------|----------|----------|----------|
| `short` | 800-1200字 | 5-6段 | 快速分享、短视频 |
| `medium` | 1500-2500字 | 8-10段 | 标准播客、深入探讨 |
| `long` | 3000-5000字 | 12-15段 | 深度课程、技术教程 |

## 脚本质量评分

### 评分标准

- **90-100分：** 优秀 ✅
  - 可直接用于音频生成
  - 无需优化

- **75-89分：** 良好 👍
  - 建议微调
  - 但也可直接使用

- **60-74分：** 一般 ⚠️
  - 建议优化
  - 系统会自动优化

- **0-59分：** 较差 ❌
  - 需要大幅调整
  - 建议手动修改

### 检查维度

**1. 通畅性（Fluency）**
- 句子长度：平均不超过25字，单句不超过50字
- 过渡词：使用"然后"、"但是"、"所以"等连接词
- 用词重复：避免同一词汇过度使用

**2. 口语化（Colloquialism）**
- 书面语识别：避免"因此，"、"然而，"等正式表达
- 自然表达：使用"然后"、"但是"、"简单来说"等口语
- 听众互动：包含"我们"、"大家"、"你"等互动词汇

### 改进建议示例

```
💡 句子平均长度偏长，建议将长句拆分成2-3个短句。
💡 发现书面语表达：然而，。建议改为口语表达。
💡 与听众的互动表达偏少，建议增加"我们"、"大家"等词汇。
💡 段落间缺乏过渡词，建议增加连接词让表达更连贯。
```

## 输出文件

所有文件保存在 `/tmp/podcast-studio/` 目录：

| 文件类型 | 命名格式 | 说明 |
|----------|----------|------|
| 框架文件 | `framework_*.json` | 脚本框架结构 |
| 脚本文件 | `script_*.json` | 生成的脚本内容 |
| 优化脚本 | `script_optimized_*.json` | 优化后的脚本 |
| 元数据 | `metadata_*.json` | 完整播客信息 |
| 音频文件 | `podcast_*.mp3` | 生成的音频 |

## 查看和调试

### 查看生成的框架

```bash
cat /tmp/podcast-studio/framework_*.json | jq .
```

### 查看脚本内容

```bash
# 原始脚本
cat /tmp/podcast-studio/script_*.json | jq '.sections[].content'

# 优化后的脚本
cat /tmp/podcast-studio/script_optimized_*.json | jq '.sections[].content'
```

### 查看质量检查结果

```bash
cat /tmp/podcast-studio/metadata_*.json | jq '.quality_check'
```

## 常见问题

### Q: 脚本评分很低怎么办？

A: 检查以下几点：
1. 脚本是否过于书面化？尝试使用 `--style conversational`
2. 句子是否太长？系统会自动优化
3. 是否缺少过渡词？增加"然后"、"但是"等连接词

### Q: 如何自定义脚本模板？

A: 编辑 `/path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py` 中的 `_script_template_*` 方法。

### Q: 如何调整声音参数？

A: 创建配置文件 `~/.podcast_studio_config.json`：
```json
{
  "default_voice": "male-qn-qingse",
  "default_speed": 1.1,
  "default_vol": 1.0
}
```

### Q: 如何查看所有可用的声音？

A: 运行以下命令：
```bash
python3 /path/to/openclaw/skills/minimax-tts/scripts/tts.py --help
```

## 实际案例

### 案例1：技术科普（信息类）

```bash
python3 /path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py \
  create "区块链技术原理" \
  --style informative \
  --duration medium \
  --voice male-qn-qingse
```

**预期输出：**
- 9个段落的完整脚本
- 专业但不过于学术的表达
- 技术细节的通俗解释

### 案例2：观点分享（对话类）

```bash
python3 /path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py \
  create "远程办公的利弊" \
  --style conversational \
  --duration medium \
  --voice female-tianmei
```

**预期输出：**
- 轻松自然的表达风格
- 个人观点和真实体验
- 与听众的互动表达

### 案例3：技术深度解析（技术类）

```bash
python3 /path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py \
  create "Docker容器技术架构" \
  --style tech \
  --duration long \
  --voice male-chunhou
```

**预期输出：**
- 深入的技术细节
- 架构和实现分析
- 最佳实践和常见陷阱

## 下一步

1. **集成web_search** - 实现真实的资料收集
2. **LLM脚本生成** - 使用大语言模型生成脚本内容
3. **多声音支持** - 支持对话式多声音播客
4. **BGM集成** - 自动添加背景音乐

## 技术支持

- 查看完整文档：`/path/to/openclaw/skills/podcast-studio/SKILL.md`
- 查看更新日志：`/path/to/openclaw/skills/podcast-studio/UPDATE_2026-02-11.md`
- 运行测试：`python3 /path/to/openclaw/skills/podcast-studio/scripts/script_generator.py`
