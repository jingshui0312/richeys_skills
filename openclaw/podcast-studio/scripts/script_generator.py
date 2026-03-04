#!/usr/bin/env python3
"""
脚本生成器和检查器 - Script Generator & Checker
功能：根据主题和资料生成脚本框架、检查脚本质量、优化脚本
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Tuple


class ScriptGenerator:
    """脚本生成器 - 智能生成脚本框架和内容"""

    def __init__(self):
        self.framework_templates = {
            "informative": {
                "sections": ["intro", "background", "core_concepts", "applications", "challenges", "case_studies", "future_trends", "practical_guidance", "outro"],
                "tone": "专业、清晰、结构化",
                "language_style": "正式但不过于学术，适合大众理解"
            },
            "conversational": {
                "sections": ["intro", "background", "personal_view", "discussion_points", "questions", "real_examples", "takeaways", "call_to_action", "outro"],
                "tone": "轻松、自然、像和朋友聊天",
                "language_style": "口语化、用词接地气"
            },
            "narrative": {
                "sections": ["intro_hook", "story_beginning", "story_development", "climax", "resolution", "reflection", "outro"],
                "tone": "有故事感、引人入胜",
                "language_style": "叙事性强、有画面感"
            },
            "tech": {
                "sections": ["intro", "technical_overview", "architecture", "implementation_details", "best_practices", "common_pitfalls", "advanced_topics", "tools_resources", "outro"],
                "tone": "专业、深入、聚焦技术",
                "language_style": "技术术语准确、逻辑严谨"
            }
        }

    def generate_framework(self, topic: str, research: Dict, style: str = "informative",
                          duration: str = "short") -> Dict:
        """
        根据主题和资料特征生成脚本框架

        Args:
            topic: 主题
            research: 研究资料
            style: 播客风格
            duration: 时长预期

        Returns:
            dict: 脚本框架
        """
        # 分析资料特征
        features = self._analyze_research_features(research)

        # 根据特征调整框架
        framework = self._adjust_framework(topic, features, style, duration)

        # 为每个段落生成指导性提示
        framework = self._add_section_guides(framework, topic, research, features)

        return framework

    def _analyze_research_features(self, research: Dict) -> Dict:
        """
        分析研究资料的特征

        Returns:
            dict: 特征分析结果
        """
        features = {
            "complexity": "medium",
            "content_type": "general",
            "target_audience": "general_public",
            "key_themes": [],
            "technical_depth": 0.5,
            "emotion_tone": "neutral"
        }

        key_points = research.get("key_points", [])
        sources = research.get("sources", [])

        # 分析内容复杂度
        technical_keywords = ["算法", "架构", "技术", "系统", "平台", "API", "框架", "模型"]
        tech_count = sum(1 for point in key_points for keyword in technical_keywords if keyword in point)

        if tech_count > 3:
            features["complexity"] = "high"
            features["technical_depth"] = 0.8
            features["content_type"] = "technical"
        elif tech_count == 0:
            features["complexity"] = "low"
            features["technical_depth"] = 0.2
            features["content_type"] = "general"

        # 提取关键主题
        features["key_themes"] = self._extract_themes(key_points)

        # 判断目标受众
        if features["complexity"] == "high":
            features["target_audience"] = "technical_audience"
        else:
            features["target_audience"] = "general_public"

        return features

    def _extract_themes(self, key_points: List[str]) -> List[str]:
        """从关键点中提取主题"""
        # 简单的关键词提取（实际可使用更高级的NLP方法）
        themes = []
        theme_keywords = {
            "技术": ["技术", "算法", "系统", "平台"],
            "商业": ["商业", "市场", "应用", "价值"],
            "社会": ["社会", "影响", "改变", "趋势"],
            "未来": ["未来", "发展", "趋势", "展望"]
        }

        for theme, keywords in theme_keywords.items():
            if any(keyword in point for point in key_points for keyword in keywords):
                themes.append(theme)

        return themes if themes else ["general"]

    def _adjust_framework(self, topic: str, features: Dict, style: str, duration: str) -> Dict:
        """
        根据特征调整脚本框架
        """
        base_template = self.framework_templates.get(style, self.framework_templates["informative"])
        sections = list(base_template["sections"])

        # 根据时长调整段落数量
        if duration == "short":
            # 短播客：简化段落，聚焦核心
            if style == "conversational":
                sections = ["intro", "background", "discussion_points", "takeaways", "outro"]
            elif style == "informative":
                sections = ["intro", "background", "core_concepts", "future_trends", "outro"]
            elif style == "narrative":
                sections = ["intro_hook", "story_beginning", "story_development", "resolution", "outro"]
            elif style == "tech":
                sections = ["intro", "technical_overview", "implementation_details", "best_practices", "outro"]

        elif duration == "medium":
            # 中等时长：完整框架
            pass  # 使用默认sections

        elif duration == "long":
            # 长播客：增加深入探讨环节
            if style == "conversational":
                sections.extend(["deep_dive", "q&a"])
            elif style == "informative":
                sections.extend(["deep_analysis", "expert_insights"])
            elif style == "tech":
                sections.extend(["advanced_topics", "code_examples"])

        # 根据特征调整
        if features["complexity"] == "high" and style == "conversational":
            # 高复杂度对话风格：增加解释环节
            sections.insert(len(sections)//2, "simplification")

        return {
            "style": style,
            "duration": duration,
            "tone": base_template["tone"],
            "language_style": base_template["language_style"],
            "sections": sections,
            "features": features,
            "topic": topic
        }

    def _add_section_guides(self, framework: Dict, topic: str, research: Dict, features: Dict) -> Dict:
        """
        为每个段落添加生成指导
        """
        section_guides = {
            "intro": f"开场白：吸引听众注意，引入主题「{topic}」，简要说明今天要聊的内容。避免冗长客套，直接切入主题。",
            "background": f"背景介绍：解释{topic}的起源和发展历程，让听众建立基础认知。不要讲得太技术化，用通俗的方式。",
            "core_concepts": f"核心概念：解释{topic}的关键概念和原理。用比喻或例子帮助理解，避免堆砌专业术语。",
            "applications": f"实际应用：介绍{topic}在现实中的应用场景，最好有具体案例。让听众感受到这个主题的实际价值。",
            "challenges": f"挑战和问题：讨论{topic}面临的挑战和局限。保持客观，不要回避困难，但也要展示机遇。",
            "case_studies": f"案例分析：深入1-2个具体案例，展示{topic}的实际效果。案例要具体，有细节。",
            "future_trends": f"未来趋势：分析{topic}的发展方向和可能的变化。基于事实进行合理推测，不要天马行空。",
            "practical_guidance": f"实践建议：给听众提供可操作的建议。不要说『你可以』，直接说具体怎么做。",
            "outro": f"总结结尾：总结今天的核心观点，留下思考空间，自然结束。",
            # 对话风格特有
            "personal_view": f"个人观点：分享你对{topic}的真实看法和体验。真诚一点，不要说套话。",
            "discussion_points": f"讨论要点：提出值得思考的问题或争议点，引发听众思考。",
            "questions": f"常见问题：解答关于{topic}的常见疑问，帮助听众扫除障碍。",
            "real_examples": f"真实例子：分享你亲身经历或观察到的具体例子，增强说服力。",
            "takeaways": f"核心收获：列出今天的3-5个关键收获，帮助听众记住重点。",
            "call_to_action": f"行动号召：鼓励听众尝试或深入了解{topic}。给出具体的下一步建议。",
            # 叙事风格特有
            "intro_hook": f"开场钩子：用一个有趣的事实、问题或场景引入，抓住听众注意力。",
            "story_beginning": f"故事开端：讲述{topic}的起源故事，要有时间、地点、人物等细节。",
            "story_development": f"故事发展：描述{topic}的发展历程和关键转折点，要有冲突和解决。",
            "climax": f"高潮部分：讲述{topic}发展中的关键时刻或重大突破，要有戏剧张力。",
            "resolution": f"结局部分：描述{topic}现在的状态和成果，要有圆满感或反思。",
            "reflection": f"反思总结：从故事中提取 lessons learned，引发听众思考。",
            # 技术风格特有
            "technical_overview": f"技术概览：从技术角度解释{topic}的核心原理和架构。准确但不过于深奥。",
            "architecture": f"架构设计：详细说明{topic}的系统架构和组件关系。可以用类比帮助理解。",
            "implementation_details": f"实现细节：讲解{topic}的关键实现技术和算法。重点讲思路，不要陷入代码细节。",
            "best_practices": f"最佳实践：总结使用{topic}的最佳实践和模式。要有经验之谈。",
            "common_pitfalls": f"常见陷阱：列出使用{topic}时容易犯的错误和如何避免。要有实用价值。",
            "advanced_topics": f"进阶话题：介绍{topic}的深入主题和前沿研究。适合有一定基础的听众。",
            "tools_resources": f"工具资源：推荐学习{topic}的工具、文档、课程等资源。要有实用性和可及性。",
            # 扩展段落
            "deep_dive": f"深度探讨：选择一个核心观点进行深入分析。要有独特见解。",
            "q&a": f"问答环节：模拟回答听众可能提出的问题。要切中痛点。",
            "deep_analysis": f"深度分析：对{topic}的某个方面进行多维度分析。要有深度。",
            "expert_insights": f"专家观点：引用或转述专家对{topic}的看法。增加权威性。",
            "simplification": f"简化解释：用最通俗的方式解释{topic}的复杂概念。帮助听众跨越理解门槛。",
            "code_examples": f"代码示例：展示{topic}的实际代码实现或配置。代码要有注释和说明。"
        }

        # 为每个段落添加指导
        framework["section_guides"] = {}
        for section in framework["sections"]:
            framework["section_guides"][section] = section_guides.get(
                section,
                f"关于{topic}的{section}部分"
            )

        return framework

    def generate_script_from_framework(self, framework: Dict, research: Dict) -> Dict:
        """
        根据框架生成脚本内容（调用LLM）

        Args:
            framework: 脚本框架
            research: 研究资料

        Returns:
            dict: 生成的脚本
        """
        # 这里应该是调用LLM生成实际内容
        # 由于我们在Python环境中，暂时返回框架结构
        # 实际使用时会通过Codex调用LLM生成

        script = {
            "style": framework["style"],
            "duration": framework["duration"],
            "sections": []
        }

        for section_type in framework["sections"]:
            guide = framework["section_guides"].get(section_type, "")
            script["sections"].append({
                "type": section_type,
                "guide": guide,
                "content": "",  # 待LLM生成
                "generated_at": datetime.now().isoformat()
            })

        return script


class ScriptChecker:
    """脚本检查器 - 检查脚本通畅性和口语化"""

    def __init__(self):
        # 通畅性检查规则
        self.fluency_rules = {
            "sentence_length": {
                "max_avg_length": 25,  # 平均句长上限
                "max_single_length": 50,  # 单句长度上限
                "warning": "句子过长，可能影响收听体验"
            },
            "transition_words": {
                "required": ["但是", "然后", "所以", "因此", "不过", "另外"],
                "warning": "段落间缺乏过渡词，可能影响流畅性"
            },
            "repetition": {
                "max_repeat_distance": 100,  # 重复词的最大间隔
                "warning": "用词重复过多，影响表达丰富性"
            }
        }

        # 口语化检查规则
        self.colloquialism_rules = {
            "written_style_patterns": [
                r"因此，",
                r"然而，",
                r"综上所述，",
                r"由此可见，",
                r"故而，",
                r"基于此，"
            ],
            "good_colloquial_patterns": [
                "所以",
                "然后",
                "但是",
                "不过",
                "简单来说",
                "举个例子",
                "你想啊"
            ],
            "warning": "书面语表达过于正式，不够口语化"
        }

    def check_script(self, script: Dict) -> Dict:
        """
        检查脚本质量

        Args:
            script: 脚本字典

        Returns:
            dict: 检查结果
        """
        full_text = self._combine_sections(script)

        check_results = {
            "fluency": self._check_fluency(full_text),
            "colloquialism": self._check_colloquialism(full_text),
            "overall_score": 0,
            "suggestions": [],
            "checked_at": datetime.now().isoformat()
        }

        # 计算总体评分（简单加权）
        fluency_score = check_results["fluency"]["score"]
        colloquialism_score = check_results["colloquialism"]["score"]
        check_results["overall_score"] = (fluency_score + colloquialism_score) / 2

        # 生成改进建议
        check_results["suggestions"] = self._generate_suggestions(check_results)

        return check_results

    def _combine_sections(self, script: Dict) -> str:
        """合并所有段落文本"""
        sections = script.get("sections", [])
        return " ".join([section.get("content", "") for section in sections])

    def _check_fluency(self, text: str) -> Dict:
        """检查通畅性"""
        issues = []
        score = 100

        # 检查句子长度
        sentences = re.split(r'[。！？；\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            avg_length = sum(len(s) for s in sentences) / len(sentences)

            if avg_length > self.fluency_rules["sentence_length"]["max_avg_length"]:
                issues.append({
                    "type": "avg_sentence_length",
                    "value": avg_length,
                    "limit": self.fluency_rules["sentence_length"]["max_avg_length"],
                    "message": self.fluency_rules["sentence_length"]["warning"]
                })
                score -= 20

            # 检查超长句子
            long_sentences = [s for s in sentences if len(s) > self.fluency_rules["sentence_length"]["max_single_length"]]
            if long_sentences:
                issues.append({
                    "type": "long_sentences",
                    "count": len(long_sentences),
                    "examples": long_sentences[:3],  # 最多显示3个例子
                    "message": f"发现{len(long_sentences)}个过长句子"
                })
                score -= 15

        # 检查过渡词
        transition_count = sum(1 for word in self.fluency_rules["transition_words"]["required"] if word in text)
        if transition_count < 2:
            issues.append({
                "type": "lack_transitions",
                "count": transition_count,
                "message": self.fluency_rules["transition_words"]["warning"]
            })
            score -= 10

        # 检查重复（简化版）
        words = re.findall(r'[\w]+', text)
        word_count = {}
        for word in words:
            if len(word) > 2:  # 忽略单字和两字词
                word_count[word] = word_count.get(word, 0) + 1

        # 找出重复次数过多的词
        repeated_words = [(word, count) for word, count in word_count.items() if count > 5]
        if repeated_words:
            issues.append({
                "type": "word_repetition",
                "words": repeated_words[:5],
                "message": "部分词汇使用次数过多"
            })
            score -= 10

        return {
            "score": max(0, score),
            "issues": issues,
            "status": "good" if score >= 80 else "needs_improvement" if score >= 60 else "poor"
        }

    def _check_colloquialism(self, text: str) -> Dict:
        """检查口语化"""
        issues = []
        score = 100

        # 检查书面语表达
        written_patterns = self.colloquialism_rules["written_style_patterns"]
        found_written = []

        for pattern in written_patterns:
            if re.search(pattern, text):
                found_written.append(pattern)

        if found_written:
            issues.append({
                "type": "written_language",
                "patterns": found_written,
                "message": f"发现{len(found_written)}个书面语表达，建议改为口语"
            })
            score -= len(found_written) * 10

        # 检查是否使用好的口语表达
        good_patterns = self.colloquialism_rules["good_colloquial_patterns"]
        found_good = sum(1 for pattern in good_patterns if pattern in text)

        if found_good < 3:
            issues.append({
                "type": "lack_colloquial",
                "count": found_good,
                "message": "口语化表达偏少，可以增加一些自然的连接词"
            })
            score -= 10

        # 检查是否有"我们"、"大家"等拉近听众距离的表达
        audience_words = ["我们", "大家", "你", "咱们"]
        audience_count = sum(text.count(word) for word in audience_words)
        if audience_count < 3:
            issues.append({
                "type": "lack_audience_connection",
                "count": audience_count,
                "message": "与听众的互动表达偏少，建议增加'我们'、'大家'等词汇"
            })
            score -= 10

        return {
            "score": max(0, score),
            "issues": issues,
            "status": "good" if score >= 80 else "needs_improvement" if score >= 60 else "poor"
        }

    def _generate_suggestions(self, check_results: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []

        fluency_issues = check_results["fluency"]["issues"]
        colloquial_issues = check_results["colloquialism"]["issues"]

        # 基于通畅性问题生成建议
        for issue in fluency_issues:
            if issue["type"] == "avg_sentence_length":
                suggestions.append(
                    "💡 句子平均长度偏长，建议将长句拆分成2-3个短句。口语播客中，短句更容易理解。"
                )
            elif issue["type"] == "long_sentences":
                suggestions.append(
                    f"💡 发现{issue['count']}个过长句子（超过{self.fluency_rules['sentence_length']['max_single_length']}字），"
                    "建议在适当时机断句，或调整表达方式。"
                )
            elif issue["type"] == "lack_transitions":
                suggestions.append(
                    "💡 段落间缺乏过渡词，建议增加'然后'、'但是'、'所以'等连接词，让表达更连贯。"
                )
            elif issue["type"] == "word_repetition":
                words_str = "、".join([f"{word}({count}次)" for word, count in issue["words"][:3]])
                suggestions.append(
                    f"💡 部分词汇使用次数过多：{words_str}。建议用同义词替换，丰富表达。"
                )

        # 基于口语化问题生成建议
        for issue in colloquial_issues:
            if issue["type"] == "written_language":
                patterns_str = "、".join(issue["patterns"][:3])
                suggestions.append(
                    f"💡 发现书面语表达：{patterns_str}。建议改为口语表达，例如'因此'→'所以'、'然而'→'但是'。"
                )
            elif issue["type"] == "lack_colloquial":
                suggestions.append(
                    "💡 口语化表达偏少，建议增加'然后'、'但是'、'简单来说'、'举个例子'等自然连接词。"
                )
            elif issue["type"] == "lack_audience_connection":
                suggestions.append(
                    "💡 与听众的互动表达偏少，建议增加'我们'、'大家'、'你'等词汇，拉近与听众的距离。"
                )

        # 总体建议
        if not suggestions:
            suggestions.append("✅ 脚本质量良好，可以直接用于音频生成！")
        else:
            suggestions.append(
                "\n📝 改进方向：\n"
                "1. 朗读几遍，感受自然流畅度\n"
                "2. 用口语化表达替换书面语\n"
                "3. 适当增加停顿和语气词\n"
                "4. 加入个人观点和真实案例"
            )

        return suggestions


class ScriptOptimizer:
    """脚本优化器 - 根据检查结果优化脚本"""

    def __init__(self):
        self.replacement_rules = {
            # 书面语 → 口语化替换
            "因此，": "所以，",
            "然而，": "但是，",
            "综上所述，": "简单来说，",
            "由此可见，": "可以看出来，",
            "故而，": "所以，",
            "基于此，": "基于这个，",
            "此外，": "另外，",
            "再者，": "而且，",
            "进而，": "然后，",
            "换言之，": "换句话说，",
            "换言之，": "也就是说，"
        }

    def optimize_script(self, script: Dict, check_results: Dict) -> Dict:
        """
        优化脚本

        Args:
            script: 原始脚本
            check_results: 检查结果

        Returns:
            dict: 优化后的脚本
        """
        optimized_script = {
            "original": script,
            "optimized_sections": [],
            "changes": [],
            "optimized_at": datetime.now().isoformat()
        }

        # 如果评分已经很高，不需要优化
        if check_results["overall_score"] >= 85:
            optimized_script["optimization_needed"] = False
            optimized_script["message"] = "脚本质量良好，无需优化"
            return optimized_script

        optimized_script["optimization_needed"] = True

        # 逐段优化
        for section in script.get("sections", []):
            original_content = section.get("content", "")
            optimized_content, changes = self._optimize_section(original_content, check_results)

            optimized_script["optimized_sections"].append({
                "type": section.get("type"),
                "original": original_content,
                "optimized": optimized_content,
                "changes": changes
            })

            optimized_script["changes"].extend(changes)

        return optimized_script

    def _optimize_section(self, content: str, check_results: Dict) -> Tuple[str, List[str]]:
        """优化单个段落"""
        if not content:
            return content, []

        changes = []
        optimized = content

        # 1. 替换书面语为口语化表达
        for written, spoken in self.replacement_rules.items():
            if written in optimized:
                optimized = optimized.replace(written, spoken)
                changes.append(f"替换「{written}」→「{spoken}」")

        # 2. 拆分过长句子（简单实现）
        fluency_issues = check_results["fluency"]["issues"]
        long_sentence_issues = [i for i in fluency_issues if i["type"] == "long_sentences"]

        if long_sentence_issues:
            # 在适当位置拆分长句（在逗号或分号处）
            sentences = re.split(r'([。！？])', optimized)
            new_sentences = []
            for i in range(0, len(sentences)-1, 2):
                sentence = sentences[i] + sentences[i+1]  # 句子 + 标点
                if len(sentence) > 40:
                    # 尝试拆分
                    parts = re.split(r'，|；|、', sentence)
                    if len(parts) > 1:
                        new_sentences.extend([part + "，" for part in parts[:-1]])
                        new_sentences.append(parts[-1] + sentences[i+1])
                        changes.append("拆分长句")
                    else:
                        new_sentences.append(sentence)
                else:
                    new_sentences.append(sentence)
            optimized = "".join(new_sentences)

        # 3. 增加过渡词
        if "lack_transitions" in [i["type"] for i in fluency_issues]:
            # 简单的添加逻辑（实际应该更智能）
            optimized = self._add_transitions(optimized)
            changes.append("增加过渡词")

        # 4. 增加听众互动表达
        colloquial_issues = check_results["colloquialism"]["issues"]
        if "lack_audience_connection" in [i["type"] for i in colloquial_issues]:
            if "我们" not in optimized and "大家" not in optimized:
                # 在适当位置加入互动表达
                if optimized.strip():
                    first_sentence_end = re.search(r'[。！？]', optimized)
                    if first_sentence_end:
                        pos = first_sentence_end.end()
                        optimized = optimized[:pos] + " 我们都知道，" + optimized[pos:]
                        changes.append("增加听众互动表达")

        return optimized, changes

    def _add_transitions(self, text: str) -> str:
        """添加过渡词（智能版 - 避免重复）"""
        # 过渡词列表（移除"还有"，避免重复）
        transition_words = [
            "其实，",      # 转折说明
            "说实话，",    # 真诚表达
            "不过，",      # 轻微转折
            "说到这儿，",  # 话题衔接
            "你想想，",    # 互动思考
            "更重要的是，", # 强调重点
            "有意思的是，", # 引起兴趣
            "换句话说，"   # 解释说明
        ]
        
        sentences = re.split(r'([。！？])', text)
        result = []
        counter = 0
        used_transitions = set()  # 跟踪已使用的过渡词，避免重复
        
        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i] + sentences[i+1]
            result.append(sentence)
            counter += 1
            
            # 每隔3-4句添加一个过渡词（不是每个换行）
            if counter % 4 == 0 and i + 2 < len(sentences):
                # 选择未使用的过渡词
                available = [t for t in transition_words if t not in used_transitions]
                if not available:
                    # 如果都用过了，重置
                    used_transitions.clear()
                    available = transition_words
                
                trans_word = available[len(result) % len(available)]
                used_transitions.add(trans_word)
                result.append(trans_word)
        
        return "".join(result)


def main():
    """测试函数"""
    # 示例使用
    generator = ScriptGenerator()
    checker = ScriptChecker()
    optimizer = ScriptOptimizer()

    # 测试框架生成
    research = {
        "topic": "人工智能",
        "key_points": ["深度学习算法", "应用场景", "技术挑战", "未来趋势"],
        "sources": ["Wikipedia", "TechCrunch"]
    }

    framework = generator.generate_framework(
        topic="人工智能的发展趋势",
        research=research,
        style="conversational",
        duration="medium"
    )

    print("=== 脚本框架 ===")
    print(json.dumps(framework, ensure_ascii=False, indent=2))

    # 测试检查
    script = {
        "style": "conversational",
        "sections": [
            {
                "type": "intro",
                "content": "大家好，今天我们聊聊人工智能。然而，这是一个非常重要的话题。我们都需要了解它。"
            }
        ]
    }

    print("\n=== 脚本检查 ===")
    check_results = checker.check_script(script)
    print(json.dumps(check_results, ensure_ascii=False, indent=2))

    # 测试优化
    print("\n=== 脚本优化 ===")
    optimized = optimizer.optimize_script(script, check_results)
    print(json.dumps(optimized, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
