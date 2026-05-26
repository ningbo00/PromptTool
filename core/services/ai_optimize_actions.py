LENGTH_HINTS = {
    "简短": "输出长度控制在 50 词以内，保留最核心关键词。",
    "中等": "输出长度在 50-150 词之间，内容详略适中。",
    "详细": "输出长度在 150 词以上，尽量丰富细节描写。",
}


def build_ai_optimize_messages(
    action: str,
    original: str,
    direction: str = "",
    length: str = "中等",
) -> list[dict]:
    length_hint = LENGTH_HINTS.get(length, "")
    builders = {
        "optimize_current": _optimize_current,
        "zh_to_en": _zh_to_en,
        "generate_variants": _generate_variants,
        "score": _score,
        "extract_keywords": _extract_keywords,
        "recommend_negative": _recommend_negative,
        "compliance_check": _compliance_check,
    }
    if action not in builders:
        raise ValueError(f"Unknown AI optimize action: {action}")
    return builders[action](original=original, direction=direction, length_hint=length_hint)


def _optimize_current(original: str, direction: str, length_hint: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是一个专业的 AI 绘画 Prompt 优化专家。"
                "用户会给你一段英文 Prompt，你需要按照用户的要求对其进行优化。"
                f"{length_hint}"
                "只输出优化后的 Prompt 文本，不要有任何解释、标题或额外说明。"
            ),
        },
        {
            "role": "user",
            "content": f"优化要求：{direction}\n\n原始 Prompt：\n{original}",
        },
    ]


def _zh_to_en(original: str, direction: str, length_hint: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是一个专业的 AI 绘画/摄影 Prompt 生成专家。"
                "用户会给你一段中文场景/角色/风格描述，"
                "你需要将其转化为适合 AI 图像生成的英文 Prompt（逗号分隔关键词格式），"
                "包含主体描述、场景环境、光线风格、画面质量词。"
                f"{length_hint}"
                "只输出英文 Prompt，不要有任何解释或中文。"
            ),
        },
        {"role": "user", "content": original},
    ]


def _generate_variants(original: str, direction: str, length_hint: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是专业 AI 绘画 Prompt 优化专家。"
                "用户会给你一段英文 Prompt 和优化要求，生成 3 个不同风格的变体版本。"
                f"{length_hint}"
                "必须严格按如下格式输出，不要有任何额外说明或解释：\n"
                "[变体1]\n（第一个变体的完整 Prompt 内容）\n"
                "[变体2]\n（第二个变体的完整 Prompt 内容）\n"
                "[变体3]\n（第三个变体的完整 Prompt 内容）"
            ),
        },
        {
            "role": "user",
            "content": f"优化要求：{direction}\n\n原始 Prompt：\n{original}",
        },
    ]


def _score(original: str, direction: str, length_hint: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是 AI 绘画 Prompt 专家评审。用户会给你一段英文 Prompt，"
                "请评估其质量，同时检测词汇矛盾。"
                "输出格式严格为（用中文）：\n"
                "评分: X/10\n"
                "改进建议:\n1. ...\n2. ...\n3. ...\n"
                "矛盾检测:\n"
                "（若无明显矛盾写：✅ 无明显矛盾；若有矛盾则列出："
                "❌ [矛盾词A] 与 [矛盾词B] 存在冲突 → 建议：...）"
            ),
        },
        {"role": "user", "content": f"请评分并给出改进建议：\n{original}"},
    ]


def _extract_keywords(original: str, direction: str, length_hint: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是 Prompt 语义分析助手。请从用户提供的 Prompt 中提取关键词，"
                "输出 10-15 个最核心的英文关键词，用逗号分隔，不要解释。"
            ),
        },
        {"role": "user", "content": original},
    ]


def _recommend_negative(original: str, direction: str, length_hint: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是 AI 图像生成负面词专家。根据用户 Prompt 推荐适合排除的负面词，"
                "按分组输出，覆盖画质、人体/主体、构图、风格冲突和平台常见问题。"
            ),
        },
        {"role": "user", "content": original},
    ]


def _compliance_check(original: str, direction: str, length_hint: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是 AI 图像/视频 Prompt 合规检查助手。请检测用户 Prompt 中可能导致平台拒绝生成的"
                "违规词、敏感内容或高风险描述，并给出替代表达建议。"
            ),
        },
        {"role": "user", "content": original},
    ]
