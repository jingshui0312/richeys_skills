#!/usr/bin/env python3
"""
播客工作室 - Podcast Studio
功能：收集资料、设计脚本、生成音频、上传到TOS
新增：背景音乐混合功能
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 添加技能路径以便导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class PodcastStudio:
    """播客工作室主类"""

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
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
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

        # 2. 生成脚本框架
        print("🏗️  生成脚本框架...")
        framework = self._generate_framework(topic, research, style, duration)

        # 3. 生成脚本内容
        print("✍️  生成脚本...")
        script = self._generate_script_from_framework(framework, research)

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

    def _generate_script_from_framework(self, framework, research):
        """
        根据框架生成脚本内容 - 调用大模型生成

        Args:
            framework: 脚本框架（由 ScriptGenerator 动态生成）
            research: 研究资料

        Returns:
            dict: 脚本内容，由大模型智能生成
        """
        style = framework.get("style", "informative")
        topic = framework.get("topic", "")
        duration = framework.get("duration", "short")
        tone = framework.get("tone", "")
        language_style = framework.get("language_style", "")

        # 构建大模型 prompt
        prompt = self._build_llm_prompt(topic, style, duration, tone, language_style, research, framework)

        # 将 prompt 保存到文件，供大模型使用
        prompt_file = self.work_dir / f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)

        print(f"\n📝 脚本生成 Prompt 已保存到: {prompt_file}")
        print(f"💡 请将以下内容发送给大模型进行脚本生成:\n")
        print("=" * 60)
        print(prompt)
        print("=" * 60)

        # 返回待生成的脚本结构（实际内容由大模型填充）
        script = {
            "style": style,
            "duration": duration,
            "tone": tone,
            "language_style": language_style,
            "topic": topic,
            "research": research,
            "framework": framework,
            "prompt_file": str(prompt_file),
            "created_at": datetime.now().isoformat(),
            "needs_llm_generation": True
        }

        # 保存脚本结构到文件
        script_file = self.work_dir / f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)

        return script

    def _build_llm_prompt(self, topic, style, duration, tone, language_style, research, framework):
        """
        构建用于大模型生成的 prompt

        Args:
            topic: 主题
            style: 播客风格
            duration: 时长
            tone: 基调
            language_style: 语言风格
            research: 研究资料
            framework: 脚本框架

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

# 脚本要求
1. 结构灵活：不要使用固定的段落类型（如 intro/background/main/outro），根据主题内容自然分段
2. 内容相关：所有内容必须围绕主题展开，不要使用通用的套话模板
3. 风格匹配：严格按照指定的风格要求撰写，每种风格有不同的语气和表达方式
4. 长度适中：根据预期时长控制内容长度，short约800-1000字，medium约2000-3000字
5. 口语化：避免过于书面的表达，使用自然、流畅的口语，适合播播
6. 互动性：适当使用"我们"、"大家"等词汇，拉近与听众的距离

{research_section}

# 输出格式
请以JSON格式返回脚本，格式如下：

{{
  "style": "{style}",
  "duration": "{duration}",
  "topic": "{topic}",
  "estimated_length": "预估字数",
  "sections": [
    {{
      "type": "段落类型（如：开场、背景、核心观点、案例分享、总结等，根据主题自定义）",
      "title": "段落标题（可选）",
      "content": "段落内容，完整、详细、与主题高度相关"
    }}
  ]
}}

注意事项：
- sections 数量和类型由你根据主题内容决定，不限制
- 每个 section 的 content 必须是完整的段落内容，不是占位符
- 不要使用固定的模板内容，根据主题真实情况生成
- 如果有具体的案例、数据、故事，请详细描述

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

                for opt_section in optimized_result["optimized_sections"]:
                    optimized_script["sections"].append({
                        "type": opt_section["type"],
                        "content": opt_section["optimized"]
                    })

                print(f"✨ 脚本已优化，共进行{len(optimized_result['changes'])}处修改")

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
        # 合并所有段落的文本
        sections_text = [section["content"] for section in script["sections"]]
        # 在段落之间保留明显的分隔，创造自然停顿
        full_text = "\n\n".join(sections_text)

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
