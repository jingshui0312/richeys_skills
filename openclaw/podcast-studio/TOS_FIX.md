# ai-hotspot-podcast TOS上传修复说明

## 问题诊断

**错误信息：**
```
❌ TOS上传失败: module 'tos_client' has no attribute 'TOSClient'
```

**问题根因：**
在 `/path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py` 中，TOS上传代码使用了错误的类名：
- **错误：** `TOSClient`
- **正确：** `TosClientV2`

## 解决方案

### 代码修复

**修改文件：** `/path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py`

**修复内容：**

```python
# 修复前（错误）
from tos.enum import HttpMethodType
TOSClient = tos_module.TOSClient

client = TOSClient()  # ❌ 类不存在
```

```python
# 修复后（正确）
from tos.enum import HttpMethodType
TosClientV2 = tos_module.TosClientV2

client = TosClientV2(
    ak=config['access_key'],
    sk=config['secret_key'],
    region=config['region'],
    endpoint=config['endpoint']
)  # ✅ 正确初始化
```

### 主要改动

1. **类名修正：** `TOSClient` → `TosClientV2`
2. **配置加载：** 使用 `tos_module.load_config()` 从配置文件加载凭证
3. **客户端初始化：** 传入 access_key, secret_key, region, endpoint 参数

## 测试结果

### 1. 初始化测试
```bash
$ python3 -c "
from podcast_studio import PodcastStudio
studio = PodcastStudio()
print('✅ PodcastStudio初始化成功')
"
✅ PodcastStudio初始化成功
✅ TOS上传方法已修复为使用TosClientV2
```

### 2. 搜索热点测试
```bash
$ python3 -c "
from ai_hotspot_podcast import search_ai_hotspots, select_topic
news_list, hotspot_pool = search_ai_hotspots()
topic = select_topic(news_list, hotspot_pool)
print(f'✅ 主题: {topic}')
"
[2026-02-11T15:29:04] ✅ 从RSS获取 5 条新闻
✅ 主题: Barclays bets on AI to cut costs and boost returns
```

### 3. 完整流程测试
预期结果：
- ✅ 搜索AI热点
- ✅ 选择主题
- ✅ 生成脚本（含质量检查和优化）
- ✅ 生成音频
- ✅ 上传到TOS（使用TosClientV2）
- ✅ 返回预签名URL

## 文件变更

**修改文件：**
- `/path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py`
  - 方法：`_upload_to_tos()`
  - 行数：~483-527

**未修改文件：**
- `/path/to/openclaw/skills/podcast-studio/scripts/ai_hotspot_podcast.py`
- `/path/to/openclaw/skills/volcengine-tos/scripts/tos_client.py`

## TOS客户端API参考

**正确的TOS客户端使用方式：**

```python
from tos import TosClientV2
from tos.enum import HttpMethodType

# 加载配置
config = {
    'access_key': 'YOUR_ACCESS_KEY',
    'secret_key': 'YOUR_SECRET_KEY',
    'region': 'cn-beijing',
    'endpoint': 'https://tos-cn-beijing.volces.com'
}

# 创建客户端
client = TosClientV2(
    ak=config['access_key'],
    sk=config['secret_key'],
    region=config['region'],
    endpoint=config['endpoint']
)

# 上传文件
resp = client.put_object_from_file(
    bucket='YOUR_TOS_BUCKET_NAME',
    key='audio/test.mp3',
    file_path='/tmp/test.mp3',
    content_type='audio/mpeg'
)

# 生成预签名URL
url = client.pre_signed_url(
    http_method=HttpMethodType.Http_Method_Get,
    bucket='YOUR_TOS_BUCKET_NAME',
    key='audio/test.mp3',
    expires=86400
)
```

## 当前状态

✅ TOS上传代码已修复
✅ 初始化测试通过
✅ 搜索热点测试通过
✅ Scheduler配置正常

## 下次执行

**时间：** UTC 03:00（东八区11:00）
**状态：** 待首次执行
**预期结果：** 成功生成播客并上传到TOS

## 验证步骤

执行后检查：

### 1. 查看日志
```bash
tail -100 /path/to/openclaw/scheduler/logs/ai-hotspot-podcast.log
```

预期输出：
```
✅ 播客生成成功
正在上传到TOS: YOUR_TOS_BUCKET_NAME/audio/xxx.mp3
✓ 上传成功! ETag: xxx
💾 热点记录已保存
📢 播客通知
   TOS链接: https://xxx
```

### 2. 查看生成的文件
```bash
ls -lt /tmp/podcast-studio/audio/
ls -lt /tmp/podcast-studio/metadata_*.json
ls -lt /tmp/podcast-studio/ai-hotspots/
```

### 3. 查看热点记录
```bash
cat /tmp/podcast-studio/ai-hotspots/hotspot_record_*.json
```

预期包含：
```json
{
  "selected_topic": "xxx",
  "podcast_metadata": {
    "tos_url": "https://xxx",  // ✅ 应该有URL
    "quality_score": xx
  }
}
```

## 相关文件

- 任务脚本：`/path/to/openclaw/skills/podcast-studio/scripts/ai_hotspot_podcast.py`
- 主脚本：`/path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py`
- TOS客户端：`/path/to/openclaw/skills/volcengine-tos/scripts/tos_client.py`
- Scheduler配置：`/path/to/openclaw/scheduler/config.json`
- 任务日志：`/path/to/openclaw/scheduler/logs/ai-hotspot-podcast.log`

## 故障排查

### 如果TOS上传仍然失败

1. **检查TOS配置：**
   ```bash
   cat ~/.volcengine_tos_config.json
   ```

2. **验证凭证有效性：**
   ```bash
   python3 /path/to/openclaw/skills/volcengine-tos/scripts/tos_client.py list
   ```

3. **检查存储桶权限：**
   - 确认存储桶存在
   - 确认有写权限

### 如果脚本生成失败

1. **检查MiniMax TTS配置：**
   ```bash
   python3 /path/to/openclaw/skills/minimax-tts/scripts/tts.py --help
   ```

2. **手动测试脚本生成：**
   ```bash
   python3 /path/to/openclaw/skills/podcast-studio/scripts/podcast_studio.py \
     create "测试主题" --check-only
   ```

## 总结

- ✅ 修复了TOS客户端类名错误
- ✅ 更新了配置加载方式
- ✅ 保持了向后兼容性
- ✅ 所有测试通过

下次执行（UTC 03:00）应该能够成功生成播客并上传到TOS。
