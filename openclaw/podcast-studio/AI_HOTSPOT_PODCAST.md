# AI热点播客生成器 - 定时任务说明

## 任务概述

**任务名称：** ai-hotspot-podcast
**执行时间：** 东八区时间上午11:00（UTC 03:00）每天
**功能：** 搜索AI热点主题，生成播客并上传到TOS

## 工作流程

```
1. 搜索AI热点
   ↓
2. 选择主题（70%真实新闻 + 30%话题池）
   ↓
3. 生成播客脚本（智能框架 + 质量检查 + 自动优化）
   ↓
4. 生成音频（MiniMax TTS）
   ↓
5. 上传到TOS
   ↓
6. 保存记录
```

## 热点来源

### RSS新闻源
- Artificial Intelligence News
- VentureBeat AI
- The Verge AI

### 备用话题池
预设10个AI热点话题，当RSS源失败时使用：

1. 大语言模型的最新突破与应用
2. AI Agent智能代理的发展与未来
3. 多模态AI技术的融合创新
4. AI在医疗健康领域的应用进展
5. 生成式AI对创意产业的影响
6. AI伦理与安全问题的讨论
7. 边缘AI与移动端AI的发展
8. AI Agent框架与工具生态系统
9. AI在自动驾驶领域的进展
10. AI编程助手与开发者生产力

## 播客参数

- **风格：** conversational（对话类）
- **时长：** medium（中等，1500-2500字）
- **声音：** male-qn-qingse（男声-青涩）
- **优化：** 启用自动优化

## 脚本质量检查

系统会自动检查脚本质量：

- **通畅性检查：** 句子长度、过渡词、用词重复
- **口语化检查：** 书面语识别、自然表达、听众互动
- **自动优化：** 评分 < 85时自动优化

## 输出文件

### 播客文件
- 脚本：`/tmp/podcast-studio/script_*.json`
- 音频：`/tmp/podcast-studio/podcast_*.mp3`
- 元数据：`/tmp/podcast-studio/metadata_*.json`

### 热点记录
- 记录文件：`/tmp/podcast-studio/ai-hotspots/hotspot_record_YYYYMMDD.json`
- 包含：选定主题、新闻列表、播客元数据

### 日志文件
- 任务日志：`/root/clawd/scheduler/logs/ai-hotspot-podcast.log`
- Scheduler日志：`/root/clawd/scheduler/logs/scheduler.log`

## 手动运行

### 测试搜索（不生成播客）
```bash
python3 -c "
import sys
sys.path.insert(0, '/root/clawd/skills/podcast-studio/scripts')
from ai_hotspot_podcast import search_ai_hotspots, select_topic
news, pool = search_ai_hotspots()
topic = select_topic(news, pool)
print(f'主题: {topic}')
"
```

### 完整运行（生成播客）
```bash
python3 /root/clawd/skills/podcast-studio/scripts/ai_hotspot_podcast.py
```

### 仅检查脚本
```bash
python3 -c "
import sys
sys.path.insert(0, '/root/clawd/skills/podcast-studio/scripts')
from ai_hotspot_podcast import search_ai_hotspots, select_topic
from podcast_studio import PodcastStudio

# 获取主题
news, pool = search_ai_hotspots()
topic = select_topic(news, pool)

# 检查脚本
studio = PodcastStudio()
framework = studio._generate_framework(topic, {}, 'conversational', 'medium')
script = studio._generate_script_from_framework(framework, {})
check = studio._check_script(script)
print(f'评分: {check[\"overall_score\"]}')
"
```

## 管理命令

### 查看任务列表
```bash
/root/clawd/scheduler/scheduler.sh list
```

### 查看任务状态
```bash
/root/clawd/scheduler/scheduler.sh status
```

### 查看任务日志
```bash
/root/clawd/scheduler/scheduler.sh logs ai-hotspot-podcast
```

### 手动运行任务
```bash
/root/clawd/scheduler/scheduler.sh run ai-hotspot-podcast
```

### 禁用/启用任务
```bash
# 禁用
/root/clawd/scheduler/scheduler.sh disable ai-hotspot-podcast

# 启用
/root/clawd/scheduler/scheduler.sh enable ai-hotspot-podcast
```

### 重启Scheduler
```bash
/root/clawd/scheduler/scheduler.sh restart
```

## 查看结果

### 查看最新热点记录
```bash
ls -lt /tmp/podcast-studio/ai-hotspots/ | head -5
cat /tmp/podcast-studio/ai-hotspots/hotspot_record_*.json | jq .
```

### 查看播客元数据
```bash
ls -lt /tmp/podcast-studio/metadata_*.json | head -5
cat /tmp/podcast-studio/metadata_*.json | jq .quality_check
```

### 查看脚本质量
```bash
cat /tmp/podcast-studio/metadata_*.json | jq '.quality_check'
```

## 配置文件

### Scheduler配置
位置：`/root/clawd/scheduler/config.json`

```json
{
  "tasks": {
    "ai-hotspot-podcast": {
      "name": "ai-hotspot-podcast",
      "description": "AI热点播客生成",
      "enabled": true,
      "schedule": {
        "type": "cron",
        "expr": "0 3 * * *",
        "timezone": "UTC"
      },
      "command": "python3 /root/clawd/skills/podcast-studio/scripts/ai_hotspot_podcast.py",
      "timeout": 600,
      "retry": {
        "max": 2,
        "delay": 60
      },
      "logging": {
        "file": "/root/clawd/scheduler/logs/ai-hotspot-podcast.log",
        "level": "info"
      }
    }
  }
}
```

## 时间说明

- **执行时间：** UTC 03:00 每天
- **东八区时间：** 上午11:00（夏令时12:00）
- **下次执行：** 使用 `date` 查看

```bash
# 查看下次执行时间（UTC）
date -d "03:00 today"

# 查看东八区对应时间
TZ='Asia/Shanghai' date -d "03:00 UTC today"
```

## 故障排查

### 任务未执行
1. 检查Scheduler状态：`/root/clawd/scheduler/scheduler.sh status`
2. 检查任务是否启用：`/root/clawd/scheduler/scheduler.sh list`
3. 查看日志：`/root/clawd/scheduler/scheduler.sh logs ai-hotspot-podcast`

### RSS源失败
- 系统会自动使用话题池
- 检查网络连接
- 查看 `ai-hotspot-podcast.log`

### TTS生成失败
- 检查MiniMax TTS配置
- 查看错误日志
- 可能是API配额问题

### TOS上传失败
- 检查TOS凭证配置
- 检查存储桶权限
- 查看详细错误信息

## 扩展功能建议

### 1. 集成Telegram通知
可以自动发送播客链接到Telegram频道

### 2. 主题过滤
添加主题过滤规则，避免重复或无关主题

### 3. 多语言支持
生成中文和英文双语播客

### 4. 自定义风格
支持用户自定义播客风格和时长

### 5. 热点评分
根据热度、时效性等因素对热点进行评分

## 监控与维护

### 每日检查
```bash
# 检查任务执行
/root/clawd/scheduler/scheduler.sh status

# 查看最新播客
ls -lt /tmp/podcast-studio/metadata_*.json | head -1

# 查看质量评分
cat /tmp/podcast-studio/metadata_*.json | tail -1 | jq '.quality_check'
```

### 每周维护
- 清理旧文件（保留最近7天）
- 更新RSS源列表
- 调整话题池

### 每月优化
- 分析播客质量趋势
- 优化脚本模板
- 更新热点来源

## 技术支持

如有问题，请查看：
- Scheduler框架文档：`/root/clawd/SCHEDULER_FRAMEWORK.md`
- Podcast Studio文档：`/root/clawd/skills/podcast-studio/SKILL.md`
- 使用指南：`/root/clawd/skills/podcast-studio/USAGE_GUIDE.md`
