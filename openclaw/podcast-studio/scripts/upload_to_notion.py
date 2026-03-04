#!/usr/bin/env python3
"""
上传播客脚本到 Notion
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


class NotionUploader:
    """Notion 上传器"""
    
    def __init__(self, api_key=None, database_id=None, parent_page_id=None):
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id
        self.parent_page_id = parent_page_id or os.getenv("NOTION_PARENT_PAGE_ID")
        self.base_url = "https://api.notion.com/v1"
        
        if not self.api_key:
            raise ValueError("缺少 NOTION_API_KEY，请在环境变量中设置或传入参数")
    
    def _call_api(self, endpoint, method="POST", data=None):
        """调用 Notion API"""
        url = f"{self.base_url}/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        try:
            req = urllib.request.Request(
                url,
                method=method,
                headers=headers,
                data=json.dumps(data).encode("utf-8") if data else None
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                response_text = resp.read().decode("utf-8")
                return json.loads(response_text)
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            print(f"❌ Notion API 错误: HTTP {e.code}")
            print(f"   响应: {error_body}")
            raise
        except Exception as e:
            print(f"❌ Notion API 调用失败: {e}")
            raise
    
    def create_page(self, title, content, properties=None):
        """
        创建 Notion 页面
        
        Args:
            title: 页面标题
            content: 页面内容（Markdown格式）
            properties: 自定义属性（字典）
        
        Returns:
            str: 页面 ID
        """
        # 优先使用 parent_page_id（创建子页面），否则使用 database_id（创建数据库行）
        if self.parent_page_id:
            # 创建子页面（科技日报模式）
            data = {
                "parent": {"page_id": self.parent_page_id},
                "properties": {
                    "title": [{"text": {"content": title}}]
                },
                "children": self._markdown_to_blocks(content)
            }
        elif self.database_id:
            # 创建数据库行（播客数据库模式）
            page_properties = {
                "Title": {
                    "title": [{"text": {"content": title}}]
                }
            }
            
            # 添加自定义属性
            if properties:
                for key, value in properties.items():
                    if isinstance(value, str):
                        page_properties[key] = {"rich_text": [{"text": {"content": value}}]}
                    elif isinstance(value, list):
                        page_properties[key] = {"multi_select": [{"name": v} for v in value]}
                    elif isinstance(value, bool):
                        page_properties[key] = {"checkbox": value}
                    elif isinstance(value, (int, float)):
                        page_properties[key] = {"number": value}
            
            # 构建页面内容
            blocks = self._markdown_to_blocks(content)
            
            data = {
                "parent": {"database_id": self.database_id},
                "properties": page_properties,
                "children": blocks
            }
        else:
            raise ValueError("需要配置 parent_page_id 或 database_id")
        
        result = self._call_api("pages", data=data)
        page_id = result.get("id")
        
        print(f"✅ Notion 页面创建成功: {page_id}")
        return page_id
    
    def _markdown_to_blocks(self, markdown_text):
        """
        将 Markdown 文本转换为 Notion blocks（简化版）
        
        Args:
            markdown_text: Markdown 文本
        
        Returns:
            list: Notion blocks
        """
        blocks = []
        
        # 按段落分割
        paragraphs = markdown_text.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 检测标题
            if para.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": para[2:]}}]
                    }
                })
            elif para.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": para[3:]}}]
                    }
                })
            elif para.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": para[4:]}}]
                    }
                })
            else:
                # 普通段落
                # Notion API 限制每个 block 最多 2000 字符
                if len(para) > 1900:
                    # 分割长段落
                    chunks = [para[i:i+1900] for i in range(0, len(para), 1900)]
                    for chunk in chunks:
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            }
                        })
                else:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": para}}]
                        }
                    })
        
        return blocks


def upload_podcast_script(podcast_metadata, database_id=None, parent_page_id=None):
    """
    上传播客脚本到 Notion（主入口函数）
    
    Args:
        podcast_metadata: 播客元数据（包含主题、脚本、音频链接等）
        database_id: Notion 数据库 ID（可选，用于数据库模式）
        parent_page_id: Notion 父页面 ID（可选，用于子页面模式）
    
    Returns:
        str: Notion 页面 ID，失败返回 None
    """
    # 获取配置（复用科技日报的配置）
    api_key = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_KEY")
    database_id = database_id or os.getenv("NOTION_PODCAST_DATABASE_ID")
    parent_page_id = parent_page_id or os.getenv("NOTION_PARENT_PAGE_ID")
    
    if not api_key:
        print("⚠️  未配置 NOTION_API_KEY，跳过 Notion 上传")
        print("💡 提示：请在环境变量中设置 NOTION_API_KEY 或 NOTION_KEY")
        print("   export NOTION_API_KEY='secret_xxx'")
        return None
    
    if not database_id and not parent_page_id:
        print("⚠️  未配置 NOTION_PODCAST_DATABASE_ID 或 NOTION_PARENT_PAGE_ID，跳过 Notion 上传")
        print("💡 提示：请在环境变量中设置")
        print("   export NOTION_PARENT_PAGE_ID='xxx'  # 推荐使用科技日报的父页面")
        print("   export NOTION_PODCAST_DATABASE_ID='xxx'  # 或者使用数据库")
        return None
    
    # 初始化上传器
    uploader = NotionUploader(api_key, database_id, parent_page_id)
    
    # 构建标题
    topic = podcast_metadata.get("topic", "未知主题")
    created_at = podcast_metadata.get("created_at", datetime.now().isoformat())
    
    # 构建内容
    script = podcast_metadata.get("script", {})
    sections = script.get("sections", [])
    
    content_parts = [f"# {topic}\n"]
    content_parts.append(f"创建时间: {created_at}\n")
    
    # 添加音频链接
    tos_url = podcast_metadata.get("tos_url")
    if tos_url:
        content_parts.append(f"\n[🔊 收听播客]({tos_url})\n")
    
    # 添加脚本内容
    for i, section in enumerate(sections, 1):
        section_type = section.get("type", "段落")
        section_content = section.get("content", "")
        
        content_parts.append(f"\n## {i}. {section_type}\n")
        content_parts.append(f"{section_content}\n")
    
    # 添加质量评分
    quality_check = podcast_metadata.get("quality_check", {})
    if quality_check:
        content_parts.append(f"\n---\n")
        content_parts.append(f"## 质量评分\n")
        content_parts.append(f"- 总分: {quality_check.get('overall_score', 0)}/100\n")
        content_parts.append(f"- 口语化: {quality_check.get('colloquialism_score', 0)}/100\n")
    
    content = "\n".join(content_parts)
    
    # 构建属性
    properties = {
        "状态": "已完成",
        "创建日期": created_at[:10],  # YYYY-MM-DD
    }
    
    # 上传到 Notion
    try:
        page_id = uploader.create_page(
            title=f"📻 {topic}",
            content=content,
            properties=properties
        )
        return page_id
    except Exception as e:
        print(f"❌ 上传到 Notion 失败: {e}")
        return None


def main():
    """测试函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="上传播客脚本到 Notion")
    parser.add_argument("metadata_file", help="播客元数据 JSON 文件")
    parser.add_argument("--database-id", help="Notion 数据库 ID")
    
    args = parser.parse_args()
    
    # 读取元数据
    with open(args.metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 上传
    page_id = upload_podcast_script(metadata, args.database_id)
    
    if page_id:
        print(f"✅ 成功！页面 ID: {page_id}")
    else:
        print("❌ 上传失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
