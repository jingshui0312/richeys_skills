#!/usr/bin/env python3
"""
播客工作室 - Podcast Studio
功能：收集资料、设计脚本、生成音频、上传到TOS
新增：背景音乐混合功能、自动LLM脚本生成、并发控制
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
import re
import threading
import time
from datetime import datetime
from pathlib import Path

# 添加技能路径以便导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class PodcastStudio:
    """播客工作室主类"""
    
    # 类级别信号量：限制并发 LLM 请求数（所有实例共享）
    _llm_semaphore = threading.Semaphore(3)
    _request_counter = 0  # 请求计数器（用于日志）
    _counter_lock = threading.Lock()  # 计数器锁

    def __init__(self, config_file=None):
        self.config = self._load_config(config_file)
        self.work_dir = Path("/tmp/podcast-studio")
        self.work_dir.mkdir(exist_ok=True)

        # BGM设置
        self.bgm_file = self.config.get("bgm_file", "")
        self.bgm_volume = self.config.get("bgm_volume", 0.3)  # BGM音量（相对语音的百分比）
        self.bgm_fade_in = self.config.get("bgm_fade_in", 2000)  # 淡入时长（毫秒）
        self.bgm_fade_out = self.config.get("bgm_fade_out", 3000)  # 淡出时长（毫秒）

    def _load_config(self, config_file):
        """加载配置"""
        # 优先使用指定的配置文件
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 尝试加载默认配置文件
        default_configs = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"),
            os.path.expanduser("~/.podcast_studio_config.json"),
        ]

        for config_path in default_configs:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    print(f"📄 加载配置文件: {config_path}")
                    return json.load(f)

        # 没有找到配置文件，返回默认配置
        print("⚠️  未找到配置文件，使用默认配置")
        return {
            "tos_bucket": "YOUR_TOS_BUCKET_NAME",
            "default_voice": "male-qn-qingse",
            "default_speed": 1.1,
            "default_vol": 1.0,
            "output_format": "mp3",
            "bgm_file": "",  # 背景音乐文件路径
            "bgm_volume": 0.3,  # BGM音量（0.1-1.0）
            "bgm_fade_in": 2000,  # 淡入时长（毫秒）
            "bgm_fade_out": 3000  # 淡出时长（毫秒）
        }

    def _mix_with_bgm(self, voice_file, output_file):
        """
        将语音与背景音乐混合

        Args:
            voice_file: 语音文件路径
            output_file: 输出文件路径

        Returns:
            str: 混合后的音频文件路径
        """
        if not self.bgm_file or not os.path.exists(self.bgm_file):
            print("⚠️  未配置BGM或BGM文件不存在，跳过背景音乐混合")
            return voice_file

        try:
            from pydub import AudioSegment

            print(f"🎵 正在混合背景音乐...")

            # 加载语音
            voice = AudioSegment.from_mp3(voice_file)
            voice_duration = len(voice)
            print(f"   语音时长: {voice_duration / 1000:.2f} 秒")

            # 加载BGM
            bgm = AudioSegment.from_mp3(self.bgm_file)
            bgm = bgm - (10 * (1.0 - self.bgm_volume))  # 调整BGM音量
            print(f"   BGM时长: {len(bgm) / 1000:.2f} 秒")
            print(f"   BGM音量: {self.bgm_volume * 100}%")

            # 循环BGM以匹配语音长度
            bgm_loops = (voice_duration // len(bgm)) + 1
            bgm = bgm * bgm_loops
            bgm = bgm[:voice_duration]

            # 添加淡入淡出效果
            bgm = bgm.fade_in(self.bgm_fade_in)
            bgm = bgm.fade_out(self.bgm_fade_out)

            # 混合音频
            result = voice.overlay(bgm)

            # 导出
            result.export(output_file, format="mp3", bitrate="128k")

            print(f"✅ 背景音乐混合完成: {output_file}")

            return output_file

        except ImportError:
            print("⚠️  pydub未安装，跳过背景音乐混合")
            return voice_file
        except Exception as e:
            print(f"❌ 背景音乐混合失败: {e}")
            return voice_file

    def _load_llm_config(self):
        """
        加载LLM配置（优先从config.json，其次从article-extractor/.env，最后从环境变量）
        """
        api_key = ""
        base_url = "https://api.z.ai/api/coding/paas/v4"
        model = "glm-5"
        timeout = 180

        # 尝试从article-extractor的.env文件加载（共享API密钥）
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip().strip('"').strip("'")
                        os.environ[key.strip()] = value

        # 优先从config.json读取LLM配置
        llm_config = self.config.get("llm", {})
        if llm_config:
            base_url = llm_config.get("base_url", base_url)
            model = llm_config.get("model", model)
            timeout = llm_config.get("timeout", timeout)

            # 从环境变量读取API密钥
            api_key_env = llm_config.get("api_key_env", "ZAI_API_KEY")
            api_key = os.getenv(api_key_env, "")

        # 后备：从环境变量读取（兼容旧配置）
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY', '')
        if not llm_config.get("base_url"):
            base_url = os.getenv('OPENAI_BASE_URL', base_url)
        if not llm_config.get("model"):
            model = os.getenv('OPENAI_MODEL', model)

        return {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "timeout": timeout
        }

    def _call_llm_api(self, prompt, timeout=None, max_retries=3):
        """
        调用LLM API生成内容（带重试机制和并发控制）

        Args:
            prompt: 提示文本
            timeout: 超时时间（秒），None则使用配置值
            max_retries: 最大重试次数（默认3次）

        Returns:
            str: LLM返回的内容，失败返回None
        """
        config = self._load_llm_config()

        if not config["api_key"]:
            print("⚠️  未设置 API 密钥，无法自动生成脚本")
            return None

        # 使用配置中的超时时间
        if timeout is None:
            timeout = config.get("timeout", 180)

        url = f"{config['base_url'].rstrip('/')}/chat/completions"

        body = {
            "model": config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的播客脚本作家。根据要求生成高质量、口语化的播客脚本。"
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 4000
        }

        # 获取请求编号（用于日志）
        with self._counter_lock:
            self._request_counter += 1
            request_id = self._request_counter
        
        # 使用信号量控制并发（最多3个同时进行）
        with self._llm_semaphore:
            print(f"🔒 [请求#{request_id}] 获取并发锁，开始调用 LLM API...")
            
            # 重试逻辑
            for attempt in range(max_retries):
                try:
                    req = urllib.request.Request(
                        url,
                        method="POST",
                        headers={
                            "Authorization": f"Bearer {config['api_key']}",
                            "Content-Type": "application/json",
                        },
                        data=json.dumps(body).encode("utf-8")
                    )

                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        response_text = resp.read().decode("utf-8")
                        response = json.loads(response_text)

                        if "choices" in response and len(response["choices"]) > 0:
                            message = response["choices"][0]["message"]
                            # GLM-4.7可能返回reasoning_content而不是content
                            content = message.get("content") or message.get("reasoning_content", "")
                            print(f"✅ [请求#{request_id}] LLM脚本生成成功")
                            return content
                        else:
                            print(f"⚠️  [请求#{request_id}] LLM返回格式异常: {response}")
                            return None

                except urllib.error.HTTPError as e:
                    error_body = e.read().decode("utf-8")
                    
                    # 检测429速率限制
                    if e.code == 429:
                        wait_time = (attempt + 1) * 30  # 指数退避：30s, 60s, 90s
                        print(f"⚠️  [请求#{request_id}] API速率限制 (429)，等待{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ [请求#{request_id}] 达到最大重试次数，LLM API不可用")
                            return None
                    
                    # 其他HTTP错误
                    print(f"❌ [请求#{request_id}] LLM API HTTP {e.code}: {error_body}")
                    return None
                    
                except urllib.error.URLError as e:
                    # 网络错误，重试
                    wait_time = (attempt + 1) * 10
                    print(f"⚠️  [请求#{request_id}] 网络错误: {e.reason}，等待{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ [请求#{request_id}] 达到最大重试次数，网络不可用")
                        return None
                        
                except Exception as e:
                    print(f"❌ [请求#{request_id}] LLM API 调用失败: {e}")
                    import traceback
                    traceback.print_exc()
                    return None
            
            return None

    def create_podcast(self, topic, subtopics=None, duration="short", voice=None, style="informative", optimize=True, use_bgm=True):
        """
        创建播客：从资料收集到音频上传的完整流程

        Args:
            topic: 播客主题
            subtopics: 子主题列表（可选）
            duration: 时长预期 (short=3-5min, medium=10-15min, long=20-30min)
            voice: 使用的声音
            style: 播客风格 (informative, conversational, narrative, tech)
            optimize: 是否启用脚本优化（默认启用）
            use_bgm: 是否使用背景音乐（默认启用）

        Returns:
            dict: 包含脚本、音频文件、TOS链接等信息
        """
        print(f"🎙️  开始创建播客: {topic}")

        # 1. 收集资料（占位符 - 实际调用web search）
        print("📚 收集资料...")
        research = self._collect_research(topic, subtopics)

        # 2. AI 深度分析（新增 - 参考url-to-infographic）
        print("🤖 深度分析内容...")
        analysis = self._analyze_content_deep(topic, research, style)

        # 3. 生成脚本框架
        print("🏗️  生成脚本框架...")
        framework = self._generate_framework(topic, research, style, duration)

        # 4. 生成脚本内容（使用分析结果）
        print("✍️  生成脚本...")
        script = self._generate_script_from_framework(framework, research, analysis)

        # 4. 脚本质量检查
        print("🔍 检查脚本质量...")
        check_results = self._check_script(script)

        # 5. 脚本优化（可选）
        if optimize and check_results["overall_score"] < 85:
            print("⚡  优化脚本...")
            script = self._optimize_script(script, check_results)
        elif optimize:
            print("✅ 脚本质量良好，无需优化")

        # 6. 生成音频
        print("🔊 生成音频...")
        audio_file = self._generate_audio(script, voice)

        # 7. 混合背景音乐（如果启用）
        if use_bgm and self.bgm_file:
            mixed_audio_file = audio_file.replace(".mp3", "_with_bgm.mp3")
            mixed_audio_file = self._mix_with_bgm(audio_file, mixed_audio_file)
            if mixed_audio_file != audio_file:
                audio_file = mixed_audio_file

        # 8. 上传到TOS
        print("☁️  上传到TOS...")
        tos_url = self._upload_to_tos(audio_file, topic)

        # 9. 保存脚本和元数据
        print("💾 保存元数据...")
        metadata = self._save_metadata(topic, script, research, audio_file, tos_url, framework, check_results)

        # 10. 上传到 Notion（如果启用）
        if self.config.get("upload_to_notion", False):
            print("📝 上传脚本到 Notion...")
            try:
                # 动态导入上传模块
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "upload_to_notion",
                    os.path.join(os.path.dirname(__file__), "upload_to_notion.py")
                )
                notion_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(notion_module)
                
                # 调用上传函数（复用科技日报的配置）
                page_id = notion_module.upload_podcast_script(metadata)
                
                if page_id:
                    metadata["notion_page_id"] = page_id
                    print(f"✅ Notion 页面创建成功: {page_id}")
                else:
                    print("⚠️  Notion 上传失败（可能未配置 API 密钥）")
            except Exception as e:
                print(f"⚠️  Notion 上传失败: {e}")

        print(f"✅ 播客创建完成！")
        print(f"📄 音频文件: {audio_file}")
        print(f"🔗 TOS链接: {tos_url}")

        return metadata

    def _collect_research(self, topic, subtopics=None):
        """
        收集研究资料（占位符 - 需要集成web_search）

        实际实现时应该：
        1. 使用web_search API搜索相关内容
        2. 使用web_fetch API获取详细资料
        3. 整理和总结关键信息
        """
        return {
            "topic": topic,
            "subtopics": subtopics or [],
            "key_points": [
                "待实现：通过web_search收集资料",
                "待实现：提取关键信息",
                "待实现：整理成结构化数据"
            ],
            "sources": [],
            "collected_at": datetime.now().isoformat()
        }

    def _analyze_content_deep(self, topic, research, style):
        """
        深度内容分析（参考url-to-infographic的AI深度分析）

        提取结构化信息：
        - 核心观点（3-5个）
        - 案例/故事（2-3个）
        - 数据/统计（具体数字）
        - 类比/比喻（1-2个）
        - 争议点/反直觉观点
        - 听众痛点/共鸣点
        - 幽默元素（槽点、自嘲）
        - 金句/总结（易传播的观点）

        Args:
            topic: 主题
            research: 研究资料
            style: 播客风格

        Returns:
            dict: 深度分析结果
        """
        print("   🔍 正在进行深度分析...")

        # 如果研究资料太少，直接返回基础分析
        if not research.get("key_points") or research.get("key_points", []) == ["待实现：通过web_search收集资料"]:
            print("   ⚠️  研究资料不足，使用智能推断")
            return self._analyze_with_llm(topic, style)

        # 有研究资料时，进行深度分析
        return self._analyze_with_llm(topic, style, research)

    def _analyze_with_llm(self, topic, style, research=None):
        """
        使用LLM进行深度内容分析

        Args:
            topic: 主题
            style: 风格
            research: 研究资料（可选）

        Returns:
            dict: 分析结果
        """
        # 构建分析prompt
        prompt = self._build_analysis_prompt(topic, style, research)

        # 保存prompt到文件（调试用）
        analysis_prompt_file = self.work_dir / f"analysis_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(analysis_prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)

        print(f"   🤖 调用LLM进行深度分析...")

        # 调用LLM
        response = self._call_llm_api(prompt, timeout=90)

        if response is None:
            print("   ⚠️  LLM分析失败，使用默认分析")
            return self._get_default_analysis(topic)

        # 解析JSON结果
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接匹配JSON
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("未找到JSON格式数据")

            analysis = json.loads(json_str)
            print("   ✅ 深度分析完成")

            # 保存分析结果
            analysis_file = self.work_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)

            return analysis

        except Exception as e:
            print(f"   ⚠️  解析分析结果失败: {e}，使用默认分析")
            return self._get_default_analysis(topic)

    def _build_analysis_prompt(self, topic, style, research=None):
        """
        构建深度分析的prompt

        Args:
            topic: 主题
            style: 风格
            research: 研究资料（可选）

        Returns:
            str: 分析prompt
        """
        # 基础信息
        base_info = f"""你是一位专业的播客内容分析师。请对以下主题进行深度分析，提取用于制作高质量播客的关键元素。

# 分析主题
{topic}

# 播客风格
{style}"""

        # 添加研究资料（如果有）
        if research and research.get("key_points"):
            research_info = f"\n\n# 参考资料要点\n"
            for i, kp in enumerate(research.get("key_points", []), 1):
                research_info += f"{i}. {kp}\n"
            base_info += research_info

        # 分析任务
        analysis_task = """

# 分析任务
请深入分析这个主题，提取以下关键元素：

1. **core_viewpoints** (核心观点): 3-5个最核心、最有价值的观点
   - 每个观点应该是独立的、有深度的见解
   - 避免套话，要有具体性和独特性

2. **cases_and_stories** (案例和故事): 2-3个真实案例或故事
   - 每个案例要具体、生动、有细节
   - 格式: {"name": "案例名称", "description": "详细描述", "lesson": "启示"}

3. **data_and_stats** (数据和统计): 具体的数字、百分比、研究数据
   - 数据要具体，不要用"很多人"这种模糊表达
   - 格式: {"data": "具体数据", "source": "来源", "context": "背景说明"}

4. **analogies_and_metaphors** (类比和比喻): 1-2个生动的类比
   - 帮助听众理解复杂概念
   - 要贴近生活、容易产生共鸣

5. **controversial_points** (争议点/反直觉观点): 挑战常识的观点
   - 引发思考，不要平铺直叙
   - 要有论证支撑

6. **audience_pain_points** (听众痛点): 听众可能遇到的问题
   - 要具体、真实、能引发共鸣
   - 避免"很多人会遇到"这种空泛表述

7. **humor_elements** (幽默元素): 1-2个幽默点
   - 可以是自嘲、吐槽、讽刺
   - 要自然，不要生硬

8. **golden_quotes** (金句): 1-2个易传播的总结性观点
   - 简洁、有力、容易记住
   - 可以作为播客的slogan

# 输出格式
请以JSON格式输出：

{
  "core_viewpoints": ["观点1", "观点2", "观点3"],
  "cases_and_stories": [
    {"name": "案例名", "description": "描述", "lesson": "启示"}
  ],
  "data_and_stats": [
    {"data": "数据", "source": "来源", "context": "背景"}
  ],
  "analogies_and_metaphors": ["类比1", "类比2"],
  "controversial_points": ["争议点1", "争议点2"],
  "audience_pain_points": ["痛点1", "痛点2"],
  "humor_elements": ["幽默点1", "幽默点2"],
  "golden_quotes": ["金句1", "金句2"]
}

注意：
- 所有内容都要围绕主题，不要泛泛而谈
- 如果某个领域没有合适的内容，可以留空数组[]
- 确保输出的是纯JSON，不要添加任何解释
"""

        return base_info + analysis_task

    def _get_default_analysis(self, topic):
        """
        获取默认分析结果（当LLM分析失败时使用）

        Args:
            topic: 主题

        Returns:
            dict: 默认分析结果
        """
        return {
            "core_viewpoints": [
                f"{topic}正在改变我们的生活方式",
                f"理解{topic}的核心原理很重要",
                f"{topic}的未来发展值得关注"
            ],
            "cases_and_stories": [],
            "data_and_stats": [],
            "analogies_and_metaphors": [],
            "controversial_points": [],
            "audience_pain_points": [
                "对新技术感到困惑",
                "不知道如何入门"
            ],
            "humor_elements": [],
            "golden_quotes": [f"了解{topic}，就是了解未来"]
        }

    def _generate_framework(self, topic, research, style, duration):
        """
        生成脚本框架（使用智能框架生成器）

        Args:
            topic: 主题
            research: 研究资料
            style: 播客风格
            duration: 时长预期

        Returns:
            dict: 脚本框架
        """
        try:
            from script_generator import ScriptGenerator
            generator = ScriptGenerator()
            framework = generator.generate_framework(topic, research, style, duration)
        except Exception as e:
            print(f"⚠️  框架生成失败，使用默认模板: {e}")
            framework = {
                "style": style,
                "duration": duration,
                "sections": ["intro", "main", "details", "outro"],
                "features": {},
                "topic": topic
            }

        # 保存框架到文件
        framework_file = self.work_dir / f"framework_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(framework_file, 'w', encoding='utf-8') as f:
            json.dump(framework, f, ensure_ascii=False, indent=2)

        return framework

    def _generate_script_from_framework(self, framework, research, analysis=None):
        """
        根据框架生成脚本内容 - 自动调用大模型生成

        Args:
            framework: 脚本框架（由 ScriptGenerator 动态生成）
            research: 研究资料
            analysis: 深度分析结果（新增）

        Returns:
            dict: 脚本内容，由大模型智能生成
        """
        style = framework.get("style", "informative")
        topic = framework.get("topic", "")
        duration = framework.get("duration", "short")
        tone = framework.get("tone", "")
        language_style = framework.get("language_style", "")

        # 构建大模型 prompt（使用分析结果）
        prompt = self._build_llm_prompt(topic, style, duration, tone, language_style, research, framework, analysis)

        # 将 prompt 保存到文件（用于调试）
        prompt_file = self.work_dir / f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)

        print(f"\n📝 脚本生成 Prompt 已保存到: {prompt_file}")
        print(f"🤖 调用大模型生成脚本...")

        # 调用 LLM API 生成内容
        llm_response = self._call_llm_api(prompt, timeout=120)

        if llm_response is None:
            # LLM失败，不使用默认脚本，直接报错
            raise RuntimeError(
                f"LLM API不可用，无法生成播客脚本。\n"
                f"主题: {topic}\n"
                f"建议：\n"
                f"1. 检查API密钥是否正确\n"
                f"2. 检查网络连接\n"
                f"3. 稍后重试（可能是速率限制）\n"
                f"4. 使用 --skip-llm 参数跳过LLM生成（仅用于测试）"
            )
        
        # 解析 LLM 返回的内容
        script = self._parse_llm_response(llm_response, topic, style, duration, tone, language_style, framework)
        script["llm_generated"] = True
        script["prompt_file"] = str(prompt_file)
        print(f"✅ 脚本生成完成，共 {len(script.get('sections', []))} 个段落")

        # 添加元数据
        script["research"] = research
        script["framework"] = framework
        script["created_at"] = datetime.now().isoformat()

        # 保存脚本到文件
        script_file = self.work_dir / f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)

        return script

    def _create_default_script(self, topic, style, duration, tone, language_style):
        """
        创建默认脚本（当LLM失败时使用）- 改进版：更充实的内容

        Args:
            topic: 主题
            style: 风格
            duration: 时长
            tone: 基调
            language_style: 语言风格

        Returns:
            dict: 默认脚本
        """
        # 根据时长确定段落数量
        if duration == "short":
            section_count = 5
        elif duration == "medium":
            section_count = 10
        else:  # long
            section_count = 15

        sections = []

        # 开场钩子（用数据和问题开场）
        sections.append({
            "type": "开场钩子",
            "content": f"大家好，今天我们来聊聊{topic}。\n\n" +
                      f"你有没有想过，{topic}正在悄悄改变我们的世界？\n\n" +
                      f"最近我看到一个数据，关于{topic}的搜索量在过去一年增长了300%，这说明什么？说明越来越多人开始关注这个领域了。\n\n" +
                      f"那今天，我们就来深入聊聊这个话题。"
        })

        # 核心观点1：背景介绍（根据主题关键词生成相关内容）
        topic_lower = topic.lower()
        
        if any(kw in topic_lower for kw in ["ai", "人工智能", "智能", "机器学习", "ml"]):
            background = f"首先，让我们搞清楚{topic}到底是什么。\n\n" + \
                        f"简单来说，这是人工智能技术在特定领域的应用。\n\n" + \
                        f"人工智能不是科幻小说，它已经在我们的生活中无处不在。从手机里的语音助手，到银行的欺诈检测系统，再到推荐算法，都是AI的实际应用。\n\n" + \
                        f"而{topic}，正是这个大趋势中的一个缩影。它代表了AI如何渗透到具体的行业和场景中，解决实际问题。"
        elif any(kw in topic_lower for kw in ["金融", "财务", "银行", "投资", "交易"]):
            background = f"首先，让我们搞清楚{topic}到底是什么。\n\n" + \
                        f"简单来说，这是技术在金融领域的创新应用。\n\n" + \
                        f"金融行业一直是技术创新的前沿阵地。从ATM机到移动支付，从高频交易到智能投顾，技术一直在改变金融的面貌。\n\n" + \
                        f"而{topic}，代表了金融科技的最新进展。它可能会改变传统的工作方式，提升效率，降低成本，甚至创造全新的商业模式。"
        elif any(kw in topic_lower for kw in ["区块链", "加密", "比特币", "web3"]):
            background = f"首先，让我们搞清楚{topic}到底是什么。\n\n" + \
                        f"简单来说，这是区块链技术在实际场景中的应用。\n\n" + \
                        f"区块链不仅仅是加密货币，它本质上是一种分布式账本技术，可以确保数据的透明性、不可篡改性和去中心化。\n\n" + \
                        f"而{topic}，正是这种技术在特定领域的落地尝试。它可能会改变我们记录信息、验证身份、进行交易的方式。"
        else:
            background = f"首先，让我们搞清楚{topic}到底是什么。\n\n" + \
                        f"简单来说，这是技术在实际场景中的应用。\n\n" + \
                        f"在当今快速发展的技术世界里，我们每天都能看到新的突破和创新。有些是渐进式的改进，有些是颠覆性的变革。\n\n" + \
                        f"而{topic}，代表了这个领域的一个发展方向。它可能是一个新的工具、一种新的方法，或者一个新的思维方式。"
        
        sections.append({
            "type": "核心观点",
            "title": "什么是" + topic,
            "content": background
        })

        # 核心观点2：为什么重要
        sections.append({
            "type": "核心观点",
            "title": "为什么" + topic + "这么重要",
            "content": f"那为什么{topic}现在这么火呢？\n\n" +
                      f"我觉得有几个原因。\n\n" +
                      f"第一，技术成熟了。以前可能只是概念，但现在真的能落地应用了。\n\n" +
                      f"第二，成本降低了。以前只有大公司用得起，现在中小企业甚至个人都能用。\n\n" +
                      f"第三，效果显著。不管是提升效率，还是创造新的可能性，{topic}都在证明它的价值。"
        })

        # 核心观点3：实际应用（根据主题生成相关案例）
        if section_count >= 7:
            topic_lower = topic.lower()
            
            if any(kw in topic_lower for kw in ["ai", "智能", "代理", "agent"]):
                case_study = f"说到应用，我给你讲个真实的趋势。\n\n" + \
                           f"现在越来越多的企业开始部署AI代理来处理重复性工作。\n\n" + \
                           f"比如在客服领域，AI代理可以24小时在线回答常见问题，处理订单查询，甚至识别情绪进行安抚。在数据分析领域，AI代理可以自动收集、清洗、分析数据，生成报告。\n\n" + \
                           f"这不仅仅是提升效率，更是改变了工作的性质。人类可以从重复劳动中解放出来，专注于创造性的工作。\n\n" + \
                           f"所以你看，{topic}不是空中楼阁，它正在实际工作中发挥作用。"
            elif any(kw in topic_lower for kw in ["金融", "财务", "交易"]):
                case_study = f"说到应用，金融行业正在快速拥抱技术创新。\n\n" + \
                           f"比如在风险管理方面，传统方法依赖人工审核和经验判断，现在可以用算法实时分析海量数据，识别潜在风险。\n\n" + \
                           f"在交易领域，量化交易和算法交易已经成为主流，机器可以在毫秒级别做出决策。\n\n" + \
                           f"在客户服务方面，智能客服可以处理80%以上的常见问题，大大降低了运营成本。\n\n" + \
                           f"所以你看，{topic}代表了金融行业数字化转型的方向。"
            else:
                case_study = f"说到应用，这个领域正在快速发展。\n\n" + \
                           f"从初创公司到大型企业，都在尝试将新技术应用到实际业务中。\n\n" + \
                           f"有些应用可能还在实验阶段，但已经展现出巨大的潜力。有些已经投入生产，产生了实际的商业价值。\n\n" + \
                           f"关键是要找到合适的场景，既不是为了技术而技术，也不是固守旧方法拒绝改变。\n\n" + \
                           f"所以你看，{topic}不是空中楼阁，它正在寻找落地场景。"
            
            sections.append({
                "type": "案例分享",
                "title": "实际应用案例",
                "content": case_study
            })

        # 核心观点4：挑战和争议（根据主题生成相关争议）
        if section_count >= 8:
            topic_lower = topic.lower()
            
            if any(kw in topic_lower for kw in ["ai", "智能", "代理", "agent"]):
                controversy = f"当然，{topic}也不是完美的，行业里确实有很多争议。\n\n" + \
                            f"最大的担心是什么？是失控。\n\n" + \
                            f"当AI系统变得越来越智能，我们如何确保它按照人类的意图行动？当AI代理可以自主决策时，出了问题谁负责？\n\n" + \
                            f"还有人担心就业问题。如果AI可以完成大部分工作，人类还能做什么？这不仅是技术问题，更是社会问题。\n\n" + \
                            f"我觉得这些担心都有道理。技术本身是中立的，关键看我们怎么设计、部署、监管它。\n\n" + \
                            f"所以，发展技术的同时，也要建立相应的规范和伦理准则。"
            elif any(kw in topic_lower for kw in ["金融", "交易"]):
                controversy = f"当然，{topic}也带来了不少争议。\n\n" + \
                            f"最大的担心是什么？是系统性风险。\n\n" + \
                            f"当算法主导交易决策时，一个小bug可能导致连锁反应。2010年的美股闪崩就是前车之鉴。\n\n" + \
                            f"还有人担心公平性问题。拥有先进技术的机构是否会获得不公平的优势？普通投资者会不会处于劣势？\n\n" + \
                            f"监管也是个难题。技术发展太快，监管往往跟不上。如何在创新和安全之间找到平衡？\n\n" + \
                            f"我觉得这些问题都需要认真对待，不能因为追求效率就忽视风险。"
            else:
                controversy = f"当然，{topic}也不是完美的，行业里也有很多争议和讨论。\n\n" + \
                            f"有人担心技术会不会被滥用？隐私安全怎么保证？\n\n" + \
                            f"有人担心发展速度太快，社会来不及适应？\n\n" + \
                            f"还有人担心技术壁垒，只有少数大公司能掌握核心技术？\n\n" + \
                            f"我觉得这些担心都有道理。技术本身是中立的，关键看我们怎么用。\n\n" + \
                            f"所以，发展技术的同时，也要建立相应的规范和伦理准则。"
            
            sections.append({
                "type": "争议讨论",
                "title": "有哪些挑战和争议",
                "content": controversy
            })

        # 核心观点5：未来展望（根据主题生成相关展望）
        if section_count >= 9:
            topic_lower = topic.lower()
            
            if any(kw in topic_lower for kw in ["ai", "智能", "代理"]):
                future = f"那{topic}的未来会怎样呢？\n\n" + \
                       f"我个人是比较乐观的，但也有担忧。\n\n" + \
                       f"乐观的一面是，未来3-5年，我们会看到AI技术更加成熟、更加普及。使用门槛会越来越低，普通人也能轻松使用强大的AI工具。\n\n" + \
                       f"但担忧的一面是，技术发展太快，社会适应可能跟不上。我们需要更多关于AI伦理、AI安全的讨论和研究。\n\n" + \
                       f"可能再过几年，{topic}就会像现在的互联网一样，成为我们生活和工作中不可或缺的一部分。\n\n" + \
                       f"到那时候，我们再回过头来看今天的讨论，可能会有完全不同的感受。"
            elif any(kw in topic_lower for kw in ["金融", "交易"]):
                future = f"那{topic}的未来会怎样呢？\n\n" + \
                       f"我觉得金融行业的技术变革才刚刚开始。\n\n" + \
                       f"未来3-5年，我们会看到更多传统金融业务被技术重构。从支付到借贷，从投资到保险，每个环节都可能被重新定义。\n\n" + \
                       f"监管也会更加完善。随着技术的发展，监管方式也会进化，找到创新和安全的平衡点。\n\n" + \
                       f"对于普通人来说，金融服务会更加便捷、透明、低成本。这可能是最大的受益。\n\n" + \
                       f"当然，这也意味着传统从业者需要不断学习新技能，适应新环境。"
            else:
                future = f"那{topic}的未来会怎样呢？\n\n" + \
                       f"我个人是比较乐观的。\n\n" + \
                       f"我觉得未来3-5年，我们会看到更多{topic}的落地应用。而且，随着技术的进步，使用门槛会越来越低。\n\n" + \
                       f"可能再过几年，{topic}就会像现在的互联网一样，成为我们生活的一部分。\n\n" + \
                       f"到那时候，我们再回过头来看今天的讨论，可能会有完全不同的感受。"
            
            sections.append({
                "type": "未来展望",
                "title": topic + "的未来会怎样",
                "content": future
            })

        # 互动环节
        if section_count >= 6:
            sections.append({
                "type": "互动提问",
                "content": f"说到这里，我想问问大家。\n\n" +
                          f"你对{topic}有什么看法？\n\n" +
                          f"你在工作或生活中，有没有接触过相关的应用？\n\n" +
                          f"欢迎在评论区分享你的经验和想法。\n\n" +
                          f"我觉得这种讨论很有价值，因为每个人的视角都不一样，我们可以从彼此的分享中学到很多。"
            })

        # 总结和金句
        sections.append({
            "type": "金句总结",
            "content": f"好，今天关于{topic}的分享就到这里。\n\n" +
                      f"我们聊了什么是{topic}，为什么它很重要，有哪些应用和挑战，以及未来的发展。\n\n" +
                      f"最后，我想用一句话总结今天的分享：\n\n" +
                      f"了解{topic}，就是在了解未来。\n\n" +
                      f"希望今天的分享对你有帮助。如果你觉得有价值，别忘了分享给朋友。\n\n" +
                      f"我们下次再见！"
        })

        return {
            "style": style,
            "duration": duration,
            "tone": tone,
            "language_style": language_style,
            "topic": topic,
            "sections": sections,
            "default_script": True,
            "section_count": len(sections)
        }

    def _parse_llm_response(self, llm_text, topic, style, duration, tone, language_style, framework):
        """
        解析LLM返回的文本为脚本结构

        Args:
            llm_text: LLM返回的文本
            topic: 主题
            style: 风格
            duration: 时长
            tone: 基调
            language_style: 语言风格
            framework: 框架

        Returns:
            dict: 脚本结构
        """
        # 尝试解析 JSON 格式
        try:
            # 查找 JSON 块
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', llm_text)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)

                # 检查是否有 sections 字段
                if "sections" in parsed and isinstance(parsed["sections"], list):
                    # 检查是否sections的第一项又是一个JSON字符串（双重嵌套）
                    if len(parsed["sections"]) > 0:
                        first_section = parsed["sections"][0]
                        # 如果第一项是字典且content是JSON字符串
                        if isinstance(first_section, dict) and "content" in first_section:
                            content = first_section["content"]
                            # 检查content是否又是JSON
                            if content.strip().startswith("```json"):
                                nested_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                                if nested_match:
                                    nested_json_str = nested_match.group(1)
                                    nested_parsed = json.loads(nested_json_str)
                                    # 使用嵌套的JSON
                                    if "sections" in nested_parsed:
                                        parsed = nested_parsed
                    
                    print(f"✅ JSON解析成功，共 {len(parsed.get('sections', []))} 个段落")
                    return {
                        "style": parsed.get("style", style),
                        "duration": parsed.get("duration", duration),
                        "tone": tone,
                        "language_style": language_style,
                        "topic": parsed.get("topic", topic),
                        "sections": parsed["sections"]
                    }
        except Exception as e:
            print(f"⚠️  JSON解析失败: {e}")

        # 如果 JSON 解析失败，按段落分割文本
        print("⚠️  JSON解析失败，尝试按段落分割")
        sections = []
        paragraphs = [p.strip() for p in llm_text.split('\n\n') if p.strip()]

        for para in paragraphs:
            # 过滤掉标记文本
            if para.startswith('```') or para.startswith('#') or para.startswith('**'):
                continue

            sections.append({
                "type": "paragraph",
                "content": para
            })

        # 如果没有段落，将整个文本作为一个段落
        if not sections:
            cleaned_text = re.sub(r'```[\s\S]*?```', '', llm_text)
            cleaned_text = re.sub(r'#+\s*', '', cleaned_text)
            cleaned_text = cleaned_text.strip()

            if cleaned_text:
                sections.append({
                    "type": "paragraph",
                    "content": cleaned_text
                })

        return {
            "style": style,
            "duration": duration,
            "tone": tone,
            "language_style": language_style,
            "topic": topic,
            "sections": sections
        }

    def _build_llm_prompt(self, topic, style, duration, tone, language_style, research, framework, analysis=None):
        """
        构建用于大模型生成的 prompt（使用深度分析结果）

        Args:
            topic: 主题
            style: 播客风格
            duration: 时长
            tone: 基调
            language_style: 语言风格
            research: 研究资料
            framework: 脚本框架
            analysis: 深度分析结果（新增）

        Returns:
            str: 大模型 prompt
        """
        # 风格描述
        style_descriptions = {
            "informative": "信息类 - 正式、结构化、信息密集，适合知识科普、技术讲解",
            "conversational": "对话类（理工男风格）- 理性、克制、不油腻，像和同事聊天，口语化、轻松、互动性强",
            "narrative": "叙事类 - 有故事感、引人入胜，有情节起伏，适合故事、历史、人物传记",
            "tech": "技术类 - 专业、深入、聚焦技术，技术术语准确、逻辑严谨"
        }

        # 收集研究资料
        key_points = research.get("key_points", [])
        sources = research.get("sources", [])

        research_section = ""
        if key_points:
            research_section += "\n## 参考资料要点\n"
            for i, kp in enumerate(key_points, 1):
                research_section += f"{i}. {kp}\n"

        if sources:
            research_section += "\n## 资料来源\n"
            for i, src in enumerate(sources, 1):
                research_section += f"{i}. {src}\n"

        if not research_section:
            research_section = "\n## 参考资料说明\n暂无具体资料，请根据主题自行搜索和整理相关内容。"

        # 构建深度分析部分（新增）
        analysis_section = ""
        if analysis:
            analysis_section = "\n## 深度分析结果\n"
            analysis_section += "以下是经过AI深度分析提取的关键元素，**必须在脚本中充分利用这些内容**：\n\n"

            # 核心观点
            if analysis.get("core_viewpoints"):
                analysis_section += "### 核心观点（必须融入脚本）\n"
                for i, vp in enumerate(analysis["core_viewpoints"], 1):
                    analysis_section += f"{i}. {vp}\n"
                analysis_section += "\n"

            # 案例和故事
            if analysis.get("cases_and_stories"):
                analysis_section += "### 案例和故事（必须详细讲述）\n"
                for case in analysis["cases_and_stories"]:
                    name = case.get("name", "未命名案例")
                    desc = case.get("description", "")
                    lesson = case.get("lesson", "")
                    analysis_section += f"- **{name}**: {desc}"
                    if lesson:
                        analysis_section += f" （启示：{lesson}）"
                    analysis_section += "\n"
                analysis_section += "\n"

            # 数据和统计
            if analysis.get("data_and_stats"):
                analysis_section += "### 数据和统计（必须引用）\n"
                for data in analysis["data_and_stats"]:
                    d = data.get("data", "")
                    src = data.get("source", "")
                    ctx = data.get("context", "")
                    analysis_section += f"- {d}"
                    if ctx:
                        analysis_section += f" - {ctx}"
                    if src:
                        analysis_section += f" （来源：{src}）"
                    analysis_section += "\n"
                analysis_section += "\n"

            # 类比和比喻
            if analysis.get("analogies_and_metaphors"):
                analysis_section += "### 类比和比喻（用于解释复杂概念）\n"
                for analogy in analysis["analogies_and_metaphors"]:
                    analysis_section += f"- {analogy}\n"
                analysis_section += "\n"

            # 争议点
            if analysis.get("controversial_points"):
                analysis_section += "### 争议点/反直觉观点（用于引发思考）\n"
                for point in analysis["controversial_points"]:
                    analysis_section += f"- {point}\n"
                analysis_section += "\n"

            # 听众痛点
            if analysis.get("audience_pain_points"):
                analysis_section += "### 听众痛点（用于建立共鸣）\n"
                for pain in analysis["audience_pain_points"]:
                    analysis_section += f"- {pain}\n"
                analysis_section += "\n"

            # 幽默元素
            if analysis.get("humor_elements"):
                analysis_section += "### 幽默元素（自然融入）\n"
                for humor in analysis["humor_elements"]:
                    analysis_section += f"- {humor}\n"
                analysis_section += "\n"

            # 金句
            if analysis.get("golden_quotes"):
                analysis_section += "### 金句（用于总结和升华）\n"
                for quote in analysis["golden_quotes"]:
                    analysis_section += f"- {quote}\n"
                analysis_section += "\n"

        # 构建 prompt
        prompt = f"""你是一位专业的播客脚本作家。请根据以下要求生成播客脚本。

# 播客主题
{topic}

# 播客风格
{style_descriptions.get(style, style)}

# 基调和语言风格
- 基调：{tone}
- 语言风格：{language_style}

# 预期时长
{duration}（short=3-5分钟，medium=10-15分钟，long=20-30分钟）
{research_section}
{analysis_section}# 脚本创作要求（重要！）

## 内容要求
1. **充分利用分析结果**：如果提供了深度分析，必须将核心观点、案例、数据、类比等内容融入脚本
2. **避免套话**：不要使用"这是一个非常有意思的话题"这种空洞的开场，直接切入主题
3. **具体化表达**：用具体的数据、案例、故事代替模糊的描述
4. **引发思考**：使用争议点、反直觉观点来吸引听众注意力

## 结构要求
1. **开场钩子**（必须）：用数据、故事、争议点或问题开场，不要用套话
2. **主体内容**：围绕核心观点展开，穿插案例、数据、类比
3. **互动环节**：至少包含1-2个向听众提问或引发思考的环节
4. **金句总结**：用简洁有力的金句结尾，易于传播

## 趣味性要求
1. **幽默元素**：自然融入1-2个幽默点（自嘲、吐槽、讽刺）
2. **类比比喻**：用生活化的类比解释复杂概念
3. **故事化**：用具体案例代替抽象理论
4. **情感共鸣**：触及听众的痛点和共鸣点

## 语言风格
1. **口语化**：避免书面语，使用自然流畅的口语
2. **互动性**：使用"我们"、"大家"、"你"等词汇
3. **节奏感**：长短句结合，避免平铺直叙
4. **风格匹配**：严格按照指定的风格（{style}）撰写
5. **⚠️ 避免重复连接词**：
   - 不要反复使用"还有"、"然后"等单一连接词
   - 连接词要多样化：其实、说实话、不过、但是、所以、因此、而且、另外、再说、值得一提的是等
   - 使用自然的过渡：用换行、停顿、提问等方式代替连接词
   - 避免每句话都用连接词开头，很多时候直接说就行

## 长度要求
- short: 800-1000字（3-5分钟）
- medium: 2000-3000字（10-15分钟）
- long: 4000-6000字（20-30分钟）

# 输出格式
请以JSON格式返回脚本：

{{
  "style": "{style}",
  "duration": "{duration}",
  "topic": "{topic}",
  "estimated_length": "预估字数",
  "sections": [
    {{
      "type": "段落类型（如：开场钩子、核心观点、案例分享、互动提问、金句总结等）",
      "title": "段落标题（可选）",
      "content": "段落内容，完整、详细、有深度、有温度"
    }}
  ]
}}

# 关键提醒
- ⚠️ **必须使用深度分析中的内容**（如果提供了分析结果）
- ⚠️ **不要使用模板化的开场和结尾**
- ⚠️ **每个段落必须有实质内容，不是占位符**
- ⚠️ **数据、案例、故事必须具体，不要模糊描述**

现在，请生成关于"{topic}"的播客脚本。"""

        return prompt

    def _check_script(self, script):
        """
        检查脚本质量

        Args:
            script: 脚本字典

        Returns:
            dict: 检查结果
        """
        try:
            from script_generator import ScriptChecker
            checker = ScriptChecker()
            check_results = checker.check_script(script)

            # 打印检查结果
            print(f"\n📊 脚本质量评分: {check_results['overall_score']:.1f}/100")
            print(f"   通畅性: {check_results['fluency']['score']} - {check_results['fluency']['status']}")
            print(f"   口语化: {check_results['colloquialism']['score']} - {check_results['colloquialism']['status']}")

            # 如果有建议，显示部分
            if check_results["suggestions"]:
                print(f"\n💡 改进建议（共{len(check_results['suggestions'])}条）:")
                for suggestion in check_results["suggestions"][:3]:  # 只显示前3条
                    print(f"   {suggestion}")

            return check_results
        except Exception as e:
            print(f"⚠️  脚本检查失败: {e}")
            return {"overall_score": 100, "fluency": {"score": 100}, "colloquialism": {"score": 100}, "suggestions": []}

    def _optimize_script(self, script, check_results):
        """
        优化脚本

        Args:
            script: 原始脚本
            check_results: 检查结果

        Returns:
            dict: 优化后的脚本
        """
        try:
            from script_generator import ScriptOptimizer
            optimizer = ScriptOptimizer()
            optimized_result = optimizer.optimize_script(script, check_results)

            if optimized_result.get("optimization_needed"):
                # 提取优化后的脚本
                optimized_script = {
                    "style": script.get("style"),
                    "duration": script.get("duration"),
                    "sections": []
                }

                # 安全检查：确保 optimized_sections 存在
                optimized_sections = optimized_result.get("optimized_sections", [])
                if not optimized_sections:
                    print("⚠️  优化结果缺少 optimized_sections，使用原始脚本")
                    return script

                for opt_section in optimized_sections:
                    optimized_script["sections"].append({
                        "type": opt_section.get("type", "paragraph"),
                        "content": opt_section.get("optimized", "")
                    })

                print(f"✨ 脚本已优化，共进行{len(optimized_result.get('changes', []))}处修改")

                # 保存优化后的脚本
                script_file = self.work_dir / f"script_optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(script_file, 'w', encoding='utf-8') as f:
                    json.dump(optimized_script, f, ensure_ascii=False, indent=2)

                return optimized_script
            else:
                return script
        except Exception as e:
            print(f"⚠️  脚本优化失败: {e}")
            return script

    def _generate_audio(self, script, voice):
        """
        根据脚本生成音频

        Args:
            script: 脚本字典
            voice: 使用的声音

        Returns:
            str: 音频文件路径
        """
        # 检查脚本是否有sections字段且内容不为空
        if "sections" in script and script["sections"]:
            # 检查每个 section 是否有 content
            valid_sections = []
            for section in script["sections"]:
                if isinstance(section, dict) and "content" in section and section["content"]:
                    valid_sections.append(section)
                else:
                    print(f"⚠️  跳过无效的 section: {section}")

            if valid_sections:
                # 合并所有段落的文本
                sections_text = [section["content"] for section in valid_sections]
                # 在段落之间保留明显的分隔，创造自然停顿
                full_text = "\n\n".join(sections_text)
            else:
                # 所有 section 都没有 content，使用主题生成默认文本
                topic = script.get("topic", "未知主题")
                print("⚠️  脚本 sections 缺少有效的 content，使用默认文本")
                full_text = f"""今天我们来聊聊{topic}。这是一个非常有意思的话题。

首先，让我们了解一下{topic}的背景。这个领域正在快速发展，越来越多的人开始关注它。

在接下来的时间里，我们会深入探讨{topic}的核心概念、实际应用以及未来的发展趋势。

希望今天的分享能给你带来一些启发和思考。让我们开始吧。"""
        else:
            # 脚本没有sections，使用主题生成默认文本
            topic = script.get("topic", "未知主题")
            full_text = f"""今天我们来聊聊{topic}。这是一个非常有意思的话题。

首先，让我们了解一下{topic}的背景。这个领域正在快速发展，越来越多的人开始关注它。

在接下来的时间里，我们会深入探讨{topic}的核心概念、实际应用以及未来的发展趋势。

希望今天的分享能给你带来一些启发和思考。让我们开始吧。"""

        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.work_dir / f"podcast_{timestamp}.mp3"

        # 动态导入TTS
        try:
            sys.path.insert(0, 'minimax-tts/scripts')
            import importlib.util
            spec = importlib.util.spec_from_file_location("tts", "minimax-tts/scripts/tts.py")
            tts_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tts_module)
            text_to_speech = tts_module.text_to_speech

            # 调用TTS生成音频
            text_to_speech(
                text=full_text,
                voice=voice,
                speed=self.config.get("default_speed", 1.1),
                vol=self.config.get("default_vol", 1.0),
                emotion=None,
                pitch=0,
                output=str(output_file)
            )
        except Exception as e:
            print(f"❌ 音频生成失败: {e}")
            # 如果TTS失败，创建一个占位符文件
            with open(output_file, 'w') as f:
                f.write(f"音频生成占位符\n文本长度: {len(full_text)} 字符\n错误信息: {str(e)}")

        return str(output_file)

    def _upload_to_tos(self, audio_file, topic):
        """
        上传音频到TOS

        Args:
            audio_file: 音频文件路径
            topic: 播客主题

        Returns:
            str: TOS URL
        """
        try:
            # 动态导入TOS客户端
            import importlib.util
            spec = importlib.util.spec_from_file_location("tos_client", "volcengine-tos/scripts/tos_client.py")
            tos_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tos_module)
            from tos.enum import HttpMethodType
            TosClientV2 = tos_module.TosClientV2

            # 加载TOS配置
            config = tos_module.load_config()
            if config is None:
                raise Exception("TOS配置未找到，请先配置TOS凭证")

            client = TosClientV2(
                ak=config['access_key'],
                sk=config['secret_key'],
                region=config['region'],
                endpoint=config['endpoint']
            )
            bucket = self.config.get("tos_bucket", "YOUR_TOS_BUCKET_NAME")

            # 生成对象键名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_topic = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in topic)
            key = f"audio/{safe_topic}_{timestamp}.mp3"

            # 上传文件
            print(f"正在上传到TOS: {bucket}/{key}")
            resp = client.put_object_from_file(
                bucket=bucket,
                key=key,
                file_path=audio_file,
                content_type='audio/mpeg',
            )
            print(f"✓ 上传成功! ETag: {resp.etag}")

            # 生成预签名URL（有效期24小时）
            result = client.pre_signed_url(
                http_method=HttpMethodType.Http_Method_Get,
                bucket=bucket,
                key=key,
                expires=86400,
            )

            return result.signed_url

        except Exception as e:
            print(f"❌ TOS上传失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _save_metadata(self, topic, script, research, audio_file, tos_url, framework=None, check_results=None):
        """
        保存播客元数据

        Args:
            topic: 主题
            script: 脚本字典
            research: 研究资料
            audio_file: 音频文件路径
            tos_url: TOS链接
            framework: 脚本框架（可选）
            check_results: 脚本检查结果（可选）

        Returns:
            dict: 元数据字典
        """
        metadata = {
            "topic": topic,
            "script": script,
            "research": research,
            "audio_file": audio_file,
            "tos_url": tos_url,
            "created_at": datetime.now().isoformat()
        }

        if framework:
            metadata["framework"] = framework
        if check_results:
            metadata["quality_check"] = {
                "overall_score": check_results["overall_score"],
                "fluency_score": check_results["fluency"]["score"],
                "colloquialism_score": check_results["colloquialism"]["score"],
                "suggestions_count": len(check_results["suggestions"])
            }

        # 保存到文件
        metadata_file = self.work_dir / f"metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return metadata

    def list_podcasts(self):
        """列出已创建的播客"""
        metadata_files = list(self.work_dir.glob("metadata_*.json"))
        podcasts = []

        for file in metadata_files:
            with open(file, 'r', encoding='utf-8') as f:
                podcasts.append(json.load(f))

        return podcasts

    def generate_audio_from_script(self, script_json_path, voice=None, use_bgm=True):
        """
        从JSON脚本文件生成音频

        Args:
            script_json_path: 脚本JSON文件路径
            voice: 使用的声音（可选）
            use_bgm: 是否使用背景音乐（默认启用）

        Returns:
            str: 音频文件路径
        """
        # 读取脚本
        with open(script_json_path, 'r', encoding='utf-8') as f:
            script = json.load(f)

        print(f"🎙️  开始生成音频...")
        print(f"📝 主题: {script.get('topic', 'Unknown')}")
        print(f"🎨 风格: {script.get('style', 'Unknown')}")

        # 生成音频
        audio_file = self._generate_audio(script, voice)

        # 混合背景音乐
        if use_bgm and self.bgm_file:
            mixed_audio_file = audio_file.replace(".mp3", "_with_bgm.mp3")
            mixed_audio_file = self._mix_with_bgm(audio_file, mixed_audio_file)
            if mixed_audio_file != audio_file:
                audio_file = mixed_audio_file

        # 上传到TOS
        print("☁️  上传到TOS...")
        tos_url = self._upload_to_tos(audio_file, script.get('topic', 'Unknown'))

        # 保存元数据
        print("💾 保存元数据...")
        metadata = self._save_metadata(
            topic=script.get('topic', 'Unknown'),
            script=script,
            research={},
            audio_file=audio_file,
            tos_url=tos_url
        )

        print(f"\n✅ 音频生成完成！")
        print(f"📄 音频文件: {audio_file}")
        print(f"🔗 TOS链接: {tos_url}")

        return metadata


def main():
    parser = argparse.ArgumentParser(description="播客工作室 - Podcast Studio")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 创建播客命令
    create_parser = subparsers.add_parser('create', help='创建新播客')
    create_parser.add_argument('topic', help='播客主题')
    create_parser.add_argument('--subtopics', nargs='+', help='子主题列表')
    create_parser.add_argument('--duration', choices=['short', 'medium', 'long'],
                              default='short', help='时长预期 (short=3-5min, medium=10-15min, long=20-30min)')
    create_parser.add_argument('--voice', help='声音选择')
    create_parser.add_argument('--style', choices=['informative', 'conversational', 'narrative', 'tech'],
                              default='informative', help='播客风格 (informative/conversational/narrative/tech)')
    create_parser.add_argument('--config', help='配置文件路径')
    create_parser.add_argument('--no-optimize', action='store_true', help='禁用脚本优化')
    create_parser.add_argument('--no-bgm', action='store_true', help='禁用背景音乐')
    create_parser.add_argument('--check-only', action='store_true', help='仅检查脚本，不生成音频')

    # 列出播客命令
    list_parser = subparsers.add_parser('list', help='列出已创建的播客')

    # 从脚本生成音频命令
    audio_parser = subparsers.add_parser('generate-audio', help='从JSON脚本文件生成音频')
    audio_parser.add_argument('script_file', help='脚本JSON文件路径')
    audio_parser.add_argument('--voice', help='声音选择')
    audio_parser.add_argument('--config', help='配置文件路径')
    audio_parser.add_argument('--no-bgm', action='store_true', help='禁用背景音乐')

    args = parser.parse_args()

    studio = PodcastStudio(config_file=getattr(args, 'config', None))

    if args.command == 'create':
        if args.check_only:
            # 仅检查模式
            print("🔍 脚本检查模式\n")

            # 收集资料
            research = studio._collect_research(args.topic, args.subtopics)

            # 生成框架
            framework = studio._generate_framework(args.topic, research, args.style, args.duration)

            # 生成脚本
            script = studio._generate_script_from_framework(framework, research)

            # 检查脚本
            check_results = studio._check_script(script)

            print(f"\n📊 最终评分: {check_results['overall_score']:.1f}/100")
            print("\n💡 所有改进建议:")
            for i, suggestion in enumerate(check_results.get("suggestions", []), 1):
                print(f"{i}. {suggestion}")
        else:
            result = studio.create_podcast(
                topic=args.topic,
                subtopics=args.subtopics,
                duration=args.duration,
                voice=args.voice,
                style=args.style,
                optimize=not args.no_optimize,
                use_bgm=not args.no_bgm
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == 'list':
        podcasts = studio.list_podcasts()
        print(f"📚 已创建的播客 ({len(podcasts)}个):")
        for i, pod in enumerate(podcasts, 1):
            print(f"\n{i}. {pod['topic']}")
            print(f"   风格: {pod['script']['style']}")
            print(f"   创建时间: {pod['created_at']}")
            print(f"   音频: {pod['audio_file']}")
            if pod['tos_url']:
                print(f"   TOS链接: {pod['tos_url']}")

    elif args.command == 'generate-audio':
        result = studio.generate_audio_from_script(
            script_json_path=args.script_file,
            voice=args.voice,
            use_bgm=not args.no_bgm
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
