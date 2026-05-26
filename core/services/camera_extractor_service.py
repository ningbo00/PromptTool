DETAIL_FIELDS = [
    ("linework", "线条风格"),
    ("shading", "明暗处理"),
    ("lighting", "打光方式"),
    ("palette", "色彩调性"),
    ("composition", "构图风格"),
    ("mood", "情绪基调"),
    ("motion", "动态描述"),
]


def build_extractor_detail(preset: dict) -> str:
    zh = preset.get("zh_details", {})
    keywords = preset.get("keywords", [])
    detail_lines = [
        f"【{preset['name']}】",
        f"✦ {preset.get('zh_summary', '')}",
        "",
    ]
    for key, label in DETAIL_FIELDS:
        detail_lines.append(f"{label}：{zh.get(key, preset.get(key, ''))}")
    detail_lines.extend([
        f"背景细节：{preset.get('background_detail', '')}",
        "",
        f"注入关键词（{len(keywords)} 个）：{', '.join(keywords)}",
    ])
    return "\n".join(detail_lines)


def count_keyword_matches(keywords: list[str], *existing_groups: list[str]) -> int:
    existing = [value for group in existing_groups for value in group]
    return sum(
        1
        for keyword in keywords
        for existing_keyword in existing
        if _is_match(keyword, existing_keyword)
    )


def matched_keywords_by_group(
    keywords: list[str],
    groups: dict[str, list[str]],
) -> dict[str, set[str]]:
    return {
        group_name: {
            existing_keyword
            for existing_keyword in existing_keywords
            for keyword in keywords
            if _is_match(keyword, existing_keyword)
        }
        for group_name, existing_keywords in groups.items()
    }


def append_keywords_to_extra(current: str, keywords: list[str]) -> str:
    keyword_text = ", ".join(keywords)
    current = current.strip()
    if not keyword_text:
        return current
    return f"{current}, {keyword_text}" if current else keyword_text


def _is_match(keyword: str, existing_keyword: str) -> bool:
    keyword = keyword.lower()
    existing_keyword = existing_keyword.lower()
    return existing_keyword in keyword or keyword in existing_keyword
