# 播客 Notion 集成配置指南

## 功能说明

每次生成播客时，系统会自动将脚本上传到 Notion，包含：
- 播客主题和创建时间
- 完整脚本内容（按段落组织）
- 音频链接（TOS）
- 质量评分

## 配置步骤（使用科技日报的 Notion 目录）

### 方式 1：使用科技日报的父页面（推荐）

播客脚本会和科技日报在同一个 Notion 目录下，方便管理。

```bash
# 1. 检查是否已配置科技日报的 Notion
env | grep NOTION

# 2. 如果没有，添加以下配置到 ~/.bashrc
export NOTION_KEY="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"
export NOTION_PARENT_PAGE_ID="2f73bc49-a699-804e-a04b-fa79d992f160"

# 3. 重新加载
source ~/.bashrc
```

### 方式 2：使用独立的播客数据库

如果希望播客单独管理，可以创建专用数据库。

### 方式 2：使用独立的播客数据库

如果希望播客单独管理，可以创建专用数据库。

1. **创建 Notion 集成**：
   - 访问 https://www.notion.so/my-integrations
   - 点击 "+ New integration"
   - 填写信息并提交
   - 复制 **Internal Integration Token**（以 `secret_` 开头）

2. **创建播客数据库**：
   - 在 Notion 中创建新页面
   - 添加数据库（Table视图）
   - 添加属性：Title、状态、创建日期
   - 复制数据库 ID（URL 最后一部分）

3. **分享数据库**：
   - 在数据库页面点击 "..." → "Add connections"
   - 选择刚创建的集成

4. **配置环境变量**：
```bash
export NOTION_API_KEY="secret_xxxxxxxxxxxxx"
export NOTION_PODCAST_DATABASE_ID="a8aec43384f447ca8f6f44589f2e123"
```

## 测试

### 快速测试

```bash
# 检查环境变量
echo $NOTION_API_KEY
echo $NOTION_PODCAST_DATABASE_ID

# 测试上传（使用测试数据）
python3 << 'EOF'
import os
import sys
sys.path.insert(0, '/root/clawd/skills/podcast-studio/scripts')
from upload_to_notion import upload_podcast_script

test_metadata = {
    "topic": "测试播客",
    "created_at": "2026-02-28T00:00:00",
    "tos_url": "https://example.com/test.mp3",
    "script": {
        "sections": [
            {"type": "开场", "content": "这是测试内容。"}
        ]
    },
    "quality_check": {
        "overall_score": 85,
        "colloquialism_score": 90
    }
}

page_id = upload_podcast_script(test_metadata)
print(f"✅ 测试成功: {page_id}")
EOF
```

### 完整测试

```bash
# 生成播客（会自动上传到 Notion）
cd /root/clawd/skills/podcast-studio
python3 scripts/podcast_studio.py create "测试主题" --duration short
```

## 故障排查

### 问题 1: "未配置 NOTION_API_KEY"

**解决方案**：
```bash
# 检查环境变量
echo $NOTION_API_KEY

# 如果为空，重新设置
export NOTION_API_KEY="secret_xxx"
source ~/.bashrc
```

### 问题 2: "未配置 NOTION_PODCAST_DATABASE_ID"

**解决方案**：
1. 打开 Notion 数据库页面
2. 从 URL 复制数据库 ID
3. 设置环境变量：
```bash
export NOTION_PODCAST_DATABASE_ID="your-database-id"
```

### 问题 3: "Notion API 错误: HTTP 401"

**原因**：API 密钥无效或未分享数据库

**解决方案**：
1. 检查 API 密钥是否正确（以 `secret_` 开头）
2. 确认数据库已分享给集成（步骤 3）

### 问题 4: "Notion API 错误: HTTP 404"

**原因**：数据库 ID 错误

**解决方案**：
1. 重新从 URL 复制数据库 ID
2. 确保没有多余的空格或换行

### 问题 5: 上传成功但 Notion 中看不到

**原因**：数据库属性不匹配

**解决方案**：
确保数据库包含以下属性：
- Title (标题)
- 状态 (Select)
- 创建日期 (Date)

## 使用示例

### 查看上传的页面

上传成功后，在 Notion 中：
1. 打开播客数据库
2. 可以看到新增的页面
3. 页面标题格式：`📻 {主题}`
4. 包含完整脚本和音频链接

### 自动化流程

播客系统会在以下情况自动上传：
- 定时任务（每天11:00）
- 手动生成播客
- 批量生成播客

## 禁用功能

如果不需要上传到 Notion，可以：

### 方法 1: 修改配置文件

```json
{
  "upload_to_notion": false,
  ...
}
```

### 方法 2: 移除环境变量

```bash
unset NOTION_API_KEY
unset NOTION_PODCAST_DATABASE_ID
```

## 高级配置

### 自定义属性

可以在 `upload_to_notion.py` 中添加自定义属性：

```python
properties = {
    "状态": "已完成",
    "创建日期": created_at[:10],
    "Tags": ["科技", "AI"],  # 添加标签
    "评分": quality_check.get('overall_score', 0),  # 添加评分
}
```

### 自定义内容格式

修改 `_markdown_to_blocks` 函数以支持更多 Markdown 格式：
- 列表
- 代码块
- 引用
- 分割线

## 隐私与安全

⚠️ **重要提示**：
- **不要**将 API 密钥提交到 Git
- **不要**在公开场合分享数据库 ID
- API 密钥具有完全访问权限，请妥善保管
- 定期轮换 API 密钥（建议每 90 天）

## 费用说明

- Notion API: **免费**
- 限制：3 requests/second
- 建议在配置文件中启用速率限制

## 参考文档

- [Notion API 官方文档](https://developers.notion.com/)
- [创建集成指南](https://developers.notion.com/docs/create-a-notion-integration)
- [数据库操作](https://developers.notion.com/docs/working-with-databases)
