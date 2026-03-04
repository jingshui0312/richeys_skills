#!/usr/bin/env python3
"""
AI热点播客生成器 - AI Hotspot Podcast Generator
功能：智能搜索AI热点主题，生成播客并上传到TOS
改进：增加时效性、专业性、吸引力的主题采集
"""

import sys
import os
import json
import feedparser
import random
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error
import re

# 添加技能路径
sys.path.insert(0, 'os.path.dirname(os.path.abspath(__file__))')
sys.path.insert(0, 'os.path.dirname(os.path.abspath(__file__))')


# 高质量AI新闻RSS源（分级）
AI_NEWS_SOURCES = {
    "tier1": [  # 顶级源：权威、及时、高质量
        "https://hnrss.org/frontpage",  # Hacker News首页
        "https://www.reddit.com/r/MachineLearning/hot.rss",  # Reddit ML热门
        "https://www.reddit.com/r/artificial/hot.rss",  # Reddit AI热门
    ],
    "tier2": [  # 次级源：专业媒体
        "https://openai.com/blog/rss.xml",  # OpenAI官方博客
        "https://www.anthropic.com/news/rss",  # Anthropic新闻
        "https://deepmind.com/blog/rss.xml",  # DeepMind博客
        "https://www.theverge.com/ai-artificial-intelligence/rss.xml",
        "https://venturebeat.com/ai/feed/",
    ],
    "tier3": [  # 第三级：综合AI新闻
        "https://www.artificialintelligence-news.com/feed/",
        "https://www.artificialintelligence-news.com/feed/",
    ]
}

# 时效性AI热点话题池（2026年2月更新 - 紧贴当前AI核心主题）
AI_HOTSPOT_POOL = [
    # === 大语言模型与推理 ===
    {
        "title": "DeepSeek-R1：开源推理模型的突破与影响",
        "keywords": ["DeepSeek", "R1", "推理模型", "开源", "reasoning"],
        "priority": 10,  # 最高优先级
        "category": "LLM"
    },
    {
        "title": "Claude 3.7 Sonnet：混合推理模型的实际应用",
        "keywords": ["Claude", "3.7", "Sonnet", "混合推理", "Anthropic"],
        "priority": 9,
        "category": "LLM"
    },
    {
        "title": "OpenAI o3/o4：推理能力的边界与挑战",
        "keywords": ["OpenAI", "o3", "o4", "推理", "reasoning"],
        "priority": 9,
        "category": "LLM"
    },
    {
        "title": "GPT-5何时发布？大模型的下一个里程碑",
        "keywords": ["GPT-5", "OpenAI", "大模型", "发布"],
        "priority": 8,
        "category": "LLM"
    },
    
    # === AI Agent ===
    {
        "title": "Devin之后：AI软件工程师的进化之路",
        "keywords": ["Devin", "AI工程师", "Agent", "软件开发"],
        "priority": 9,
        "category": "Agent"
    },
    {
        "title": "多智能体协作：从AutoGPT到Claude Agent",
        "keywords": ["多智能体", "Agent", "协作", "AutoGPT"],
        "priority": 8,
        "category": "Agent"
    },
    {
        "title": "Agent框架大战：LangChain vs AutoGen vs CrewAI",
        "keywords": ["Agent", "框架", "LangChain", "AutoGen", "CrewAI"],
        "priority": 7,
        "category": "Agent"
    },
    
    # === 开源与生态 ===
    {
        "title": "开源大模型生态：Llama 4与Mistral的竞争",
        "keywords": ["开源", "Llama", "Mistral", "生态"],
        "priority": 8,
        "category": "开源"
    },
    {
        "title": "模型微调新范式：LoRA、QLoRA到DoRA",
        "keywords": ["微调", "LoRA", "QLoRA", "DoRA"],
        "priority": 7,
        "category": "开源"
    },
    
    # === 多模态与视觉 ===
    {
        "title": "视觉语言模型：GPT-4V、Gemini Pro Vision实战对比",
        "keywords": ["视觉语言", "GPT-4V", "Gemini", "多模态"],
        "priority": 8,
        "category": "多模态"
    },
    {
        "title": "AI图像生成：DALL-E 3、Midjourney v7与Stable Diffusion 4",
        "keywords": ["图像生成", "DALL-E", "Midjourney", "Stable Diffusion"],
        "priority": 7,
        "category": "多模态"
    },
    {
        "title": "视频生成：Sora、Runway与Pika的技术路线",
        "keywords": ["视频生成", "Sora", "Runway", "Pika"],
        "priority": 8,
        "category": "多模态"
    },
    
    # === 应用与落地 ===
    {
        "title": "AI编程助手：Cursor、Windsurf与GitHub Copilot Workspace",
        "keywords": ["编程助手", "Cursor", "Copilot", "开发效率"],
        "priority": 8,
        "category": "应用"
    },
    {
        "title": "RAG技术演进：从向量检索到GraphRAG",
        "keywords": ["RAG", "向量检索", "GraphRAG", "知识库"],
        "priority": 7,
        "category": "应用"
    },
    {
        "title": "AI搜索：Perplexity、SearchGPT与传统搜索引擎的博弈",
        "keywords": ["AI搜索", "Perplexity", "SearchGPT"],
        "priority": 7,
        "category": "应用"
    },
    
    # === 行业影响 ===
    {
        "title": "AI取代程序员？从IBM、Google的裁员说起",
        "keywords": ["AI", "裁员", "程序员", "工作"],
        "priority": 9,
        "category": "行业"
    },
    {
        "title": "AI伦理与监管：EU AI Act的全球影响",
        "keywords": ["AI伦理", "监管", "EU AI Act", "合规"],
        "priority": 7,
        "category": "行业"
    },
    {
        "title": "AI算力争夺战：NVIDIA、AMD与自研芯片的较量",
        "keywords": ["算力", "NVIDIA", "AMD", "芯片"],
        "priority": 7,
        "category": "行业"
    },
    
    # === 前沿研究 ===
    {
        "title": "世界模型：从LeCun的JEPA到物理世界模拟",
        "keywords": ["世界模型", "JEPA", "LeCun", "物理模拟"],
        "priority": 6,
        "category": "研究"
    },
    {
        "title": "AI与科学发现：AlphaFold 3与蛋白质设计",
        "keywords": ["AI", "科学发现", "AlphaFold", "蛋白质"],
        "priority": 7,
        "category": "研究"
    },
    {
        "title": "AGI路线之争：Scaling Law vs 架构创新",
        "keywords": ["AGI", "Scaling Law", "架构", "路线"],
        "priority": 6,
        "category": "研究"
    },
]


def fetch_ai_news_from_rss(tier="all", max_per_source=3):
    """
    从RSS源获取AI新闻（分级获取）

    Args:
        tier: 获取哪个级别的源（"tier1", "tier2", "tier3", "all"）
        max_per_source: 每个源最多获取几条

    Returns:
        list: AI新闻列表（带评分）
    """
    print(f"[{datetime.now().isoformat()}] 📡 从RSS源获取AI新闻（分级：{tier}）...")

    all_news = []

    sources_to_fetch = []
    if tier == "all":
        sources_to_fetch = AI_NEWS_SOURCES["tier1"] + AI_NEWS_SOURCES["tier2"] + AI_NEWS_SOURCES["tier3"]
        tier_scores = {**{s: 10 for s in AI_NEWS_SOURCES["tier1"]},
                      **{s: 7 for s in AI_NEWS_SOURCES["tier2"]},
                      **{s: 5 for s in AI_NEWS_SOURCES["tier3"]}}
    else:
        sources_to_fetch = AI_NEWS_SOURCES.get(tier, [])
        tier_scores = {s: 10 for s in sources_to_fetch}

    for feed_url in sources_to_fetch:
        try:
            print(f"  - 尝试: {feed_url}")
            feed = feedparser.parse(feed_url, timeout=10)

            # 提取前N条新闻
            for entry in feed.entries[:max_per_source]:
                title = entry.get('title', '')
                link = entry.get('link', '')
                published = entry.get('published', '')

                # 过滤：确保标题包含AI相关关键词
                ai_keywords = ['AI', 'artificial intelligence', 'machine learning',
                             'deep learning', 'neural network', 'LLM', 'GPT',
                             'Claude', 'Gemini', 'ChatGPT', '人工智能', '机器学习',
                             'OpenAI', 'Anthropic', 'DeepMind', 'agent', 'reasoning',
                             'model', 'neural', 'training', 'inference']

                if any(keyword.lower() in title.lower() for keyword in ai_keywords):
                    # 计算时效性得分
                    recency_score = calculate_recency_score(published)
                    
                    # 计算吸引力得分
                    attraction_score = calculate_attraction_score(title)
                    
                    # 综合得分 = 源质量 + 时效性 + 吸引力
                    total_score = tier_scores.get(feed_url, 5) + recency_score + attraction_score

                    all_news.append({
                        "title": title,
                        "url": link,
                        "published": published,
                        "source": feed_url,
                        "score": total_score,
                        "recency_score": recency_score,
                        "attraction_score": attraction_score
                    })

        except Exception as e:
            print(f"  ⚠️  RSS源失败 ({feed_url}): {e}")
            continue

    # 按得分排序
    all_news.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"[{datetime.now().isoformat()}] ✅ 从RSS获取 {len(all_news)} 条新闻（已按质量排序）")

    return all_news


def calculate_recency_score(published_str):
    """
    计算时效性得分（越新越高）

    Args:
        published_str: 发布时间字符串

    Returns:
        int: 时效性得分（0-5）
    """
    if not published_str:
        return 2  # 默认中等
    
    try:
        # 尝试解析时间（简化版，实际需要更复杂的解析）
        from email.utils import parsedate_to_datetime
        pub_time = parsedate_to_datetime(published_str)
        now = datetime.now(pub_time.tzinfo)
        
        hours_ago = (now - pub_time).total_seconds() / 3600
        
        if hours_ago < 24:  # 24小时内
            return 5
        elif hours_ago < 72:  # 3天内
            return 4
        elif hours_ago < 168:  # 一周内
            return 3
        elif hours_ago < 720:  # 一个月内
            return 2
        else:
            return 1
    except:
        return 2


def calculate_attraction_score(title):
    """
    计算吸引力得分（基于标题特征）

    Args:
        title: 标题

    Returns:
        int: 吸引力得分（0-5）
    """
    score = 0
    
    # 高吸引力的关键词
    high_attraction_keywords = [
        "突破", "首次", "重大", "革命", "震惊", "新发布", "launch",
        "breakthrough", "first", "revolutionary", "stunning", "game-changing",
        "GPT-5", "AGI", "取代", "裁员", "安全", "漏洞", "attack"
    ]
    
    # 中等吸引力的关键词
    medium_attraction_keywords = [
        "新", "改进", "升级", "对比", "实战", "应用", "开源",
        "new", "improved", "upgrade", "comparison", "real-world", "open-source"
    ]
    
    title_lower = title.lower()
    
    for keyword in high_attraction_keywords:
        if keyword.lower() in title_lower:
            score += 3
            break
    
    for keyword in medium_attraction_keywords:
        if keyword.lower() in title_lower:
            score += 2
            break
    
    # 有数字的标题通常更吸引人
    if re.search(r'\d+', title):
        score += 1
    
    # 有问号的标题通常更吸引人
    if '?' in title:
        score += 1
    
    return min(score, 5)


def select_topic_intelligent(news_list, hotspot_pool):
    """
    智能选择播客主题（综合考虑时效性、重要性、吸引力、去重）

    Args:
        news_list: 新闻列表（带评分）
        hotspot_pool: 话题池（带优先级）

    Returns:
        str: 选定的主题标题
    """
    # 加载历史记录（避免重复）
    history = load_topic_history()
    
    # 候选主题列表
    candidates = []
    
    # 添加新闻候选
    for news in news_list[:10]:  # 只考虑前10条高质量新闻
        if news["title"] not in history:
            candidates.append({
                "title": news["title"],
                "score": news["score"],
                "type": "news",
                "source": news["url"]
            })
    
    # 添加话题池候选
    for topic in hotspot_pool:
        if topic["title"] not in history:
            # 话题池得分 = 优先级 * 2（转换为10分制）
            candidates.append({
                "title": topic["title"],
                "score": topic["priority"] * 2,
                "type": "pool",
                "category": topic["category"]
            })
    
    if not candidates:
        print(f"[{datetime.now().isoformat()}] ⚠️  无新主题，使用最高优先级话题池")
        return max(hotspot_pool, key=lambda x: x["priority"])["title"]
    
    # 按得分排序
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # 从前5个中随机选择（避免总是选第一个）
    top_candidates = candidates[:5]
    selected = random.choice(top_candidates)
    
    # 保存到历史记录
    save_topic_history(selected["title"])
    
    source_info = f"来源：{selected.get('source', '话题池')}" if selected["type"] == "news" else f"分类：{selected.get('category', '综合')}"
    print(f"[{datetime.now().isoformat()}] 📌 选定主题: {selected['title']}")
    print(f"   得分: {selected['score']} | 类型: {selected['type']} | {source_info}")
    
    return selected["title"]


def load_topic_history(days=30):
    """
    加载历史主题记录（避免重复）

    Args:
        days: 查询多少天内的历史

    Returns:
        set: 历史主题集合
    """
    history_file = Path("/tmp/podcast-studio/ai-hotspots/topic_history.json")
    history = set()
    
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                history = {item["topic"] for item in data if item["date"] > cutoff_date}
        except:
            pass
    
    return history


def save_topic_history(topic):
    """
    保存主题到历史记录

    Args:
        topic: 主题标题
    """
    history_file = Path("/tmp/podcast-studio/ai-hotspots/topic_history.json")
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = []
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass
    
    data.append({
        "topic": topic,
        "date": datetime.now().isoformat()
    })
    
    # 只保留最近90天
    cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
    data = [item for item in data if item["date"] > cutoff_date]
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def search_ai_hotspots():
    """
    搜索AI热点主题（智能组合RSS和话题池）

    Returns:
        tuple: (新闻列表, 话题池)
    """
    print(f"[{datetime.now().isoformat()}] 🔍 开始搜索AI热点（智能模式）...")

    # 从分级RSS获取新闻
    news_list = fetch_ai_news_from_rss(tier="all", max_per_source=3)

    # 使用时效性话题池
    hotspot_pool = AI_HOTSPOT_POOL

    return news_list, hotspot_pool


def select_topic(news_list, hotspot_pool):
    """
    选择播客主题（包装函数）

    Args:
        news_list: 新闻列表
        hotspot_pool: 话题池

    Returns:
        str: 选定的主题标题
    """
    return select_topic_intelligent(news_list, hotspot_pool)


def generate_podcast(topic, style="conversational", duration="medium"):
    """
    生成播客

    Args:
        topic: 播客主题
        style: 播客风格
        duration: 时长

    Returns:
        dict: 播客元数据
    """
    print(f"[{datetime.now().isoformat()}] 🎙️  开始生成播客: {topic}")

    try:
        from podcast_studio import PodcastStudio

        studio = PodcastStudio()

        # 生成播客
        result = studio.create_podcast(
            topic=topic,
            subtopics=None,
            duration=duration,
            voice="male-qn-qingse",  # 使用默认男声
            style=style,
            optimize=True
        )

        print(f"[{datetime.now().isoformat()}] ✅ 播客生成成功")

        return result

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ❌ 播客生成失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def save_hotspot_record(topic, news_list, metadata):
    """
    保存热点记录

    Args:
        topic: 选定的主题
        news_list: 新闻列表
        metadata: 播客元数据
    """
    record = {
        "date": datetime.now().isoformat(),
        "selected_topic": topic,
        "news_count": len(news_list),
        "top_news": [
            {
                "title": n["title"],
                "score": n.get("score", 0),
                "source": n.get("source", "")
            }
            for n in news_list[:5]
        ] if news_list else [],
        "podcast_metadata": {
            "topic": metadata.get("topic"),
            "script_style": metadata.get("script", {}).get("style"),
            "duration": metadata.get("script", {}).get("duration"),
            "audio_file": metadata.get("audio_file"),
            "tos_url": metadata.get("tos_url"),
            "quality_score": metadata.get("quality_check", {}).get("overall_score"),
            "created_at": metadata.get("created_at")
        }
    }

    # 保存到文件
    record_dir = Path("/tmp/podcast-studio/ai-hotspots")
    record_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    record_file = record_dir / f"hotspot_record_{date_str}.json"

    with open(record_file, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    print(f"[{datetime.now().isoformat()}] 💾 热点记录已保存: {record_file}")

    return record_file


def send_notification(topic, metadata):
    """
    发送通知（记录日志）

    Args:
        topic: 主题
        metadata: 播客元数据
    """
    try:
        quality_score = metadata.get("quality_check", {}).get("overall_score", 0)
        tos_url = metadata.get("tos_url", "N/A")

        print(f"[{datetime.now().isoformat()}] 📢 播客通知")
        print(f"   主题: {topic}")
        print(f"   质量评分: {quality_score}")
        print(f"   TOS链接: {tos_url}")

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ⚠️  通知失败: {e}")


def main():
    """主函数"""
    try:
        print(f"[{datetime.now().isoformat()}] 🚀 AI热点播客生成器启动（智能版）")

        # 1. 搜索AI热点（智能）
        news_list, hotspot_pool = search_ai_hotspots()

        # 2. 选择主题（智能）
        topic = select_topic(news_list, hotspot_pool)

        # 3. 生成播客
        metadata = generate_podcast(
            topic=topic,
            style="conversational",  # 使用对话风格
            duration="medium"  # 中等时长
        )

        # 4. 保存记录
        record_file = save_hotspot_record(topic, news_list, metadata)

        # 5. 发送通知
        send_notification(topic, metadata)

        print(f"[{datetime.now().isoformat()}] ✨ 任务完成！")
        return True

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ❌ 任务失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
